"""
PlantCare AI - One-Click Environment & Dependency Diagnostic Script
Run this script to verify that all required packages, models, and configs are properly installed.
Usage: python check_environment.py
"""
import sys
import os
from pathlib import Path

# Fix Keras home path to project local directory
BASE_DIR = Path(__file__).resolve().parent
os.environ["KERAS_HOME"] = str(BASE_DIR / ".keras")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# Safe Unicode / UTF-8 stdout configuration for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def print_status(component, status, note=""):
    symbol = "  [PASS] [OK] " if status else "  [FAIL] [X]  "
    color_prefix = "\033[92m" if status else "\033[91m"
    color_suffix = "\033[0m"
    msg = f"{color_prefix}{symbol}{component:<35} {note}{color_suffix}"
    print(msg)
    return status

def main():
    print("\n" + "="*70)
    print("      PLANTCARE AI - SYSTEM HEALTH & DEPENDENCY AUDIT")
    print("="*70 + "\n")
    
    all_ok = True
    
    # 1. Python Version Check
    py_ver = sys.version_info
    py_ok = (py_ver.major == 3 and py_ver.minor >= 10)
    all_ok &= print_status("Python Version (>= 3.10)", py_ok, f"Detected: {sys.version.split()[0]}")
    
    # 2. Check Core Dependencies
    packages = [
        ("streamlit", "Streamlit UI Engine"),
        ("tensorflow", "Deep Learning Backbone"),
        ("PIL", "Pillow Image Processing"),
        ("numpy", "Numerical Array Compute"),
        ("pydantic", "Schema Validation"),
        ("dotenv", "Environment Configuration"),
        ("google.genai", "Neural Vision Core"),
    ]
    
    for mod_name, desc in packages:
        try:
            mod = __import__(mod_name)
            ver = getattr(mod, "__version__", "Installed")
            print_status(f"{mod_name} ({desc})", True, f"Version: {ver}")
        except ImportError as e:
            all_ok &= print_status(f"{mod_name} ({desc})", False, f"Missing! Run: pip install {mod_name}")

    # 3. Check Workspace & Model Files
    base_dir = Path(__file__).resolve().parent
    model_keras = base_dir / "models" / "plant_disease_model.keras"
    labels_file = base_dir / "models" / "class_labels.json"
    catalog_file = base_dir / "server" / "catalog.json"
    dataset_test = base_dir / "dataset" / "test"
    env_file = base_dir / ".env.local"
    
    print("\n" + "-"*70)
    print("      PROJECT ARTIFACTS & MODEL VERIFICATION")
    print("-"*-70 + "\n")
    
    # Check Model File
    if model_keras.exists():
        size_mb = round(model_keras.stat().st_size / (1024 * 1024), 2)
        print_status("Trained Keras Model", True, f"{model_keras.name} ({size_mb} MB)")
    else:
        all_ok &= print_status("Trained Keras Model", False, "Missing models/plant_disease_model.keras!")
        
    # Check Class Labels
    if labels_file.exists():
        import json
        with open(labels_file, "r", encoding="utf-8") as f:
            labels = json.load(f)
        print_status("Model Class Labels", True, f"{len(labels)} classes mapped")
    else:
        all_ok &= print_status("Model Class Labels", False, "Missing models/class_labels.json!")
        
    # Check Disease Catalog
    if catalog_file.exists():
        import json
        with open(catalog_file, "r", encoding="utf-8") as f:
            cat = json.load(f)
        print_status("Botanical Care Catalog", True, f"{len(cat)} diseases with treatment & prevention")
    else:
        all_ok &= print_status("Botanical Care Catalog", False, "Missing server/catalog.json!")
        
    # Check Dataset Test Folders
    if dataset_test.exists():
        subfolders = [p.name for p in dataset_test.iterdir() if p.is_dir()]
        total_test_imgs = len(list(dataset_test.glob("*/*.jpg")))
        print_status("Test Dataset Folders", len(subfolders) >= 8, f"{len(subfolders)} classes, {total_test_imgs} test images")
    else:
        all_ok &= print_status("Test Dataset Folders", False, "Missing dataset/test folder!")

    # Check Environment API Config
    if env_file.exists():
        print_status("Environment File (.env.local)", True, "Configured")
    else:
        all_ok &= print_status("Environment File (.env.local)", False, "Missing .env.local! Copy from main setup.")

    print("\n" + "="*70)
    if all_ok:
        print("  \033[92mSUCCESS: All packages and files are 100% READY!\033[0m")
        print("  To launch the app, run:  streamlit run streamlit_app.py")
        print("="*70 + "\n")
        return 0
    else:
        print("  \033[91mWARNING: Some dependencies or files are missing!\033[0m")
        print("  To fix packages, run:    pip install -r requirements.txt")
        print("="*70 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
