"""
Seed Script: Populate Cosmos DB with IT Help Desk data for all 5 MCP Tool Modules.

Containers seeded:
  1. tickets        - Sample support tickets (Ticket Management MCP)
  2. knowledgebase  - Troubleshooting KB articles (Knowledge Base MCP)
  3. systems        - Infrastructure status (System Monitoring MCP)
  4. incidents      - Active incidents (System Monitoring MCP)
  5. employees      - Employee directory (Employee Services MCP)
  6. security_alerts - Security threats (Security Operations MCP)
  7. access_requests - Pending access requests (Security Operations MCP)
  8. compliance     - Compliance policies (Security Operations MCP)
"""

import os
import sys
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential

COSMOS_ENDPOINT = os.environ.get(
    "COSMOS_ENDPOINT",
    "https://cosmos-challenge5-mhdnafeklrure.documents.azure.com:443/"
)
DATABASE_NAME = "helpdesk-db"


def get_client():
    credential = DefaultAzureCredential()
    return CosmosClient(COSMOS_ENDPOINT, credential=credential)


def seed_container(db, container_name, items):
    container = db.get_container_client(container_name)
    count = 0
    for item in items:
        container.upsert_item(item)
        count += 1
    print(f"  [{container_name}] Seeded {count} items")
    return count


