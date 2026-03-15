// MCP Server deployed as Container App

param location string
param containerEnvName string
param mcpAppName string
param mcpServerImage string
param logAnalyticsCustomerId string
@secure()
param logAnalyticsSharedKey string
param openAiEndpoint string
param apimGatewayUrl string

resource containerEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerEnvName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsSharedKey
      }
    }
  }
}

resource mcpApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: mcpAppName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8080
        transport: 'http'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'mcp-server'
          image: mcpServerImage
          command: [
            'python'
            '-m'
            'uvicorn'
            'server:app'
            '--host'
            '0.0.0.0'
            '--port'
            '8080'
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: openAiEndpoint
            }
            {
              name: 'APIM_GATEWAY_URL'
              value: apimGatewayUrl
            }
            {
              name: 'MCP_SERVER_PORT'
              value: '8080'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 3
        rules: [
          {
            name: 'http-rule'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

output mcpServerUrl string = 'https://${mcpApp.properties.configuration.ingress.fqdn}'
output mcpAppName string = mcpApp.name
output mcpAppPrincipalId string = mcpApp.identity.principalId
