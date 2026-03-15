"""
MCP Tool 4: Employee Services (backed by Cosmos DB)
HR lookup, employee directory, leave management, and onboarding help.
Container: employees (partition key: /department)
"""

import json
from .cosmos_client import get_container

CONTAINER_NAME = "employees"

ONBOARDING_CHECKLIST = [
    {"step": 1, "task": "Set up laptop and install required software via Company Portal", "owner": "IT Operations"},
    {"step": 2, "task": "Activate email account and configure Outlook", "owner": "IT Operations"},
    {"step": 3, "task": "Set up MFA on Microsoft Authenticator", "owner": "Employee + IT"},
    {"step": 4, "task": "Complete security awareness training (LMS)", "owner": "Employee"},
    {"step": 5, "task": "Join required Teams channels and distribution lists", "owner": "Employee + Manager"},
    {"step": 6, "task": "Request access to department-specific systems via Service Catalog", "owner": "Manager"},
    {"step": 7, "task": "VPN setup for remote access", "owner": "IT Operations"},
    {"step": 8, "task": "Badge activation and office access registration", "owner": "Facilities"},
]


def lookup_employee(query: str) -> str:
    """Look up an employee by name, email, or employee ID.

    :param query: Employee name, email, or ID (e.g. 'Sarah Johnson', 'sarah.johnson@company.com', 'E1001')
    :return: JSON with employee details
    """
    container = get_container(CONTAINER_NAME)
    query_lower = query.lower()

    sql = "SELECT * FROM c WHERE CONTAINS(LOWER(c.name), @q) OR CONTAINS(LOWER(c.email), @q) OR LOWER(c.id) = @q"
    items = list(container.query_items(
        query=sql,
        parameters=[{"name": "@q", "value": query_lower}],
        enable_cross_partition_query=True,
    ))
    if not items:
        return json.dumps({"message": f"No employee found matching '{query}'."})

    results = [{
        "id": e["id"], "name": e["name"], "email": e["email"],
        "department": e["department"], "title": e["title"],
        "manager": e["manager"], "location": e["location"],
        "phone": e["phone"],
    } for e in items]
    return json.dumps({"count": len(results), "employees": results}, indent=2)


def get_leave_balance(employee_id: str) -> str:
    """Check leave balance for an employee (annual, sick, personal days).

    :param employee_id: Employee ID, e.g. E1001
    :return: JSON with leave balance details
    """
    container = get_container(CONTAINER_NAME)
    sql = "SELECT * FROM c WHERE c.id = @id"
    items = list(container.query_items(
        query=sql,
        parameters=[{"name": "@id", "value": employee_id.upper()}],
        enable_cross_partition_query=True,
    ))
    if not items:
        return json.dumps({"error": f"Employee {employee_id} not found."})
    emp = items[0]
    lb = emp.get("leave_balance", {})
    return json.dumps({
        "employee": emp["name"], "employee_id": emp["id"],
        "leave_balance": lb, "total_available": sum(lb.values()),
    }, indent=2)


def get_department_directory(department: str = "") -> str:
    """Get the employee directory for a specific department or list all departments.

    :param department: Department name like Engineering, IT Operations, Marketing. Leave empty for all departments.
    :return: JSON with department directory
    """
    container = get_container(CONTAINER_NAME)

    if department:
        sql = "SELECT * FROM c WHERE LOWER(c.department) = @dept"
        items = list(container.query_items(
            query=sql,
            parameters=[{"name": "@dept", "value": department.lower()}],
            enable_cross_partition_query=True,
        ))
        if not items:
            all_depts = list({r["department"] for r in container.query_items(query="SELECT c.department FROM c", enable_cross_partition_query=True)})
            return json.dumps({"error": f"Department '{department}' not found.", "available_departments": all_depts})
        members = [{"id": e["id"], "name": e["name"], "title": e["title"], "email": e["email"]} for e in items]
        return json.dumps({"department": department, "headcount": len(members), "members": members}, indent=2)

    items = list(container.query_items(query="SELECT c.department FROM c", enable_cross_partition_query=True))
    depts = {}
    for e in items:
        d = e["department"]
        depts[d] = depts.get(d, 0) + 1
    return json.dumps({"total_employees": len(items), "departments": depts}, indent=2)


def get_onboarding_checklist() -> str:
    """Get the new employee onboarding checklist with all required IT setup steps.

    :return: JSON with onboarding steps
    """
    return json.dumps({"total_steps": len(ONBOARDING_CHECKLIST), "checklist": ONBOARDING_CHECKLIST}, indent=2)


ALL_FUNCTIONS = {lookup_employee, get_leave_balance, get_department_directory, get_onboarding_checklist}
