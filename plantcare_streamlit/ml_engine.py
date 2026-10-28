"""
TensorFlow/Keras Inference Engine for Plant Disease Detection
Offline prediction engine with MobileNetV2 architecture and curated care catalog.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from PIL import Image
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[1]
os.environ.setdefault("KERAS_HOME", str(BASE_DIR / ".keras"))
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
MODELS_DIR = BASE_DIR / "models"
CATALOG_PATH = BASE_DIR / "server" / "catalog.json"

_MODEL = None
_LABELS = None
_CATALOG = None


def get_model():
    """Lazy load the Keras model once."""
    global _MODEL
    if _MODEL is None:
        import tensorflow as tf
        keras_path = MODELS_DIR / "plant_disease_model.keras"
        h5_path = MODELS_DIR / "plant_disease_model.h5"
        
        target = keras_path if keras_path.exists() else h5_path
        if not target.exists():
            raise FileNotFoundError(f"Model file not found at {target}. Run training first.")
        
        _MODEL = tf.keras.models.load_model(str(target), compile=False)
    return _MODEL


def get_labels():
    """Load class label index mappings."""
    global _LABELS
    if _LABELS is None:
        labels_path = MODELS_DIR / "class_labels.json"
        if not labels_path.exists():
            raise FileNotFoundError(f"Class labels not found at {labels_path}")
        with open(labels_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            # Keys might be strings in json, convert to int
            _LABELS = {int(k): v for k, v in raw.items()}
    return _LABELS


def get_catalog():
    """Load disease care information catalog."""
    global _CATALOG
    if _CATALOG is None:
        if not CATALOG_PATH.exists():
            _CATALOG = []
        else:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                _CATALOG = json.load(f)
    return _CATALOG


def lookup_care(class_id: str) -> dict:
    """Find care and symptoms matching the detected class."""
    catalog = get_catalog()
    for item in catalog:
        if class_id in item.get("class_ids", []):
            return item
    # Fallback default
    parts = class_id.split("___")
    plant = parts[0].replace("_", " ") if parts else "Plant"
    condition = parts[1].replace("_", " ") if len(parts) > 1 else "Unknown"
    return {
        "plant": plant,
        "condition": condition,
        "symptoms": ["Visible discoloration, spotting, or leaf surface changes."],
        "care": ["Isolate affected leaves and monitor plant growth.", "Avoid overwatering the foliage."],
        "prevention": ["Maintain proper soil drainage and adequate sunlight."],
        "sources": [{"title": "Agricultural Extension Service", "url": "https://extension.umn.edu"}]
    }


def predict_image(image_input) -> dict:
    """
    Accepts PIL Image or bytes, preprocesses to 224x224, and predicts via Keras.
    Returns:
        dict: {
            'class_id': str,
            'plant': str,
            'condition': str,
            'is_healthy': bool,
            'confidence': float, # 0.0 - 100.0
            'symptoms': list[str],
            'care': list[str],
            'prevention': list[str],
            'sources': list[dict]
        }
    """
    if isinstance(image_input, (str, Path)):
        img = Image.open(image_input)
    elif isinstance(image_input, bytes):
        import io
        img = Image.open(io.BytesIO(image_input))
    elif isinstance(image_input, Image.Image):
        img = image_input
    else:
        raise ValueError("Invalid image input format. Pass PIL Image, bytes, str or Path.")

    # 1. Preprocessing (Resize & RGB conversion)
    img_rgb = img.convert("RGB").resize((224, 224), Image.Resampling.LANCZOS)
    img_array = np.array(img_rgb, dtype=np.float32)
    img_batch = np.expand_dims(img_array, axis=0)  # Shape (1, 224, 224, 3)

    # 2. Model Prediction
    model = get_model()
    labels = get_labels()

    # The saved bundle already includes its training-time 1/255 rescaling.
    # Do not normalize a second time or change preprocessing without retraining.
    preds = np.asarray(model(img_batch, training=False))[0]
    if preds.shape != (len(labels),) or not np.all(np.isfinite(preds)):
        raise ValueError("The model output does not match its ordered labels.")
    if list(labels) != list(range(len(labels))) or np.any(preds < 0) or not np.isclose(preds.sum(), 1.0, atol=0.01):
        raise ValueError("Invalid label order or classifier output.")
    top_idx = int(np.argmax(preds))
    confidence = float(preds[top_idx]) * 100.0
    class_id = labels.get(top_idx, "Unknown")

    # 3. Disease Information Lookup
    info = lookup_care(class_id)
    is_healthy = "healthy" in class_id.lower() or "healthy" in info.get("condition", "").lower()

    return {
        "class_id": class_id,
        "slug": info.get("slug", class_id.lower().replace("___", "-").replace("_", "-")),
        "plant": info.get("plant", class_id.split("___")[0].replace("_", " ")),
        "condition": info.get("condition", class_id.split("___")[1].replace("_", " ") if "___" in class_id else class_id),
        "scientific_name": info.get("scientific_name"),
        "severity": info.get("severity", "Normal"),
        "is_healthy": is_healthy,
        "confidence": round(confidence, 1),
        "symptoms": info.get("symptoms", []),
        "care": info.get("care", []),
        "prevention": info.get("prevention", []),
        "sources": info.get("sources", []),
        "decision_policy": "calibrated-mobilenet-v2",
        "score_type": "softmax_confidence",
        "calibrated": False,
        "probabilities": {labels[i]: round(float(preds[i]) * 100, 1) for i in range(len(labels))}
    }
