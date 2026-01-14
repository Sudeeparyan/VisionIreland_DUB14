# =============================================================================
# Comic Audio Narrator - Start Backend + Frontend
# =============================================================================
# Usage: .\start_all.ps1
# Press Ctrl+C to stop
# =============================================================================

$ErrorActionPreference = "Continue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendPath = Join-Path $ScriptRoot "backend"
$FrontendPath = Join-Path $ScriptRoot "frontend"
$VenvPython = "D:\AI\VisionIreland_DUB14_clean\.venv\Scripts\python.exe"

# Clear screen and show header
Clear-Host
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "       COMIC AUDIO NARRATOR - FULL STACK LAUNCHER          " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# -----------------------------------------------------------------------------
# STEP 1: Check prerequisites
# -----------------------------------------------------------------------------
Write-Host "[STEP 1] Checking prerequisites..." -ForegroundColor Yellow

# Check Python
if (Test-Path $VenvPython) {
    $pyVer = & $VenvPython --version 2>&1
    Write-Host "  [OK] Python: $pyVer" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Python not found at: $VenvPython" -ForegroundColor Red
    exit 1
}

# Check Node
$nodeVer = node --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Node.js: $nodeVer" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Node.js not installed" -ForegroundColor Red
    exit 1
}

# Check directories
if (-not (Test-Path $BackendPath)) {
    Write-Host "  [ERROR] Backend folder not found" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $FrontendPath)) {
    Write-Host "  [ERROR] Frontend folder not found" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] Directories found" -ForegroundColor Green

# -----------------------------------------------------------------------------
# STEP 2: Kill existing processes on ports
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[STEP 2] Freeing ports 8000 and 3000..." -ForegroundColor Yellow

foreach ($port in @(8000, 3000)) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        $proc = Get-Process -Id $conn[0].OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  Stopping $($proc.ProcessName) on port $port..." -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
        }
    }
}
Write-Host "  [OK] Ports cleared" -ForegroundColor Green

# -----------------------------------------------------------------------------
# STEP 3: Start Backend
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[STEP 3] Starting Backend on port 8000..." -ForegroundColor Yellow

$backendProc = Start-Process -FilePath $VenvPython `
    -ArgumentList "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000" `
    -WorkingDirectory $BackendPath `
    -PassThru `
    -WindowStyle Normal

Write-Host "  [OK] Backend started (PID: $($backendProc.Id))" -ForegroundColor Green

# Wait for backend to be ready
Write-Host "  Waiting for backend to initialize..." -ForegroundColor Gray
$backendReady = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 2 -ErrorAction Stop
        $backendReady = $true
        Write-Host "  [OK] Backend is healthy!" -ForegroundColor Green
        break
    } catch {
        Write-Host "  ..." -NoNewline -ForegroundColor Gray
    }
}
Write-Host ""
if (-not $backendReady) {
    Write-Host "  [WARN] Backend may still be starting..." -ForegroundColor Yellow
}

# -----------------------------------------------------------------------------
# STEP 4: Start Frontend
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[STEP 4] Starting Frontend on port 3000..." -ForegroundColor Yellow

$frontendProc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c", "npm run dev" `
    -WorkingDirectory $FrontendPath `
    -PassThru `
    -WindowStyle Normal

Write-Host "  [OK] Frontend started (PID: $($frontendProc.Id))" -ForegroundColor Green

# Wait for frontend
Write-Host "  Waiting for frontend to compile..." -ForegroundColor Gray
Start-Sleep -Seconds 8

# -----------------------------------------------------------------------------
# STEP 5: Show Summary
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "                  SERVICES STARTED                         " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend API:    http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API Docs:       http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Frontend:       http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend PID:  $($backendProc.Id)" -ForegroundColor Gray
Write-Host "  Frontend PID: $($frontendProc.Id)" -ForegroundColor Gray
Write-Host ""
Write-Host "  To stop: Close the terminal windows or run:" -ForegroundColor Yellow
Write-Host "    Stop-Process -Id $($backendProc.Id),$($frontendProc.Id) -Force" -ForegroundColor Yellow
Write-Host ""

# -----------------------------------------------------------------------------
# STEP 6: Quick health check
# -----------------------------------------------------------------------------
Write-Host "[STEP 6] Running health checks..." -ForegroundColor Yellow

# Backend check
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "  [OK] Backend: HEALTHY" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Backend: NOT RESPONDING" -ForegroundColor Red
}

# Frontend check
try {
    $frontCheck = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
    Write-Host "  [OK] Frontend: RUNNING" -ForegroundColor Green
} catch {
    Write-Host "  [WARN] Frontend: Still compiling (check browser)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Open http://localhost:3000 in your browser to use the app" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
