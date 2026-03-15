"""
MCP Server - IT Help Desk Tools
Provides real-time tools for the Help Desk agent:
  - Ticket management (create, search, update)
  - Knowledge base search for troubleshooting
  - System health monitoring
  - SLA calculations
"""

import os
import json
from datetime import datetime, timezone, timedelta
from mcp.server.fastmcp import FastMCP

# ---- In-Memory Data Stores ----
TICKETS = {}
TICKET_COUNTER = {"val": 1000}

SYSTEMS = {
    "email-server": {"name": "Email Server (Exchange Online)", "status": "operational", "uptime": "99.97%", "last_incident": "2026-03-10 14:22 UTC", "response_time_ms": 45},
    "vpn-gateway": {"name": "VPN Gateway", "status": "degraded", "uptime": "98.5%", "last_incident": "2026-03-15 06:10 UTC", "response_time_ms": 320},
    "erp-system": {"name": "ERP System (SAP)", "status": "operational", "uptime": "99.99%", "last_incident": "2026-02-28 09:00 UTC", "response_time_ms": 120},
    "active-directory": {"name": "Active Directory", "status": "operational", "uptime": "99.99%", "last_incident": "2026-01-15 03:40 UTC", "response_time_ms": 12},
    "file-storage": {"name": "File Storage (SharePoint)", "status": "operational", "uptime": "99.95%", "last_incident": "2026-03-12 18:30 UTC", "response_time_ms": 85},
    "ci-cd-pipeline": {"name": "CI/CD Pipeline (Azure DevOps)", "status": "outage", "uptime": "95.2%", "last_incident": "2026-03-15 07:45 UTC", "response_time_ms": None},
    "database-cluster": {"name": "Database Cluster (SQL)", "status": "operational", "uptime": "99.98%", "last_incident": "2026-03-01 12:00 UTC", "response_time_ms": 8},
    "monitoring-stack": {"name": "Monitoring (Grafana/Prometheus)", "status": "operational", "uptime": "99.90%", "last_incident": "2026-03-08 22:15 UTC", "response_time_ms": 60},
}

KNOWLEDGE_BASE = [
    {"id": "KB001", "title": "VPN Connection Drops Frequently", "category": "Network",
     "symptoms": ["vpn disconnects", "vpn slow", "vpn timeout", "cannot connect vpn"],
     "solution": "1. Restart the VPN client.\n2. Check your internet connection stability.\n3. Try switching VPN protocols (IKEv2 -> OpenVPN).\n4. Clear VPN client cache: Settings > Advanced > Clear Cache.\n5. If persists, escalate to Network Team with VPN logs."},
    {"id": "KB002", "title": "Email Not Syncing on Mobile", "category": "Email",
     "symptoms": ["email not syncing", "outlook mobile", "email not updating", "no new mail"],
     "solution": "1. Force close and reopen the Outlook app.\n2. Check Settings > Accounts > verify sync is enabled.\n3. Remove and re-add the account.\n4. Ensure battery optimization is disabled for Outlook.\n5. Check if the email server is operational in system status."},
    {"id": "KB003", "title": "Password Reset / Account Locked", "category": "Identity",
     "symptoms": ["password reset", "locked out", "cannot login", "account locked", "forgot password"],
     "solution": "1. Go to https://passwordreset.company.com (self-service portal).\n2. Verify identity via MFA.\n3. Set a new password (min 12 chars, 1 uppercase, 1 number, 1 symbol).\n4. Wait 5 minutes for AD sync.\n5. If self-service fails, IT can unlock via Active Directory."},
    {"id": "KB004", "title": "Slow Computer Performance", "category": "Hardware",
     "symptoms": ["computer slow", "laptop slow", "freezing", "takes long to boot", "program not responding"],
     "solution": "1. Restart your computer (full shutdown, not sleep).\n2. Check Task Manager (Ctrl+Shift+Esc) for high CPU/memory usage.\n3. Close unnecessary background apps.\n4. Run Disk Cleanup: Start > type 'Disk Cleanup'.\n5. Check available disk space (need >10% free).\n6. If >3 years old, request hardware refresh."},
    {"id": "KB005", "title": "Cannot Access Shared Drive / SharePoint", "category": "Access",
     "symptoms": ["shared drive", "sharepoint access denied", "network drive", "file share", "permission denied"],
     "solution": "1. Verify you have the correct permissions (check with your manager).\n2. Open SharePoint in browser > try signing out and back in.\n3. For mapped drives: net use Z: /delete then net use Z: \\\\server\\share.\n4. Clear browser cache for SharePoint.\n5. If permission issue, request access via Service Catalog."},
    {"id": "KB006", "title": "Printer Not Working", "category": "Hardware",
     "symptoms": ["printer", "cannot print", "print queue stuck", "printer offline"],
     "solution": "1. Verify the printer is powered on and connected.\n2. Clear the print queue: Services > Print Spooler > Restart.\n3. Remove and re-add the printer.\n4. Update printer drivers.\n5. Try printing a test page from Settings > Printers."},
    {"id": "KB007", "title": "MFA / Two-Factor Authentication Issues", "category": "Identity",
     "symptoms": ["mfa not working", "authenticator app", "two factor", "verification code", "mfa reset"],
     "solution": "1. Ensure your phone time is auto-synced.\n2. Try 'I can't use my authenticator app' option for SMS fallback.\n3. If all MFA methods fail, visit IT Service Desk with photo ID for MFA reset.\n4. For lost phone: contact IT immediately to disable old MFA."},
    {"id": "KB008", "title": "Software Installation Request", "category": "Software",
     "symptoms": ["install software", "need application", "software request", "new program"],
     "solution": "1. Check the Company Portal app for pre-approved software.\n2. If not in portal, submit a Software Request via Service Catalog.\n3. Required approvals: your manager + IT security.\n4. Typical turnaround: 1-3 business days.\n5. Note: Admin rights are not granted for self-install."},
    {"id": "KB009", "title": "Teams / Video Call Quality Issues", "category": "Communication",
     "symptoms": ["teams lag", "video call quality", "audio issues", "teams freezing", "echo in call"],
     "solution": "1. Check internet speed (need >5 Mbps up/down).\n2. Close other bandwidth-heavy apps.\n3. Turn off video if bandwidth is limited.\n4. Use ethernet instead of Wi-Fi for important calls.\n5. Update Teams and clear cache: %AppData%\\Microsoft\\Teams > delete Cache."},
    {"id": "KB010", "title": "CI/CD Pipeline Build Failures", "category": "DevOps",
     "symptoms": ["pipeline failed", "build broken", "deployment failed", "ci cd error", "azure devops"],
     "solution": "1. Check the build logs for specific error messages.\n2. Common causes: dependency version conflicts, expired secrets, quota limits.\n3. Retry the build (transient failures ~2% of the time).\n4. For secret expiry: rotate in Key Vault and update pipeline variables.\n5. Check system status for DevOps service health."},
]

