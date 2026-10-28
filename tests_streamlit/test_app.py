import sys
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def app(page="Home"):
    instance = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=20)
    instance.query_params["page"] = page
    return instance.run()

def test_native_navigation_and_search():
    at = app()
    assert not at.exception
    at.button(key="nav_Plant Library").click().run()
    assert at.session_state["page"] == "Plant Library"
    assert len([b for b in at.button if b.key and b.key.startswith("guide_")]) == 10
    at.text_input(key="library_search").set_value("early blight").run()
    assert len([b for b in at.button if b.key and b.key.startswith("guide_")]) == 1
    at.button(key="guide_tomato-early-blight").click().run()
    assert not at.exception
    assert any("What to look for" in m.value for m in at.markdown)

def test_direct_detection_sample_and_remove_without_provider_call(monkeypatch):
    def fail_paid(*_args, **_kwargs):
        raise AssertionError("Ordinary UI changes must never invoke Gemini")
    monkeypatch.setattr("plantcare_streamlit.detect.analyze_leaf", fail_paid)
    at = app("Detect")
    at.button(key="choose-sample-leaf-spotted").click().run()
    assert at.session_state["detect_input_origin"] == "sample"
    assert at.button(key="run-detection")
    at.button(key="remove-leaf").click().run()
    assert "detect_input" not in at.session_state
    assert "detect_result" not in at.session_state
    assert not at.exception

def test_about_native_links_and_profile():
    at = app("About")
    assert not at.exception
    at.button(key="about_library").click().run()
    assert at.session_state["page"] == "Plant Library"
    assert not at.exception

def test_real_result_renders_without_claiming_confirmation():
    # Fixture responses validate UI plumbing, not botanical accuracy.
    at = app("Detect")
    at.session_state["detect_result"] = {
        "status":"unsupported_image", "plant":None, "condition":None,
        "explanation":"No leaf is visible.", "uncertainty":"No plant diagnosis is established.",
        "catalog":{"matched":False},"general_guidance":[],"observations":[],
        "warnings":["Choose a clear leaf photo."],"sources":[],"request_id":"test-request",
        "provider":{"model":"fixture-model"}
    }
    at.run()
    assert not at.exception
    assert not at.success
    assert at.button(key="result-another")
    assert at.download_button(key="result-download")
    assert not any(b.key == "result-share" for b in at.button)
