# Startup script for Comic Audio Narrator Backend
# Usage: .\start.ps1

$env:PYTHONPATH = $PSScriptRoot
Set-Location $PSScriptRoot
D:\AI\VisionIreland_DUB14_clean\.venv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 8000
