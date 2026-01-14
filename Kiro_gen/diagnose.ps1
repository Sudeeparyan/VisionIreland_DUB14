# =============================================================================
# Comic Audio Narrator - Quick Diagnostic Script
# =============================================================================
# Run this script to diagnose issues: .\diagnose.ps1
# Share the output with AI for troubleshooting
# =============================================================================

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendPath = Join-Path $ScriptRoot "backend"
$FrontendPath = Join-Path $ScriptRoot "frontend"
$VenvPath = "D:\AI\VisionIreland_DUB14_clean\.venv"
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "         COMIC AUDIO NARRATOR - DIAGNOSTIC REPORT                    " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# =============================================================================
Write-Host "1. SYSTEM INFORMATION" -ForegroundColor Yellow
Write-Host ("=" * 70)
Write-Host "Date/Time: $(Get-Date)"
Write-Host "Computer: $env:COMPUTERNAME"
Write-Host "User: $env:USERNAME"
Write-Host "PowerShell: $($PSVersionTable.PSVersion)"
Write-Host ""

# =============================================================================
Write-Host "2. PYTHON ENVIRONMENT" -ForegroundColor Yellow
Write-Host ("=" * 70)

if (Test-Path $PythonExe) {
    Write-Host "[OK] Python executable found: $PythonExe" -ForegroundColor Green
    $pythonVersion = & $PythonExe --version 2>&1
    Write-Host "  Version: $pythonVersion"
    
    Write-Host ""
    Write-Host "  Key Packages:" -ForegroundColor Cyan
    $packages = @("fastapi", "uvicorn", "boto3", "pydantic", "pydantic-settings", "python-multipart")
    foreach ($pkg in $packages) {
        $installed = & $PythonExe -m pip show $pkg 2>&1
        if ($LASTEXITCODE -eq 0) {
            $versionLine = $installed | Select-String "Version:"
            if ($versionLine) {
                $version = $versionLine.ToString().Split(":")[1].Trim()
                Write-Host "    [OK] $pkg : $version" -ForegroundColor Green
            }
        } else {
            Write-Host "    [MISSING] $pkg : NOT INSTALLED" -ForegroundColor Red
        }
    }
} else {
    Write-Host "[ERROR] Python not found at: $PythonExe" -ForegroundColor Red
}
Write-Host ""

# =============================================================================
Write-Host "3. NODE.JS ENVIRONMENT" -ForegroundColor Yellow
Write-Host ("=" * 70)

$nodeVersion = $null
$npmVersion = $null

$nodeCheck = & node --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Node.js: $nodeCheck" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Node.js: NOT INSTALLED" -ForegroundColor Red
}

$npmCheck = & npm --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] npm: v$npmCheck" -ForegroundColor Green
} else {
    Write-Host "[ERROR] npm: NOT INSTALLED" -ForegroundColor Red
}

$nodeModulesPath = Join-Path $FrontendPath "node_modules"
if (Test-Path $nodeModulesPath) {
    Write-Host "[OK] node_modules: EXISTS" -ForegroundColor Green
} else {
    Write-Host "[MISSING] node_modules: Run 'npm install' in frontend folder" -ForegroundColor Red
}
Write-Host ""

# =============================================================================
Write-Host "4. AWS CONFIGURATION" -ForegroundColor Yellow
Write-Host ("=" * 70)

$envFile = Join-Path $BackendPath ".env"
if (Test-Path $envFile) {
    Write-Host "[OK] .env file found" -ForegroundColor Green
    $envContent = Get-Content $envFile -Raw
    
    # Check AWS_REGION
    if ($envContent -match "AWS_REGION=(.+)") {
        Write-Host "  [OK] AWS_REGION: $($matches[1].Trim())" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] AWS_REGION: NOT SET" -ForegroundColor Red
    }
    
    # Check AWS_ACCESS_KEY_ID
    if ($envContent -match "AWS_ACCESS_KEY_ID=(.+)") {
        $keyId = $matches[1].Trim()
        $preview = $keyId.Substring(0, [Math]::Min(10, $keyId.Length)) + "..."
        Write-Host "  [OK] AWS_ACCESS_KEY_ID: $preview" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] AWS_ACCESS_KEY_ID: NOT SET" -ForegroundColor Red
    }
    
    # Check AWS_SECRET_ACCESS_KEY
    if ($envContent -match "AWS_SECRET_ACCESS_KEY=(.+)") {
        Write-Host "  [OK] AWS_SECRET_ACCESS_KEY: [HIDDEN]" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] AWS_SECRET_ACCESS_KEY: NOT SET" -ForegroundColor Red
    }
    
    # Check AWS_SESSION_TOKEN
    if ($envContent -match "AWS_SESSION_TOKEN=(.+)") {
        Write-Host "  [OK] AWS_SESSION_TOKEN: [SET - Check if expired]" -ForegroundColor Green
        Write-Host "  [WARN] Session tokens typically expire in 1-12 hours" -ForegroundColor Yellow
    } else {
        Write-Host "  [INFO] AWS_SESSION_TOKEN: Not set (may be needed)" -ForegroundColor Gray
    }
} else {
    Write-Host "[ERROR] .env file NOT FOUND at: $envFile" -ForegroundColor Red
}
Write-Host ""