# ---- MCP Server Setup ----
mcp = FastMCP(
    name="HelpDesk-MCP-Server",
    instructions="IT Help Desk tools for ticket management, troubleshooting, and system monitoring.",
)


@mcp.tool()
def create_ticket(
    title: str,
    description: str,
    priority: str = "medium",
    category: str = "General",
    reporter_email: str = "user@company.com",
) -> str:
    """Create a new IT support ticket.

    Args:
        title: Short summary of the issue.
        description: Detailed description of the problem.
        priority: Priority level - low, medium, high, or critical.
        category: Category like Network, Email, Hardware, Identity, Software, DevOps.
        reporter_email: Email of the person reporting the issue.
    """
    TICKET_COUNTER["val"] += 1
    ticket_id = f"INC{TICKET_COUNTER['val']:05d}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    sla_hours = {"critical": 1, "high": 4, "medium": 8, "low": 24}
    sla_h = sla_hours.get(priority.lower(), 8)
    sla_due = (datetime.now(timezone.utc) + timedelta(hours=sla_h)).strftime("%Y-%m-%d %H:%M:%S UTC")

    ticket = {
        "ticket_id": ticket_id, "title": title, "description": description,
        "priority": priority.lower(), "category": category, "status": "open",
        "reporter": reporter_email, "assigned_to": "Unassigned",
        "created_at": now, "updated_at": now, "sla_due": sla_due,
        "resolution": None, "notes": [],
    }
    TICKETS[ticket_id] = ticket
    return json.dumps({"message": f"Ticket {ticket_id} created successfully.", "ticket": ticket}, indent=2)


@mcp.tool()
def search_tickets(query: str = "", status: str = "", priority: str = "") -> str:
    """Search existing support tickets by keyword, status, or priority.

    Args:
        query: Search keyword in title or description. Leave empty to list all.
        status: Filter by status (open, in-progress, resolved, closed).
        priority: Filter by priority (low, medium, high, critical).
    """
    results = []
    for t in TICKETS.values():
        if query and query.lower() not in t["title"].lower() and query.lower() not in t["description"].lower():
            continue
        if status and t["status"] != status.lower():
            continue
        if priority and t["priority"] != priority.lower():
            continue
        results.append({
            "ticket_id": t["ticket_id"], "title": t["title"], "priority": t["priority"],
            "status": t["status"], "assigned_to": t["assigned_to"],
            "created_at": t["created_at"], "sla_due": t["sla_due"],
        })
    if not results:
        return json.dumps({"message": "No tickets found matching your criteria.", "count": 0})
    return json.dumps({"count": len(results), "tickets": results}, indent=2)


