import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from conftest import PlumbingClassifier, PlumbingGemini
from app.main import create_app


def test_health_ready_and_missing_model(client, valid_image):
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["model"]["ready"] is False
    assert health.json()["gemini"]["enabled"] is False
    assert client.get("/api/ready").status_code == 503
    response = client.post("/api/analyze", files={"image": ("leaf.jpg", valid_image, "image/jpeg")})
    assert response.status_code == 503
    assert response.json()["code"] == "model_unavailable"
    assert response.headers["x-request-id"] == response.json()["request_id"]
    assert "tensorflow" not in __import__("sys").modules


@pytest.mark.parametrize("payload,code", [(b"", "empty_image"), (b"not-an-image", "invalid_image"), (b"\xff\xd8\xff\xe0broken", "invalid_image")])
def test_invalid_images_are_not_model_results(client, payload, code):
    response = client.post("/api/analyze", files={"image": ("leaf.jpg", payload, "image/jpeg")})
    assert response.status_code == 422
    assert response.json()["code"] == code
    assert "confidence" not in response.json()


def test_one_file_required_and_no_arbitrary_urls(client, valid_image):
    response = client.post("/api/analyze", files={"wrong": ("leaf.jpg", valid_image, "image/jpeg")})
    assert response.status_code == 422
    response = client.post("/api/analyze", json={"url": "https://example.com/leaf.jpg"})
    assert response.status_code == 415
    response = client.post("/api/analyze", files=[("image", ("a.jpg", valid_image)), ("image", ("b.jpg", valid_image))])
    assert response.status_code == 400


def test_oversized_body_is_rejected_before_parse(settings):
    settings.max_upload_mb = 1
    with TestClient(create_app(settings)) as test_client:
        response = test_client.post("/api/analyze", content=b"x" * (settings.max_request_bytes + 1),
                                    headers={"Content-Type": "multipart/form-data; boundary=x"})
        assert response.status_code == 413
        assert response.json()["code"] == "image_too_large"


def test_decode_pixel_limit_and_small_image(client):
    image = Image.new("RGB", (8, 8))
    output = io.BytesIO()
    image.save(output, "PNG")
    response = client.post("/api/analyze", files={"image": ("leaf.png", output.getvalue())})
    assert response.status_code == 422
    assert response.json()["code"] == "poor_quality_image"


def test_plumbing_contract_not_accuracy(plumbing_client, valid_image):
    response = plumbing_client.post("/api/analyze", files={"image": ("leaf.jpg", valid_image, "image/jpeg")})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["schema_version"] == "1.0"
    assert body["status"] == "success"
    assert body["model"]["version"] == "TEST-PLUMBING-NOT-TRAINED"
    assert body["model"]["predicted_class"] == "Tomato___Early_blight"
    assert body["confidence"] == 92
    assert body["top_predictions"][0]["score"] == 0.92
    assert body["sources"][0]["url"].startswith("https://extension.umn.edu/")
    assert body["gemini"]["status"] == "disabled"
    assert body["timings_ms"]["inference"] >= 0


def test_actual_decoded_format_not_filename(plumbing_client, valid_image):
    response = plumbing_client.post("/api/analyze", files={"image": ("disguised.exe", valid_image, "application/octet-stream")})
    assert response.status_code == 200


def test_rate_limit_and_cors(settings, valid_image):
    settings.rate_limit_per_minute = 1
    with TestClient(create_app(settings, model_service=PlumbingClassifier(), gemini_service=PlumbingGemini())) as test_client:
        response = test_client.post("/api/analyze", files={"image": ("leaf.jpg", valid_image)},
                                    headers={"Origin": "http://localhost:5173"})
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
        limited = test_client.post("/api/analyze", files={"image": ("leaf.jpg", valid_image)})
        assert limited.status_code == 429
        assert int(limited.headers["retry-after"]) > 0
        denied = test_client.options("/api/analyze", headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "POST"})
        assert denied.status_code == 400


def test_catalog_educational_mapping(client, plumbing_client):
    absent = client.get("/api/plants").json()
    assert all(not item["model_supported"] for item in absent["items"])
    items = plumbing_client.get("/api/plants").json()["items"]
    assert next(item for item in items if item["slug"] == "tomato-early-blight")["model_supported"]
    powdery = plumbing_client.get("/api/plants/grape-powdery-mildew").json()
    assert powdery["class_ids"] == [] and powdery["model_supported"] is False
    assert plumbing_client.get("/api/plants/not-a-condition").status_code == 404


def test_gemini_key_not_exposed(client):
    text = client.get("/api/health").text
    assert "api_key" not in text.lower()
    assert "Images are processed temporarily" in text
