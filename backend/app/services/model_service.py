import asyncio
import hashlib
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from app.core.errors import PublicError

logger = logging.getLogger("plantcare.model")


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def split_label(label: str) -> tuple[str, str]:
    if "___" not in label:
        return label.replace("_", " "), "Unknown"
    plant, condition = label.split("___", 1)
    plant = plant.replace("_(maize)", "").replace("_(including_sour)", "").replace(",_bell", " bell").replace("_", " ")
    return plant, condition.replace("_", " ").strip().title()


class ModelService:
    def __init__(self, settings):
        self.settings = settings
        self.model = None
        self.labels = []
        self.metadata = {}
        self.state = "not_initialized"
        self.error_code = None
        self._gate = threading.BoundedSemaphore(settings.model_concurrency)
        self._executor = ThreadPoolExecutor(max_workers=settings.model_concurrency, thread_name_prefix="plantcare-inference")

    @property
    def ready(self):
        return self.model is not None and self.state == "ready"

    def load(self):
        paths = (self.settings.model_path, self.settings.class_labels_path, self.settings.model_metadata_path)
        if not all(path.is_file() for path in paths):
            self.state, self.error_code = "unavailable", "model_artifacts_missing"
            return
        try:
            labels = json.loads(paths[1].read_text(encoding="utf-8"))
            metadata = json.loads(paths[2].read_text(encoding="utf-8"))
            if not isinstance(labels, list) or len(labels) < 2 or len(labels) > 1000:
                raise ValueError("Invalid ordered labels.")
            if not all(isinstance(item, str) and 0 < len(item) <= 200 for item in labels) or len(set(labels)) != len(labels):
                raise ValueError("Labels must be unique ordered strings.")
            if metadata.get("labels_sha256") != sha256_file(paths[1]) or metadata.get("model_sha256") != sha256_file(paths[0]):
                raise ValueError("Artifact checksum mismatch.")
            required = {"input_shape": [224, 224, 3], "preprocessing": "mobilenet_v2",
                        "normalization_in_model": True, "output_type": "probabilities",
                        "resize_policy": "bilinear_stretch"}
            if any(metadata.get(key) != value for key, value in required.items()):
                raise ValueError("Preprocessing contract mismatch.")
            if not isinstance(metadata.get("model_version"), str) or not metadata["model_version"]:
                raise ValueError("Model version is required.")
            policy = metadata.get("decision_policy", {})
            if policy.get("validated"):
                if not all(isinstance(policy.get(key), (int, float)) and 0 <= policy[key] <= 1 for key in ("min_score", "min_margin")):
                    raise ValueError("Invalid validation policy.")
                if policy.get("selection_split") != "validation":
                    raise ValueError("Decision thresholds must come from validation.")
            # Only local, operator-provided, checksum-matching artifacts are loaded.
            import tensorflow as tf
            tf.config.threading.set_inter_op_parallelism_threads(1)
            tf.config.threading.set_intra_op_parallelism_threads(2)
            model = tf.keras.models.load_model(paths[0], compile=False, safe_mode=True)
            if tuple(model.input_shape[1:]) != (224, 224, 3) or tuple(model.output_shape[1:]) != (len(labels),):
                raise ValueError("Model shape does not match labels.")
            self.model, self.labels, self.metadata = model, labels, metadata
            self.state, self.error_code = "ready", None
        except ImportError:
            self.state, self.error_code = "unavailable", "tensorflow_not_installed"
        except Exception as exc:
            self.state, self.error_code = "invalid", "model_bundle_invalid"
            logger.warning("Model initialization rejected: %s", type(exc).__name__)

    def _predict(self, array):
        try:
            result = np.asarray(self.model(array[None, ...], training=False).numpy(), dtype=np.float64)[0]
            if result.shape != (len(self.labels),) or not np.all(np.isfinite(result)):
                raise ValueError("Invalid model output.")
            if np.any(result < 0) or np.any(result > 1) or abs(float(result.sum()) - 1) > 0.01:
                raise ValueError("Expected probabilities; refusing invalid output or double-softmax.")
            return result
        finally:
            self._gate.release()

    async def predict(self, array):
        if not self.ready:
            raise PublicError(503, "model_unavailable", "The trained model is unavailable. The operator must install and verify a trained model bundle.")
        if not self._gate.acquire(blocking=False):
            raise PublicError(503, "model_busy", "The model is processing another image. Please try again shortly.", 2)
        try:
            # A cancelled HTTP request does not release the native-inference gate early.
            # The worker owns it until TensorFlow actually finishes.
            future = asyncio.get_running_loop().run_in_executor(self._executor, self._predict, array)
        except BaseException:
            self._gate.release()
            raise
        try:
            return await asyncio.shield(future)
        except asyncio.CancelledError:
            def consume_error(done):
                if not done.cancelled():
                    done.exception()
            future.add_done_callback(consume_error)
            raise
        except Exception:
            raise PublicError(500, "inference_failed", "The image could not be analyzed. Please try another clear photo.")

    def public_info(self):
        info = {
            "ready": self.ready, "state": self.state, "error_code": self.error_code,
            "model_version": self.metadata.get("model_version"),
            "supported_labels": self.labels if self.ready else [],
            "preprocessing": {key: self.metadata.get(key) for key in
                              ("input_shape", "preprocessing", "normalization_in_model", "resize_policy", "output_type")},
            "evaluation": self.metadata.get("evaluation"),
            "decision_policy": self.metadata.get("decision_policy"),
            "limitations": [
                "This is a closed-set crop classifier. Scores do not prove species identity or exclude unknown conditions.",
                "Dataset-test evaluation is separate from real phone/field-photo validation.",
                "A healthy-class match does not rule out all diseases, pests, or nutrient issues.",
            ],
        }
        return info

    def close(self):
        self._executor.shutdown(wait=False, cancel_futures=True)
