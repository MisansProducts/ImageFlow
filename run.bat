@echo off
setlocal enabledelayedexpansion

REM Gets the directory where this script (run.bat) is located and removes the trailing backslash from the path
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Creates virtual environment if it doesn't exist
if not exist "%SCRIPT_DIR%\venv" (
    echo Creating virtual environment...
    python -m venv "%SCRIPT_DIR%\venv"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Upgrades pip
"%SCRIPT_DIR%\venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo ERROR: Failed to upgrade pip
    pause
    exit /b 1
)

REM Verifies requirements
echo Verifying dependencies...
"%SCRIPT_DIR%\venv\Scripts\python.exe" -m pip install -r "%SCRIPT_DIR%\requirements.txt" --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Runs the main Python script
echo Running main script...
"%SCRIPT_DIR%\venv\Scripts\python.exe" "%SCRIPT_DIR%\main.py"
if errorlevel 1 (
    echo ERROR: Python script failed
    pause
    exit /b 1
)

pause