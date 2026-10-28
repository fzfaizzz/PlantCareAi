@echo off
title PlantCare AI - Launch Engine
color 0A

echo ======================================================================
echo                     PLANTCARE AI - LAUNCH SYSTEM
echo ======================================================================
echo.

:: Detect Python executable (Use backend\.venv if present, otherwise system python)
if exist "backend\.venv\Scripts\python.exe" (
    echo [INFO] Detected project virtual environment in backend\.venv
    set "PY_CMD=backend\.venv\Scripts\python.exe"
    set "PIP_CMD=backend\.venv\Scripts\pip.exe"
) else (
    set "PY_CMD=python"
    set "PIP_CMD=pip"
)

:: 1. Check Python installation
%PY_CMD% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH!
    echo Please install Python 3.10 or 3.11 from https://www.python.org
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [1/3] Python environment ready:
%PY_CMD% --version
echo.

:: 2. Run Dependency & Artifact Audit
echo [2/3] Checking dependencies and models...
%PY_CMD% check_environment.py
if %errorlevel% neq 0 (
    echo.
    echo [NOTICE] Installing missing packages now...
    %PIP_CMD% install -r requirements.txt
    echo.
    echo Re-checking environment...
    %PY_CMD% check_environment.py
)

:: 3. Launch App using detected Python
echo.
echo [3/3] Starting PlantCare AI Streamlit Web Application...
echo Browser will automatically open at http://localhost:8501
echo.
%PY_CMD% -m streamlit run streamlit_app.py

pause
