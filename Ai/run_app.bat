@echo off
title Maps Lead Generator Server
cd /d "%~dp0"
echo Starting Lead Generator Application...
start python -m uvicorn main:app --host 0.0.0.0 --port 8000
timeout /t 4 /nobreak >nul
start http://localhost:8000