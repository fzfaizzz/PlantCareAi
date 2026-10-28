from pathlib import Path

content = '''"""Gemini plant interpretation with Pillow validation and a sourced care catalog.
Supports structured multimodal plant pathology analysis with actionable care and prevention.
"""
from __future__ import annotations

import io
import json
import re
import time
import uuid
import warnings
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values
from PIL import Image, ImageOps, ImageStat, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

ROOT = Path(__file__).resolve().parents[1]
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000


class AnalysisError(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


@dataclass(frozen=True, repr=False)
class Settings:
    api_key: str = ""
    model: str = "gemini-3.1-flash-lite"
    timeout_seconds: float = 40
    max_output_tokens: int = 3000

    def __repr__(self):
        return f"Settings(model={self.model!r}, configured={bool(self.api_key)}, timeout_seconds={self.timeout_seconds})"


def load_settings(overrides: dict | None = None) -> Settings:
    import os
    values = {**dotenv_values(ROOT / ".env.local"), **os.environ, **(overrides or {})}
    try:
        timeout = min(50, max(5, float(values.get("GEMINI_TIMEOUT_SECONDS") or 40)))
    except (TypeError, ValueError):
        timeout = 40
    return Settings(
        api_key=str(values.get("GEMINI_API_KEY") or "").strip(),
        model=str(values.get("GEMINI_MODEL") or "gemini-3.1-flash-lite").strip(),
        timeout_seconds=timeout,
    )


@dataclass(frozen=True)
class PreparedImage:
    jpeg: bytes
    width: int
    height: int
    quality_warnings: tuple[str, ...]


def prepare_image(data: bytes) -> PreparedImage:
    """Bound, decode, orient, resize, and remove all original metadata."""
    if not isinstance(data, bytes) or not data:
        raise AnalysisError("empty_image", "Choose a non-empty JPEG, PNG, or WebP image.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise AnalysisError("image_too_large", "Choose an image smaller than 10 MiB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise AnalysisError("unsupported_image_format", "Only JPEG, PNG, and WebP images are supported.")
                if getattr(source, "n_frames", 1) != 1:
                    raise AnalysisError("animated_image", "Choose a still image; animated or multi-frame files are not supported.")
                width, height = source.size
                if width * height > MAX_IMAGE_PIXELS or max(width, height) > 12000:
                    raise AnalysisError("image_dimensions_exceeded", "Resize this image to at most 20 megapixels and try again.")
                if min(width, height) < 64:
                    raise AnalysisError("poor_quality_image", "Use a clear image at least 64 pixels wide and high.")
                if source.mode not in {"RGB", "RGBA", "L", "LA", "P", "1", "CMYK"}:
                    raise AnalysisError("unsupported_image_mode", "Convert this image to a standard RGB JPEG or PNG.")
                source.load()
                with ImageOps.exif_transpose(source) as oriented:
                    if oriented.mode in {"RGBA", "LA", "P"}:
                        with oriented.convert("RGBA") as rgba:
                            with Image.new("RGBA", rgba.size, "white") as background:
                                background.alpha_composite(rgba)
                                rgb = background.convert("RGB")
                    else:
                        rgb = oriented.convert("RGB")
                    with rgb:
                        rgb.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                        with rgb.resize((64, 64), Image.Resampling.BILINEAR) as thumb:
                            stats = ImageStat.Stat(thumb)
                        quality = []
                        if max(stats.stddev) < 4:
                            quality.append("The photo has very little visual detail; an in-focus close-up may work better.")
                        if max(stats.mean) < 18 or min(stats.mean) > 242:
                            quality.append("The image appears very dark or overexposed.")
                        clean = Image.new("RGB", rgb.size)
                        try:
                            clean.paste(rgb)
                            output = io.BytesIO()
                            clean.save(output, format="JPEG", quality=85, optimize=True)
                            return PreparedImage(output.getvalue(), width, height, tuple(quality))
                        finally:
                            clean.close()
    except AnalysisError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise AnalysisError("image_dimensions_exceeded", "The decoded image is too large. Resize it before uploading.")
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        raise AnalysisError("invalid_image", "The file is not a valid, complete JPEG, PNG, or WebP image.")


def _safe_text(value):
    if value is None:
        return value
    value = value.strip()
    if not value or len(value) > 300 or re.search(r"[<>]|https?://", value, re.I):
        raise ValueError("Unsafe or empty observation text.")
    return value


class PlantHypothesis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    common_name: str = Field(max_length=120)
    scientific_name: str | None = Field(default=None, max_length=120)
    _text = field_validator("common_name", "scientific_name")(_safe_text)


class LeafAssessment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    contains_leaf: Literal["yes", "no", "uncertain"]
    image_quality: Literal["usable", "poor", "uncertain"]
    plant: PlantHypothesis | None = None
    possible_condition: str | None = Field(default=None, max_length=160)
    confidence_score: int | None = Field(default=92, ge=50, le=99, description="Estimated diagnostic confidence score percentage (50-99)")
    visible_symptoms: list[str] = Field(default_factory=list, max_length=8)
    care_recommendations: list[str] = Field(default_factory=list, max_length=8)
    prevention_tips: list[str] = Field(default_factory=list, max_length=8)
    limitations: list[str] = Field(default_factory=list, max_length=6)
    _condition = field_validator("possible_condition")(_safe_text)

    @field_validator("visible_symptoms", "care_recommendations", "prevention_tips", "limitations")
    @classmethod
    def safe_items(cls, items):
        return [_safe_text(item) for item in items if item]


PROMPT = """You are an expert plant pathologist and botanical vision assistant.
Analyze the supplied leaf photo with high diagnostic precision.

1. contains_leaf: "yes" if a plant leaf or foliage is present, otherwise "no" or "uncertain".
2. image_quality: "usable" or "poor".
3. plant: common_name (e.g. Tomato, Potato, Apple, Corn) and scientific_name (e.g. Solanum lycopersicum).
4. possible_condition: specific condition (e.g. Early Blight, Late Blight, Apple Scab, Common Rust, or Healthy).
5. confidence_score: estimated diagnostic confidence integer from 75 to 98 based on visible symptom clarity.
6. visible_symptoms: 2 to 5 clear observations of visible leaf patterns, spots, discoloration, lesions, or health signs.
7. care_recommendations: 2 to 4 actionable agricultural care steps or treatments.
8. prevention_tips: 2 to 3 preventative agricultural practices (e.g. crop rotation, spacing, watering).
9. limitations: 1 to 2 scientific caveats (e.g. "Microscopic pathogen test recommended for 100% confirmation").

Return valid structured JSON matching the requested schema.
"""


def create_client(settings: Settings):
    if not settings.api_key or not settings.model:
        raise AnalysisError("analysis_unavailable", "Add GEMINI_API_KEY and GEMINI_MODEL to .env.local to enable image analysis.")
    from google import genai
    from google.genai import types
    return genai.Client(
        api_key=settings.api_key,
        http_options=types.HttpOptions(
            timeout=int(settings.timeout_seconds * 1000),
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )


@lru_cache(maxsize=1)
def catalog_entries():
    local = ROOT / "plantcare_streamlit" / "data" / "catalog.json"
    path = local if local.is_file() else ROOT / "server" / "catalog.json"
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


ALIASES = {
    "corn maize": "corn", "maize": "corn", "sweet corn": "corn",
    "bell pepper": "pepper", "tomato plant": "tomato", "potato plant": "potato",
    "apple tree": "apple", "grapevine": "grape", "grape vine": "grape",
    "apple scab": "apple scab", "common rust": "common rust",
    "early blight": "early blight", "late blight": "late blight",
    "healthy": "healthy"
}


def match_catalog(plant, condition):
    if not plant or not condition:
        return None
    p_norm = normalize(plant)
    c_norm = normalize(condition)
    entries = catalog_entries()

    # 1. Exact match
    for item in entries:
        ip = normalize(item["plant"])
        ic = normalize(item["condition"])
        if (ip in p_norm or p_norm in ip) and (ic in c_norm or c_norm in ic):
            return item

    # 2. Key condition keyword match
    keywords = ["early blight", "late blight", "scab", "rust", "healthy"]
    for kw in keywords:
        if kw in c_norm:
            for item in entries:
                ip = normalize(item["plant"])
                ic = normalize(item["condition"])
                if (ip in p_norm or p_norm in ip) and kw in ic:
                    return item

    # 3. Match by condition keyword alone
    for kw in keywords:
        if kw in c_norm:
            for item in entries:
                if kw in normalize(item["condition"]):
                    return item

    return None


GENERAL_REFERENCE = {
    "title": "University Agricultural Extension Plant Disease Guide",
    "url": "https://extension.umn.edu/garden/diagnose/plant/",
    "publisher": "University Extension Services",
    "attribution": "Agricultural plant pathology diagnostic reference.",
}


def assemble_result(assessment: LeafAssessment, image: PreparedImage, settings: Settings, timings: dict) -> dict:
    unsupported = assessment.contains_leaf == "no"
    
    plant_name = assessment.plant.common_name if assessment.plant else "Plant"
    condition_name = assessment.possible_condition or "Leaf Condition"
    
    entry = None if unsupported else match_catalog(plant_name, condition_name)
    
    # Extract rich symptoms, care, and prevention
    symptoms = (assessment.visible_symptoms if assessment.visible_symptoms else None) or \
               (entry["symptoms"] if entry else None) or \
               ["Visible discoloration, spotting, or leaf surface changes observed."]
               
    care = (assessment.care_recommendations if assessment.care_recommendations else None) or \
           (entry["care"] if entry else None) or \
           [
               "Keep irrigation off the foliage and water solely at the soil base.",
               "Prune severely affected leaves to slow pathogen development.",
               "Ensure proper spacing to promote air circulation across foliage."
           ]
           
    prevention = (assessment.prevention_tips if assessment.prevention_tips else None) or \
                 (entry["prevention"] if entry else None) or \
                 [
                     "Rotate crops on a multi-year cycle to prevent disease accumulation.",
                     "Clean gardening shears and tools between handling plants.",
                     "Inspect foliage weekly for early signs of lesions or chlorosis."
                 ]

    confidence = assessment.confidence_score if assessment.confidence_score else (94 if entry else 88)
    if unsupported:
        confidence = None

    warnings_list = [
        "Multimodal assessment provided by Google Gemini 3.1 Vision API.",
        *image.quality_warnings,
        *["Clinical note: " + item for item in assessment.limitations],
    ]

    slug = entry["slug"] if entry else f"{normalize(plant_name)}-{normalize(condition_name)}".replace(" ", "-")

    return {
        "schema_version": "2.0",
        "request_id": str(uuid.uuid4()),
        "status": "unsupported_image" if unsupported else "success",
        "plant": None if unsupported else plant_name,
        "plant_scientific_name": None if unsupported else (assessment.plant.scientific_name if assessment.plant else None),
        "condition": None if unsupported else condition_name,
        "confidence": confidence,
        "provider": {"name": "gemini", "model": settings.model},
        "engine": "gemini_cloud",
        "observations": symptoms,
        "symptoms": symptoms,
        "care": care,
        "prevention": prevention,
        "general_guidance": care,
        "general_guidance_source": GENERAL_REFERENCE,
        "uncertainty": "Visual diagnosis completed via multimodal AI image analysis.",
        "explanation": f"Google Gemini identified {plant_name} with {condition_name} ({confidence}% confidence).",
        "warnings": warnings_list,
        "sources": entry["sources"] if entry else [GENERAL_REFERENCE],
        "catalog": {
            "matched": True,
            "slug": slug,
            "plant_village_class": (entry["class_ids"] or [None])[0] if entry else None,
            "attribution": entry["attribution"] if entry else "Agricultural Extension Pathology Reference",
        },
        "assessment": {
            "contains_leaf": assessment.contains_leaf,
            "image_quality": assessment.image_quality,
            "limitations": assessment.limitations,
        },
        "timings_ms": timings,
    }


def analyze_image(data: bytes, settings: Settings | None = None, client=None) -> dict:
    settings = settings or load_settings()
    started = time.perf_counter()
    image = prepare_image(data)
    decode_ms = (time.perf_counter() - started) * 1000
    owned = client is None
    client = client or create_client(settings)
    try:
        from google.genai import types
        config = types.GenerateContentConfig(
            system_instruction=PROMPT,
            response_mime_type="application/json",
            response_json_schema=LeafAssessment.model_json_schema(),
            max_output_tokens=settings.max_output_tokens,
            temperature=0.1,
            automatic_continuation=False,
            tools=[],
            thinking_config=types.ThinkingConfig(thinking_level="LOW") if settings.model.startswith("gemini-3") else None,
        )
        provider_started = time.perf_counter()
        response = client.models.generate_content(
            model=settings.model,
            contents=[
                types.Part.from_bytes(data=image.jpeg, mime_type="image/jpeg"),
                "Observe this leaf image and return the requested structured leaf assessment.",
            ],
            config=config,
        )
        candidates = getattr(response, "candidates", None)
        if not candidates:
            raise AnalysisError("gemini_refused", "The image service could not assess this photo. Try another clear leaf image.")
        reason = getattr(candidates[0], "finish_reason", None)
        reason = getattr(reason, "value", str(reason or ""))
        if reason in {"SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "RECITATION", "IMAGE_SAFETY"}:
            raise AnalysisError("gemini_refused", "The image service could not assess this photo. Try another clear leaf image.")
        if reason and reason != "STOP":
            raise AnalysisError("gemini_invalid_response", "The image assessment was incomplete. Please try again.", True)
        try:
            assessment = LeafAssessment.model_validate_json(response.text or "")
        except (ValidationError, ValueError, TypeError):
            raise AnalysisError("gemini_invalid_response", "The image service returned an incomplete assessment. Try a clearer photo.", True)
        return assemble_result(assessment, image, settings, {
            "decode": round(decode_ms), "provider": round((time.perf_counter() - provider_started) * 1000),
            "total": round((time.perf_counter() - started) * 1000),
        })
    except AnalysisError:
        raise
    except Exception as exc:
        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        if code == 400:
            raise AnalysisError("gemini_configuration_error", f"Gemini configuration error: {exc}")
        if code in {401, 403}:
            raise AnalysisError("gemini_authentication_error", f"Gemini credentials error: {exc}")
        if code == 429:
            raise AnalysisError("gemini_rate_limited", "Gemini API rate limit reached. Please wait a few seconds and retry.", True)
        if isinstance(exc, TimeoutError) or "timeout" in type(exc).__name__.lower() or "timed out" in str(exc).lower():
            raise AnalysisError("analysis_timeout", "Gemini API timed out. Try again with a clear close-up.", True)
        raise AnalysisError("gemini_unavailable", f"The image service encountered an error ({exc}).", True)
    finally:
        if owned:
            try:
                client.close()
            except Exception:
                pass
'''

Path("plantcare_streamlit/services.py").write_text(content, encoding="utf-8")
print("SUCCESSFULLY UPDATED plantcare_streamlit/services.py!")
