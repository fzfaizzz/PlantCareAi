import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
from plantcare_streamlit.ml_engine import predict_image

for img_p in [
    Path("public/assets/plants/sample-leaf-spotted.webp"),
    Path("public/assets/plants/sample-leaf-healthy.webp"),
    Path("public/assets/plants/sample-leaf-closeup.webp"),
]:
    if img_p.exists():
        res = predict_image(img_p.read_bytes())
        print("Image:", img_p.name)
        print("  Plant:", res.get("plant"))
        print("  Condition:", res.get("condition"))
        print("  Confidence:", res.get("confidence"))
        print("  Slug:", res.get("slug"))
