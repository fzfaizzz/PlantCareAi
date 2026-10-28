"""A searchable native Streamlit library of sourced plant care guides."""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from .ui import asset, esc, navigate, render_html

_DIRECTORY = Path(__file__).resolve().parent
_CATALOG = _DIRECTORY / "data" / "catalog.json"
_CARD_META = {
    "tomato-healthy": ("Tomato", "Green leaves without obvious disease-like spots.", "tomato-healthy-library"),
    "tomato-early-blight": ("Tomato", "Brown spots with rings, often starting on older leaves.", "tomato-early-blight-library"),
    "tomato-late-blight": ("Tomato", "Large brown patches that can spread across the leaf.", "tomato-leaf-spot-library"),
    "potato-healthy": ("Potato", "Green leaves without obvious disease-like markings.", "potato-healthy-library"),
    "potato-late-blight": ("Potato", "Dark patches and rapidly browning leaf tissue.", "potato-late-blight-library"),
    "apple-scab": ("Apple", "Olive-green to brown spots on leaves and fruit.", "apple-scab-library"),
    "apple-black-rot": ("Apple", "Leaf spots and dark lesions on fruit or branches.", "apple-black-rot-library"),
    "corn-healthy": ("Corn", "Green leaves without visible rust or disease-like spots.", "corn-healthy-library"),
    "corn-common-rust": ("Corn", "Small reddish-brown raised spots on the leaves.", "corn-common-rust-library"),
    "grape-powdery-mildew": ("Grape", "A white powdery coating on leaves and stems.", "grape-powdery-mildew-library"),
}


@st.cache_data(show_spinner=False)
def _load_entries() -> list[dict]:
    entries = json.loads(_CATALOG.read_text(encoding="utf-8"))
    return [entry for entry in entries if entry["slug"] in _CARD_META]


def _matches(entry: dict, query: str, category: str, plant: str) -> bool:
    if plant != "All Plants" and entry["plant"] != plant:
        return False
    if category == "Healthy" and entry["condition"].lower() != "healthy":
        return False
    if category not in {"All", "Healthy"} and entry["plant"] != category:
        return False
    haystack = " ".join([
        entry["plant"], entry["condition"], *entry.get("symptoms", []),
        _CARD_META[entry["slug"]][1],
    ]).lower()
    return all(word in haystack for word in query.lower().split())


def _clear_filters() -> None:
    st.session_state["library_search"] = ""
    st.session_state["library_plant"] = "All Plants"


@st.dialog("Plant care guide", width="large")
def _show_guide(entry: dict) -> None:
    _, description, image = _CARD_META[entry["slug"]]
    photo, copy = st.columns([1, 1.25], gap="large")
    with photo:
        st.image(asset(image), caption="AI-generated reference illustration.", width="stretch")
    with copy:
        st.caption(entry["plant"])
        st.subheader(entry["condition"])
        st.write(description)
        st.markdown("**What to look for**")
        for symptom in entry.get("symptoms", []):
            st.markdown(f"- {symptom}")
        st.markdown("**Care**")
        for instruction in entry.get("care", []):
            st.markdown(f"- {instruction}")
        if entry.get("prevention"):
            st.markdown("**Prevention**")
            for instruction in entry["prevention"]:
                st.markdown(f"- {instruction}")
        if entry.get("sources"):
            st.markdown("**Sources**")
            for source in entry["sources"]:
                st.link_button(source["title"] + " ↗", source["url"], width="stretch")
    st.caption("General reference information. Similar symptoms can have different causes.")
    st.button("Analyse a leaf", key=f"guide_detect_{entry['slug']}", type="primary", on_click=navigate, args=("Detect",), width="stretch")


def _card(entry: dict) -> None:
    _, description, image = _CARD_META[entry["slug"]]
    healthy = entry["condition"].lower() == "healthy"
    with st.container(border=True, key=f"library-card-{entry['slug']}"):
        render_html(f'''<article class="library-guide-card">
          <div class="library-guide-photo">
            <img src="{asset(image)}" alt="Illustration of {esc(entry['plant'])}: {esc(entry['condition'])}" loading="lazy">
            <span class="library-guide-status {'healthy' if healthy else 'condition'}">{'Healthy reference' if healthy else 'Condition guide'}</span>
          </div>
          <div class="library-guide-copy">
            <span class="library-guide-crop">{esc(entry['plant'])}</span>
            <h2>{esc(entry['condition'])}</h2>
            <p>{esc(description)}</p>
          </div>
        </article>''')
        if st.button("View guide →", key=f"guide_{entry['slug']}", width="stretch"):
            _show_guide(entry)


def render_library() -> None:
    render_html("<style>" + (_DIRECTORY / "library.css").read_text(encoding="utf-8") + "</style>")
    with st.container(key="library-page"):
        render_html('''<header class="library-heading"><h1>Plant Disease Library</h1><p>Find a plant or leaf problem. Open a guide for symptoms and care.</p></header>''')
        all_entries = _load_entries()
        plants = ["All Plants", *sorted({entry["plant"] for entry in all_entries})]
        if st.session_state.get("library_plant") not in plants:
            st.session_state["library_plant"] = "All Plants"
        with st.container(key="library-filters"):
            search_col, select_col = st.columns([3, 1], gap="medium")
            with search_col:
                query = st.text_input("Search guides", placeholder="Try tomato, leaf spots or healthy", key="library_search")
            with select_col:
                plant = st.selectbox("Plant", plants, key="library_plant")
        entries = [entry for entry in all_entries if _matches(entry, query, "All", plant)]
        count = len(entries)
        st.caption(f"{count} {'guide' if count == 1 else 'guides'}")
        if entries:
            with st.container(key="library-grid"):
                for entry in entries:
                    _card(entry)
        else:
            with st.container(border=True, key="library-empty"):
                st.subheader("No guides found")
                st.write("Try another plant or a simpler search, such as spots or healthy.")
                st.button("Clear filters", key="library_clear", on_click=_clear_filters)
        st.caption("Reference images are AI-generated illustrations. Care guides include source links.")
