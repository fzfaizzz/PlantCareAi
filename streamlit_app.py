from pathlib import Path
import streamlit as st
from plantcare_streamlit.ui import asset, render_html, decorations, navigate, esc, render_theme, entrance
from plantcare_streamlit.home import render_home
from plantcare_streamlit.detect import render_detect
from plantcare_streamlit.library import render_library
from plantcare_streamlit.about import render_about

st.set_page_config(page_title="PlantCare AI - A greener tomorrow", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")
render_theme()
entrance()
decorations()
allowed = ["Home", "Plant Library", "About", "Detect"]
if "page" not in st.session_state:
    st.session_state.page = st.query_params.get("page", "Home")
if st.session_state.page not in allowed:
    st.session_state.page = "Home"

with st.container(key="navbar"):
    brand, center_nav, end_action = st.columns([1, 1, 1], vertical_alignment="center", gap="small")
    with brand:
        render_html('<a class="brand" href="?page=Home"><span class="brand-leaf"></span><span>PlantCare AI</span></a>')
    with center_nav:
        with st.container(key="navbar-links"):
            home_link, library_link = st.columns([1, 1.35], gap="small")
            with home_link:
                st.button("Home", key="nav_Home", type="primary" if st.session_state.page == "Home" else "tertiary", on_click=navigate, args=("Home",), width="stretch")
            with library_link:
                st.button("Plant Library", key="nav_Plant Library", type="primary" if st.session_state.page == "Plant Library" else "tertiary", on_click=navigate, args=("Plant Library",), width="stretch")
    with end_action:
        with st.container(key="navbar-about"):
            st.button("About", key="nav_About", type="primary", on_click=navigate, args=("About",), width="stretch")

if st.session_state.page == "Home":
    render_home()
    render_detect()
elif st.session_state.page == "Detect":
    render_detect()
elif st.session_state.page == "Plant Library":
    render_library()
else:
    render_about()