@mcp.tool()
def update_ticket(
    ticket_id: str,
    status: str = "",
    assigned_to: str = "",
    priority: str = "",
    add_note: str = "",
    resolution: str = "",
) -> str:
    """Update an existing support ticket.

    Args:
        ticket_id: The ticket ID (e.g., INC01001).
        status: New status (open, in-progress, resolved, closed).
        assigned_to: Assign to a team member or team.
        priority: Change priority (low, medium, high, critical).
        add_note: Add a note or comment to the ticket.
        resolution: Resolution details (when resolving).
    """
    ticket = TICKETS.get(ticket_id.upper())
    if not ticket:
        return json.dumps({"error": f"Ticket {ticket_id} not found."})

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    changes = []
    if status:
        ticket["status"] = status.lower()
        changes.append(f"Status -> {status}")
    if assigned_to:
        ticket["assigned_to"] = assigned_to
        changes.append(f"Assigned to -> {assigned_to}")
    if priority:
        ticket["priority"] = priority.lower()
        changes.append(f"Priority -> {priority}")
    if resolution:
        ticket["resolution"] = resolution
        ticket["status"] = "resolved"
        changes.append("Ticket resolved")
    if add_note:
        ticket["notes"].append({"time": now, "note": add_note})
        changes.append("Note added")
    ticket["updated_at"] = now

    return json.dumps({
        "message": f"Ticket {ticket_id} updated: {', '.join(changes) if changes else 'no changes'}",
        "ticket": ticket,
    }, indent=2)


@mcp.tool()
def search_knowledge_base(query: str) -> str:
    """Search the IT knowledge base for troubleshooting solutions.

    Args:
        query: Describe the issue or symptoms (e.g., 'VPN keeps disconnecting').
    """
    query_lower = query.lower()
    scored = []
    for article in KNOWLEDGE_BASE:
        score = 0
        for symptom in article["symptoms"]:
            if symptom in query_lower:
                score += 3
            else:
                for word in symptom.split():
                    if word in query_lower:
                        score += 1
        for word in article["title"].lower().split():
            if word in query_lower:
                score += 1
        if score > 0:
            scored.append((score, article))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:3]
    if not top:
        return json.dumps({"message": f"No KB articles found for: '{query}'. Consider creating a ticket.", "articles": []})

    articles = [{"id": a["id"], "title": a["title"], "category": a["category"], "solution": a["solution"]} for _, a in top]
    return json.dumps({"count": len(articles), "articles": articles}, indent=2)


@mcp.tool()
def get_system_status(system_name: str = "") -> str:
    """Check real-time status of IT systems and infrastructure.

    Args:
        system_name: Specific system to check (e.g., 'vpn-gateway'). Leave empty for full dashboard.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if system_name:
        sys_info = SYSTEMS.get(system_name.lower().replace(" ", "-"))
        if not sys_info:
            return json.dumps({"error": f"System '{system_name}' not found.", "available": list(SYSTEMS.keys())})
        return json.dumps({"timestamp": now, "system": sys_info}, indent=2)

    summary = {"operational": 0, "degraded": 0, "outage": 0}
    systems_list = []
    for key, s in SYSTEMS.items():
        summary[s["status"]] = summary.get(s["status"], 0) + 1
        systems_list.append({"id": key, "name": s["name"], "status": s["status"], "response_time_ms": s["response_time_ms"]})
    return json.dumps({
        "timestamp": now,
        "overall_health": "degraded" if summary["outage"] > 0 or summary["degraded"] > 0 else "all systems operational",
        "summary": summary, "systems": systems_list,
    }, indent=2)


@mcp.tool()
def calculate_sla_metrics(ticket_id: str = "") -> str:
    """Calculate SLA compliance metrics for tickets.

    Args:
        ticket_id: Specific ticket ID to check SLA, or empty for overall metrics.
    """
    now = datetime.now(timezone.utc)

    if ticket_id:
        ticket = TICKETS.get(ticket_id.upper())
        if not ticket:
            return json.dumps({"error": f"Ticket {ticket_id} not found."})
        sla_due = datetime.strptime(ticket["sla_due"], "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)
        remaining = sla_due - now
        breached = remaining.total_seconds() < 0
        return json.dumps({
            "ticket_id": ticket["ticket_id"], "priority": ticket["priority"],
            "status": ticket["status"], "sla_due": ticket["sla_due"],
            "time_remaining": str(remaining) if not breached else "BREACHED",
            "sla_breached": breached,
        }, indent=2)

    total = len(TICKETS)
    if total == 0:
        return json.dumps({"message": "No tickets to calculate SLA for.", "total_tickets": 0})
    breached = sum(1 for t in TICKETS.values()
                   if datetime.strptime(t["sla_due"], "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc) < now
                   and t["status"] not in ("resolved", "closed"))
    compliance = ((total - breached) / total * 100) if total > 0 else 100
    return json.dumps({"total_tickets": total, "sla_breached": breached, "sla_compliance_pct": round(compliance, 1)}, indent=2)


@mcp.tool()
def get_current_time() -> str:
    """Get the current date and time in UTC."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


# ============================================================================
# Starlette Application with MCP SSE transport + health check
# ============================================================================
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount


async def health(request):
    return JSONResponse({"status": "healthy", "server": "HelpDesk-MCP-Server"})


mcp_app = mcp.sse_app()

app = Starlette(
    routes=[
        Route("/health", health),
        Mount("/", app=mcp_app),
    ],
)

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("MCP_SERVER_PORT", "8080"))
    print(f"Starting Help Desk MCP server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
