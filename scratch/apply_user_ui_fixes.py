import re
from pathlib import Path

def patch_result_py():
    p = Path("plantcare_streamlit/result.py")
    raw = p.read_text(encoding="utf-8")
    is_crlf = "\r\n" in raw
    content = raw.replace("\r\n", "\n")

    # 1. In photo_col: Remove thumbnails and replace with left-actions (Analyse Another Leaf + Download Result)
    old_photo_thumbs = """        with photo_col:
            render_html('<div class="result-photo"><img style="--photo-zoom:' + str(zoom) + '" src="' + photo + '" alt="Your uploaded leaf"><span class="uploaded-badge"><span aria-hidden="true">▧</span> Uploaded Image</span><span class="result-grid"></span><span class="result-light-line" aria-hidden="true"></span><i class="photo-corner tl"></i><i class="photo-corner tr"></i><i class="photo-corner bl"></i><i class="photo-corner br"></i></div>')
            with st.container(key="result-thumbs"):
                thumbnails = st.columns([1, 1, 1, 1.1], gap="small")
                for index, column in enumerate(thumbnails[:3]):
                    with column:
                        with st.container(key="result-thumb-" + str(index)):
                            selected = " selected" if st.session_state.get("result_photo_view", 0) == index else ""
                            render_html('<div class="result-thumbnail' + selected + '"><img style="--thumb-zoom:' + str([1, 1.4, 1.8][index]) + '" src="' + photo + '" alt="Detail view ' + str(index + 1) + ' of uploaded image"></div>')
                            st.button(["View full photo", "View leaf detail", "View closer detail"][index], key="result-view-" + str(index), on_click=_view, args=(index,), width="stretch")
                with thumbnails[3]:
                    with st.container(key="result-add"):
                        st.button("⊕\\nAdd Another", key="result-add-another", on_click=on_another, width="stretch")"""

    new_photo_thumbs = """        with photo_col:
            render_html('<div class="result-photo"><img style="--photo-zoom:1" src="' + photo + '" alt="Your uploaded leaf"><span class="uploaded-badge"><span aria-hidden="true">🌿</span> Uploaded Image</span><span class="result-grid"></span><span class="result-light-line" aria-hidden="true"></span><i class="photo-corner tl"></i><i class="photo-corner tr"></i><i class="photo-corner bl"></i><i class="photo-corner br"></i></div>')
            with st.container(key="result-actions"):
                another, download = st.columns([1.18, 1], gap="small")
                with another:
                    st.button("Analyse Another Leaf", icon=":material/eco:", type="primary", key="result-another", on_click=on_another, width="stretch")
                with download:
                    st.download_button("Download Result", _report_html(result, photo), file_name="PlantCare-leaf-result.html", mime="text/html", icon=":material/download:", key="result-download", width="stretch")"""

    # 2. In detail_col: Remove top model banner
    old_banner_code = """render_html('<div class="engine-badge-banner">' + ('<div style="background:#e8f4fc;border:1px solid #c2e7ff;border-radius:10px;padding:8px 14px;font-size:13px;color:#0b57d0;font-weight:600;margin-bottom:12px;display:flex;align-items:center;gap:8px"><span>🔬</span> Model: Advanced Deep Botanical Neural Network (High-Resolution Visual Analysis)</div>' if result.get("engine") == "gemini_cloud" else '<div style="background:#edf7ed;border:1px solid #c8e6c9;border-radius:10px;padding:8px 14px;font-size:13px;color:#1b5e20;font-weight:600;margin-bottom:12px;display:flex;align-items:center;gap:8px"><span>⚡</span> Model: MobileNetV2 Convolutional Neural Network (PlantVillage Trained · 96.5% Accuracy)</div>' ) + '</div><article class="result-summary">"""
    new_banner_code = """render_html('<article class="result-summary">"""

    # 3. In detail_col: Remove old bottom actions with Share button
    old_bottom_actions = """            with st.container(key="result-actions"):
                another, download, share = st.columns([1.3, 1, 1.05], gap="small")
                with another:
                    st.button("Analyse Another Leaf", icon=":material/eco:", type="primary", key="result-another", on_click=on_another, width="stretch")
                with download:
                    st.download_button("Download Result", _report_html(result, photo), file_name="PlantCare-leaf-result.html", mime="text/html", icon=":material/download:", key="result-download", width="stretch")
                with share:
                    if st.button("Share Result", icon=":material/share:", key="result-share", width="stretch"):
                        _share_dialog(result)"""

    assert old_photo_thumbs in content, "old_photo_thumbs not found in result.py"
    assert old_banner_code in content, "old_banner_code not found in result.py"
    assert old_bottom_actions in content, "old_bottom_actions not found in result.py"

    content = content.replace(old_photo_thumbs, new_photo_thumbs)
    content = content.replace(old_banner_code, new_banner_code)
    content = content.replace(old_bottom_actions, "")

    if is_crlf:
        content = content.replace("\n", "\r\n")
    p.write_text(content, encoding="utf-8")
    print("SUCCESS: plantcare_streamlit/result.py updated!")

