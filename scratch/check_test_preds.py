import os
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
os.environ["KERAS_HOME"] = str(BASE_DIR / ".keras")
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
from plantcare_streamlit.ml_engine import predict_image

for c in ["Potato___Late_blight", "Tomato___Early_blight"]:
    print(f"=== Testing {c} ===")
    for p in sorted((BASE_DIR / "dataset" / "test" / c).glob("*.jpg")):
        res = predict_image(p)
        print(f"  {p.name} --> {res['class_id']} ({res['confidence']}%)")
