"""
MCP Tool 5: Security Operations (backed by Cosmos DB)
Security alerts, access requests, compliance audit, and threat monitoring.
Containers: security_alerts (/severity), access_requests (/status), compliance (/id)
"""

import json
from datetime import datetime, timezone
from .cosmos_client import get_container

ALERTS_CONTAINER = "security_alerts"
ACCESS_CONTAINER = "access_requests"
COMPLIANCE_CONTAINER = "compliance"

ACCESS_REQUEST_POLICIES = {
    "standard_software": {"approval_levels": 1, "approvers": ["Direct Manager"], "sla_hours": 24},
    "privileged_access": {"approval_levels": 2, "approvers": ["Direct Manager", "Security Team"], "sla_hours": 48},
    "admin_rights": {"approval_levels": 3, "approvers": ["Direct Manager", "Security Team", "CISO"], "sla_hours": 72},
    "vendor_access": {"approval_levels": 2, "approvers": ["Project Lead", "Security Team"], "sla_hours": 48},
    "production_db": {"approval_levels": 3, "approvers": ["Direct Manager", "DBA Team Lead", "Security Team"], "sla_hours": 72},
}


def get_security_alerts(severity: str = "") -> str:
    """Get active security alerts and threats. Filter by severity if needed.

    :param severity: Filter by severity - critical, high, medium, low. Leave empty for all.
    :return: JSON with security alerts
    """
    container = get_container(ALERTS_CONTAINER)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if severity:
        sql = "SELECT * FROM c WHERE c.severity = @sev"
        items = list(container.query_items(query=sql, parameters=[{"name": "@sev", "value": severity.lower()}], enable_cross_partition_query=True))
    else:
        items = list(container.query_items(query="SELECT * FROM c", enable_cross_partition_query=True))

    alerts = [{k: v for k, v in a.items() if not k.startswith("_")} for a in items]
    return json.dumps({"timestamp": now, "total_alerts": len(alerts), "alerts": alerts}, indent=2)


def check_access_request_policy(access_type: str) -> str:
    """Check the approval policy and SLA for a specific type of access request.

    :param access_type: Type of access - standard_software, privileged_access, admin_rights, vendor_access, production_db
    :return: JSON with approval requirements
    """
    policy = ACCESS_REQUEST_POLICIES.get(access_type.lower().replace(" ", "_"))
    if not policy:
        return json.dumps({
            "error": f"Access type '{access_type}' not found.",
            "available_types": list(ACCESS_REQUEST_POLICIES.keys()),
        })
    return json.dumps({"access_type": access_type, "policy": policy}, indent=2)


def get_compliance_report(policy_name: str = "") -> str:
    """Get security compliance report for a specific policy or all policies.

    :param policy_name: Specific policy like password_policy, mfa_enrollment. Leave empty for full report.
    :return: JSON with compliance percentages and non-compliant counts
    """
    container = get_container(COMPLIANCE_CONTAINER)

    if policy_name:
        key = policy_name.lower().replace(" ", "_")
        sql = "SELECT * FROM c WHERE c.id = @id"
        items = list(container.query_items(query=sql, parameters=[{"name": "@id", "value": key}], enable_cross_partition_query=True))
        if not items:
            all_ids = [r["id"] for r in container.query_items(query="SELECT c.id FROM c", enable_cross_partition_query=True)]
            return json.dumps({"error": f"Policy '{policy_name}' not found.", "available_policies": all_ids})
        p = items[0]
        return json.dumps({"policy": p["id"], "details": {"compliant": p["compliant"], "non_compliant_users": p["non_compliant_users"], "policy": p["policy"]}}, indent=2)

    items = list(container.query_items(query="SELECT * FROM c", enable_cross_partition_query=True))
    if not items:
        return json.dumps({"message": "No compliance policies found."})
    overall = round(sum(p["compliant"] for p in items) / len(items), 1)
    policies = {p["id"]: {"compliance_pct": p["compliant"], "non_compliant_users": p["non_compliant_users"]} for p in items}
    return json.dumps({"overall_compliance_pct": overall, "policies": policies}, indent=2)


def list_pending_access_requests() -> str:
    """List all pending access requests that need approval.

    :return: JSON with pending access requests
    """
    container = get_container(ACCESS_CONTAINER)
    items = list(container.query_items(query="SELECT * FROM c", enable_cross_partition_query=True))
    clean = [{k: v for k, v in r.items() if not k.startswith("_")} for r in items]
    pending_count = sum(1 for r in clean if "pending" in r.get("status", ""))
    return json.dumps({"total_pending": pending_count, "requests": clean}, indent=2)


ALL_FUNCTIONS = {get_security_alerts, check_access_request_policy, get_compliance_report, list_pending_access_requests}
