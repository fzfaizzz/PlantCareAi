import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import plantcare_streamlit.detect as detect
    import plantcare_streamlit.result as result
    import plantcare_streamlit.ml_engine as ml_engine
    import plantcare_streamlit.services as services
    print("ALL MODULES IMPORTED CLEANLY WITHOUT ERRORS!")
except Exception as e:
    print(f"IMPORT ERROR: {type(e).__name__}: {e}")
    sys.exit(1)
