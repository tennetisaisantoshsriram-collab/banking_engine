@echo off
echo Starting Banking Engine...
cd /d "%~dp0backend"
start "" "http://localhost:8001"
venv\Scripts\python.exe main.py
pause
