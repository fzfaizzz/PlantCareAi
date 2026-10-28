import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
from plantcare_streamlit.services import load_settings, analyze_image

settings = load_settings()
test_image_path = Path("public/assets/plants/sample-leaf-spotted.webp")
image_bytes = test_image_path.read_bytes()

res = analyze_image(image_bytes, settings)
print(json.dumps(res, indent=2))
