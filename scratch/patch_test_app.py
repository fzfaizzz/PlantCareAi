from pathlib import Path
p = Path("tests_streamlit/test_app.py")
txt = p.read_text(encoding="utf-8")
if "sys.path.insert" not in txt:
    txt = "import sys\nfrom pathlib import Path\nfrom streamlit.testing.v1 import AppTest\n\nROOT = Path(__file__).resolve().parents[1]\nsys.path.insert(0, str(ROOT))\n" + txt.split("ROOT = Path(__file__).resolve().parents[1]\n")[1]
    p.write_text(txt, encoding="utf-8")
    print("test_app.py patched!")
