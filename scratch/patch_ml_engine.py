from pathlib import Path

file_path = Path("plantcare_streamlit/ml_engine.py")
content = file_path.read_text(encoding="utf-8")

# Add environment variables
old_header = """from __future__ import annotations

import json"""
new_header = """from __future__ import annotations

import os
import json"""
if old_header in content:
    content = content.replace(old_header, new_header)

old_env = """BASE_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE_DIR / "models\""""
new_env = """BASE_DIR = Path(__file__).resolve().parents[1]
os.environ.setdefault("KERAS_HOME", str(BASE_DIR / ".keras"))
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
MODELS_DIR = BASE_DIR / "models\""""
if old_env in content:
    content = content.replace(old_env, new_env)

# Add scientific_name and severity to return dict
old_return = """"condition": info.get("condition", class_id.split("___")[1].replace("_", " ") if "___" in class_id else class_id),
        "is_healthy": is_healthy,"""
new_return = """"condition": info.get("condition", class_id.split("___")[1].replace("_", " ") if "___" in class_id else class_id),
        "scientific_name": info.get("scientific_name"),
        "severity": info.get("severity", "Normal"),
        "is_healthy": is_healthy,"""
if old_return in content:
    content = content.replace(old_return, new_return)

file_path.write_text(content, encoding="utf-8")
print("ml_engine.py patched successfully!")
