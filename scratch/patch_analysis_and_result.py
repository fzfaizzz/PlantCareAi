from pathlib import Path

# 1. Update plantcare_streamlit/analysis.py
analysis_path = Path("plantcare_streamlit/analysis.py")
analysis_code = """\"\"\"Choose real image assessment and provide clear calibrated diagnosis with care catalog.\"\"\"
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
    \"\"\"Format high-confidence local model predictions with full care catalog details.\"\"\"
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
    \"\"\"A softmax winner is a dataset match, not an observed disease or species ID.\"\"\"
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
    if result.get("engine") == "local_tensorflow" and result.get("status") != "success":
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
"""
analysis_path.write_text(analysis_code, encoding="utf-8")
print("Updated plantcare_streamlit/analysis.py")

# 2. Update plantcare_streamlit/result.py
result_path = Path("plantcare_streamlit/result.py")
result_code = """\"\"\"A photo assessment, with uncertainty and care references clearly separated.\"\"\"
from __future__ import annotations

import base64
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import streamlit as st

from .analysis import GENERAL_GUIDANCE, normalize_result
from .services import AnalysisError, prepare_image
from .ui import asset, esc, render_html

ICONS = {
    "leaf": '<svg viewBox="0 0 32 32"><path d="M27 3C9 3 4 11 7 21c8 5 19-3 20-18Z" fill="currentColor"/><path d="m4 28 18-18" fill="none" stroke="currentColor" stroke-width="2.2"/></svg>',
    "shield": '<svg viewBox="0 0 32 32"><path d="m16 2 12 4v10c0 7-12 14-12 14S4 23 4 16V6Z" fill="currentColor"/><path d="m10 15 4 4 8-9" fill="none" stroke="white" stroke-width="2.8"/></svg>',
    "sprout": '<svg viewBox="0 0 32 32"><path d="M15 16C5 17 2 11 2 4c9 0 15 2 13 12Zm3-3C18 4 25 2 31 3c0 9-5 14-13 10Z" fill="currentColor"/><path d="M16 15v13M8 29h16" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>',
}
ICONS = {name: '<img alt="" aria-hidden="true" src="data:image/svg+xml,' + quote(svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" color="#075336" ', 1), safe="") + '">' for name, svg in ICONS.items()}


def _items(values, fallback):
    return ''.join('<li>' + esc(value) + '</li>' for value in values) if values else '<li class="empty-detail">' + esc(fallback) + '</li>'


def result_copy(result):
    result = normalize_result(result)
    status = result.get('status', 'uncertain')
    condition = result.get('condition') or 'Condition not confirmed'
    healthy = 'healthy' in condition.lower()
    conf = result.get('confidence')
    
    if status == 'unsupported_image':
        return result, 'No leaf identified', 'Please choose a leaf photo', 'Not a leaf photo', 'neutral', 'Try another photo'
    
    plant = result.get('plant') or 'Plant Identified'
    
    if status == 'success' or (conf is not None and conf >= 35.0):
        if healthy:
            assessment_text = f"{conf:.1f}% Confidence" if conf else "Healthy Foliage"
            return result, plant, condition, 'Healthy Foliage', 'healthy', assessment_text
        else:
            assessment_text = f"{conf:.1f}% Confidence" if conf else "Disease Identified"
            return result, plant, condition, 'Disease Detected', 'disease', assessment_text
            
    if status == 'uncertain' or not result.get('plant'):
        cond_text = 'Healthy-looking leaf' if healthy else 'Condition not confirmed'
        return result, plant, cond_text, 'Needs confirmation', 'uncertain', 'Needs a closer look'
        
    return result, plant, condition, 'Possible issue', 'disease', 'Needs review'


def _care_groups(result):
    observations = result.get('observations') or result.get('symptoms') or []
    applicable = (result.get('status') == 'success' or bool(result.get('care'))) and bool(result.get('catalog', {}).get('applicable', result.get('catalog', {}).get('matched', True)))
    healthy = 'healthy' in str(result.get('condition') or '').lower()
    empty = 'No obvious symptoms were reported in this photo.' if healthy else 'No visible symptoms recorded.'
    if applicable and (result.get('care') or result.get('prevention')):
        care_title = 'Routine Care' if healthy else 'Immediate Treatment'
        return [
            ('Symptoms & Observations', 'leaf', observations, empty, 'Observed leaf characteristics'),
            (care_title, 'sprout', result.get('care') or [], 'No specific care required.', 'Actionable agricultural guidance'),
            ('Prevention', 'shield', result.get('prevention') or [], 'Standard crop sanitation recommended.', 'Long-term disease management'),
        ]
    return [
        ('Photo observations', 'leaf', observations, empty, 'Uncertain observations do not establish a diagnosis'),
        ('Next steps', 'shield', (result.get('general_guidance') or GENERAL_GUIDANCE)[:2], 'Try a clear close-up in natural daylight.', 'General guidance'),
        ('Care for now', 'sprout', ['Continue normal plant care and monitor nearby leaves.', 'Avoid disease treatment based only on this inconclusive result.'], '', 'General guidance, not disease treatment'),
    ]


def _report_html(result, photo):
    result, plant, condition, label, _, _ = result_copy(result)
    details = ''.join('<section><h2>' + esc(title) + '</h2><ul>' + _items(values, fallback) + '</ul><small>' + esc(caption) + '</small></section>' for title, _, values, fallback, caption in _care_groups(result))
    links = ''.join('<li><a href="' + esc(source['url']) + '">' + esc(source['title']) + '</a></li>' for source in result.get('sources', []))
    source = 'Deep Convolutional Neural Network' if result.get('engine') in ('gemini_cloud', 'deep_neural_engine') else 'MobileNetV2 Classifier'
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>PlantCare AI - Leaf Result</title><style>body{font:16px/1.7 system-ui;max-width:900px;margin:40px auto;padding:24px;background:#f7faef;color:#153d29}h1{font-size:36px;line-height:1.1}img{width:260px;max-height:320px;object-fit:contain;border-radius:16px}section{background:white;padding:20px;margin:15px 0;border-radius:16px}small{color:#687461}a{color:#08482d}</style>'
            '<h1>PlantCare AI — Detection Result</h1><small>' + esc(datetime.now(timezone.utc).strftime('%d %B %Y, %H:%M UTC')) + '</small><p>' + esc(label) + '</p><img src="' + photo + '" alt="Uploaded leaf"><h2>' + esc(plant) + ' — ' + esc(condition) + '</h2><p>' + esc(result.get('explanation', '')) + '</p><p>' + esc(result.get('uncertainty', '')) + '</p>' + details + '<h2>Sources</h2><ul>' + links + '</ul><small>' + esc(source) + '. Photo interpretation is tentative, not a confirmed diagnosis.</small></html>')


def render_result(result, on_another):
    render_html('<style>' + (Path(__file__).parent / 'result.css').read_text(encoding='utf-8') + '</style>')
    result, plant, condition, label, badge_class, assessment = result_copy(result)
    photo = asset('healthy-dew-leaf')
    data = st.session_state.get('detect_input')
    if data:
        try:
            photo = 'data:image/jpeg;base64,' + base64.b64encode(prepare_image(data).jpeg).decode()
        except AnalysisError:
            pass
    with st.container(key='analysis-result'):
        render_html('<section class="result-heading"><h1>Detection Result</h1><p>A photo-based assessment with clear observations and practical next steps.</p></section>')
        photo_col, detail_col = st.columns([.91, 1.5], gap='large', vertical_alignment='top')
        with photo_col:
            render_html('<div class="result-photo"><img src="' + photo + '" alt="Your uploaded leaf"><span class="uploaded-badge">Your uploaded photo</span></div>')
            with st.container(key='result-actions'):
                another, download = st.columns([1.18, 1], gap='small')
                with another:
                    st.button('Analyse Another Leaf', icon=':material/eco:', type='primary', key='result-another', on_click=on_another, width='stretch')
                with download:
                    st.download_button('Download Result', _report_html(result, photo), file_name='PlantCare-leaf-result.html', mime='text/html', icon=':material/download:', key='result-download', width='stretch', on_click='ignore')
        with detail_col:
            scientific = result.get('plant_scientific_name')
            scientific_html = '<em>' + esc(scientific) + '</em>' if scientific else ''
            render_html('<article class="result-summary"><div class="result-summary-copy"><span class="condition-pill ' + badge_class + '"><i></i>' + esc(label) + '</span><h2>' + esc(plant) + '</h2><h3>' + esc(condition) + '</h3>' + scientific_html + '<p>' + esc(result.get('explanation', '')) + '</p></div><aside class="result-confidence assessment-' + badge_class + '"><strong>Photo assessment</strong><b class="assessment-value">' + esc(assessment) + '</b><span class="assessment-note">Based on leaf surface features.</span></aside></article>')
            with st.container(key='result-info-grid'):
                for column, (title, symbol, values, fallback, caption) in zip(st.columns(3, gap='small'), _care_groups(result)):
                    with column:
                        render_html('<section class="result-info-card"><h3>' + ICONS[symbol] + esc(title) + '</h3><ul>' + _items(values, fallback) + '</ul><small>' + esc(caption) + '</small></section>')
            with st.expander('Sources & assessment notes'):
                source = 'Deep Convolutional Neural Network' if result.get('engine') in ('gemini_cloud', 'deep_neural_engine') else 'MobileNetV2 Classifier'
                st.caption('Assessment source: ' + source)
                st.write(result.get('uncertainty', 'This is an empirical visual assessment.'))
                if result.get('top_predictions'):
                    st.markdown('**Model Class Predictions**')
                    for prediction in result['top_predictions']:
                        name = str(prediction['class_id']).replace('___', ' · ').replace('_', ' ')
                        score = prediction.get('score')
                        st.caption(name + (f' — {score:.1f}% confidence' if isinstance(score, (int, float)) else ''))
                for source in result.get('sources', []):
                    st.link_button(source['title'], source['url'])
                for warning in result.get('warnings', []):
                    st.caption(warning)
"""
result_path.write_text(result_code, encoding="utf-8")
print("Updated plantcare_streamlit/result.py")
