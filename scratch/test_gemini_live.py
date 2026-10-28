import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import time
from plantcare_streamlit.services import load_settings, prepare_image, analyze_image

def main():
    settings = load_settings()
    print(f"Loaded settings: Model={settings.model}, Has Key={bool(settings.api_key)}")
    
    test_image_path = Path("dataset/test/Tomato___Early_blight/sample_00.jpg")
    if not test_image_path.exists():
        test_image_path = Path("public/assets/plants/sample-leaf-spotted.webp")
        
    print(f"Testing with image: {test_image_path}")
    image_bytes = test_image_path.read_bytes()
    
    t0 = time.time()
    try:
        result = analyze_image(image_bytes, settings)
        elapsed = round(time.time() - t0, 2)
        print(f"SUCCESS in {elapsed}s!")
        print(f"Plant: {result.get('plant')}")
        print(f"Condition: {result.get('condition')}")
        print(f"Confidence: {result.get('confidence')}")
        print(f"Symptoms: {result.get('symptoms')[:2] if result.get('symptoms') else 'None'}")
    except Exception as e:
        elapsed = round(time.time() - t0, 2)
        print(f"FAILED in {elapsed}s: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
