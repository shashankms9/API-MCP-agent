"""
MCP Tool 3: System Monitoring (backed by Cosmos DB)
Real-time infrastructure health checks, performance metrics, and incident tracking.
Containers: systems (partition key: /region), incidents (partition key: /severity)
"""

import json
from datetime import datetime, timezone
from .cosmos_client import get_container

SYSTEMS_CONTAINER = "systems"
INCIDENTS_CONTAINER = "incidents"


def get_system_status(system_name: str = "") -> str:
    """Check real-time health status of IT systems and infrastructure.

    :param system_name: Specific system to check, e.g. 'vpn-gateway' or 'email-server'. Leave empty for full dashboard.
    :return: JSON with system health details
    """
    container = get_container(SYSTEMS_CONTAINER)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if system_name:
        key = system_name.lower().replace(" ", "-")
        sql = "SELECT * FROM c WHERE c.id = @id"
        items = list(container.query_items(query=sql, parameters=[{"name": "@id", "value": key}], enable_cross_partition_query=True))
        if not items:
            all_ids = [r["id"] for r in container.query_items(query="SELECT c.id FROM c", enable_cross_partition_query=True)]
            return json.dumps({"error": f"System '{system_name}' not found.", "available_systems": all_ids})
        sys_info = items[0]
        return json.dumps({"timestamp": now, "system": {k: v for k, v in sys_info.items() if not k.startswith("_")}}, indent=2)

    items = list(container.query_items(query="SELECT * FROM c", enable_cross_partition_query=True))
    summary = {"operational": 0, "degraded": 0, "outage": 0}
    systems_list = []
    for s in items:
        summary[s["status"]] = summary.get(s["status"], 0) + 1
        systems_list.append({"id": s["id"], "name": s["name"], "status": s["status"], "response_time_ms": s.get("response_time_ms")})
    return json.dumps({
        "timestamp": now,
        "overall_health": "degraded" if summary.get("outage", 0) > 0 or summary.get("degraded", 0) > 0 else "all systems operational",
        "summary": summary, "systems": systems_list,
    }, indent=2)


def get_system_performance(system_name: str) -> str:
    """Get detailed performance metrics for a specific system (CPU, memory, response time).

    :param system_name: The system ID, e.g. 'database-cluster', 'vpn-gateway'
    :return: JSON with performance metrics
    """
    container = get_container(SYSTEMS_CONTAINER)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    key = system_name.lower().replace(" ", "-")
    sql = "SELECT * FROM c WHERE c.id = @id"
    items = list(container.query_items(query=sql, parameters=[{"name": "@id", "value": key}], enable_cross_partition_query=True))
    if not items:
        all_ids = [r["id"] for r in container.query_items(query="SELECT c.id FROM c", enable_cross_partition_query=True)]
        return json.dumps({"error": f"System '{system_name}' not found.", "available_systems": all_ids})

    s = items[0]
    perf = {
        "timestamp": now,
        "system": s["name"],
        "status": s["status"],
        "metrics": {
            "response_time_ms": s.get("response_time_ms"),
            "cpu_utilization_pct": s.get("cpu_pct"),
            "memory_utilization_pct": s.get("mem_pct"),
            "uptime": s.get("uptime"),
            "region": s.get("region"),
        },
        "health_assessment": (
            "CRITICAL - System is unresponsive" if s["status"] == "outage" else
            "WARNING - Performance degraded" if s["status"] == "degraded" or (s.get("cpu_pct") and s["cpu_pct"] > 80) else
            "HEALTHY"
        ),
    }
    return json.dumps(perf, indent=2)


def get_active_incidents() -> str:
    """Get all currently active infrastructure incidents and their latest updates.

    :return: JSON with active incidents
    """
    container = get_container(INCIDENTS_CONTAINER)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    items = list(container.query_items(query="SELECT * FROM c", enable_cross_partition_query=True))
    clean = [{k: v for k, v in inc.items() if not k.startswith("_")} for inc in items]
    return json.dumps({"timestamp": now, "active_incidents": len(clean), "incidents": clean}, indent=2)


def get_current_time() -> str:
    """Get the current date and time in UTC. Useful for SLA calculations and timestamps.

    :return: Current UTC timestamp
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


ALL_FUNCTIONS = {get_system_status, get_system_performance, get_active_incidents, get_current_time}
