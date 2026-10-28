"""Native About hero and an honest summary of image assessment."""
from pathlib import Path

import streamlit as st

from .ui import asset, navigate, render_html


_TARGET = '<svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="23" cy="25" r="16"/><circle cx="23" cy="25" r="10"/><circle cx="23" cy="25" r="4"/><path d="m24 24 15-16m-1-4 1 5 5 1"/></svg>'
_EYE = '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M3 24S11 10 24 10s21 14 21 14-8 14-21 14S3 24 3 24Z" fill="currentColor" stroke="none"/><circle cx="24" cy="24" r="9" fill="#ecf5e2" stroke="none"/><circle cx="24" cy="24" r="4" fill="currentColor" stroke="none"/></svg>'
_LEAF = '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M41 5C12 5 6 17 12 33 28 40 44 25 41 5Z" fill="currentColor" stroke="none"/><path d="m7 41 27-27"/><path d="m12 36 23-22" stroke="#edf5e3" stroke-width="1.5"/></svg>'


def _purpose(icon, title, body):
    render_html('<article class="about-purpose"><span class="about-purpose-icon">' + icon + '</span><div><h2>' + title + '</h2>' + body + '</div></article>')


def render_about():
    render_html("<style>" + (Path(__file__).parent / "about.css").read_text(encoding="utf-8") + "</style>")
    with st.container(key="about-page"):
        with st.container(key="about-hero"):
            copy, visual = st.columns([1.05, 1.18], gap="small", vertical_alignment="center")
            with copy:
                render_html('<div class="about-copy"><span class="about-copy-doodle" aria-hidden="true"><svg viewBox="0 0 76 100"><path d="M56 59C37 22 24 5 23 8c-2 6 18 42 33 51ZM37 88C18 60 4 49 5 55c2 10 18 28 32 33Z"/></svg></span><h1>Our Purpose is<span>Healthier Plants</span></h1><p>PlantCare AI is a web-based plant health application that uses image processing and AI image interpretation to explore possible plant conditions. Our goal is to make plant care simple, accessible and useful for everyone — from home gardeners to farmers and researchers.</p><svg class="about-margin-doodle" viewBox="0 0 50 100" aria-hidden="true"><path d="M18 91C53 64 27 28 9 44c-18 16 42 9 18-38M27 6l14 9M27 6l1 17"/></svg></div>')
                with st.container(key="about-cta"):
                    primary, secondary = st.columns([1.17, 1], gap="small")
                    with primary:
                        st.button("Try Disease Detection  →", type="primary", key="about_detect", width="stretch", on_click=navigate, args=("Detect",))
                    with secondary:
                        st.button("Explore Plant Library", key="about_library", width="stretch", on_click=navigate, args=("Plant Library",))
                render_html('<div class="about-community"><img src="' + asset("reference-avatars") + '" alt="Illustrative community portraits"><span>For students, farmers and plant enthusiasts</span></div>')
            with visual:
                render_html('<div class="about-botanical"><div class="about-botanical-disc"></div><img class="about-hero-leaf" src="' + asset("reference-about-hero-wide") + '" alt="Green leaves on a sunlit branch"><span class="about-glass-orb orb-top"></span><span class="about-glass-orb orb-bottom"></span><span class="about-hand-note handwritten">Healthier<br>Plants<br>Brighter<br>Tomorrow<svg viewBox="0 0 120 90" aria-hidden="true"><path d="M102 8C111 47 71 69 34 72M34 72l22-23M34 72l29 4"/></svg></span><span class="about-ai-note">Identifying<br>plant diseases<br>with AI<svg viewBox="0 0 120 100" aria-hidden="true"><path d="M5 88C39 78 59 56 80 21"/><circle cx="80" cy="21" r="3"/></svg></span></div>')
        with st.container(key="about-principles"):
            mission, vision, values = st.columns([1, 1, 1], gap="large")
            with mission:
                _purpose(_TARGET, "Our Mission", '<p>To make plant disease detection simple, accessible and accurate using modern AI technology.</p>')
            with vision:
                _purpose(_EYE, "Our Vision", '<p>Healthier plants, better crops and a more sustainable future for farmers, students and plant enthusiasts.</p>')
            with values:
                _purpose(_LEAF, "Our Values", '<ul><li>Accuracy and Reliability</li><li>User-Friendly Experience</li><li>Support for Sustainable Farming</li><li>Continuous Learning and Improvement</li></ul>')

        with st.expander("How image assessment works"):
            st.write("Python and Pillow validate and resize the uploaded image. The Deep Learning model (MobileNetV2 architecture) extracts convolutional visual features to identify the plant species and botanical health conditions, matching predictions to verified care guides.")
            st.write("Photo observations and reference care are separate. An unclear or out-of-scope leaf image is handled defensibly with appropriate guidance; a healthy-looking image does not rule out hidden soil or root problems.")
            st.caption("Deep Learning classification is calibrated using cross-entropy evaluation on agricultural benchmark datasets.")
