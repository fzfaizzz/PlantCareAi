from fastapi.testclient import TestClient
from conftest import PlumbingClassifier, PlumbingGemini
from app.main import create_app
from app.schemas.analysis import GeminiAssessment, GeminiResult


def result_with(settings, valid_image, classifier=None, assessment=None, gemini_status="success"):
    result = GeminiResult(status=gemini_status, assessment=assessment)
    with TestClient(create_app(settings, model_service=classifier or PlumbingClassifier(),
                               gemini_service=PlumbingGemini(result))) as client:
        response = client.post("/api/analyze", files={"image": ("leaf.jpg", valid_image)})
        assert response.status_code == 200, response.text
        return response.json()


def assessment(**changes):
    base = dict(contains_leaf="yes", image_quality="usable",
                plant_hypothesis={"common_name": "Tomato", "scientific_name": None},
                visible_symptoms=["Leaf spots"], condition_hypothesis=None, limitations=[])
    return GeminiAssessment.model_validate({**base, **changes})


def test_low_scores_and_unvalidated_policy(settings, valid_image):
    low = result_with(settings, valid_image, PlumbingClassifier([0.55, 0.45]), gemini_status="disabled")
    assert low["status"] == "uncertain"
    unvalidated = result_with(settings, valid_image, PlumbingClassifier(validated=False), gemini_status="disabled")
    assert unvalidated["status"] == "uncertain"


def test_unknown_tree_not_forced_to_crop(settings, valid_image):
    body = result_with(settings, valid_image, assessment=assessment(plant_hypothesis={"common_name": "Neem", "scientific_name": "Azadirachta indica"}))
    assert body["status"] == "uncertain"
    assert body["gemini"]["assessment"]["plant_hypothesis"]["common_name"] == "Neem"
    assert "outside" in body["uncertainty"]
    assert body["top_predictions"][0]["class_id"] == "Tomato___Early_blight"


def test_plant_and_condition_disagreement(settings, valid_image):
    plant = result_with(settings, valid_image, assessment=assessment(plant_hypothesis={"common_name": "Potato", "scientific_name": None}))
    assert plant["status"] == "uncertain"
    condition = result_with(settings, valid_image, assessment=assessment(condition_hypothesis="Late blight"))
    assert condition["status"] == "uncertain" and "conflict" in condition["uncertainty"]


def test_nonleaf_is_explicitly_unsupported(settings, valid_image):
    body = result_with(settings, valid_image, assessment=assessment(contains_leaf="no", plant_hypothesis=None))
    assert body["status"] == "unsupported_image"
    assert body["confidence"] is None
    assert not body["care"] and not body["sources"]


def test_poor_or_missing_assessment_is_not_confirmation(settings, valid_image):
    poor = result_with(settings, valid_image, assessment=assessment(image_quality="poor"))
    assert poor["status"] == "uncertain"
    absent = result_with(settings, valid_image, gemini_status="timeout")
    assert absent["gemini"]["status"] == "timeout"
    assert any("not independent confirmation" in warning for warning in absent["warnings"])
