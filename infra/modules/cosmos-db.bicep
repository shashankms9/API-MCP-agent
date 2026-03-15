// Cosmos DB for MCP Tool data persistence
// Database: helpdesk-db
// Containers: tickets, knowledgebase, systems, incidents, employees, security_alerts, access_requests, compliance

param location string
param cosmosAccountName string

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: cosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
    publicNetworkAccess: 'Enabled'
  }
  tags: {
    lab: 'Microsoft Foundry Agents Frameworks Workshop'
    purpose: 'MCP Tool Data Store'
  }
}

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmosAccount
  name: 'helpdesk-db'
  properties: {
    resource: {
      id: 'helpdesk-db'
    }
  }
}

// Container: tickets (MCP 1 - Ticket Management)
resource ticketsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: 'tickets'
  properties: {
    resource: {
      id: 'tickets'
      partitionKey: {
        paths: ['/category']
        kind: 'Hash'
      }
      indexingPolicy: {
        automatic: true
        includedPaths: [{ path: '/*' }]
      }
    }
  }
}

// Container: knowledgebase (MCP 2 - Knowledge Base)
resource kbContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: 'knowledgebase'
  properties: {
    resource: {
      id: 'knowledgebase'
      partitionKey: {
        paths: ['/category']
        kind: 'Hash'
      }
    }
  }
}

// Container: systems (MCP 3 - System Monitoring)
resource systemsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: 'systems'
  properties: {
    resource: {
      id: 'systems'
      partitionKey: {
        paths: ['/region']
        kind: 'Hash'
      }
    }
  }
}

// Container: incidents (MCP 3 - System Monitoring)
resource incidentsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: 'incidents'
  properties: {
    resource: {
      id: 'incidents'
      partitionKey: {
        paths: ['/severity']
        kind: 'Hash'
      }
    }
  }
}

// Container: employees (MCP 4 - Employee Services)
resource employeesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: 'employees'
  properties: {
    resource: {
      id: 'employees'
      partitionKey: {
        paths: ['/department']
        kind: 'Hash'
      }
    }
  }
}

// Container: security_alerts (MCP 5 - Security Operations)
resource alertsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: 'security_alerts'
  properties: {
    resource: {
      id: 'security_alerts'
      partitionKey: {
        paths: ['/severity']
        kind: 'Hash'
      }
    }
  }
}

// Container: access_requests (MCP 5 - Security Operations)
resource accessRequestsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: 'access_requests'
  properties: {
    resource: {
      id: 'access_requests'
      partitionKey: {
        paths: ['/status']
        kind: 'Hash'
      }
    }
  }
}

// Container: compliance (MCP 5 - Security Operations)
resource complianceContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: 'compliance'
  properties: {
    resource: {
      id: 'compliance'
      partitionKey: {
        paths: ['/id']
        kind: 'Hash'
      }
    }
  }
}

output cosmosAccountName string = cosmosAccount.name
output cosmosEndpoint string = cosmosAccount.properties.documentEndpoint
output cosmosDatabaseName string = database.name
output cosmosAccountId string = cosmosAccount.id
