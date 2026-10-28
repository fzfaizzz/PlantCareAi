import os
import sys
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from plantcare_streamlit.ml_engine import predict_image

test_dir = BASE_DIR / "dataset" / "test"
classes = sorted([d.name for d in test_dir.iterdir() if d.is_dir()])

print(f"==================================================")
print(f"VERIFYING ALL {len(classes)} PLANTVILLAGE CLASSES")
print(f"==================================================")

total = 0
correct = 0

for cls in classes:
    imgs = list((test_dir / cls).glob("*.jpg"))
    if not imgs:
        print(f"[WARN] No test images found for {cls}")
        continue
    sample = imgs[0]
    res = predict_image(sample)
    total += 1
    is_match = (res["class_id"] == cls)
    if is_match:
        correct += 1
        status = "PASS"
    else:
        status = "FAIL"
    
    # Check care catalog presence
    has_symptoms = bool(res.get("symptoms"))
    has_care = bool(res.get("care"))
    has_prevention = bool(res.get("prevention"))
    meta_ok = has_symptoms and has_care and has_prevention

    print(f"[{status}] {cls}")
    print(f"       Predicted : {res['class_id']} ({res['confidence']}%)")
    print(f"       Plant/Cond: {res['plant']} - {res['condition']}")
    print(f"       Care Info : Symptoms: {has_symptoms}, Care: {has_care}, Prev: {has_prevention}")
    print("--------------------------------------------------")

acc = (correct / total) * 100 if total else 0
print(f"\nFinal Test Set Check: {correct}/{total} matched ({acc:.1f}%)")
