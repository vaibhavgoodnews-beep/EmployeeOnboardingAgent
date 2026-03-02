@echo off
REM Quick Start Script for Employee Onboarding Agent (Windows)

echo.
echo ======================================
echo Employee Onboarding Agent - Setup
echo ======================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)

echo.
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [3/4] Installing dependencies...
pip install -r requirements.txt

echo.
echo [4/4] Setting up secrets...
if not exist ".streamlit\secrets.toml" (
    echo.
    echo Please create .streamlit\secrets.toml with your Google API key:
    echo.
    echo Copy the template from .streamlit\secrets.toml.template
    echo And add your actual API key
) else (
    echo Secrets file already exists
)

echo.
echo ======================================
echo Setup Complete!
echo ======================================
echo.
echo To start the app, run:
echo   streamlit run app.py
echo.
pause
