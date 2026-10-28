from pathlib import Path

def patch():
    p = Path("plantcare_streamlit/detect.py")
    content = p.read_text(encoding="utf-8")
    
    # Replace radio button with actions + hidden toggle
    old_block = """                        col_mode1, col_mode2 = st.columns([2, 1])
                        with col_mode1:
                            engine_mode = st.radio(
                                "Analyze this image using",
                                ["Trained TensorFlow/Keras Model (100% Offline / Fast)", "Gemini Cloud API (Online)"],
                                format_func=lambda value: "On this device" if "TensorFlow" in value else "Gemini cloud analysis",
                                index=0,
                                horizontal=True,
                                key="engine_choice"
                            )

                        if "Gemini" in engine_mode:
                            st.caption("Cloud analysis sends a resized photo to Google Gemini.")
                        actions = st.columns([2, 1])
                        with actions[0]:
                            analyze_clicked = st.button("Detect Disease  →", type="primary",
                                                        key="run-detection", width="stretch")
                        with actions[1]:
                            st.button("Remove", on_click=_remove_image, key="remove-leaf", width="stretch")"""
                            
    new_block = """                        actions = st.columns([2, 1])
                        with actions[0]:
                            analyze_clicked = st.button("Detect Disease  →", type="primary",
                                                        key="run-detection", width="stretch")
                        with actions[1]:
                            st.button("Remove", on_click=_remove_image, key="remove-leaf", width="stretch")

                        # Hidden / Advanced AI Expander (Collapsed by default, offline DL is standard)
                        with st.expander("⚙️ Advanced AI Engine Settings", expanded=False):
                            use_gemini = st.toggle(
                                "Enable Gemini 3.1 Multimodal Vision (Cloud)",
                                value=False,
                                key="enable_gemini_vision",
                                help="Switch from offline TensorFlow MobileNetV2 to online Google Gemini Vision API."
                            )
                            if use_gemini:
                                st.info("☁️ **Gemini Cloud Vision Active**: Leaf photo will be processed by Google Gemini. (Automatic fallback to local ML if offline).")
                            else:
                                st.caption("⚡ **Local Offline DL Engine (Default)**: MobileNetV2 Neural Network running 100% locally on CPU.")"""

    old_logic = """                                    result = None
                                    if "Gemini" in engine_mode:
                                        try:
                                            with st.status("Analyzing via Gemini Cloud API...", expanded=True) as pending:
                                                result = analyze_image(data, load_settings())
                                                pending.update(label="Cloud Assessment Ready", state="complete", expanded=False)
                                        except Exception:
                                            # Fallback immediately to offline model if Gemini fails or times out
                                            st.warning("Cloud API was unavailable or slow. Seamlessly switched to local Trained Model!")
                                            result = None"""

    new_logic = """                                    result = None
                                    if use_gemini:
                                        try:
                                            with st.status("Analyzing via Gemini Cloud API...", expanded=True) as pending:
                                                result = analyze_image(data, load_settings())
                                                result["engine"] = "gemini_cloud"
                                                pending.update(label="Cloud Assessment Ready", state="complete", expanded=False)
                                        except Exception as exc:
                                            # Fallback immediately to offline model if Gemini fails or times out
                                            st.warning(f"Gemini Cloud API was unavailable or slow ({exc}). Seamlessly switched to local Trained Model!")
                                            result = None"""

    # Also add "engine": "local_tensorflow" to the local result dictionary
    old_local_res = """"probabilities": ml_res.get("probabilities", {})
                                            }"""
    new_local_res = """"probabilities": ml_res.get("probabilities", {}),
                                                "engine": "local_tensorflow"
                                            }"""

    # Normalize line endings for replacement
    content_normalized = content.replace("\r\n", "\n")
    if old_block in content_normalized and old_logic in content_normalized:
        content_normalized = content_normalized.replace(old_block, new_block)
        content_normalized = content_normalized.replace(old_logic, new_logic)
        content_normalized = content_normalized.replace(old_local_res, new_local_res)
        p.write_text(content_normalized, encoding="utf-8")
        print("SUCCESSFULLY PATCHED detect.py!")
    else:
        print("TARGET BLOCKS NOT FOUND")
        if old_block not in content_normalized:
            print("old_block failed to match")
        if old_logic not in content_normalized:
            print("old_logic failed to match")

if __name__ == "__main__":
    patch()
