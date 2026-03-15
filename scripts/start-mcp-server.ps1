# ============================================================================
# Quick local setup - Start MCP server locally for development/testing
# ============================================================================

param(
    [int]$Port = 8080
)

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Starting MCP Server Locally" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Load .env if it exists
$envFile = "$PSScriptRoot\..\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim(), "Process")
        }
    }
    Write-Host "[INFO] Loaded .env file" -ForegroundColor Green
}

# Install MCP server dependencies
Write-Host "[INFO] Installing MCP server dependencies..." -ForegroundColor Yellow
Push-Location "$PSScriptRoot\..\src\mcp-server"
pip install -r requirements.txt --quiet
Pop-Location

# Start the server
Write-Host "[INFO] Starting MCP server on port $Port..." -ForegroundColor Yellow
$env:MCP_SERVER_PORT = $Port
python "$PSScriptRoot\..\src\mcp-server\server.py"
