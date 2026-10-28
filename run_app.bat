@echo off
title PlantCare AI - Disease Detection System
echo ===================================================
echo       PlantCare AI - Disease Detection System
echo ===================================================
echo.
echo Starting Streamlit Application...
echo Local URL: http://localhost:8501
echo.

if exist "backend\.venv\Scripts\python.exe" (
    set "PY_CMD=backend\.venv\Scripts\python.exe"
) else (
    set "PY_CMD=python"
)

%PY_CMD% -m streamlit run streamlit_app.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Streamlit failed to launch!
    echo Running dependency check...
    %PY_CMD% check_environment.py
)

pause