def main():
    print(f"Connecting to Cosmos DB: {COSMOS_ENDPOINT}")
    client = get_client()
    db = client.get_database_client(DATABASE_NAME)
    total = 0

    # ---- MCP 1: Ticket Management ----
    print("\n=== MCP 1: Ticket Management ===")
    tickets = [
        {"id": "INC01001", "ticket_id": "INC01001", "title": "VPN disconnects every 30 minutes",
         "description": "Since Monday morning, my VPN connection drops every 30 minutes. I have to reconnect manually each time. I'm using the Cisco AnyConnect client on Windows 11.",
         "priority": "high", "category": "Network", "status": "open",
         "reporter": "sarah.johnson@company.com", "assigned_to": "Network Team",
         "created_at": "2026-03-15 08:30:00 UTC", "updated_at": "2026-03-15 09:00:00 UTC",
         "sla_due": "2026-03-15 12:30:00 UTC", "resolution": None,
         "notes": [{"time": "2026-03-15 09:00:00 UTC", "note": "Assigned to Network Team for investigation."}]},
        {"id": "INC01002", "ticket_id": "INC01002", "title": "Cannot access SharePoint project site",
         "description": "Getting 403 Forbidden when trying to access the Engineering team SharePoint site. I was able to access it last week. My manager approved my access.",
         "priority": "medium", "category": "Access", "status": "in_progress",
         "reporter": "alex.kim@company.com", "assigned_to": "Raj Patel",
         "created_at": "2026-03-14 14:00:00 UTC", "updated_at": "2026-03-15 08:15:00 UTC",
         "sla_due": "2026-03-14 22:00:00 UTC", "resolution": None,
         "notes": [
             {"time": "2026-03-14 15:00:00 UTC", "note": "Checking SharePoint admin permissions."},
             {"time": "2026-03-15 08:15:00 UTC", "note": "Found permission mismatch. Fixing now."},
         ]},
        {"id": "INC01003", "ticket_id": "INC01003", "title": "Laptop blue screen after Windows update",
         "description": "After installing KB5036893 update, my Dell Latitude 5540 blue screens with DRIVER_IRQL_NOT_LESS_OR_EQUAL about once per hour.",
         "priority": "high", "category": "Hardware", "status": "open",
         "reporter": "jessica.williams@company.com", "assigned_to": "Unassigned",
         "created_at": "2026-03-15 07:45:00 UTC", "updated_at": "2026-03-15 07:45:00 UTC",
         "sla_due": "2026-03-15 11:45:00 UTC", "resolution": None, "notes": []},
        {"id": "INC01004", "ticket_id": "INC01004", "title": "Email not syncing on iPhone",
         "description": "Outlook on my iPhone 15 stopped syncing emails 2 days ago. I can access email on my laptop fine. Already tried removing and re-adding the account.",
         "priority": "medium", "category": "Email", "status": "open",
         "reporter": "maria.rodriguez@company.com", "assigned_to": "Unassigned",
         "created_at": "2026-03-14 16:30:00 UTC", "updated_at": "2026-03-14 16:30:00 UTC",
         "sla_due": "2026-03-15 00:30:00 UTC", "resolution": None, "notes": []},
        {"id": "INC01005", "ticket_id": "INC01005", "title": "CI/CD pipeline blocked - expired secrets",
         "description": "Production deployment pipeline in Azure DevOps failed. Build logs show expired Key Vault secrets for the database connection string. Release is blocked.",
         "priority": "critical", "category": "DevOps", "status": "in_progress",
         "reporter": "maria.rodriguez@company.com", "assigned_to": "Level 2 Support",
         "created_at": "2026-03-15 07:50:00 UTC", "updated_at": "2026-03-15 08:10:00 UTC",
         "sla_due": "2026-03-15 08:50:00 UTC", "resolution": None,
         "notes": [
             {"time": "2026-03-15 08:00:00 UTC", "note": "ESCALATED to Level 2 Support: Production deployment blocked."},
             {"time": "2026-03-15 08:10:00 UTC", "note": "Identifying expired secrets in Key Vault."},
         ]},
        {"id": "INC01006", "ticket_id": "INC01006", "title": "MFA not working after phone replacement",
         "description": "Got a new phone and the authenticator app MFA codes aren't working. I can't log into any company systems. Need urgent reset.",
         "priority": "high", "category": "Identity", "status": "resolved",
         "reporter": "james.thompson@company.com", "assigned_to": "Emily Davis",
         "created_at": "2026-03-14 09:00:00 UTC", "updated_at": "2026-03-14 10:30:00 UTC",
         "sla_due": "2026-03-14 13:00:00 UTC", "resolution": "MFA reset completed. User re-enrolled with new phone's Authenticator app.",
         "notes": [
             {"time": "2026-03-14 09:20:00 UTC", "note": "Verified identity with photo ID at service desk."},
             {"time": "2026-03-14 10:30:00 UTC", "note": "MFA reset and re-enrollment completed."},
         ]},
        {"id": "INC01007", "ticket_id": "INC01007", "title": "Printer queue stuck on Floor 3",
         "description": "The HP LaserJet on Floor 3 has a stuck print queue. Multiple users cannot print. Restarting Print Spooler didn't help.",
         "priority": "low", "category": "Hardware", "status": "open",
         "reporter": "emily.davis@company.com", "assigned_to": "Unassigned",
         "created_at": "2026-03-15 09:00:00 UTC", "updated_at": "2026-03-15 09:00:00 UTC",
         "sla_due": "2026-03-16 09:00:00 UTC", "resolution": None, "notes": []},
    ]
    total += seed_container(db, "tickets", tickets)

    # ---- MCP 2: Knowledge Base ----
    print("\n=== MCP 2: Knowledge Base ===")
    kb_articles = [
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
        {"id": "KB011", "title": "Outlook Calendar Sync Issues", "category": "Email",
         "symptoms": ["calendar not syncing", "meeting missing", "outlook calendar", "double booking"],
         "solution": "1. In Outlook, File > Account Settings > repair the account.\n2. Clear the offline cache: File > Account Settings > Data Files > truncate OST file.\n3. Verify calendar permissions under Calendar Properties > Permissions.\n4. Check free/busy status publishing is enabled.\n5. Restart Outlook in safe mode: outlook.exe /safe."},
        {"id": "KB012", "title": "Wi-Fi Connectivity Problems", "category": "Network",
         "symptoms": ["wifi not connecting", "wifi slow", "wireless drops", "no internet", "wifi password"],
         "solution": "1. Forget the network and reconnect with current credentials.\n2. Run: ipconfig /flushdns in Command Prompt.\n3. Disable and re-enable the Wi-Fi adapter.\n4. Move closer to the access point.\n5. If office Wi-Fi, verify you're on the corporate SSID, not guest.\n6. Submit a desk move request for persistent coverage issues."},
    ]
    total += seed_container(db, "knowledgebase", kb_articles)

    # ---- MCP 3: System Monitoring ----
    print("\n=== MCP 3: System Monitoring ===")
    systems = [
        {"id": "email-server", "name": "Email Server (Exchange Online)", "status": "operational", "uptime": "99.97%", "last_incident": "2026-03-10 14:22 UTC", "response_time_ms": 45, "cpu_pct": 28, "mem_pct": 52, "region": "East US 2"},
        {"id": "vpn-gateway", "name": "VPN Gateway", "status": "degraded", "uptime": "98.5%", "last_incident": "2026-03-15 06:10 UTC", "response_time_ms": 320, "cpu_pct": 78, "mem_pct": 81, "region": "East US 2"},
        {"id": "erp-system", "name": "ERP System (SAP)", "status": "operational", "uptime": "99.99%", "last_incident": "2026-02-28 09:00 UTC", "response_time_ms": 120, "cpu_pct": 45, "mem_pct": 67, "region": "West US"},
        {"id": "active-directory", "name": "Active Directory", "status": "operational", "uptime": "99.99%", "last_incident": "2026-01-15 03:40 UTC", "response_time_ms": 12, "cpu_pct": 15, "mem_pct": 35, "region": "East US 2"},
        {"id": "file-storage", "name": "File Storage (SharePoint)", "status": "operational", "uptime": "99.95%", "last_incident": "2026-03-12 18:30 UTC", "response_time_ms": 85, "cpu_pct": 32, "mem_pct": 58, "region": "East US 2"},
        {"id": "ci-cd-pipeline", "name": "CI/CD Pipeline (Azure DevOps)", "status": "outage", "uptime": "95.2%", "last_incident": "2026-03-15 07:45 UTC", "response_time_ms": None, "cpu_pct": None, "mem_pct": None, "region": "Central US"},
        {"id": "database-cluster", "name": "Database Cluster (SQL)", "status": "operational", "uptime": "99.98%", "last_incident": "2026-03-01 12:00 UTC", "response_time_ms": 8, "cpu_pct": 55, "mem_pct": 72, "region": "East US 2"},
        {"id": "monitoring-stack", "name": "Monitoring (Grafana/Prometheus)", "status": "operational", "uptime": "99.90%", "last_incident": "2026-03-08 22:15 UTC", "response_time_ms": 60, "cpu_pct": 22, "mem_pct": 40, "region": "East US 2"},
        {"id": "kubernetes-cluster", "name": "Kubernetes Cluster (AKS)", "status": "operational", "uptime": "99.95%", "last_incident": "2026-03-05 11:30 UTC", "response_time_ms": 15, "cpu_pct": 62, "mem_pct": 70, "region": "East US 2"},
        {"id": "dns-server", "name": "DNS Server", "status": "operational", "uptime": "99.999%", "last_incident": "2025-12-20 01:00 UTC", "response_time_ms": 3, "cpu_pct": 8, "mem_pct": 20, "region": "Global"},
    ]
    total += seed_container(db, "systems", systems)

    incidents = [
        {"id": "INC-SYS-001", "system": "ci-cd-pipeline", "severity": "critical",
         "title": "Azure DevOps build agents unresponsive",
         "started": "2026-03-15 07:45 UTC", "status": "investigating", "affected_users": 120,
         "updates": ["07:45 - Reports of pipeline failures.", "08:00 - Build agents confirmed unresponsive.", "08:15 - Engineering team engaged, investigating root cause."]},
        {"id": "INC-SYS-002", "system": "vpn-gateway", "severity": "warning",
         "title": "VPN gateway high latency",
         "started": "2026-03-15 06:10 UTC", "status": "monitoring", "affected_users": 45,
         "updates": ["06:10 - Latency spike detected on VPN gateway.", "06:30 - Traced to ISP peering issue.", "07:00 - ISP notified, monitoring for improvement."]},
    ]
    total += seed_container(db, "incidents", incidents)

    # ---- MCP 4: Employee Services ----
    print("\n=== MCP 4: Employee Services ===")
    employees = [
        {"id": "E1001", "name": "Sarah Johnson", "email": "sarah.johnson@company.com", "department": "Engineering", "title": "Senior Developer", "manager": "Mike Chen", "location": "Seattle", "phone": "+1-206-555-0101", "start_date": "2021-03-15", "leave_balance": {"annual": 12, "sick": 8, "personal": 3}},
        {"id": "E1002", "name": "Mike Chen", "email": "mike.chen@company.com", "department": "Engineering", "title": "Engineering Manager", "manager": "Lisa Park", "location": "Seattle", "phone": "+1-206-555-0102", "start_date": "2019-01-10", "leave_balance": {"annual": 18, "sick": 10, "personal": 3}},
        {"id": "E1003", "name": "Jessica Williams", "email": "jessica.williams@company.com", "department": "Marketing", "title": "Marketing Lead", "manager": "David Brown", "location": "New York", "phone": "+1-212-555-0103", "start_date": "2022-06-01", "leave_balance": {"annual": 8, "sick": 10, "personal": 2}},
        {"id": "E1004", "name": "Raj Patel", "email": "raj.patel@company.com", "department": "IT Operations", "title": "Systems Administrator", "manager": "Karen Lee", "location": "Austin", "phone": "+1-512-555-0104", "start_date": "2020-09-21", "leave_balance": {"annual": 14, "sick": 7, "personal": 3}},
        {"id": "E1005", "name": "Emily Davis", "email": "emily.davis@company.com", "department": "Human Resources", "title": "HR Specialist", "manager": "Tom Wilson", "location": "New York", "phone": "+1-212-555-0105", "start_date": "2023-02-14", "leave_balance": {"annual": 6, "sick": 10, "personal": 2}},
        {"id": "E1006", "name": "Alex Kim", "email": "alex.kim@company.com", "department": "Finance", "title": "Financial Analyst", "manager": "Nancy Garcia", "location": "Seattle", "phone": "+1-206-555-0106", "start_date": "2021-11-01", "leave_balance": {"annual": 10, "sick": 9, "personal": 3}},
        {"id": "E1007", "name": "Maria Rodriguez", "email": "maria.rodriguez@company.com", "department": "Engineering", "title": "DevOps Engineer", "manager": "Mike Chen", "location": "Austin", "phone": "+1-512-555-0107", "start_date": "2022-08-15", "leave_balance": {"annual": 9, "sick": 10, "personal": 2}},
        {"id": "E1008", "name": "James Thompson", "email": "james.thompson@company.com", "department": "IT Operations", "title": "Network Engineer", "manager": "Karen Lee", "location": "Seattle", "phone": "+1-206-555-0108", "start_date": "2020-04-01", "leave_balance": {"annual": 15, "sick": 6, "personal": 3}},
    ]
    total += seed_container(db, "employees", employees)

    # ---- MCP 5: Security Operations ----
    print("\n=== MCP 5: Security Operations ===")
    alerts = [
        {"id": "SEC-001", "severity": "critical", "type": "Brute Force Login Attempt", "source_ip": "203.0.113.42", "target": "Active Directory", "timestamp": "2026-03-15 07:30 UTC", "status": "investigating", "details": "50+ failed login attempts from external IP targeting admin accounts.", "recommended_action": "Block source IP, enforce account lockout, check for compromised credentials."},
        {"id": "SEC-002", "severity": "high", "type": "Suspicious Data Exfiltration", "source_ip": "10.0.5.23 (internal)", "target": "SharePoint", "timestamp": "2026-03-15 06:45 UTC", "status": "investigating", "details": "User downloaded 2.3 GB of files from SharePoint within 10 minutes.", "recommended_action": "Review user activity, verify business justification, consider disabling access."},
        {"id": "SEC-003", "severity": "medium", "type": "Expired SSL Certificate", "source_ip": "N/A", "target": "api.internal.company.com", "timestamp": "2026-03-14 23:00 UTC", "status": "open", "details": "SSL certificate for internal API expired yesterday. Services using this endpoint may show cert warnings.", "recommended_action": "Renew SSL certificate, update in Azure Key Vault, rotate in all dependent services."},
        {"id": "SEC-004", "severity": "low", "type": "Unusual Login Location", "source_ip": "104.28.12.45", "target": "user emily.davis@company.com", "timestamp": "2026-03-15 08:00 UTC", "status": "monitoring", "details": "Login from Brazil while user's usual location is New York. MFA was successful.", "recommended_action": "Verify with user if traveling. If not, force password reset and review session tokens."},
    ]
    total += seed_container(db, "security_alerts", alerts)

    access_requests = [
        {"id": "AR-2001", "requester": "Sarah Johnson", "type": "Production Database Read Access", "status": "pending_approval", "approver": "Security Team", "submitted": "2026-03-14 14:00 UTC"},
        {"id": "AR-2002", "requester": "Alex Kim", "type": "Power BI Premium License", "status": "approved", "approver": "Nancy Garcia", "submitted": "2026-03-13 10:00 UTC"},
        {"id": "AR-2003", "requester": "Maria Rodriguez", "type": "Azure Subscription Contributor Role", "status": "pending_approval", "approver": "CISO", "submitted": "2026-03-14 16:30 UTC"},
    ]
    total += seed_container(db, "access_requests", access_requests)

    compliance = [
        {"id": "password_policy", "compliant": 94.5, "non_compliant_users": 28, "policy": "Min 12 chars, rotation every 90 days"},
        {"id": "mfa_enrollment", "compliant": 98.2, "non_compliant_users": 9, "policy": "All users must have MFA enabled"},
        {"id": "endpoint_protection", "compliant": 97.1, "non_compliant_users": 15, "policy": "Defender for Endpoint active on all devices"},
        {"id": "data_classification", "compliant": 89.3, "non_compliant_users": 54, "policy": "All documents must be classified within 30 days"},
        {"id": "security_training", "compliant": 91.8, "non_compliant_users": 41, "policy": "Annual security awareness training completion"},
    ]
    total += seed_container(db, "compliance", compliance)

    print(f"\n{'='*50}")
    print(f"DONE: Seeded {total} total items across 8 containers")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
