# Challenge 5: Microsoft Agent Framework + MCP Tools Integration

## Overview

Build an **agent-driven service** using the **Microsoft Agent Framework** (Azure AI Agent Service) and integrate it with **MCP (Model Context Protocol)** tools for secure inference routing via **Azure API Management**.

This challenge combines:
- **Agent Framework** — Create an AI agent with defined roles, intents, and tool-use capabilities
- **MCP Integration** — Connect the agent to a remote MCP server that exposes tools
- **APIM Gateway** — Route inference requests securely between agents and models

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   User CLI   │────▶│  AI Foundry Agent │────▶│   MCP Server     │
│  (Python)    │     │  (Agent Service)  │     │  (Container App) │
└─────────────┘     └────────┬─────────┘     └────────┬─────────┘
                             │                         │
                    ┌────────▼─────────┐     ┌────────▼─────────┐
                    │  Azure OpenAI     │◀────│  APIM Gateway     │
                    │  (GPT-4o)         │     │  (Secure Routing) │
                    └──────────────────┘     └──────────────────┘
```

## Deployed Resources (Bicep)

| Resource | Purpose |
|----------|---------|
| **Azure AI Foundry Hub + Project** | Hosts the agent and provides workspace |
| **Azure OpenAI (GPT-4o)** | Language model for the agent |
| **Azure AI Services** | Multi-service cognitive endpoint |
| **Azure API Management** | Secure inference gateway with rate limiting |
| **Azure Container App** | Hosts the MCP server |
| **Azure Key Vault** | Secrets management |
| **Storage Account** | Required by AI Foundry Hub |
| **Log Analytics + App Insights** | Monitoring and diagnostics |

## Project Structure

```
challange5/
├── README.md                          # This file
├── .env.example                       # Environment variable template
├── infra/
│   ├── main.bicep                     # Main orchestrator
│   ├── main.bicepparam                # Parameter values
│   └── modules/
│       ├── ai-foundry.bicep           # AI Hub + Project + Connections
│       ├── openai.bicep               # Azure OpenAI + Model deployment
│       ├── apim.bicep                 # API Management + policies
│       ├── container-app.bicep        # MCP Server container
│       ├── keyvault.bicep             # Key Vault
│       ├── storage.bicep              # Storage Account
│       └── monitoring.bicep           # Log Analytics + App Insights
├── src/
│   ├── agent/
│   │   ├── agent_app.py              # Main agent application
│   │   ├── config.py                 # Configuration loader
│   │   └── requirements.txt          # Python dependencies
│   └── mcp-server/
│       ├── server.py                 # MCP server with tools
│       ├── requirements.txt          # Python dependencies
│       └── Dockerfile                # Container image
└── scripts/
    ├── deploy.ps1                    # Full deployment script
    └── start-mcp-server.ps1         # Local MCP server startup
```

## Prerequisites

- **Azure CLI** installed and logged in (`az login`)
- **Python 3.10+** installed
- **Azure Subscription** with access to deploy OpenAI models
- **Bicep CLI** (included with Azure CLI)

## Step-by-Step Instructions

### Task 1: Deploy Infrastructure

```powershell
# From the challange5 directory
.\scripts\deploy.ps1 -ResourceGroupName "rg-challenge5" -Location "eastus2"
```

This deploys all Azure resources and writes a `.env` file with connection details.

To deploy infrastructure only (without running the agent):
```powershell
.\scripts\deploy.ps1 -InfraOnly
```

### Task 2: Create the Agent (Agent Framework)

The agent is defined in `src/agent/agent_app.py` with:

- **Agent Role**: A helpful AI assistant that can use MCP tools
- **Intents**: Answer questions, invoke tools (time, summarize, search, calculate)
- **Communication Protocol**: Uses Azure AI Agent Service SDK with thread-based conversations

Key code that creates the agent:
```python
agent = client.agents.create_agent(
    model="gpt-4o",
    name="Challenge5-Agent",
    instructions="You are a helpful AI assistant...",
    toolset=toolset,  # MCP tools attached here
)
```

### Task 3: Connect Agent to MCP Server

The MCP server (`src/mcp-server/server.py`) exposes 4 tools:

| Tool | Description |
|------|-------------|
| `get_current_time` | Returns the current UTC time |
| `summarize_text` | Summarizes text via APIM → OpenAI |
| `lookup_knowledge_base` | Searches a simulated knowledge base |
| `calculate` | Evaluates math expressions safely |

The agent connects to the MCP server via:
```python
mcp_connection = McpToolConnection(
    url=mcp_server_url,  # MCP server SSE endpoint
    authentication=McpToolConnectionAuthentication(
        type=McpToolConnectionAuthenticationType.NONE
    ),
)
toolset.add(mcp_connection)
```

### Task 4: Configure APIM for Secure Inference

The APIM gateway (`infra/modules/apim.bicep`) provides:

- **Managed Identity Auth**: APIM authenticates to OpenAI using its system-assigned identity
- **Rate Limiting**: 60 requests per minute
- **Subscription Keys**: Required for API access
- **Monitoring**: All requests logged to Application Insights

The `summarize_text` MCP tool routes requests through APIM:
```
Agent → MCP Server → APIM Gateway → Azure OpenAI
```

### Task 5: Run the Agent

```powershell
# Start the MCP server locally (in a separate terminal)
.\scripts\start-mcp-server.ps1

# Run the agent
python src\agent\agent_app.py
```

Try these prompts:
- `What time is it?` — Invokes `get_current_time` tool
- `What is MCP?` — Invokes `lookup_knowledge_base` tool
- `Calculate 42 * 17 + 3` — Invokes `calculate` tool
- `Summarize: Azure AI Foundry provides a unified platform...` — Routes through APIM

## Verification Checklist

- [ ] Bicep deployment completes successfully with all resources created
- [ ] AI Foundry Hub and Project are visible in the Azure portal
- [ ] OpenAI model deployment (gpt-4o) is active
- [ ] APIM gateway is reachable and the OpenAI API is registered
- [ ] MCP server health check returns healthy (`GET /health`)
- [ ] Agent starts and can hold a conversation
- [ ] Agent successfully invokes MCP tools (time, knowledge base, calculate)
- [ ] Summarize tool routes through APIM gateway to OpenAI
- [ ] Application Insights shows request telemetry

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `PROJECT_CONNECTION_STRING` error | Verify `.env` file has the connection string from deployment output |
| Agent creation fails | Ensure OpenAI model is deployed and RBAC roles are assigned |
| MCP tools not available | Check MCP server is running and URL in `.env` points to `/sse` |
| APIM 401 Unauthorized | Verify APIM managed identity has "Cognitive Services OpenAI User" role |
| Deployment timeout | APIM Consumption tier can take 10-15 min; re-run if needed |
