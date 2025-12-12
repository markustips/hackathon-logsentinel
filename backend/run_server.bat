@echo off
echo Starting LogSentinel AI Backend...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo ERROR: Virtual environment not activated!
    echo Please run activate_and_install.bat first
    pause
    exit /b 1
)

echo Virtual environment activated: %VIRTUAL_ENV%
echo.

REM Start the server
python start_server.py
