from pathlib import Path

def patch_detect_css():
    p = Path("plantcare_streamlit/detect.css")
    raw = p.read_text(encoding="utf-8")
    is_crlf = "\r\n" in raw
    content = raw.replace("\r\n", "\n")

    target_block = """/* Exactly ONE button: the browse button */"""
    
    # We will replace lines 53-58 with bulletproof single-button rules
    old_css_part = """\
.st-key-leaf-upload [data-testid=stFileUploaderDropzoneInstructions],.st-key-leaf-upload [data-testid=stFileUploaderDropzone]>svg,.st-key-leaf-upload [data-testid=stFileUploaderFile],.st-key-leaf-upload [data-testid=stFileUploaderFileName] {display:none!important}
.st-key-leaf-upload [data-testid=stFileUploaderDropzone] button {width:56%!important;height:calc(48 * var(--du))!important;min-height:calc(48 * var(--du))!important;border-radius:calc(12 * var(--du))!important;background:linear-gradient(110deg,#095a40,#03412e)!important;border:0!important;padding:0 12px!important;font-size:0!important;color:transparent!important;display:flex;align-items:center;justify-content:center;box-shadow:0 5px 11px #10533210}
.st-key-leaf-upload [data-testid=stFileUploaderDropzone] button * {font-size:0!important;color:transparent!important}
.st-key-leaf-upload [data-testid=stFileUploaderDropzone] button:after {content:'📁  Choose Leaf Image';font:600 calc(15 * var(--du))/1 PlantInter,Arial,sans-serif;color:white;white-space:nowrap;letter-spacing:-.01em}"""

    new_css_part = """\
.st-key-leaf-upload [data-testid="stFileUploaderDropzoneInstructions"] > div:first-child,
.st-key-leaf-upload [data-testid="stFileUploaderDropzone"] > svg,
.st-key-leaf-upload [data-testid="stFileUploaderFile"],
.st-key-leaf-upload [data-testid="stFileUploaderFileName"],
.st-key-leaf-upload [data-testid="stFileUploaderFileData"],
.st-key-leaf-upload [data-testid="stFileUploaderDeleteBtn"],
.st-key-leaf-upload button[aria-label*="Delete"],
.st-key-leaf-upload button[aria-label*="Clear"],
.st-key-leaf-upload button[aria-label*="Remove"] {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  overflow: hidden !important;
}
.st-key-leaf-upload [data-testid="stFileUploaderDropzone"] button:not(:first-of-type) {
  display: none !important;
}
.st-key-leaf-upload [data-testid="stFileUploaderDropzone"] button:first-of-type {
  width: auto !important;
  min-width: calc(230 * var(--du)) !important;
  height: calc(48 * var(--du)) !important;
  min-height: calc(48 * var(--du)) !important;
  border-radius: calc(12 * var(--du)) !important;
  background: linear-gradient(110deg,#095a40,#03412e) !important;
  border: 0 !important;
  padding: 0 calc(24 * var(--du)) !important;
  font-size: 0 !important;
  color: transparent !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  box-shadow: 0 5px 14px rgba(9,90,64,0.2) !important;
  margin: 0 auto !important;
  cursor: pointer !important;
}
.st-key-leaf-upload [data-testid="stFileUploaderDropzone"] button:first-of-type * {
  display: none !important;
}
.st-key-leaf-upload [data-testid="stFileUploaderDropzone"] button:first-of-type:after {
  content: '📁  Choose Leaf Image' !important;
  font-family: PlantInter, Arial, sans-serif !important;
  font-size: calc(15 * var(--du)) !important;
  font-weight: 600 !important;
  color: #ffffff !important;
  white-space: nowrap !important;
  letter-spacing: -0.01em !important;
  display: block !important;
}"""

    assert old_css_part in content, "old_css_part not found in detect.css"
    content = content.replace(old_css_part, new_css_part)
    if is_crlf:
        content = content.replace("\n", "\r\n")
    p.write_text(content, encoding="utf-8")
    print("SUCCESS: plantcare_streamlit/detect.css updated!")

def patch_streamlit_app():
    p = Path("streamlit_app.py")
    raw = p.read_text(encoding="utf-8")
    is_crlf = "\r\n" in raw
    content = raw.replace("\r\n", "\n")

    old_nav = """with st.container(key="navbar"):
    brand, links = st.columns([4.2, 5.8], vertical_alignment="center", gap="small")
    with brand:
        render_html('<a class="brand" href="?page=Home"><span class="brand-leaf"></span><span>PlantCare AI</span></a>')
    with links:
        nav = st.columns([1, 1.4, 1], gap="small")
        for col, name in zip(nav, ["Home", "Plant Library", "About"]):
            with col:
                st.button(name, key="nav_" + name, type="primary" if st.session_state.page == name else "tertiary", on_click=navigate, args=(name,), width="stretch")"""

    new_nav = """with st.container(key="navbar"):
    brand, center_nav, end_action = st.columns([3.3, 4.7, 2.0], vertical_alignment="center", gap="small")
    with brand:
        render_html('<a class="brand" href="?page=Home"><span class="brand-leaf"></span><span>PlantCare AI</span></a>')
    with center_nav:
        nav = st.columns([1, 1.35], gap="small")
        with nav[0]:
            st.button("Home", key="nav_Home", type="primary" if st.session_state.page == "Home" else "tertiary", on_click=navigate, args=("Home",), width="stretch")
        with nav[1]:
            st.button("Plant Library", key="nav_Plant Library", type="primary" if st.session_state.page == "Plant Library" else "tertiary", on_click=navigate, args=("Plant Library",), width="stretch")
    with end_action:
        st.button("About", key="nav_About", type="primary", on_click=navigate, args=("About",), width="stretch")"""

    assert old_nav in content, "old_nav not found in streamlit_app.py"
    content = content.replace(old_nav, new_nav)
    if is_crlf:
        content = content.replace("\n", "\r\n")
    p.write_text(content, encoding="utf-8")
    print("SUCCESS: streamlit_app.py updated!")

if __name__ == "__main__":
    patch_detect_css()
    patch_streamlit_app()
