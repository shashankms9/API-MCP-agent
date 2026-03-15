"""
MCP Tool 1: Ticket Management (backed by Cosmos DB)
Handles creating, searching, updating, and escalating IT support tickets.
Container: tickets (partition key: /category)
"""

import json
from datetime import datetime, timezone, timedelta
from .cosmos_client import get_container

CONTAINER_NAME = "tickets"


def _get_next_ticket_id() -> str:
    """Generate the next ticket ID by querying Cosmos DB for the max."""
    container = get_container(CONTAINER_NAME)
    query = "SELECT VALUE MAX(c.ticket_id) FROM c"
    results = list(container.query_items(query=query, enable_cross_partition_query=True))
    if results and results[0]:
        num = int(results[0].replace("INC", "")) + 1
    else:
        num = 1001
    return f"INC{num:05d}"


def create_ticket(
    title: str,
    description: str,
    priority: str = "medium",
    category: str = "General",
    reporter_email: str = "user@company.com",
) -> str:
    """Create a new IT support ticket. Use this when a user reports an issue that needs tracking.

    :param title: Short summary of the issue
    :param description: Detailed description of the problem
    :param priority: Priority level - low, medium, high, or critical
    :param category: Category like Network, Email, Hardware, Identity, Software, DevOps
    :param reporter_email: Email of the person reporting the issue
    :return: JSON with ticket details and ticket ID
    """
    container = get_container(CONTAINER_NAME)
    ticket_id = _get_next_ticket_id()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    sla_hours = {"critical": 1, "high": 4, "medium": 8, "low": 24}
    sla_h = sla_hours.get(priority.lower(), 8)
    sla_due = (datetime.now(timezone.utc) + timedelta(hours=sla_h)).strftime("%Y-%m-%d %H:%M:%S UTC")

    ticket = {
        "id": ticket_id, "ticket_id": ticket_id, "title": title, "description": description,
        "priority": priority.lower(), "category": category, "status": "open",
        "reporter": reporter_email, "assigned_to": "Unassigned",
        "created_at": now, "updated_at": now, "sla_due": sla_due,
        "resolution": None, "notes": [],
    }
    container.upsert_item(ticket)
    return json.dumps({"message": f"Ticket {ticket_id} created successfully.", "ticket": ticket}, indent=2)


def search_tickets(query: str = "", status: str = "", priority: str = "") -> str:
    """Search existing support tickets by keyword, status, or priority.

    :param query: Search keyword in title or description. Leave empty to list all.
    :param status: Filter by status - open, in_progress, resolved, closed
    :param priority: Filter by priority - low, medium, high, critical
    :return: JSON with matching tickets
    """
    container = get_container(CONTAINER_NAME)
    conditions = []
    params = []
    if status:
        conditions.append("c.status = @status")
        params.append({"name": "@status", "value": status.lower()})
    if priority:
        conditions.append("c.priority = @priority")
        params.append({"name": "@priority", "value": priority.lower()})
    if query:
        conditions.append("(CONTAINS(LOWER(c.title), @q) OR CONTAINS(LOWER(c.description), @q))")
        params.append({"name": "@q", "value": query.lower()})

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    sql = f"SELECT c.ticket_id, c.title, c.priority, c.status, c.assigned_to, c.created_at, c.sla_due FROM c WHERE {where_clause}"

    results = list(container.query_items(query=sql, parameters=params, enable_cross_partition_query=True))
    if not results:
        return json.dumps({"message": "No tickets found matching your criteria.", "count": 0})
    return json.dumps({"count": len(results), "tickets": results}, indent=2)


