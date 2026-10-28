"""
Native Streamlit upload, real pending state, and accessible result cards.
Dual-stage deep learning vision pipeline for agricultural leaf assessment.
"""
from __future__ import annotations

import base64
import hashlib
import re
from pathlib import Path
from urllib.parse import quote
import streamlit as st

from .analysis import analyze_leaf, uses_cloud
from .services import AnalysisError, load_settings, prepare_image
from .ui import ROOT, asset, esc, render_html, navigate


def _render_detect_html(markup):
    # Streamlit sanitizes inline SVG out of st.html. Local SVG image sources
    # preserve the illustration while leaving its HTML sanitizer enabled.
    def svg_image(match):
        attributes, content = match.groups()
        class_match = re.search(r'class="([^"]*)"', attributes)
        class_name = class_match.group(1) if class_match else "detect-inline-icon"
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" fill="none" '
               'stroke="#0a573d" stroke-width="2.2" stroke-linecap="round" '
               'stroke-linejoin="round" ' + attributes + '>' + content + '</svg>')
        return '<img class="' + esc(class_name) + '" alt="" aria-hidden="true" src="data:image/svg+xml,' + quote(svg, safe="") + '">'
    render_html(re.sub(r'<svg\b([^>]*)>(.*?)</svg>', svg_image, markup, flags=re.DOTALL))


SAMPLES = [
    ("sample-leaf-spotted", "Spotted leaf (Early Blight)"),
    ("sample-leaf-healthy", "Green leaf (Healthy)"),
    ("sample-leaf-closeup", "Leaf close-up"),
]


def _reset_result():
    for key in ("detect_result", "detect_error", "detect_attempted_hash", "result_photo_view"):
        st.session_state.pop(key, None)


def _selected_upload():
    upload = st.session_state.get("detect_file")
    if upload is None:
        st.session_state.pop("detect_input", None)
        st.session_state.pop("detect_input_origin", None)
    else:
        st.session_state["detect_input"] = upload.getvalue()
        st.session_state["detect_input_origin"] = "upload"
    _reset_result()


def _select_sample(name):
    st.session_state["detect_input"] = (ROOT / "public" / "assets" / "plants" / (name + ".webp")).read_bytes()
    st.session_state["detect_input_origin"] = "sample"
    st.session_state.pop("detect_file", None)
    _reset_result()


def _remove_image():
    st.session_state.pop("detect_input", None)
    st.session_state.pop("detect_input_origin", None)
    st.session_state.pop("detect_file", None)
    _reset_result()


def render_result(result: dict):
    from .result import render_result as render_dashboard
    render_dashboard(result, _remove_image)


