import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plantcare_streamlit.ml_engine import predict_image

reff_dir = Path("Reff-Img")
if reff_dir.exists():
    for f in reff_dir.iterdir():
        if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
            try:
                res = predict_image(f)
                print(f"{f.name}: Plant={res['plant']}, Condition={res['condition']}, Conf={res['confidence']}%, Slug={res['slug']}")
            except Exception as e:
                print(f"{f.name}: ERROR: {e}")
else:
    print("Reff-Img directory not found")
