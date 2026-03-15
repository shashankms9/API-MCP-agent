# ============================================================================
# Challenge 5: Deploy Infrastructure + Run Agent
# ============================================================================
# Prerequisites:
#   - Azure CLI installed and logged in (az login)
#   - Bicep CLI available (comes with Azure CLI)
#   - Python 3.10+ installed
# ============================================================================

param(
    [string]$ResourceGroupName = "rg-challenge5",
    [string]$Location = "eastus2",
    [switch]$SkipInfra,
    [switch]$InfraOnly
)

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Challenge 5: Deployment Script" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# ---------- Step 1: Deploy Azure Infrastructure ----------
if (-not $SkipInfra) {
    Write-Host "`n[1/4] Creating Resource Group..." -ForegroundColor Yellow
    az group create --name $ResourceGroupName --location $Location --output none

    Write-Host "[2/4] Deploying Bicep infrastructure (this may take 10-15 minutes)..." -ForegroundColor Yellow
    $deployOutput = az deployment group create `
        --resource-group $ResourceGroupName `
        --template-file "$PSScriptRoot\..\infra\main.bicep" `
        --parameters "$PSScriptRoot\..\infra\main.bicepparam" `
        --parameters location=$Location `
        --query "properties.outputs" `
        --output json | ConvertFrom-Json

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Bicep deployment failed." -ForegroundColor Red
        exit 1
    }

    # Extract outputs
    $aiProjectName = $deployOutput.aiProjectName.value
    $openAiEndpoint = $deployOutput.openAiEndpoint.value
    $openAiName = $deployOutput.openAiName.value
    $apimGatewayUrl = $deployOutput.apimGatewayUrl.value
    $mcpServerUrl = $deployOutput.mcpServerUrl.value
    $keyVaultName = $deployOutput.keyVaultName.value
    $modelDeploymentName = $deployOutput.modelDeploymentName.value
    $aiHubName = $deployOutput.aiHubName.value

    Write-Host "[INFO] Deployment outputs:" -ForegroundColor Green
    Write-Host "  AI Hub:             $aiHubName"
    Write-Host "  AI Project:         $aiProjectName"
    Write-Host "  OpenAI Endpoint:    $openAiEndpoint"
    Write-Host "  APIM Gateway:       $apimGatewayUrl"
    Write-Host "  MCP Server:         $mcpServerUrl"
    Write-Host "  Key Vault:          $keyVaultName"

    # Get project connection string
    Write-Host "`n[3/4] Retrieving project connection string..." -ForegroundColor Yellow
    $subscriptionId = (az account show --query id -o tsv)
    $projectConnectionString = "$openAiEndpoint;$subscriptionId;$ResourceGroupName;$aiProjectName"

    # Assign current user Cognitive Services OpenAI User role
    Write-Host "[3/4] Assigning RBAC roles to current user..." -ForegroundColor Yellow
    $currentUserId = az ad signed-in-user show --query id -o tsv
    az role assignment create `
        --assignee $currentUserId `
        --role "Cognitive Services OpenAI User" `
        --scope "/subscriptions/$subscriptionId/resourceGroups/$ResourceGroupName" `
        --output none 2>$null

    # Write .env file
    $envFilePath = "$PSScriptRoot\..\.env"
    @"
# Challenge 5 - Auto-generated environment variables
PROJECT_CONNECTION_STRING=$projectConnectionString
MODEL_DEPLOYMENT_NAME=$modelDeploymentName
AZURE_OPENAI_ENDPOINT=$openAiEndpoint
APIM_GATEWAY_URL=$apimGatewayUrl
MCP_SERVER_URL=$mcpServerUrl/sse
AGENT_NAME=Challenge5-Agent
"@ | Set-Content -Path $envFilePath -Encoding UTF8

    Write-Host "[INFO] .env file written to $envFilePath" -ForegroundColor Green

    if ($InfraOnly) {
        Write-Host "`n[DONE] Infrastructure deployed. Use 'python src/agent/agent_app.py' to run the agent." -ForegroundColor Cyan
        exit 0
    }
}

# ---------- Step 2: Install Python Dependencies ----------
Write-Host "`n[4/4] Installing Python dependencies..." -ForegroundColor Yellow

Push-Location "$PSScriptRoot\..\src\agent"
pip install -r requirements.txt --quiet
Pop-Location

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host " Deployment Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review the .env file and verify the connection string"
Write-Host "  2. Run the agent:  python src/agent/agent_app.py"
Write-Host "  3. Try asking: 'What time is it?'"
Write-Host "  4. Try asking: 'Summarize: Azure AI Foundry is a platform for...'"
Write-Host ""
