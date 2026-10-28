import asyncio
import re
import time
import numpy as np
from app.schemas.analysis import AnalysisResponse, ModelSummary, TopPrediction
from app.services.model_service import split_label

BASE_WARNING = "This closed-set classifier cannot identify every plant or reject every out-of-scope image. Scores are model similarities, not guaranteed disease probabilities."


def normalized(value):
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


PLANT_ALIASES = {
    "tomato": ["tomato", "solanum lycopersicum"], "potato": ["potato", "solanum tuberosum"],
    "corn": ["corn", "maize", "zea mays"], "apple": ["apple", "malus domestica"],
    "grape": ["grape", "vitis"], "pepper bell": ["pepper", "capsicum annuum"],
    "cherry": ["cherry"], "orange": ["orange", "citrus sinensis"],
    "peach": ["peach"], "blueberry": ["blueberry"], "raspberry": ["raspberry"],
    "soybean": ["soybean", "soy bean"], "squash": ["squash"], "strawberry": ["strawberry"],
}


def plant_key(value):
    text = " " + normalized(value) + " "
    for name, aliases in PLANT_ALIASES.items():
        if any(" " + alias + " " in text for alias in aliases):
            return name
    return normalized(value)


def condition_conflict(class_condition, hypothesis):
    current, other = normalized(class_condition), normalized(hypothesis)
    if not other or other in {"unknown", "uncertain", "none"}:
        return False
    if "healthy" in current:
        return not any(word in other for word in ("healthy", "no visible", "no obvious"))
    if "healthy" in other or "no visible" in other:
        return True
    # Only distinguish explicit recognizable conditions; vague symptom descriptions are unknown.
    recognizable = ["early blight", "late blight", "black rot", "apple scab", "common rust",
                    "powdery mildew", "bacterial spot", "septoria", "leaf mold", "mosaic",
                    "yellow leaf curl", "cedar apple rust", "target spot"]
    current_names = {name for name in recognizable if name in current}
    other_names = {name for name in recognizable if name in other}
    return bool(current_names and other_names and current_names.isdisjoint(other_names))


class AnalysisService:
    def __init__(self, model, gemini, catalog):
        self.model, self.gemini, self.catalog = model, gemini, catalog

    async def analyze(self, image, request_id, decode_ms):
        started = time.perf_counter()

        async def measured_predict():
            t0 = time.perf_counter()
            scores = await self.model.predict(image.array)
            return scores, (time.perf_counter() - t0) * 1000

        prediction_task = asyncio.create_task(measured_predict())
        gemini_task = asyncio.create_task(self.gemini.assess(image.gemini_jpeg))
        try:
            (scores, inference_ms), gemini = await asyncio.gather(prediction_task, gemini_task)
        except BaseException:
            prediction_task.cancel()
            gemini_task.cancel()
            await asyncio.gather(prediction_task, gemini_task, return_exceptions=True)
            raise
        indices = np.argsort(scores)[::-1][:3]
        predictions = []
        for index in indices:
            plant, condition = split_label(self.model.labels[int(index)])
            predictions.append(TopPrediction(class_id=self.model.labels[int(index)], plant=plant,
                                             condition=condition, score=round(float(scores[index]), 6)))
        top = predictions[0]
        score = float(scores[indices[0]])
        margin = score - float(scores[indices[1]])
        policy = self.model.metadata.get("decision_policy") or {}
        warnings = [BASE_WARNING, *image.quality_warnings]
        reasons = []
        if not policy.get("validated"):
            reasons.append("The decision policy has not been validated.")
        elif score < policy["min_score"] or margin < policy["min_margin"]:
            reasons.append("Classifier scores do not meet the validation-derived decision policy.")
        if image.quality_warnings:
            reasons.append("Image-quality limitations reduce reliability.")
        if gemini.status not in {"disabled", "success"}:
            warnings.append("Optional Gemini interpretation is unavailable; this is not independent confirmation.")
        assessment = gemini.assessment
        unsupported = False
        if assessment:
            if assessment.contains_leaf == "no":
                unsupported = True
                reasons.append("The independent image assessment does not show a leaf.")
            elif assessment.contains_leaf == "uncertain":
                reasons.append("The image assessment cannot establish that a leaf is visible.")
            if assessment.image_quality in {"poor", "uncertain"}:
                reasons.append("The independent assessment reports image-quality limitations.")
            if assessment.plant_hypothesis:
                hypothesis = plant_key(assessment.plant_hypothesis.common_name)
                scope = {plant_key(split_label(label)[0]) for label in self.model.labels}
                if hypothesis not in scope:
                    reasons.append("The unverified plant hypothesis may fall outside the trained crop scope.")
                elif hypothesis != plant_key(top.plant):
                    reasons.append("TensorFlow and the independent plant hypothesis disagree.")
            else:
                warnings.append("Gemini did not provide a plant hypothesis; it did not confirm the crop.")
            if assessment.condition_hypothesis and condition_conflict(top.condition, assessment.condition_hypothesis):
                reasons.append("TensorFlow and the independent condition hypothesis conflict.")
        entry = self.catalog.get_class(top.class_id)
        if not entry:
            warnings.append("A reviewed condition-specific care entry is not available for this model class.")
        if "healthy" in top.condition.lower():
            warnings.append("A healthy-class match does not rule out every disease, pest, or nutrient problem.")
        status = "unsupported_image" if unsupported else ("uncertain" if reasons else "success")
        uncertainty = " ".join(reasons) or "This is a supported model-class match, not a definitive diagnosis; field-photo reliability may differ."
        # Condition-specific reference information is withheld for unsupported input.
        visible_entry = entry if not unsupported else None
        explanation = (
            "The image is unsuitable for leaf classification. Choose a clear leaf photo."
            if unsupported else
            f"The classifier's closest trained class is {top.plant} — {top.condition}. "
            "Reference symptoms and care below come from the curated catalog; Gemini observations are shown separately."
        )
        return AnalysisResponse(
            request_id=request_id, status=status,
            plant="Unverified" if unsupported else top.plant,
            condition="Unsupported image" if unsupported else top.condition,
            confidence=None if unsupported else round(score * 100, 2),
            symptoms=visible_entry["symptoms"] if visible_entry else [],
            care=visible_entry["care"] if visible_entry else [],
            prevention=visible_entry["prevention"] if visible_entry else [],
            uncertainty=uncertainty, explanation=explanation,
            model=ModelSummary(version=self.model.metadata["model_version"], predicted_class=top.class_id,
                               calibration_status=self.model.metadata.get("calibration", {}).get("status", "not_calibrated")),
            top_predictions=predictions, gemini=gemini, warnings=warnings,
            sources=visible_entry["sources"] if visible_entry else [],
            timings_ms={"decode": round(decode_ms, 2), "inference": round(inference_ms, 2),
                        "analysis": round((time.perf_counter() - started) * 1000, 2)},
        )
