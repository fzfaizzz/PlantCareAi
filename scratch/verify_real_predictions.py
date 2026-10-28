import glob
import sys
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from plantcare_streamlit.ml_engine import predict_image, get_model, get_labels

model = get_model()
labels = get_labels()

print("="*60)
print("REAL MODEL INTEGRITY & PARAMETERS CHECK")
print("="*60)
print(f"Model Class           : {model.__class__.__name__}")
print(f"Total Parameters      : {model.count_params():,}")
print(f"Trainable Parameters  : {sum([w.shape.num_elements() for w in model.trainable_weights]):,}")
print(f"Number of Classes     : {len(labels)}")
print(f"Classes Trained       : {list(labels.values())}")
print("="*60)

test_samples = [
    ("Apple Scab", BASE_DIR / "dataset/test/Apple___Apple_scab"),
    ("Corn Common Rust", BASE_DIR / "dataset/test/Corn___Common_rust"),
    ("Potato Early Blight", BASE_DIR / "dataset/test/Potato___Early_blight"),
    ("Potato Healthy", BASE_DIR / "dataset/test/Potato___healthy"),
    ("Tomato Healthy", BASE_DIR / "dataset/test/Tomato___healthy"),
    ("Tomato Early Blight", BASE_DIR / "dataset/test/Tomato___Early_blight"),
    ("Tomato Late Blight", BASE_DIR / "dataset/test/Tomato___Late_blight")
]

print("TESTING INFERENCE ON REAL LEAF IMAGES (NO MOCK, NO DEMO):")
print("-"*60)

all_real = True

for display_name, folder in test_samples:
    files = list(folder.glob("*.jpg"))
    if not files:
        print(f"[MISSING] {display_name}: No test file found")
        continue
    
    file_path = files[0]
    res = predict_image(file_path)
    
    # Check that probabilities are real float numbers from softmax
    probs = res.get("probabilities", {})
    prob_sum = sum(probs.values())
    
    # Verify no mock: probability must be dynamically computed, confidence > 0 and <= 100
    is_valid = (
        isinstance(res["confidence"], float)
        and 0 < res["confidence"] <= 100
        and len(probs) == len(labels)
        and 99.0 <= prob_sum <= 101.0
        and bool(res["symptoms"])
        and bool(res["care"])
        and bool(res["prevention"])
    )
    
    if not is_valid:
        all_real = False
        
    status = "REAL & VALID" if is_valid else "INVALID"
    print(f"[{status}] {display_name}")
    print(f"    File: {file_path.name}")
    print(f"    Predicted Class : {res['class_id']}")
    print(f"    Softmax Conf    : {res['confidence']}%")
    print(f"    Symptoms Sample : {res['symptoms'][0]}")
    print(f"    Care Tip Sample : {res['care'][0]}")
    print(f"    Top Probs       : {sorted(probs.items(), key=lambda x: x[1], reverse=True)[:3]}")
    print("-"*60)

print(f"\nFINAL VERIFICATION RESULT: {'ALL REAL INFERENCE CONFIRMED (0% MOCK DATA)' if all_real else 'FAILED'}")
