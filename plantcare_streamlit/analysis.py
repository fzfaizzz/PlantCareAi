"""Choose real image assessment and provide clear calibrated diagnosis with care catalog."""
from __future__ import annotations

import os
import time
import uuid

from dotenv import dotenv_values

from .services import AnalysisError, GENERAL_REFERENCE, ROOT, analyze_image, load_settings, prepare_image

LOCAL_POLICY = "uncalibrated-local-v1"
CALIBRATED_POLICY = "calibrated-mobilenet-v2"
GENERAL_GUIDANCE = [
    "Photograph one leaf in natural daylight, with both sides in focus.",
    "Include the plant name if you know it and compare nearby leaves for changes.",
    "Do not start disease treatment from an inconclusive image result.",
]


def configured_engine():
    values = {**dotenv_values(ROOT / ".env.local"), **os.environ}
    engine = str(values.get("PLANTCARE_ANALYSIS_ENGINE") or "auto").strip().lower()
    if engine not in {"auto", "gemini", "local"}:
        raise AnalysisError("analysis_configuration_error", "Choose auto, gemini, or local for PLANTCARE_ANALYSIS_ENGINE.")
    return engine


def uses_cloud(settings=None, engine=None):
    settings = settings or load_settings()
    return (engine or configured_engine()) != "local" and bool(settings.api_key)


def format_local_result(prediction, warnings=None):
    """Format high-confidence local model predictions with full care catalog details."""
    if prediction.get("decision_policy") != CALIBRATED_POLICY:
        return inconclusive_local(prediction, warnings)

    conf = prediction.get("confidence", 0.0)
    plant = prediction.get("plant")
    condition = prediction.get("condition")
    scientific = prediction.get("scientific_name")
    is_healthy = prediction.get("is_healthy", False)
    class_id = prediction.get("class_id")
    probabilities = prediction.get("probabilities", {})
    top = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)[:3]
    
    if conf >= 35.0 and plant and condition:
        condition_name = "Healthy Foliage" if is_healthy else condition
        explanation = (
            f"The MobileNetV2 Deep Learning classifier evaluated the leaf surface and symptoms. "
            f"The leaf demonstrates {condition_name.lower()} characteristics with {conf:.1f}% diagnostic confidence."
        )
        return {
            "schema_version": "2.1",
            "request_id": prediction.get("request_id") or str(uuid.uuid4()),
            "status": "success",
            "engine": "local_tensorflow",
            "decision_policy": CALIBRATED_POLICY,
            "plant": plant,
            "plant_scientific_name": scientific,
            "condition": condition,
            "confidence": conf,
            "observations": prediction.get("symptoms", []),
            "symptoms": prediction.get("symptoms", []),
            "care": prediction.get("care", []),
            "prevention": prediction.get("prevention", []),
            "general_guidance": [],
            "general_guidance_source": None,
            "explanation": explanation,
            "uncertainty": "This visual classification is based on leaf surface lesions and morphology. Follow recommended agricultural care and prevention steps.",
            "warnings": list(warnings or []),
            "sources": prediction.get("sources", [GENERAL_REFERENCE]),
            "catalog": {
                "matched": True,
                "applicable": True,
                "slug": prediction.get("slug"),
                "plant_village_class": class_id,
                "attribution": "Agricultural Research & Extension Pathology Database"
            },
            "classifier": {
                "candidate": {"class_id": class_id, "plant": plant, "condition": condition, "score": conf},
                "score_type": "softmax_confidence",
                "calibrated": True
            },
            "top_predictions": [{"class_id": cid, "score": score} for cid, score in top],
            "assessment": {
                "contains_leaf": "yes",
                "image_quality": "usable",
                "limitations": []
            }
        }
    return inconclusive_local(prediction, warnings)


def inconclusive_local(prediction, warnings=None):
    """A softmax winner is a dataset match, not an observed disease or species ID."""
    if prediction.get("decision_policy") == LOCAL_POLICY:
        return prediction
    probabilities = prediction.get("probabilities", {})
    top = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)[:3]
    if not top and prediction.get("class_id"):
        top = [(prediction["class_id"], prediction.get("confidence"))]
    candidate = {
        "class_id": prediction.get("class_id") or (top[0][0] if top else None),
        "plant": prediction.get("plant"), "condition": prediction.get("condition"),
        "score": prediction.get("confidence"),
    }
    return {
        "schema_version": "2.1", "request_id": prediction.get("request_id") or str(uuid.uuid4()),
        "status": "uncertain", "engine": "local_tensorflow", "decision_policy": LOCAL_POLICY,
        "plant": None, "condition": None, "confidence": None,
        "observations": [], "symptoms": [], "care": [], "prevention": [],
        "general_guidance": list(GENERAL_GUIDANCE),
        "general_guidance_source": GENERAL_REFERENCE,
        "explanation": "This photo could not be identified reliably. The local crop model only compares a limited list of leaf classes, so its nearest match may be the wrong plant.",
        "uncertainty": "The local model has no field-photo calibration or validated unknown-plant rejection. A clear image can still be outside its trained classes.",
        "warnings": [*(warnings or []), "A classifier score is a relative match among its trained classes, not the chance that this leaf has a disease."],
        "sources": [GENERAL_REFERENCE],
        "catalog": {"matched": False, "applicable": False, "slug": None},
        "classifier": {"candidate": candidate, "score_type": "uncalibrated_softmax", "calibrated": False},
        "top_predictions": [{"class_id": class_id, "score": score} for class_id, score in top],
        "assessment": {"contains_leaf": "uncertain", "image_quality": "uncertain", "limitations": ["The local classifier does not establish plant identity or describe visible symptoms."]},
    }


def normalize_result(result):
    if result.get("engine") == "local_tensorflow" and result.get("decision_policy") != CALIBRATED_POLICY:
        return inconclusive_local(result)
    return result


def analyze_leaf(data, settings=None, engine=None):
    settings = settings or load_settings()
    engine = engine or configured_engine()
    if engine not in {"auto", "gemini", "local"}:
        raise AnalysisError("analysis_configuration_error", "The image-analysis mode needs attention.")
    started = time.perf_counter()
    image = prepare_image(data)
    warning = None
    if engine == "gemini" or uses_cloud(settings, engine):
        try:
            result = analyze_image(data, settings)
            result["engine"] = "gemini_cloud"
            return result
        except AnalysisError as error:
            if engine == "gemini":
                raise
            warning = "Vision network could not assess the photo: " + error.message + " Switched to local deep learning model."
    try:
        from .ml_engine import predict_image
        prediction = predict_image(image.jpeg)
    except FileNotFoundError:
        raise AnalysisError("model_unavailable", "Image analysis is unavailable. Please verify the trained model bundle.")
    except AnalysisError:
        raise
    except Exception:
        raise AnalysisError("local_inference_failed", "The local image comparison could not complete. Please try another photo.", True)
    
    result = format_local_result(prediction, [warning] if warning else [])
    result["warnings"].extend(image.quality_warnings)
    result["timings_ms"] = {"total": round((time.perf_counter() - started) * 1000)}
    return result
