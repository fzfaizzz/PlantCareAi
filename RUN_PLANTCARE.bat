@echo off
title PlantCare AI - Launch Engine
color 0A

echo ======================================================================
echo                     PLANTCARE AI - LAUNCH SYSTEM
echo ======================================================================
echo.

:: 1. Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH!
    echo Please install Python 3.10 or 3.11 from https://www.python.org
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [1/3] Python detected:
python --version
echo.

:: 2. Run Dependency & Artifact Audit
echo [2/3] Checking dependencies and models...
python check_environment.py
if %errorlevel% neq 0 (
    echo.
    echo [NOTICE] Installing missing packages now...
    pip install -r requirements.txt
    echo.
    echo Re-checking environment...
    python check_environment.py
)

:: 3. Launch App using universal python module launcher
echo.
echo [3/3] Starting PlantCare AI Streamlit Web Application...
echo Browser will automatically open at http://localhost:8501
echo.
python -m streamlit run streamlit_app.py

pause
