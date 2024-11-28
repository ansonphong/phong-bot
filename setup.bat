@echo off
setlocal enabledelayedexpansion

@echo off
echo PHONG BOT: INITIALIZE SETUP
echo Checking Python installation...
pause
python --version > nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher and try again
    exit /b 1
)

:: Check for existing virtual environment
if not exist venv (
    echo Creating new virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        exit /b 1
    )
) else (
    echo Using existing virtual environment...
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    exit /b 1
)

:: Upgrade pip without breaking dependencies
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install/upgrade packages from requirements.txt
echo Installing packages from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install required packages
    exit /b 1
)

echo.
echo PHONG-BOT: SETUP COMPLETED SUCCESSFULLY!
echo - Python environment is ready
echo - All required packages are installed

:: Deactivate virtual environment
deactivate

pause