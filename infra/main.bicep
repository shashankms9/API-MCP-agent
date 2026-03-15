// ============================================================================
// Challenge 5: Microsoft Agent Framework + MCP Tools Integration
// Main Bicep deployment - Azure AI Foundry, APIM Gateway, MCP Server
// ============================================================================

targetScope = 'resourceGroup'

@description('Base name for all resources')
param baseName string = 'challenge5'

@description('Azure region for deployment')
param location string = resourceGroup().location

@description('OpenAI model deployment name')
param modelDeploymentName string = 'gpt-4o'

@description('OpenAI model name')
param modelName string = 'gpt-4o'

@description('OpenAI model version')
param modelVersion string = '2024-11-20'

@description('SKU for OpenAI model deployment')
param modelSkuName string = 'GlobalStandard'

@description('Capacity for OpenAI model deployment (in thousands of tokens per minute)')
param modelCapacity int = 50

@description('APIM publisher email')
param apimPublisherEmail string = 'admin@contoso.com'

@description('APIM publisher name')
param apimPublisherName string = 'Challenge5 Admin'

@description('MCP Server container image')
param mcpServerImage string = 'mcr.microsoft.com/azurelinux/base/python:3.12'

// ---------- Variables ----------
var uniqueSuffix = uniqueString(resourceGroup().id, baseName)
var foundryAccountName = 'foundry-${baseName}-${uniqueSuffix}'
var projectName = 'project-${baseName}-${uniqueSuffix}'
var apimName = 'apim-${baseName}-${uniqueSuffix}'
var logAnalyticsName = 'log-${baseName}-${uniqueSuffix}'
var appInsightsName = 'appi-${baseName}-${uniqueSuffix}'
var containerEnvName = 'cae-${baseName}-${uniqueSuffix}'
var mcpAppName = 'mcp-server-${uniqueSuffix}'
var cosmosAccountName = 'cosmos-${baseName}-${uniqueSuffix}'

// ---------- Log Analytics & App Insights ----------
module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring-deployment'
  params: {
    location: location
    logAnalyticsName: logAnalyticsName
    appInsightsName: appInsightsName
  }
}

// ---------- Microsoft Foundry + Project + Model Deployments ----------
module foundry 'modules/ai-foundry.bicep' = {
  name: 'foundry-deployment'
  params: {
    location: location
    foundryAccountName: foundryAccountName
    projectName: projectName
    modelDeploymentName: modelDeploymentName
    modelName: modelName
    modelVersion: modelVersion
    modelSkuName: modelSkuName
    modelCapacity: modelCapacity
  }
}

// ---------- API Management ----------
module apim 'modules/apim.bicep' = {
  name: 'apim-deployment'
  params: {
    location: location
    apimName: apimName
    publisherEmail: apimPublisherEmail
    publisherName: apimPublisherName
    appInsightsId: monitoring.outputs.appInsightsId
    appInsightsInstrumentationKey: monitoring.outputs.appInsightsInstrumentationKey
    aiServicesEndpoint: foundry.outputs.foundryEndpoint
    aiServicesId: foundry.outputs.foundryId
  }
}

// ---------- MCP Server (Container App) ----------
module mcpServer 'modules/container-app.bicep' = {
  name: 'mcp-server-deployment'
  params: {
    location: location
    containerEnvName: containerEnvName
    mcpAppName: mcpAppName
    mcpServerImage: mcpServerImage
    logAnalyticsCustomerId: monitoring.outputs.logAnalyticsCustomerId
    logAnalyticsSharedKey: monitoring.outputs.logAnalyticsSharedKey
    openAiEndpoint: foundry.outputs.foundryEndpoint
    apimGatewayUrl: apim.outputs.apimGatewayUrl
  }
}

// ---------- Cosmos DB (MCP Tool Data Store) ----------
module cosmosDb 'modules/cosmos-db.bicep' = {
  name: 'cosmos-db-deployment'
  params: {
    location: location
    cosmosAccountName: cosmosAccountName
  }
}

// ---------- Outputs ----------
output foundryName string = foundry.outputs.foundryName
output projectName string = foundry.outputs.projectName
output foundryEndpoint string = foundry.outputs.foundryEndpoint
output apimGatewayUrl string = apim.outputs.apimGatewayUrl
output apimSubscriptionKeySecretUri string = apim.outputs.subscriptionKeySecretUri
output mcpServerUrl string = mcpServer.outputs.mcpServerUrl
output modelDeploymentName string = modelDeploymentName
output cosmosEndpoint string = cosmosDb.outputs.cosmosEndpoint
output cosmosDatabaseName string = cosmosDb.outputs.cosmosDatabaseName