def patch_result_css():
    p = Path("plantcare_streamlit/result.css")
    raw = p.read_text(encoding="utf-8")
    is_crlf = "\r\n" in raw
    content = raw.replace("\r\n", "\n")

    # Add margin-top for result-actions placed under photo
    add_css = """
.result-photo + .st-key-result-actions {margin-top: 14px!important;}
.result-photo + .st-key-result-actions [data-testid=stHorizontalBlock] {gap: 10px!important;}
.result-photo + .st-key-result-actions button, .result-photo + .st-key-result-actions [data-testid=stDownloadButton] button {min-height: 48px!important; padding: 10px 12px!important;}
"""
    if "result-photo + .st-key-result-actions" not in content:
        content += add_css
        if is_crlf:
            content = content.replace("\n", "\r\n")
        p.write_text(content, encoding="utf-8")
        print("SUCCESS: plantcare_streamlit/result.css updated!")

def patch_detect_py():
    p = Path("plantcare_streamlit/detect.py")
    raw = p.read_text(encoding="utf-8")
    is_crlf = "\r\n" in raw
    content = raw.replace("\r\n", "\n")

    # When an image is selected, don't show the empty dropzone above the preview!
    target = """            with center:
                with st.container(key="leaf-upload", border=True):
                    _render_detect_html('<div class="upload-cloud" aria-hidden="true"><svg viewBox="0 0 48 48"><path d="M13 34C1 33 2 17 13 17c1-13 21-16 25-2 12 1 14 18 2 20M24 39V19m-8 8 8-8 8 8"/></svg></div>'
                                '<h3 class="upload-title">Drag & drop a leaf image here</h3>'
                                '<p class="upload-subtitle">or click to browse files</p>'
                                '<p class="upload-support">Supports JPG, JPEG, PNG, WebP (Max 10 MB)</p>')
                    st.file_uploader("Choose a leaf image", type=["jpg", "jpeg", "png", "webp"],
                                     accept_multiple_files=False, key="detect_file", on_change=_selected_upload,
                                     label_visibility="collapsed")
                _render_detect_html('<p class="upload-privacy"><svg viewBox="0 0 20 20" aria-hidden="true"><rect x="4" y="8" width="12" height="10" rx="2"/><path d="M7 8V5a3 3 0 0 1 6 0v3M10 12v3"/></svg> Your photo is not saved by this app.</p>')

                data = st.session_state.get("detect_input")
                if data:"""

    replacement = """            with center:
                data = st.session_state.get("detect_input")
                if not data:
                    with st.container(key="leaf-upload", border=True):
                        _render_detect_html('<div class="upload-cloud" aria-hidden="true"><svg viewBox="0 0 48 48"><path d="M13 34C1 33 2 17 13 17c1-13 21-16 25-2 12 1 14 18 2 20M24 39V19m-8 8 8-8 8 8"/></svg></div>'
                                    '<h3 class="upload-title">Drag & drop a leaf image here</h3>'
                                    '<p class="upload-subtitle">or click to browse files</p>'
                                    '<p class="upload-support">Supports JPG, JPEG, PNG, WebP (Max 10 MB)</p>')
                        st.file_uploader("Choose a leaf image", type=["jpg", "jpeg", "png", "webp"],
                                         accept_multiple_files=False, key="detect_file", on_change=_selected_upload,
                                         label_visibility="collapsed")
                    _render_detect_html('<p class="upload-privacy"><svg viewBox="0 0 20 20" aria-hidden="true"><rect x="4" y="8" width="12" height="10" rx="2"/><path d="M7 8V5a3 3 0 0 1 6 0v3M10 12v3"/></svg> Your photo is processed securely in real time.</p>')
                else:"""

    assert target in content, "target not found in detect.py"
    content = content.replace(target, replacement)
    if is_crlf:
        content = content.replace("\n", "\r\n")
    p.write_text(content, encoding="utf-8")
    print("SUCCESS: plantcare_streamlit/detect.py updated!")

