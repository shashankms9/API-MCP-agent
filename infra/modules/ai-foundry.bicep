// Microsoft Foundry (CognitiveServices/accounts) + Project sub-resource + Model Deployments
// Uses the newer Foundry pattern: accounts -> projects as a child resource

param location string
param foundryAccountName string
param projectName string

// Model deployment parameters
param modelDeploymentName string
param modelName string
param modelVersion string
param modelSkuName string
param modelCapacity int

// Microsoft Foundry account (CognitiveServices with AIServices kind)
resource foundryAccount 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: foundryAccountName
  location: location
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: foundryAccountName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
    allowProjectManagement: true
  }
  tags: {
    lab: 'Microsoft Foundry Agents Frameworks Workshop'
    project: projectName
  }
}

// Foundry Project (sub-resource of the Foundry account)
resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: foundryAccount
  name: toLower(projectName)
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  properties: {
    displayName: projectName
    description: 'Foundry Project for Agent Framework and MCP Tools'
  }
}

// Model deployment: gpt-4o
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: foundryAccount
  name: modelDeploymentName
  sku: {
    name: modelSkuName
    capacity: modelCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
  }
  dependsOn: [
    project
  ]
}

output foundryName string = foundryAccount.name
output projectName string = project.name
output foundryId string = foundryAccount.id
output foundryEndpoint string = foundryAccount.properties.endpoint
