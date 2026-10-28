from pathlib import Path

def patch():
    p = Path("plantcare_streamlit/result.py")
    content = p.read_text(encoding="utf-8")
    
    # 1. Update imports
    old_import = "from .services import AnalysisError, catalog_entries, prepare_image"
    new_import = "from .services import AnalysisError, analyze_image, catalog_entries, load_settings, prepare_image"
    
    # 2. Update score_label
    old_score = 'score_label = "Reported model score" if has_score else "Not provided by Gemini"'
    new_score = 'score_label = "MobileNetV2 Model Score" if has_score else "Gemini Cloud Analysis"'
    
    # 3. Add probabilities and second-opinion expanders
    old_actions_end = """                with share:
                    if st.button("Share Result", icon=":material/share:", key="result-share", width="stretch"):
                        _share_dialog(result)
            with st.expander("Sources & assessment notes"):"""
            
    new_actions_end = """                with share:
                    if st.button("Share Result", icon=":material/share:", key="result-share", width="stretch"):
                        _share_dialog(result)

            if result.get("probabilities"):
                with st.expander("📊 Model Confidence Breakdown (Softmax Class Probabilities)", expanded=False):
                    probs = result["probabilities"]
                    sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
                    for cls_name, prob in sorted_probs:
                        c1, c2 = st.columns([3, 1])
                        clean_name = cls_name.replace("___", " — ").replace("_", " ")
                        c1.markdown(f"**{clean_name}**")
                        c2.markdown(f"`{prob:.1f}%`")
                        st.progress(min(max(prob / 100.0, 0.0), 1.0))

            data = st.session_state.get("detect_input")
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
                            st.error(f"Gemini Cloud Error: {e}")

            with st.expander("Sources & assessment notes"):"""

    content_normalized = content.replace("\r\n", "\n")
    if old_import in content_normalized and old_score in content_normalized and old_actions_end in content_normalized:
        content_normalized = content_normalized.replace(old_import, new_import)
        content_normalized = content_normalized.replace(old_score, new_score)
        content_normalized = content_normalized.replace(old_actions_end, new_actions_end)
        p.write_text(content_normalized, encoding="utf-8")
        print("SUCCESSFULLY PATCHED result.py!")
    else:
        print("TARGET BLOCKS NOT FOUND IN result.py")
        if old_import not in content_normalized:
            print("old_import not found")
        if old_score not in content_normalized:
            print("old_score not found")
        if old_actions_end not in content_normalized:
            print("old_actions_end not found")

if __name__ == "__main__":
    patch()
