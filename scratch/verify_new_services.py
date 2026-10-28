import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
from plantcare_streamlit.services import load_settings, analyze_image

settings = load_settings()
img_bytes = Path("public/assets/plants/sample-leaf-spotted.webp").read_bytes()

res = analyze_image(img_bytes, settings)
print("=== GEMINI NEW RESULT ===")
print("Plant:", res["plant"])
print("Condition:", res["condition"])
print("Confidence:", res["confidence"])
print("Symptoms (count):", len(res["symptoms"]), res["symptoms"][:2])
print("Care (count):", len(res["care"]), res["care"][:2])
print("Prevention (count):", len(res["prevention"]), res["prevention"][:2])
print("Catalog slug:", res["catalog"]["slug"])