# =============================================================================
Write-Host "5. PORT STATUS" -ForegroundColor Yellow
Write-Host ("=" * 70)

$ports = @(8000, 3000)
foreach ($port in $ports) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        $process = Get-Process -Id $connection[0].OwningProcess -ErrorAction SilentlyContinue
        Write-Host "  Port $port : IN USE by $($process.ProcessName) (PID: $($process.Id))" -ForegroundColor Yellow
    } else {
        Write-Host "  Port $port : AVAILABLE" -ForegroundColor Green
    }
}
Write-Host ""

# =============================================================================
Write-Host "6. BACKEND HEALTH CHECK" -ForegroundColor Yellow
Write-Host ("=" * 70)

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 5
    Write-Host "[OK] Backend is RUNNING and HEALTHY" -ForegroundColor Green
    Write-Host "  Response: $($response | ConvertTo-Json -Compress)"
} catch {
    Write-Host "[ERROR] Backend is NOT RESPONDING" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# =============================================================================
Write-Host "7. FRONTEND HEALTH CHECK" -ForegroundColor Yellow
Write-Host ("=" * 70)

try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method GET -TimeoutSec 5 -UseBasicParsing
    Write-Host "[OK] Frontend is RUNNING (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Frontend is NOT RESPONDING" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# =============================================================================
Write-Host "8. AWS CONNECTIVITY TEST" -ForegroundColor Yellow
Write-Host ("=" * 70)

Write-Host "Testing AWS credentials..." -ForegroundColor Cyan

# Create Python test script
$testFile = Join-Path $env:TEMP "aws_test_$(Get-Random).py"
$backendPathEscaped = $BackendPath.Replace("\", "\\")

$testScript = @"
import sys
sys.path.insert(0, '$backendPathEscaped')
try:
    from src.config import settings
    import boto3
    sts = boto3.client('sts', region_name=settings.aws_region, aws_access_key_id=settings.aws_access_key_id, aws_secret_access_key=settings.aws_secret_access_key, aws_session_token=settings.aws_session_token)
    identity = sts.get_caller_identity()
    print('SUCCESS: Account=' + identity['Account'] + ', ARN=' + identity['Arn'])
except Exception as e:
    print('FAILED: ' + str(e))
"@

$testScript | Out-File -FilePath $testFile -Encoding ASCII

$result = & $PythonExe $testFile 2>&1
$resultStr = $result | Out-String

if ($resultStr -match "SUCCESS") {
    Write-Host "[OK] AWS credentials are VALID" -ForegroundColor Green
    Write-Host "  $resultStr"
} else {
    Write-Host "[ERROR] AWS credentials FAILED" -ForegroundColor Red
    Write-Host "  $resultStr" -ForegroundColor Red
    Write-Host ""
    Write-Host "  COMMON FIXES:" -ForegroundColor Yellow
    Write-Host "  1. Session token may have expired - get fresh credentials" -ForegroundColor Yellow
    Write-Host "  2. Check .env file has correct AWS credentials" -ForegroundColor Yellow
}

Remove-Item $testFile -ErrorAction SilentlyContinue
Write-Host ""

# =============================================================================
Write-Host "9. RECENT ERROR LOGS" -ForegroundColor Yellow
Write-Host ("=" * 70)

$logDir = Join-Path $BackendPath "logs"
if (Test-Path $logDir) {
    $latestLog = Get-ChildItem $logDir -Filter "*.log*" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latestLog) {
        Write-Host "Latest log: $($latestLog.FullName)" -ForegroundColor Cyan
        Write-Host "Last 10 lines:" -ForegroundColor Cyan
        Get-Content $latestLog.FullName -Tail 10 -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_ -match "ERROR|Exception") {
                Write-Host "  $_" -ForegroundColor Red
            } elseif ($_ -match "WARNING") {
                Write-Host "  $_" -ForegroundColor Yellow
            } else {
                Write-Host "  $_" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "No log files found" -ForegroundColor Gray
    }
} else {
    Write-Host "No log directory found" -ForegroundColor Gray
}
Write-Host ""

# =============================================================================
Write-Host "10. QUICK TEST - TRY TO IMPORT BACKEND" -ForegroundColor Yellow
Write-Host ("=" * 70)

$importTestFile = Join-Path $env:TEMP "import_test_$(Get-Random).py"
$importScript = @"
import sys
sys.path.insert(0, '$backendPathEscaped')
try:
    from src.main import app
    print('SUCCESS: Backend imports OK')
except Exception as e:
    print('IMPORT_ERROR: ' + str(e))
"@

$importScript | Out-File -FilePath $importTestFile -Encoding ASCII
$importResult = & $PythonExe $importTestFile 2>&1
$importResultStr = $importResult | Out-String

if ($importResultStr -match "SUCCESS") {
    Write-Host "[OK] Backend imports successfully" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Backend import failed" -ForegroundColor Red
    Write-Host "  $importResultStr" -ForegroundColor Red
}

Remove-Item $importTestFile -ErrorAction SilentlyContinue
Write-Host ""

# =============================================================================
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "                      DIAGNOSTIC COMPLETE                            " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Copy and share this output with AI for troubleshooting." -ForegroundColor Yellow
Write-Host ""
