@echo off
echo =========================================
echo Starting AI Student Quiz Portal
echo =========================================

IF NOT EXIST ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Activating virtual environment...
call .venv\Scripts\activate

echo Installing Requirements...
pip install -r requirements.txt

echo.
echo Starting Application...
python app.py

pause
