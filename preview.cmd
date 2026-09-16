@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 goto failed
python scripts/build.py
if errorlevel 1 goto failed
start "" http://localhost:8000
python scripts/serve.py
exit /b
:failed
pause
exit /b 1
