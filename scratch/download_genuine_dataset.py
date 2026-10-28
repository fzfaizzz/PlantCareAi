"""
Download genuine diverse PlantVillage photos for the 8 project classes.
Each class gets real, distinct, authentic field photos (25 train, 10 test).
"""
import os
import json
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = BASE_DIR / "dataset"
TRAIN_DIR = DATASET_DIR / "train"
TEST_DIR = DATASET_DIR / "test"

CLASS_MAP = {
    "Apple___Apple_scab": "Apple___Apple_scab",
    "Corn___Common_rust": "Corn_(maize)___Common_rust_",
    "Potato___Early_blight": "Potato___Early_blight",
    "Potato___Late_blight": "Potato___Late_blight",
    "Potato___healthy": "Potato___healthy",
    "Tomato___Early_blight": "Tomato___Early_blight",
    "Tomato___Late_blight": "Tomato___Late_blight",
    "Tomato___healthy": "Tomato___healthy"
}

def fetch_class_images():
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for local_cls, gh_cls in CLASS_MAP.items():
        print(f"--> Fetching genuine samples for {local_cls}...")
        api_url = f"https://api.github.com/repos/spMohanty/PlantVillage-Dataset/contents/raw/color/{urllib.parse.quote(gh_cls)}"
        req = urllib.request.Request(api_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                files = json.loads(resp.read().decode())
        except Exception as e:
            print(f"Error fetching directory list for {local_cls}: {e}")
            continue
        
        # Only take .JPG/.jpg files
        jpg_files = [f for f in files if f.get("name", "").lower().endswith((".jpg", ".jpeg"))]
        print(f"    Found {len(jpg_files)} remote images.")
        
        # We need 25 train images and 10 test images (total 35 distinct images)
        selected_train = jpg_files[:25]
        selected_test = jpg_files[25:35]
        
        local_train_dir = TRAIN_DIR / local_cls
        local_test_dir = TEST_DIR / local_cls
        local_train_dir.mkdir(parents=True, exist_ok=True)
        local_test_dir.mkdir(parents=True, exist_ok=True)
        
        # Clear out old augmented duplicates in both dirs
        for f in local_train_dir.glob("*.*"):
            try: f.unlink()
            except Exception: pass
        for f in local_test_dir.glob("*.*"):
            try: f.unlink()
            except Exception: pass
            
        # Download train images
        for i, item in enumerate(selected_train):
            download_url = item.get("download_url")
            out_file = local_train_dir / f"plantvillage_{i+1:03d}.jpg"
            try:
                urllib.request.urlretrieve(download_url, out_file)
            except Exception as e:
                print(f"    Failed train #{i+1}: {e}")
                
        # Download test images
        for i, item in enumerate(selected_test):
            download_url = item.get("download_url")
            out_file = local_test_dir / f"test_leaf_{i+1:03d}.jpg"
            try:
                urllib.request.urlretrieve(download_url, out_file)
            except Exception as e:
                print(f"    Failed test #{i+1}: {e}")
                
        print(f"    Successfully stored {len(list(local_train_dir.glob('*.jpg')))} train & {len(list(local_test_dir.glob('*.jpg')))} test distinct images.")

if __name__ == "__main__":
    fetch_class_images()
