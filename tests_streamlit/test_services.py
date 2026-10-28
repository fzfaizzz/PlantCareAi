"""Pure Python tests; fake providers validate plumbing, not diagnosis accuracy."""
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from plantcare_streamlit.services import (
    AnalysisError, LeafAssessment, Settings, analyze_image, assemble_result,
    load_settings, prepare_image,
)


def picture(format="JPEG", size=(128, 128), color=None):
    image = Image.new("RGB", size, color or "green")
    if color is None:
        pixels = image.load()
        for y in range(size[1]):
            for x in range(size[0]):
                pixels[x, y] = ((x * 13 + y * 7) % 255, (x * 3 + y * 11) % 255, (x * 17 + y * 5) % 255)
    output = io.BytesIO()
    image.save(output, format)
    image.close()
    return output.getvalue()


def assessment(**changes):
    data = {
        "contains_leaf": "yes", "image_quality": "usable",
        "plant": {"common_name": "Tomato", "scientific_name": "Solanum lycopersicum"},
        "possible_condition": "Early Blight", "visible_symptoms": ["Brown spots"],
        "limitations": ["Only one view of the leaf."],
    }
    return {**data, **changes}


class Provider:
    def __init__(self, data=None, error=None, finish_reason="STOP"):
        self.data = assessment() if data is None else data
        self.error = error
        self.finish_reason = finish_reason
        self.calls = []
        self.models = SimpleNamespace(generate_content=self.generate)

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        text = json.dumps(self.data) if isinstance(self.data, dict) else self.data
        return SimpleNamespace(candidates=[SimpleNamespace(finish_reason=self.finish_reason)], text=text)


@pytest.mark.parametrize("format", ["JPEG", "PNG", "WEBP"])
def test_actual_decode_and_metadata_free_normalization(format):
    result = prepare_image(picture(format))
    with Image.open(io.BytesIO(result.jpeg)) as clean:
        assert clean.format == "JPEG" and clean.mode == "RGB"
        assert clean.size == (128, 128)
        assert not clean.getexif()
    assert result.width == 128 and result.height == 128


@pytest.mark.parametrize("data,code", [
    (b"", "empty_image"), (b"not a photo", "invalid_image"),
    (b"\xff\xd8\xffbroken", "invalid_image"), (b"x" * (10 * 1024 * 1024 + 1), "image_too_large"),
], ids=["empty", "text", "corrupt-jpeg", "oversized"])
def test_invalid_and_oversized_files(data, code):
    with pytest.raises(AnalysisError) as error:
        prepare_image(data)
    assert error.value.code == code


def test_actual_format_not_filename_and_unsupported_formats():
    assert prepare_image(picture()).jpeg.startswith(b"\xff\xd8")
    with pytest.raises(AnalysisError) as error:
        prepare_image(picture("BMP"))
    assert error.value.code == "unsupported_image_format"


def test_tiny_pixel_heavy_and_bomb_images(monkeypatch):
    with pytest.raises(AnalysisError) as error:
        prepare_image(picture(size=(8, 8)))
    assert error.value.code == "poor_quality_image"
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 100)
    with pytest.raises(AnalysisError) as error:
        prepare_image(picture())
    assert error.value.code == "image_dimensions_exceeded"


def test_real_multiframe_webp_rejected():
    output = io.BytesIO()
    a, b = Image.new("RGB", (80, 80), "green"), Image.new("RGB", (80, 80), "red")
    a.save(output, "WEBP", save_all=True, append_images=[b], duration=100, loop=0)
    with pytest.raises(AnalysisError) as error:
        prepare_image(output.getvalue())
    assert error.value.code == "animated_image"


def test_exif_orientation_and_sensitive_metadata_removed():
    image = Image.new("RGB", (80, 120), "green")
    exif = Image.Exif()
    exif[274] = 6
    exif[270] = "sensitive embedded text"
    output = io.BytesIO()
    image.save(output, "JPEG", exif=exif)
    result = prepare_image(output.getvalue())
    with Image.open(io.BytesIO(result.jpeg)) as clean:
        assert clean.size == (120, 80)
        assert not clean.getexif()


def test_rgba_resize_and_quality_flags():
    result = prepare_image(picture(size=(1800, 900)))
    with Image.open(io.BytesIO(result.jpeg)) as clean:
        assert clean.size == (1600, 800)
    assert prepare_image(picture(color="green")).quality_warnings
    output = io.BytesIO()
    Image.new("RGBA", (80, 80), (0, 200, 0, 0)).save(output, "PNG")
    result = prepare_image(output.getvalue())
    with Image.open(io.BytesIO(result.jpeg)) as clean:
        assert clean.getpixel((0, 0))[0] > 240


