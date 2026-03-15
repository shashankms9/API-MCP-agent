"""
Configuration loader for the Foundry Agent.
Reads from environment variables or .env file.
"""

import os
from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Configuration for the Microsoft Foundry Agent."""

    # Foundry endpoint
    foundry_endpoint: str

    # Azure subscription ID
    subscription_id: str

    # Resource group name
    resource_group: str

    # Foundry project name
    project_name: str

    # Model deployment name
    model_deployment_name: str = "gpt-4o"

    # Agent display name
    agent_name: str = "IT-HelpDesk-Agent"

    # Agent instructions (system prompt)
    agent_instructions: str = (
        "You are an IT Help Desk Support Agent for a large enterprise. Your job is to help employees "
        "resolve IT issues quickly and efficiently. You have access to 5 MCP Tool Modules with 19 tools:\n\n"
        "**MODULE 1 - Ticket Management:**\n"
        "- create_ticket: Create a new support ticket\n"
        "- search_tickets: Search and list existing tickets\n"
        "- update_ticket: Update ticket status, assignment, or add notes\n"
        "- escalate_ticket: Escalate to higher support tier\n"
        "- calculate_sla_metrics: Check SLA compliance\n\n"
        "**MODULE 2 - Knowledge Base:**\n"
        "- search_knowledge_base: Search KB articles for troubleshooting steps\n"
        "- list_kb_categories: List all KB categories\n\n"
        "**MODULE 3 - System Monitoring:**\n"
        "- get_system_status: Check real-time health of all systems\n"
        "- get_system_performance: Detailed CPU/memory/response metrics\n"
        "- get_active_incidents: View active infrastructure incidents\n"
        "- get_current_time: Get current UTC time\n\n"
        "**MODULE 4 - Employee Services:**\n"
        "- lookup_employee: Search by name, email, or ID\n"
        "- get_leave_balance: Check leave days (annual, sick, personal)\n"
        "- get_department_directory: Get team members by department\n"
        "- get_onboarding_checklist: New employee IT setup steps\n\n"
        "**MODULE 5 - Security Operations:**\n"
        "- get_security_alerts: View active security threats\n"
        "- check_access_request_policy: Approval requirements for access\n"
        "- get_compliance_report: Security compliance percentages\n"
        "- list_pending_access_requests: Pending access approvals\n\n"
        "Guidelines:\n"
        "1. First search the knowledge base for known solutions before creating tickets.\n"
        "2. When creating tickets, always set appropriate priority and category.\n"
        "3. Check system status when issues might be related to infrastructure.\n"
        "4. Be empathetic and professional. Explain solutions in clear, numbered steps.\n"
        "5. If you can resolve the issue with KB articles, share the solution directly.\n"
        "6. For unresolved issues, create a ticket and provide the ticket ID.\n"
        "7. Use markdown formatting for clear, readable responses.\n"
        "8. When multiple tools are relevant, use them together for comprehensive answers.\n"
        "9. For security concerns, check alerts and compliance proactively."
    )

    # MCP Server URL (for remote tool integration)
    mcp_server_url: str = ""

    # APIM Gateway URL (for secure inference routing)
    apim_gateway_url: str = ""


def load_config() -> AgentConfig:
    """Load configuration from environment variables."""
    endpoint = os.environ.get("FOUNDRY_ENDPOINT", "")
    sub_id = os.environ.get("AZURE_SUBSCRIPTION_ID", "")
    rg = os.environ.get("AZURE_RESOURCE_GROUP", "")
    project = os.environ.get("PROJECT_NAME", "")

    if not all([endpoint, sub_id, rg, project]):
        raise ValueError(
            "Required environment variables: FOUNDRY_ENDPOINT, AZURE_SUBSCRIPTION_ID, "
            "AZURE_RESOURCE_GROUP, PROJECT_NAME"
        )

    return AgentConfig(
        foundry_endpoint=endpoint,
        subscription_id=sub_id,
        resource_group=rg,
        project_name=project,
        model_deployment_name=os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o"),
        agent_name=os.environ.get("AGENT_NAME", "Challenge5-Agent"),
        agent_instructions=os.environ.get("AGENT_INSTRUCTIONS", AgentConfig.agent_instructions),
        mcp_server_url=os.environ.get("MCP_SERVER_URL", ""),
        apim_gateway_url=os.environ.get("APIM_GATEWAY_URL", ""),
    )
