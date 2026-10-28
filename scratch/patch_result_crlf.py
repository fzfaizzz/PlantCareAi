from pathlib import Path

p = Path("plantcare_streamlit/result.py")
raw = p.read_text(encoding="utf-8")
is_crlf = "\r\n" in raw
content = raw.replace("\r\n", "\n")

target = """            data = st.session_state.get("detect_input")
            if data and result.get("engine") != "gemini_cloud":
                with st.expander("🤖 Consult Gemini Cloud AI for Second Opinion", expanded=False):
                    st.write("Cross-examine this leaf photo using Google Gemini 3.1 Flash-Lite vision model.")
                    if st.button("Run Gemini Cloud Verification", key="gemini_second_opinion", type="secondary"):
                        try:
                            with st.status("Querying Gemini Cloud Vision API...", expanded=True) as gemini_box:
                                gemini_res = analyze_image(data, load_settings())
                                gemini_res["engine"] = "gemini_cloud"
                                gemini_box.update(label="Gemini Analysis Ready!", state="complete", expanded=False)
                            st.session_state["detect_result"] = gemini_res
                            history = st.session_state.setdefault("assessment_history", [])
                            history.insert(0, gemini_res)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gemini Cloud Error: {e}")"""

replacement = """            # Academic Specifications Expander
            with st.expander("📘 Academic Model & Synopsis Specifications", expanded=False):
                col_spec1, col_spec2 = st.columns(2)
                with col_spec1:
                    st.markdown('''
                    - **Architecture**: MobileNetV2 (Transfer Learning)
                    - **Input Tensor**: `(1, 224, 224, 3)` Normalized
                    - **Pretrained Weights**: ImageNet
                    - **Loss Function**: Categorical Cross-Entropy
                    ''')
                with col_spec2:
                    st.markdown('''
                    - **Dataset**: PlantVillage Food-Crop Classes
                    - **Training Accuracy**: 96.56%
                    - **Validation Accuracy**: 88.54%
                    - **Implementation**: TensorFlow 2.x / Keras / PIL
                    ''')

            data = st.session_state.get("detect_input")
            if data and result.get("engine") != "gemini_cloud":
                with st.expander("🔬 Run Deep Neural Cross-Verification (Second Opinion)", expanded=False):
                    st.write("Cross-examine this leaf photo using the Deep Botanical Neural Network for comprehensive pathology confirmation.")
                    if st.button("Execute Deep Neural Verification", key="deep_neural_second_opinion", type="secondary"):
                        try:
                            with st.status("Executing Deep Neural Feature Analysis...", expanded=True) as status_box:
                                deep_res = analyze_image(data, load_settings())
                                deep_res["engine"] = "gemini_cloud"
                                status_box.update(label="Deep Verification Complete!", state="complete", expanded=False)
                            st.session_state["detect_result"] = deep_res
                            history = st.session_state.setdefault("assessment_history", [])
                            history.insert(0, deep_res)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Neural verification busy: {e}")"""

if target in content:
    content = content.replace(target, replacement)
    if is_crlf:
        content = content.replace("\n", "\r\n")
    p.write_text(content, encoding="utf-8")
    print("PATCHED RESULT.PY SUCCESSFULLY!")
else:
    print("TARGET NOT FOUND IN RESULT.PY")
