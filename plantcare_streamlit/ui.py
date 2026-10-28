import base64
import html
from functools import lru_cache
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "public" / "assets" / "plants"

def esc(value):
    return html.escape(str(value), quote=True)

@lru_cache(maxsize=64)
def asset(name):
    name = name if name.endswith(".webp") else name + ".webp"
    path = (ASSETS / name).resolve()
    if path.parent != ASSETS.resolve():
        raise ValueError("Invalid asset path")
    return "data:image/webp;base64," + base64.b64encode(path.read_bytes()).decode()

def render_html(markup):
    st.html(markup)

def navigate(page):
    st.session_state["page"] = page
    st.query_params["page"] = page


def decorations():
    render_html(f'''<div class="botanical-frame" aria-hidden="true"><img class="corner upper-left" src="{asset('reference-leaf-upper-left')}"><img class="corner upper-right" src="{asset('reference-leaf-upper-right')}"><img class="corner lower-left" src="{asset('home-foliage-bottom-left')}"><img class="corner lower-right" src="{asset('home-foliage-bottom-right')}"></div>''')


def render_theme():
    font_rules = []
    for file_name, family in [("inter", "PlantInter"), ("inter-tight", "PlantTight"), ("caveat", "Caveat")]:
        encoded = base64.b64encode((ROOT / "plantcare_streamlit/assets/fonts" / (file_name + ".woff2")).read_bytes()).decode()
        font_rules.append("@font-face{font-family:'" + family + "';src:url(data:font/woff2;base64," + encoded + ");font-weight:100 900;font-display:swap}")
    render_html("<style>" + "".join(font_rules) + (ROOT / "plantcare_streamlit/theme.css").read_text(encoding="utf-8") + "</style>")


def entrance():
    if st.session_state.get("entrance_shown"):
        return
    st.session_state["entrance_shown"] = True
    render_html('<div class="plant-entrance" aria-hidden="true"><div class="entrance-sculpture"><i></i><b></b><span></span></div><strong>PlantCare AI</strong><small>A greener tomorrow</small></div>')
