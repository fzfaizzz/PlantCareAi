import asyncio
import hashlib
import json
import threading
from types import SimpleNamespace
import numpy as np
import pytest
from app.core.errors import PublicError
from app.services.model_service import ModelService


def test_missing_bundle_never_imports_tensorflow(settings):
    model = ModelService(settings)
    model.load()
    assert model.ready is False
    assert model.error_code == "model_artifacts_missing"
    model.close()


def write_bundle(settings, **metadata_changes):
    settings.model_path.write_bytes(b"not-a-trained-checkpoint")
    settings.class_labels_path.write_text(json.dumps(["Tomato___healthy", "Tomato___Early_blight"]))
    metadata = {
        "model_version": "invalid-test-only",
        "input_shape": [224, 224, 3], "preprocessing": "mobilenet_v2",
        "normalization_in_model": True, "output_type": "probabilities",
        "resize_policy": "bilinear_stretch",
        "model_sha256": hashlib.sha256(settings.model_path.read_bytes()).hexdigest(),
        "labels_sha256": hashlib.sha256(settings.class_labels_path.read_bytes()).hexdigest(),
    }
    metadata.update(metadata_changes)
    settings.model_metadata_path.write_text(json.dumps(metadata))


@pytest.mark.parametrize("changes", [
    {"model_sha256": "wrong"}, {"labels_sha256": "wrong"},
    {"normalization_in_model": False}, {"output_type": "logits"},
    {"input_shape": [128, 128, 3]}, {"decision_policy": {"validated": True, "min_score": 0.8, "min_margin": 0.1}},
])
def test_corrupt_or_inconsistent_bundle_rejected_before_tensorflow(settings, changes):
    write_bundle(settings, **changes)
    model = ModelService(settings)
    model.load()
    assert model.ready is False
    assert model.error_code == "model_bundle_invalid"
    model.close()


def test_duplicate_label_mapping_rejected(settings):
    write_bundle(settings)
    settings.class_labels_path.write_text(json.dumps(["duplicate", "duplicate"]))
    model = ModelService(settings)
    model.load()
    assert model.error_code == "model_bundle_invalid"
    model.close()


def test_cancel_does_not_free_native_worker(settings):
    started, finish = threading.Event(), threading.Event()
    model = ModelService(settings)
    model.labels = ["a", "b"]
    model.state = "ready"

    def blocked_call(array, training=False):
        started.set()
        assert finish.wait(3)
        return SimpleNamespace(numpy=lambda: np.array([[0.8, 0.2]]))

    model.model = blocked_call

    async def scenario():
        task = asyncio.create_task(model.predict(np.zeros((224, 224, 3), dtype=np.float32)))
        await asyncio.to_thread(started.wait, 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        with pytest.raises(PublicError) as error:
            await model.predict(np.zeros((224, 224, 3), dtype=np.float32))
        assert error.value.code == "model_busy"
        finish.set()
        await asyncio.sleep(0.05)

    try:
        asyncio.run(scenario())
    finally:
        finish.set()
        model.close()


def test_real_trained_artifact_acceptance_is_separate():
    import os
    from pathlib import Path
    from app.core.config import Settings
    bundle = os.getenv("PLANTCARE_REAL_MODEL_BUNDLE")
    if not bundle:
        pytest.skip("No genuine trained/evaluated production artifact supplied; plumbing tests are not accuracy evidence.")
    directory = Path(bundle)
    settings = Settings(_env_file=None, app_env="test", model_path=directory / "plant_disease_model.keras",
                        class_labels_path=directory / "class_labels.json", model_metadata_path=directory / "model_metadata.json")
    model = ModelService(settings)
    try:
        model.load()
        assert model.ready, model.error_code
        assert model.metadata.get("training_completed") is True
        assert model.metadata.get("evaluation")
    finally:
        model.close()
