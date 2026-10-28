"""Test-only plumbing fixtures. These are not trained crop classifiers."""
import io
import sys
from pathlib import Path
import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(BACKEND_ROOT.parent))

from app.core.config import Settings
from app.main import create_app
from app.schemas.analysis import GeminiResult


def image_bytes(fmt="JPEG", size=(128, 128)):
    pixels = np.random.default_rng(7).integers(30, 220, (*size[::-1], 3), dtype=np.uint8)
    image = Image.fromarray(pixels)
    output = io.BytesIO()
    image.save(output, format=fmt)
    return output.getvalue()


@pytest.fixture
def valid_image():
    return image_bytes()


@pytest.fixture
def settings(tmp_path):
    return Settings(_env_file=None, app_env="test", model_path=tmp_path / "missing.keras",
                    class_labels_path=tmp_path / "labels.json", model_metadata_path=tmp_path / "metadata.json",
                    rate_limit_per_minute=120)


class PlumbingClassifier:
    """Only exercises response/integration mechanics; never used by the application."""
    ready = True
    state = "ready"
    error_code = None
    labels = ["Tomato___Early_blight", "Tomato___healthy"]
    metadata = {
        "model_version": "TEST-PLUMBING-NOT-TRAINED",
        "decision_policy": {"validated": True, "selection_split": "validation", "min_score": 0.8, "min_margin": 0.1},
    }

    def __init__(self, scores=None, validated=True):
        self.scores = np.array(scores if scores is not None else [0.92, 0.08])
        self.metadata = {**self.metadata, "decision_policy": {**self.metadata["decision_policy"], "validated": validated}}

    def load(self):
        pass

    def close(self):
        pass

    def public_info(self):
        return {"ready": True, "supported_labels": self.labels}

    async def predict(self, array):
        assert array.shape == (224, 224, 3)
        assert array.dtype == np.float32
        return self.scores


class PlumbingGemini:
    state = "disabled"

    def __init__(self, result=None):
        self.result = result or GeminiResult(status="disabled")

    async def start(self):
        pass

    async def close(self):
        pass

    def health(self):
        return {"enabled": False, "state": "disabled", "sends_image_to_google": False}

    async def assess(self, image):
        assert image[:2] == b"\xff\xd8"
        return self.result


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as test_client:
        yield test_client


@pytest.fixture
def plumbing_client(settings):
    with TestClient(create_app(settings, model_service=PlumbingClassifier(), gemini_service=PlumbingGemini())) as test_client:
        yield test_client
