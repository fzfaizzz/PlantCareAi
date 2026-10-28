from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Source(BaseModel):
    title: str
    url: HttpUrl
    publisher: str = "University of Minnesota Extension"


class PlantHypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid", str_max_length=120)
    common_name: str
    scientific_name: str | None = None


class GeminiAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", str_max_length=300)
    contains_leaf: Literal["yes", "no", "uncertain"]
    plant_hypothesis: PlantHypothesis | None = None
    image_quality: Literal["usable", "poor", "uncertain"]
    visible_symptoms: list[str] = Field(default_factory=list, max_length=8)
    condition_hypothesis: str | None = None
    limitations: list[str] = Field(default_factory=list, max_length=6)


class GeminiResult(BaseModel):
    status: Literal["disabled", "unavailable", "success", "quota_exceeded", "timeout", "refused", "invalid_response", "authentication_error"] = "disabled"
    assessment: GeminiAssessment | None = None
    model: str | None = None
    attribution: str = "Optional independent Google Gemini image interpretation; hypotheses are unverified."


class TopPrediction(BaseModel):
    class_id: str
    plant: str
    condition: str
    score: float = Field(ge=0, le=1)


class ModelSummary(BaseModel):
    version: str
    predicted_class: str
    score_type: str = "classifier_softmax_score"
    calibration_status: str = "not_calibrated"


class AnalysisResponse(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    request_id: str
    status: Literal["success", "uncertain", "unsupported_image"]
    plant: str
    condition: str
    confidence: float | None = Field(default=None, ge=0, le=100)
    symptoms: list[str] = Field(default_factory=list)
    care: list[str] = Field(default_factory=list)
    prevention: list[str] = Field(default_factory=list)
    uncertainty: str
    explanation: str
    model: ModelSummary
    top_predictions: list[TopPrediction]
    gemini: GeminiResult
    warnings: list[str]
    sources: list[Source] = Field(default_factory=list)
    timings_ms: dict[str, float]