def update_ticket(
    ticket_id: str,
    status: str = "",
    assigned_to: str = "",
    priority: str = "",
    add_note: str = "",
    resolution: str = "",
) -> str:
    """Update an existing support ticket's status, assignment, priority, or add notes.

    :param ticket_id: The ticket ID, e.g. INC01001
    :param status: New status - open, in_progress, resolved, closed
    :param assigned_to: Assign to a team member or team name
    :param priority: Change priority - low, medium, high, critical
    :param add_note: Add a note or comment to the ticket
    :param resolution: Resolution details when resolving the ticket
    :return: JSON with updated ticket
    """
    container = get_container(CONTAINER_NAME)
    # Find the ticket
    sql = "SELECT * FROM c WHERE c.ticket_id = @tid"
    items = list(container.query_items(query=sql, parameters=[{"name": "@tid", "value": ticket_id.upper()}], enable_cross_partition_query=True))
    if not items:
        return json.dumps({"error": f"Ticket {ticket_id} not found."})

    ticket = items[0]
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
    container.upsert_item(ticket)

    return json.dumps({
        "message": f"Ticket {ticket_id} updated: {', '.join(changes) if changes else 'no changes'}",
        "ticket": {k: v for k, v in ticket.items() if not k.startswith("_")},
    }, indent=2)


def escalate_ticket(ticket_id: str, escalation_reason: str, escalate_to: str = "Level 2 Support") -> str:
    """Escalate a ticket to a higher support tier.

    :param ticket_id: The ticket ID to escalate
    :param escalation_reason: Why this ticket needs escalation
    :param escalate_to: Target team - Level 2 Support, Level 3 Engineering, Management
    :return: JSON with escalation details
    """
    container = get_container(CONTAINER_NAME)
    sql = "SELECT * FROM c WHERE c.ticket_id = @tid"
    items = list(container.query_items(query=sql, parameters=[{"name": "@tid", "value": ticket_id.upper()}], enable_cross_partition_query=True))
    if not items:
        return json.dumps({"error": f"Ticket {ticket_id} not found."})

    ticket = items[0]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    ticket["assigned_to"] = escalate_to
    ticket["priority"] = "high" if ticket["priority"] in ("low", "medium") else ticket["priority"]
    ticket["notes"].append({"time": now, "note": f"ESCALATED to {escalate_to}: {escalation_reason}"})
    ticket["updated_at"] = now
    container.upsert_item(ticket)

    return json.dumps({
        "message": f"Ticket {ticket_id} escalated to {escalate_to}.",
        "ticket": {k: v for k, v in ticket.items() if not k.startswith("_")},
    }, indent=2)


def calculate_sla_metrics(ticket_id: str = "") -> str:
    """Calculate SLA compliance metrics for a specific ticket or all tickets.

    :param ticket_id: Specific ticket ID to check, or empty for overall metrics
    :return: JSON with SLA compliance data
    """
    container = get_container(CONTAINER_NAME)
    now = datetime.now(timezone.utc)

    if ticket_id:
        sql = "SELECT * FROM c WHERE c.ticket_id = @tid"
        items = list(container.query_items(query=sql, parameters=[{"name": "@tid", "value": ticket_id.upper()}], enable_cross_partition_query=True))
        if not items:
            return json.dumps({"error": f"Ticket {ticket_id} not found."})
        ticket = items[0]
        sla_due = datetime.strptime(ticket["sla_due"], "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)
        remaining = sla_due - now
        breached = remaining.total_seconds() < 0
        return json.dumps({
            "ticket_id": ticket["ticket_id"], "priority": ticket["priority"],
            "status": ticket["status"], "sla_due": ticket["sla_due"],
            "time_remaining": str(remaining) if not breached else "BREACHED",
            "sla_breached": breached,
        }, indent=2)

    sql = "SELECT c.ticket_id, c.status, c.sla_due FROM c"
    items = list(container.query_items(query=sql, enable_cross_partition_query=True))
    total = len(items)
    if total == 0:
        return json.dumps({"message": "No tickets to calculate SLA for.", "total_tickets": 0})
    breached = sum(1 for t in items
                   if datetime.strptime(t["sla_due"], "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc) < now
                   and t["status"] not in ("resolved", "closed"))
    compliance = ((total - breached) / total * 100) if total > 0 else 100
    return json.dumps({
        "total_tickets": total, "sla_breached": breached,
        "sla_compliance_pct": round(compliance, 1),
    }, indent=2)


ALL_FUNCTIONS = {create_ticket, search_tickets, update_ticket, escalate_ticket, calculate_sla_metrics}
