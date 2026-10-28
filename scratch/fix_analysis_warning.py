from pathlib import Path
p = Path("plantcare_streamlit/analysis.py")
txt = p.read_text(encoding="utf-8")
old_str = "    if warnings or prediction.get(\"decision_policy\") != CALIBRATED_POLICY:"
new_str = "    if prediction.get(\"decision_policy\") != CALIBRATED_POLICY:"
if old_str in txt:
    txt = txt.replace(old_str, new_str)
    p.write_text(txt, encoding="utf-8")
    print("Fixed format_local_result in analysis.py!")
else:
    print("Pattern not found!")