def test_real_service_request_contract_and_no_invented_scores():
    provider = Provider()
    result = analyze_image(picture(), Settings(api_key="TEST-NOT-REAL", model="gemini-3.1-flash-lite"), client=provider)
    assert result["schema_version"] == "2.0"
    assert result["status"] == "success"
    assert result["confidence"] is None
    assert result["catalog"]["plant_village_class"] == "Tomato___Early_blight"
    assert result["observations"] == ["Brown spots"]
    assert result["provider"] == {"name": "gemini", "model": "gemini-3.1-flash-lite"}
    assert result["sources"][0]["url"].startswith("https://extension.umn.edu/")
    assert "model" not in result and "top_predictions" not in result
    assert len(provider.calls) == 1
    config = provider.calls[0]["config"]
    assert config.response_schema is None
    assert config.response_json_schema["type"] == "object"
    assert config.response_json_schema["additionalProperties"] is False
    assert config.automatic_continuation is False
    assert config.max_output_tokens == 3000
    assert config.thinking_config.thinking_level.value == "LOW"
    assert "TEST-NOT-REAL" not in str(provider.calls)


def test_unknown_crop_separate_general_guidance_not_care():
    provider = Provider(assessment(plant={"common_name": "Neem", "scientific_name": "Azadirachta indica"}, possible_condition="Unknown"))
    result = analyze_image(picture(), Settings(model="test"), client=provider)
    assert result["status"] == "uncertain"
    assert result["plant"] == "Neem"
    assert result["catalog"]["matched"] is False
    assert not result["care"] and not result["prevention"]
    assert len(result["general_guidance"]) == 2
    assert result["general_guidance_source"]["url"].startswith("https://apps.extension.umn.edu/")


def test_nonleaf_poorphoto_and_noidentity_policies():
    result = analyze_image(picture(), Settings(model="test"), client=Provider(assessment(contains_leaf="no", plant=None, possible_condition=None)))
    assert result["status"] == "unsupported_image"
    assert result["plant"] is None and not result["care"] and not result["sources"]
    result = analyze_image(picture(), Settings(model="test"), client=Provider(assessment(image_quality="poor")))
    assert result["status"] == "uncertain"
    result = analyze_image(picture(), Settings(model="test"), client=Provider(assessment(plant=None, possible_condition=None)))
    assert result["status"] == "uncertain"


@pytest.mark.parametrize("value", [
    {}, {"confidence": 99}, assessment(visible_symptoms=["<script>"]),
    assessment(limitations=["https://invented.example"]),
    assessment(plant={"common_name": "Tomato"}), assessment(possible_condition=""),
])
def test_malformed_semantic_output_is_rejected(value):
    provider = Provider(value)
    with pytest.raises(AnalysisError) as error:
        analyze_image(picture(), Settings(model="test"), client=provider)
    assert error.value.code == "gemini_invalid_response"


@pytest.mark.parametrize("code,expected", [
    (401, "gemini_authentication_error"), (403, "gemini_authentication_error"),
    (429, "gemini_rate_limited"), (503, "gemini_unavailable"),
])
def test_provider_failure_no_retry_or_secret_disclosure(code, expected):
    error = RuntimeError("PRIVATE API KEY AND PROVIDER DATA")
    error.code = code
    provider = Provider(error=error)
    with pytest.raises(AnalysisError) as caught:
        analyze_image(picture(), Settings(model="test"), client=provider)
    assert caught.value.code == expected
    assert "PRIVATE" not in caught.value.message
    assert len(provider.calls) == 1


def test_refusal_truncation_timeout_and_missing_config():
    for reason, code in [("SAFETY", "gemini_refused"), ("MAX_TOKENS", "gemini_invalid_response")]:
        with pytest.raises(AnalysisError) as error:
            analyze_image(picture(), Settings(model="test"), client=Provider(finish_reason=reason))
        assert error.value.code == code
    with pytest.raises(AnalysisError) as error:
        analyze_image(picture(), Settings(model="test"), client=Provider(error=TimeoutError("private")))
    assert error.value.code == "analysis_timeout"
    with pytest.raises(AnalysisError) as error:
        analyze_image(picture(), Settings(api_key=""))
    assert error.value.code == "analysis_unavailable"


def test_private_settings_never_reveal_key_repr():
    settings = load_settings({"GEMINI_API_KEY": "PRIVATE-TEST", "GEMINI_MODEL": "gemini-3.1-flash-lite"})
    assert settings.api_key == "PRIVATE-TEST"
    assert "PRIVATE-TEST" not in repr(settings)
    assert "configured=True" in repr(settings)
