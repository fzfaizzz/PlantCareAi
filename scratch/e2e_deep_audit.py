import sys
import io
import time
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plantcare_streamlit.ml_engine import predict_image, get_model, get_labels
from plantcare_streamlit.services import load_settings, prepare_image, analyze_image, AnalysisError
import json

def test_ml_classes():
    print("\n--- 1. AUDITING 8 FOOD-CROP ML INFERENCE CLASSES ---")
    test_dir = Path("dataset/test")
    labels = get_labels()
    print(f"Loaded {len(labels)} class labels from models/class_labels.json")
    
    passed = 0
    total = 0
    for class_folder in sorted(test_dir.iterdir()):
        if class_folder.is_dir():
            sample_files = list(class_folder.glob("*.jpg")) + list(class_folder.glob("*.png"))
            if sample_files:
                sample_file = sample_files[0]
                total += 1
                t0 = time.time()
                res = predict_image(sample_file)
                latency = round((time.time() - t0) * 1000, 1)
                
                # Check assertions
                assert res["plant"] is not None and len(res["plant"]) > 0, "Plant name empty"
                assert res["condition"] is not None and len(res["condition"]) > 0, "Condition name empty"
                assert 0.0 <= res["confidence"] <= 100.0, f"Confidence out of range: {res['confidence']}"
                assert len(res["symptoms"]) > 0, "Symptoms empty"
                assert len(res["care"]) > 0, "Care recommendations empty"
                assert len(res["prevention"]) > 0, "Prevention tips empty"
                assert len(res["sources"]) > 0, "Sources empty"
                assert len(res["probabilities"]) == 8, f"Expected 8 class probabilities, got {len(res['probabilities'])}"
                
                print(f"  [PASS] {class_folder.name:<25} -> {res['plant']} ({res['condition']}) | Conf: {res['confidence']}% | Latency: {latency}ms")
                passed += 1
                
    print(f"ML Classes Result: {passed}/{total} Passed successfully.")
    assert passed == 8, f"Expected 8 passed, got {passed}"

def test_image_edge_cases():
    print("\n--- 2. AUDITING IMAGE PREPROCESSING & EDGE CASES ---")
    
    # 1. Grayscale (L mode)
    gray = Image.new("L", (300, 300), color=128)
    buf = io.BytesIO()
    gray.save(buf, format="JPEG")
    res = predict_image(buf.getvalue())
    assert res["plant"] is not None
    print("  [PASS] Grayscale (L mode) image handled cleanly.")

    # 2. RGBA with Alpha
    rgba = Image.new("RGBA", (300, 300), color=(100, 150, 50, 200))
    buf = io.BytesIO()
    rgba.save(buf, format="PNG")
    res = predict_image(buf.getvalue())
    assert res["plant"] is not None
    print("  [PASS] RGBA (Transparent PNG) handled cleanly.")

    # 3. High Resolution (3840 x 2160)
    high_res = Image.new("RGB", (3840, 2160), color=(80, 140, 60))
    buf = io.BytesIO()
    high_res.save(buf, format="JPEG", quality=85)
    res = predict_image(buf.getvalue())
    assert res["plant"] is not None
    print("  [PASS] 4K Ultra-HD Resolution (3840x2160) resized and handled cleanly.")

    # 4. Tiny Image (64x64 minimum boundary)
    tiny = Image.new("RGB", (64, 64), color=(60, 120, 50))
    buf = io.BytesIO()
    tiny.save(buf, format="JPEG")
    res = predict_image(buf.getvalue())
    assert res["plant"] is not None
    print("  [PASS] Minimum boundary (64x64) handled cleanly.")

    # 5. Corrupt / Empty data rejection
    try:
        prepare_image(b"not-a-photo")
        assert False, "Should have raised AnalysisError"
    except AnalysisError as e:
        assert e.code == "invalid_image"
        print("  [PASS] Corrupt non-image payload rejected with invalid_image.")

    try:
        prepare_image(b"")
        assert False, "Should have raised AnalysisError"
    except AnalysisError as e:
        assert e.code == "empty_image"
        print("  [PASS] Empty byte payload rejected with empty_image.")

def test_catalog_integrity():
    print("\n--- 3. AUDITING DATA CATALOG INTEGRITY ---")
    for path in [Path("server/catalog.json"), Path("plantcare_streamlit/data/catalog.json")]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) >= 10, f"{path} has fewer than 10 items ({len(data)})"
        slugs = set()
        for item in data:
            assert "slug" in item and item["slug"]
            assert "plant" in item and item["plant"]
            assert "condition" in item and item["condition"]
            assert "symptoms" in item and len(item["symptoms"]) > 0
            assert "care" in item and len(item["care"]) > 0
            assert "prevention" in item and len(item["prevention"]) > 0
            assert "sources" in item and len(item["sources"]) > 0
            assert item["slug"] not in slugs, f"Duplicate slug: {item['slug']}"
            slugs.add(item["slug"])
        print(f"  [PASS] {path}: {len(data)} verified entries with complete schemas.")

def test_live_gemini():
    print("\n--- 4. AUDITING LIVE GEMINI MULTIMODAL API ---")
    settings = load_settings()
    sample = Path("public/assets/plants/sample-leaf-spotted.webp")
    assert sample.exists()
    
    t0 = time.time()
    res = analyze_image(sample.read_bytes(), settings)
    elapsed = round(time.time() - t0, 2)
    
    assert res["status"] in ["success", "uncertain"]
    assert res["plant"] is not None
    assert res["condition"] is not None
    assert len(res["observations"]) > 0
    assert len(res["care"]) > 0
    assert len(res["prevention"]) > 0
    assert res["provider"]["name"] == "gemini"
    print(f"  [PASS] Gemini Cloud Vision live query returned in {elapsed}s:")
    print(f"         Plant: {res['plant']} | Condition: {res['condition']} | Symptoms: {len(res['observations'])} items | Care: {len(res['care'])} items")

if __name__ == "__main__":
    print("==================================================")
    print("      PLANTCARE AI - SENIOR QA DEEP AUDIT         ")
    print("==================================================")
    test_ml_classes()
    test_image_edge_cases()
    test_catalog_integrity()
    test_live_gemini()
    print("\n==================================================")
    print(">>> ALL AUDIT SUITES PASSED EMPIRICALLY (100%) <<<")
    print("==================================================")
