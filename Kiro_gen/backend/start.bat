@echo off
REM Startup script for Comic Audio Narrator Backend

set PYTHONPATH=%~dp0
D:\AI\VisionIreland_DUB14_clean\.venv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8000
