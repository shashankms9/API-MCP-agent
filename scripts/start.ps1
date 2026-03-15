# ============================================================================
# Start IT Help Desk Application
# Launches Backend (port 8000) and Frontend (port 5000)
# ============================================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot | Split-Path -Parent

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " IT Help Desk - Starting Servers" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Verify .env exists
$envFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "[ERROR] .env file not found. Run 'azd up' first to provision and configure." -ForegroundColor Red
    exit 1
}

# Start Backend (port 8000) in background
Write-Host "`n[1/2] Starting Backend API on port 8000..." -ForegroundColor Yellow
$backendPath = Join-Path $ProjectRoot "src" "backend" "app.py"
$backendJob = Start-Process -FilePath "python" -ArgumentList $backendPath -WorkingDirectory $ProjectRoot -PassThru -NoNewWindow

Start-Sleep -Seconds 3

# Start Frontend (port 5000) in background
Write-Host "[2/2] Starting Frontend UI on port 5000..." -ForegroundColor Yellow
$frontendPath = Join-Path $ProjectRoot "src" "frontend" "app.py"
$frontendJob = Start-Process -FilePath "python" -ArgumentList $frontendPath -WorkingDirectory $ProjectRoot -PassThru -NoNewWindow

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " IT Help Desk is Running!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend UI:   http://localhost:5000" -ForegroundColor White
Write-Host "  Backend API:   http://localhost:8000" -ForegroundColor White
Write-Host "  Health Check:  http://localhost:5000/health" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all servers." -ForegroundColor Yellow
Write-Host ""

# Wait for either process to exit
try {
    while ($true) {
        if ($backendJob.HasExited) {
            Write-Host "[WARN] Backend process exited with code $($backendJob.ExitCode)" -ForegroundColor Yellow
            break
        }
        if ($frontendJob.HasExited) {
            Write-Host "[WARN] Frontend process exited with code $($frontendJob.ExitCode)" -ForegroundColor Yellow
            break
        }
        Start-Sleep -Seconds 2
    }
} finally {
    # Clean up both processes
    Write-Host "`nStopping servers..." -ForegroundColor Yellow
    if (-not $backendJob.HasExited) { Stop-Process -Id $backendJob.Id -Force -ErrorAction SilentlyContinue }
    if (-not $frontendJob.HasExited) { Stop-Process -Id $frontendJob.Id -Force -ErrorAction SilentlyContinue }
    Write-Host "Servers stopped." -ForegroundColor Green
}