def render_detect():
    if st.session_state.get("detect_result"):
        render_result(st.session_state["detect_result"])
        return
    _render_detect_html("<style>" + (Path(__file__).parent / "detect.css").read_text(encoding="utf-8") + "</style>")
    settings = load_settings()
    cloud_mode = uses_cloud(settings)
    with st.container(key="detect-page"):
        state_class = " detect-has-input" if st.session_state.get("detect_input") else ""
        with st.container(key="detect-heading-block"):
            _render_detect_html('<section class="detect-heading' + state_class + '"><h1>Detect Plant Diseases<br>with a Single Leaf Photo</h1><p>Upload a leaf image to identify possible plant conditions.<br> Get helpful insights and plant-care recommendations.</p></section>')
        with st.container(key="detect-composition"):
            left, center, right = st.columns([1, 1.42, 1], gap="small", vertical_alignment="center")
            with left:
                with st.container(key="detect-samples"):
                    _render_detect_html('<p class="handwritten upload-note">Upload<br>a leaf</p><svg class="upload-note-arrow" viewBox="0 0 100 70" aria-hidden="true"><path d="M5 10C47 3 80 22 85 52m0 0-18-12m18 12 4-20"/></svg><svg class="sample-small-arrow" viewBox="0 0 70 65" aria-hidden="true"><path d="M8 46C33 54 49 40 54 21m0 0-12 9m12-9 4 13"/></svg>')
                    for index, (name, label) in enumerate(SAMPLES):
                        with st.container(key="detect-sample-" + str(index)):
                            _render_detect_html('<div class="sample-photo"><img src="' + asset(name) + '" alt="' + esc(label) + '"></div>')
                            st.button(label, key="choose-" + name, on_click=_select_sample, args=(name,), width="stretch")
            with center:
                data = st.session_state.get("detect_input")
                if not data:
                    with st.container(key="leaf-upload", border=True):
                        _render_detect_html('<div class="upload-cloud" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M20 16.6A4.5 4.5 0 0 0 18 8a6 6 0 0 0-11.7-1.7A5 5 0 0 0 4 16.5M12 20V10m-4 4 4-4 4 4"/></svg></div>'
                                    '<h3 class="upload-title">Drag & drop a leaf image here</h3>'
                                    '<p class="upload-subtitle">or click to browse files</p>'
                                    '<p class="upload-support">Supports JPG, JPEG, PNG, WebP (Max 10 MB)</p>'
                                    '<span class="choose-leaf-control" aria-hidden="true"><svg viewBox="0 0 24 24" style="stroke:#fff"><rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1.5"/><path d="m3 17 5-5 4 4 4-6 5 7"/></svg><span>Choose Leaf Image</span></span>')
                        st.file_uploader("Choose a leaf image", type=["jpg", "jpeg", "png", "webp"],
                                         accept_multiple_files=False, key="detect_file", on_change=_selected_upload,
                                         label_visibility="collapsed")
                    privacy = 'Image features are analyzed using Deep Neural Network inference.'
                    _render_detect_html('<p class="upload-privacy"><svg viewBox="0 0 20 20" aria-hidden="true"><rect x="4" y="8" width="12" height="10" rx="2"/><path d="M7 8V5a3 3 0 0 1 6 0v3M10 12v3"/></svg> ' + privacy + '</p>')
                else:
                    try:
                        prepared = prepare_image(data)
                    except AnalysisError as error:
                        st.error(error.message)
                        st.button("Remove image", on_click=_remove_image, key="remove-invalid")
                        data = None
                    else:
                        st.image(prepared.jpeg, caption="Selected leaf", width="stretch")

                        actions = st.columns([2, 1])
                        with actions[0]:
                            analyze_clicked = st.button("Detect Disease  →", type="primary",
                                                        key="run-detection", width="stretch")
                        with actions[1]:
                            st.button("Remove", on_click=_remove_image, key="remove-leaf", width="stretch")

                        fingerprint = hashlib.sha256(data).hexdigest()
                        if analyze_clicked:
                            if fingerprint == st.session_state.get("detect_attempted_hash") and st.session_state.get("detect_result"):
                                st.info("This photo is already assessed. Choose another photo to run a new analysis.")
                            else:
                                _reset_result()
                                st.session_state["detect_attempted_hash"] = fingerprint
                                scan = st.empty()
                                photo = base64.b64encode(prepared.jpeg).decode()
                                scan.markdown(
                                    '<div class="leaf-scanner"><img alt="Leaf being assessed" src="data:image/jpeg;base64,' +
                                    photo + '"><span class="scan-beam"></span><span class="scan-corners"></span></div>',
                                    unsafe_allow_html=True,
                                )
                                try:
                                    with st.status("Looking closely at your leaf…", expanded=True) as pending:
                                        st.write("Checking the visible features and matching any suitable care reference.")
                                        result = analyze_leaf(data, settings)
                                        pending.update(label="Assessment ready", state="complete", expanded=False)

                                    st.session_state["detect_result"] = result
                                    history = st.session_state.setdefault("assessment_history", [])
                                    history.insert(0, result)
                                    del history[20:]
                                    navigate("Detect")
                                    st.rerun()
                                except AnalysisError as error:
                                    st.session_state["detect_error"] = error.message
                                except Exception:
                                    st.session_state["detect_error"] = "The image assessment could not complete. Please try again."
                                finally:
                                    scan.empty()

            with right:
                _render_detect_html('<div class="detect-botanical"><img alt="" src="' + asset("reference-detect-hero") + '"><svg class="detect-leaf-doodle" viewBox="0 0 65 80" aria-hidden="true"><path d="M48 56C34 17 19 4 19 8s15 37 29 48ZM31 71C13 48 3 45 7 51s14 17 24 20Z"/></svg><span class="handwritten healthy-note">Healthy<br>Plants<br>Happier<br>Tomorrow<svg viewBox="0 0 55 40" aria-hidden="true"><path d="m5 30 30-17-18 22 32-23"/></svg></span></div>')
        if st.session_state.get("detect_error"):
            st.error(st.session_state["detect_error"])
        with st.container(key="detect-feature-block"):
            _render_detect_html('<div class="detect-feature-band"><div><span class="detect-feature-icon"><svg viewBox="0 0 32 32"><circle cx="16" cy="16" r="7"/><path d="M16 2v5m0 18v5M2 16h5m18 0h5M6 6l4 4m12 12 4 4M6 26l4-4M22 10l4-4"/></svg></span><span><strong>AI Leaf Analysis</strong><small>Insights from your leaf photo</small></span></div><div><span class="detect-feature-icon"><svg viewBox="0 0 32 32"><path d="M26 5C9 5 5 13 9 23c12 3 19-5 17-18ZM7 27l14-15"/></svg></span><span><strong>Plant Disease Library</strong><small>Explore common plant conditions</small></span></div><div><span class="detect-feature-icon"><svg viewBox="0 0 32 32"><path d="M16 3 27 7v9c0 7-11 13-11 13S5 23 5 16V7Z"/><path d="m11 16 4 4 8-9"/></svg></span><span><strong>Care Recommendations</strong><small>Symptoms and plant-care tips</small></span></div></div>')
    # This local script sizes the composition only; uploaded/provider content never enters it.
    standalone = "true" if st.session_state.get("page") == "Detect" else "false"
    st.html(DETECT_LAYOUT_SCRIPT.replace("__STANDALONE__", standalone), unsafe_allow_javascript=True)


DETECT_LAYOUT_SCRIPT = """<script>
(() => {
  window.__plantcareDetectCleanup?.();
  const page=document.querySelector('.st-key-detect-page');
  const navbar=document.querySelector('.st-key-navbar');
  if(!page)return;
  const events=new AbortController(), options={signal:events.signal};
  page.id='detect';
  const update=()=>{
    const viewport=window.visualViewport?.height || window.innerHeight;
    const header=__STANDALONE__ && navbar ? navbar.getBoundingClientRect().height+28 : 0;
    page.style.setProperty('--detect-stage-h',Math.max(1,viewport-header)+'px');
  };
  update();
  const observer=new ResizeObserver(update);if(navbar)observer.observe(navbar);
  window.addEventListener('resize',update,options);
  window.visualViewport?.addEventListener('resize',update,options);
  document.addEventListener('click',event=>{
    if(event.defaultPrevented || event.button!==0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey)return;
    const link=event.target.closest?.('a[href="#detect"]');
    if(!link)return;
    event.preventDefault();
    page.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
  },options);
  window.__plantcareDetectCleanup=()=>{observer.disconnect();events.abort();};
})();
</script>"""
