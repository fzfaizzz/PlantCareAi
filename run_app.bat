@echo off
title PlantCare AI - Disease Detection System
echo ===================================================
echo       PlantCare AI - Disease Detection System
echo ===================================================
echo.
echo Starting Streamlit Application...
echo Local URL: http://localhost:8501
echo.

:: Use python -m streamlit to prevent hardcoded .venv path errors across different PCs
python -m streamlit run streamlit_app.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Streamlit failed to launch!
    echo Running dependency check...
    python check_environment.py
)

pause
