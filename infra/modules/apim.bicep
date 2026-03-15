// Azure API Management for secure inference routing

param location string
param apimName string
param publisherEmail string
param publisherName string
param appInsightsId string
param appInsightsInstrumentationKey string
param aiServicesEndpoint string
param aiServicesId string

resource apim 'Microsoft.ApiManagement/service@2023-09-01-preview' = {
  name: apimName
  location: location
  sku: {
    name: 'Consumption'
    capacity: 0
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: publisherName
  }
}

// Diagnostics logger for App Insights
resource apimLogger 'Microsoft.ApiManagement/service/loggers@2023-09-01-preview' = {
  parent: apim
  name: 'appinsights-logger'
  properties: {
    loggerType: 'applicationInsights'
    resourceId: appInsightsId
    credentials: {
      instrumentationKey: appInsightsInstrumentationKey
    }
  }
}

// Named value for AI Services endpoint
resource aiServicesEndpointNamedValue 'Microsoft.ApiManagement/service/namedValues@2023-09-01-preview' = {
  parent: apim
  name: 'ai-services-endpoint'
  properties: {
    displayName: 'ai-services-endpoint'
    value: aiServicesEndpoint
    secret: false
  }
}

// API: Azure AI Services inference proxy
resource openAiApi 'Microsoft.ApiManagement/service/apis@2023-09-01-preview' = {
  parent: apim
  name: 'azure-openai-api'
  properties: {
    displayName: 'Azure AI Foundry Inference API'
    description: 'Proxy API for routing inference requests to Azure AI Services (Foundry) via APIM'
    subscriptionRequired: true
    path: 'openai'
    protocols: [
      'https'
    ]
    serviceUrl: '${aiServicesEndpoint}openai'
  }
}

// Chat completions operation
resource chatCompletions 'Microsoft.ApiManagement/service/apis/operations@2023-09-01-preview' = {
  parent: openAiApi
  name: 'chat-completions'
  properties: {
    displayName: 'Chat Completions'
    method: 'POST'
    urlTemplate: '/deployments/{deployment-id}/chat/completions?api-version={api-version}'
    templateParameters: [
      {
        name: 'deployment-id'
        required: true
        type: 'string'
      }
      {
        name: 'api-version'
        required: true
        type: 'string'
      }
    ]
  }
}

// Policy: Use managed identity for OpenAI authentication
resource apiPolicy 'Microsoft.ApiManagement/service/apis/policies@2023-09-01-preview' = {
  parent: openAiApi
  name: 'policy'
  properties: {
    format: 'xml'
    value: '''
<policies>
  <inbound>
    <base />
    <authentication-managed-identity resource="https://cognitiveservices.azure.com/" />
    <set-header name="Content-Type" exists-action="override">
      <value>application/json</value>
    </set-header>
    <rate-limit calls="60" renewal-period="60" />
  </inbound>
  <backend>
    <base />
  </backend>
  <outbound>
    <base />
  </outbound>
  <on-error>
    <base />
  </on-error>
</policies>
'''
  }
}

// RBAC: Grant APIM managed identity "Cognitive Services OpenAI User" on the AI Services resource
resource apimOpenAiRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(apim.id, aiServicesId, 'CognitiveServicesOpenAIUser')
  scope: resourceGroup()
  properties: {
    principalId: apim.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd') // Cognitive Services OpenAI User
  }
}

// Subscription for the API
resource apimSubscription 'Microsoft.ApiManagement/service/subscriptions@2023-09-01-preview' = {
  parent: apim
  name: 'mcp-agent-subscription'
  properties: {
    displayName: 'MCP Agent Subscription'
    scope: '/apis/${openAiApi.id}'
    state: 'active'
  }
}

output apimGatewayUrl string = apim.properties.gatewayUrl
output apimName string = apim.name
output subscriptionKeySecretUri string = 'Use Azure Portal to retrieve the subscription key for "${apimSubscription.name}"'