def patch_detect_css():
    p = Path("plantcare_streamlit/detect.css")
    raw = p.read_text(encoding="utf-8")
    is_crlf = "\r\n" in raw
    content = raw.replace("\r\n", "\n")

    old_btn = ".st-key-leaf-upload [data-testid=stFileUploaderDropzone] button:after {content:'▧  Choose Image';font:500 calc(16 * var(--du))/1 PlantInter,Arial,sans-serif;color:white;white-space:nowrap}"
    new_btn = ".st-key-leaf-upload [data-testid=stFileUploaderDropzone] button:after {content:'📁  Choose Leaf Image';font:600 calc(15 * var(--du))/1 PlantInter,Arial,sans-serif;color:white;white-space:nowrap;letter-spacing:-.01em}"

    assert old_btn in content, "old_btn not found in detect.css"
    content = content.replace(old_btn, new_btn)
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
    brand, links, account = st.columns([3.2, 4.2, 2.2], vertical_alignment="center", gap="small")
    with brand:
        render_html('<a class="brand" href="?page=Home"><span class="brand-leaf"></span><span>PlantCare AI</span></a>')
    with links:
        nav = st.columns([1, 1.6, 1], gap="small")
        for col, name in zip(nav, ["Home", "Plant Library", "About"]):
            with col:
                st.button(name, key="nav_" + name, type="primary" if st.session_state.page == name else "tertiary", on_click=navigate, args=(name,), width="stretch")
    with account:
        login, signup = st.columns(2, gap="small")
        with login:
            if st.button("Hi, " + st.session_state.profile_name if st.session_state.get("profile_name") else "Log in", key="login", width="stretch"):
                profile_dialog()
        with signup:
            if st.button("Sign up", key="signup", type="primary", width="stretch"):
                profile_dialog()"""

    new_nav = """with st.container(key="navbar"):
    brand, links = st.columns([4.2, 5.8], vertical_alignment="center", gap="small")
    with brand:
        render_html('<a class="brand" href="?page=Home"><span class="brand-leaf"></span><span>PlantCare AI</span></a>')
    with links:
        nav = st.columns([1, 1.4, 1], gap="small")
        for col, name in zip(nav, ["Home", "Plant Library", "About"]):
            with col:
                st.button(name, key="nav_" + name, type="primary" if st.session_state.page == name else "tertiary", on_click=navigate, args=(name,), width="stretch")"""

    assert old_nav in content, "old_nav not found in streamlit_app.py"
    content = content.replace(old_nav, new_nav)
    if is_crlf:
        content = content.replace("\n", "\r\n")
    p.write_text(content, encoding="utf-8")
    print("SUCCESS: streamlit_app.py updated!")

def patch_test_app():
    p = Path("tests_streamlit/test_app.py")
    raw = p.read_text(encoding="utf-8")
    is_crlf = "\r\n" in raw
    content = raw.replace("\r\n", "\n")

    # In test_about_native_links_and_profile: remove login click
    old_about_test = """def test_about_native_links_and_profile():
    at = app("About")
    assert not at.exception
    at.button(key="about_library").click().run()
    assert at.session_state["page"] == "Plant Library"
    at.button(key="login").click().run()
    name = next(item for item in at.text_input if item.label == "Your first name")
    assert name.label == "Your first name"
    assert next(item for item in at.button if item.label == "Save profile")
    # Dialog fragment form submission is exercised in the real browser check.
    assert not at.exception"""

    new_about_test = """def test_about_native_links_and_profile():
    at = app("About")
    assert not at.exception
    at.button(key="about_library").click().run()
    assert at.session_state["page"] == "Plant Library"
    assert not at.exception"""

    # In test_real_result_renders_without_claiming_confirmation: result-share is removed, result-download is present
    old_result_test = """    assert at.button(key="result-another")
    assert at.button(key="result-share")"""

    new_result_test = """    assert at.button(key="result-another")
    assert at.download_button(key="result-download")
    assert not at.button(key="result-share")"""

    assert old_about_test in content, "old_about_test not found in test_app.py"
    assert old_result_test in content, "old_result_test not found in test_app.py"

    content = content.replace(old_about_test, new_about_test)
    content = content.replace(old_result_test, new_result_test)
    if is_crlf:
        content = content.replace("\n", "\r\n")
    p.write_text(content, encoding="utf-8")
    print("SUCCESS: tests_streamlit/test_app.py updated!")

if __name__ == "__main__":
    patch_result_py()
    patch_result_css()
    patch_detect_py()
    patch_detect_css()
    patch_streamlit_app()
    patch_test_app()
