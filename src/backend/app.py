"""
IT Help Desk — Backend API Server
Exposes REST endpoints for all 5 MCP tool modules and the Foundry agent chat.

Architecture:
  Frontend (port 5000) ──▶ Backend (port 8000) ──▶ Cosmos DB
                                               ──▶ Foundry Agent ──▶ Function Tools ──▶ Cosmos DB

Endpoints:
  POST /api/chat                       — Agent chat (Foundry + function-call loop)
  POST /api/reset                      — Reset conversation thread

  GET  /api/tickets?status=&priority=&query=  — Search tickets
  POST /api/tickets                    — Create ticket
  PUT  /api/tickets/<id>               — Update ticket
  POST /api/tickets/<id>/escalate      — Escalate ticket
  GET  /api/tickets/sla                — SLA metrics
  GET  /api/tickets/<id>/sla           — SLA for one ticket

  GET  /api/kb?q=<query>               — Search knowledge base
  GET  /api/kb/categories              — List KB categories

  GET  /api/systems                    — All system statuses
  GET  /api/systems/<id>               — Single system status
  GET  /api/systems/<id>/performance   — System performance metrics
  GET  /api/incidents                  — Active incidents

  GET  /api/employees?q=<query>        — Search employees
  GET  /api/employees/<id>             — Single employee
  GET  /api/employees/<id>/leave       — Leave balance
  GET  /api/departments                — Department directory
  GET  /api/departments/<name>         — Specific department
  GET  /api/onboarding                 — Onboarding checklist

  GET  /api/security/alerts?severity=  — Security alerts
  GET  /api/security/compliance        — Compliance report
  GET  /api/security/compliance/<name> — Single compliance policy
  GET  /api/security/access-requests   — Pending access requests
  GET  /api/security/access-policy/<t> — Access request policy

  GET  /api/tools                      — List all registered tools
  GET  /health                         — Health check
"""

import os
import sys
import json
import time
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# ── Paths ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent  # src/
sys.path.insert(0, str(ROOT / "agent"))
sys.path.insert(0, str(ROOT / "mcp-server"))

# ── Env ────────────────────────────────────────────────────────────
env_path = ROOT.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# ── Tool modules ───────────────────────────────────────────────────
from tools.ticket_management import (
    ALL_FUNCTIONS as TICKET_FUNCS,
    create_ticket, search_tickets, update_ticket,
    escalate_ticket, calculate_sla_metrics,
)
from tools.knowledge_base import (
    ALL_FUNCTIONS as KB_FUNCS,
    search_knowledge_base, list_kb_categories,
)
from tools.system_monitoring import (
    ALL_FUNCTIONS as MONITORING_FUNCS,
    get_system_status, get_system_performance,
    get_active_incidents, get_current_time,
)
from tools.employee_services import (
    ALL_FUNCTIONS as EMPLOYEE_FUNCS,
    lookup_employee, get_leave_balance,
    get_department_directory, get_onboarding_checklist,
)
from tools.security_operations import (
    ALL_FUNCTIONS as SECURITY_FUNCS,
    get_security_alerts, check_access_request_policy,
    get_compliance_report, list_pending_access_requests,
)

# ── Foundry Agent SDK ─────────────────────────────────────────────
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import (
    MessageRole, RunStatus, ToolSet, FunctionTool,
    ToolOutput, RequiredFunctionToolCall,
)
from azure.identity import DefaultAzureCredential
from config import load_config

# ── Flask app ──────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)  # Allow frontend on different port

# ── Singletons ─────────────────────────────────────────────────────
_client = None
_agent = None
_toolset = None
_func_lookup = None
_threads = {}


def _build_toolset():
    ts = ToolSet()
    all_fns = set()
    all_fns.update(TICKET_FUNCS)
    all_fns.update(KB_FUNCS)
    all_fns.update(MONITORING_FUNCS)
    all_fns.update(EMPLOYEE_FUNCS)
    all_fns.update(SECURITY_FUNCS)
    ts.add(FunctionTool(functions=all_fns))
    lookup = {f.__name__: f for f in all_fns}
    print(f"[BACKEND] ToolSet: {len(all_fns)} functions from 5 MCP modules")
    return ts, lookup


def _get_agent():
    global _client, _agent, _toolset, _func_lookup
    if _client is None:
        cfg = load_config()
        cred = DefaultAzureCredential()
        _client = AgentsClient(endpoint=cfg.foundry_endpoint, credential=cred)
        _toolset, _func_lookup = _build_toolset()
        _agent = _client.create_agent(
            model=cfg.model_deployment_name,
            name=cfg.agent_name,
            instructions=cfg.agent_instructions,
            toolset=_toolset,
        )
        print(f"[BACKEND] Agent created: {_agent.name} (id={_agent.id})")
    return _client, _agent


# ── Helper: parse tool JSON result ────────────────────────────────
def _j(result_str):
    """Parse a JSON string returned by a tool function."""
    return json.loads(result_str)


# ═══════════════════════════════════════════════════════════════════
# 1. AGENT CHAT
# ═══════════════════════════════════════════════════════════════════

@app.route("/api/chat", methods=["POST"])
def chat():
    """Send a message to the Foundry agent, execute tool calls, return the reply."""
    try:
        data = request.get_json()
        user_msg = (data.get("message") or "").strip()
        session_id = data.get("session_id", "default")
        if not user_msg:
            return jsonify({"error": "Empty message"}), 400

        client, agent = _get_agent()

        if session_id not in _threads:
            t = client.threads.create()
            _threads[session_id] = t.id
            print(f"[CHAT] New thread {t.id} for session {session_id}")
        thread_id = _threads[session_id]

        client.messages.create(thread_id=thread_id, role=MessageRole.USER, content=user_msg)
        run = client.runs.create(thread_id=thread_id, agent_id=agent.id)
        print(f"[CHAT] Run {run.id} status={run.status}")

        tools_used = []
        for _ in range(120):
            run = client.runs.get(thread_id=thread_id, run_id=run.id)

            if run.status == RunStatus.REQUIRES_ACTION and run.required_action:
                outputs = []
                for tc in run.required_action.submit_tool_outputs.tool_calls:
                    if isinstance(tc, RequiredFunctionToolCall):
                        fname = tc.function.name
                        try:
                            args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                        except json.JSONDecodeError:
                            args = {}
                        fn = _func_lookup.get(fname)
                        if fn:
                            print(f"[TOOL] {fname}({args})")
                            try:
                                result = fn(**args)
                            except Exception as e:
                                result = json.dumps({"error": str(e)})
                            tools_used.append(fname)
                        else:
                            result = json.dumps({"error": f"Unknown function: {fname}"})
                        outputs.append(ToolOutput(tool_call_id=tc.id, output=str(result)))
                if outputs:
                    client.runs.submit_tool_outputs(thread_id=thread_id, run_id=run.id, tool_outputs=outputs)

            elif run.status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED, RunStatus.EXPIRED):
                break
            time.sleep(0.5)

        if run.status == RunStatus.FAILED:
            return jsonify({"error": f"Agent run failed: {run.last_error}"}), 500
        if run.status != RunStatus.COMPLETED:
            return jsonify({"error": f"Run ended with status: {run.status}"}), 500

        last = client.messages.get_last_message_text_by_role(thread_id=thread_id, role=MessageRole.AGENT)
        return jsonify({
            "response": last.text.value if last else "(no response)",
            "tools_used": tools_used,
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/reset", methods=["POST"])
def reset():
    data = request.get_json() or {}
    sid = data.get("session_id", "default")
    _threads.pop(sid, None)
    return jsonify({"status": "ok"})


# ═══════════════════════════════════════════════════════════════════
# 2. TICKET MANAGEMENT
# ═══════════════════════════════════════════════════════════════════

@app.route("/api/tickets", methods=["GET"])
def api_search_tickets():
    q = request.args.get("query", "")
    status = request.args.get("status", "")
    priority = request.args.get("priority", "")
    return jsonify(_j(search_tickets(query=q, status=status, priority=priority)))


@app.route("/api/tickets", methods=["POST"])
def api_create_ticket():
    d = request.get_json()
    return jsonify(_j(create_ticket(
        title=d.get("title", ""),
        description=d.get("description", ""),
        priority=d.get("priority", "medium"),
        category=d.get("category", "General"),
        reporter_email=d.get("reporter_email", "user@company.com"),
    )))


@app.route("/api/tickets/<ticket_id>", methods=["PUT"])
def api_update_ticket(ticket_id):
    d = request.get_json()
    return jsonify(_j(update_ticket(
        ticket_id=ticket_id,
        status=d.get("status", ""),
        assigned_to=d.get("assigned_to", ""),
        priority=d.get("priority", ""),
        add_note=d.get("add_note", ""),
        resolution=d.get("resolution", ""),
    )))


@app.route("/api/tickets/<ticket_id>/escalate", methods=["POST"])
def api_escalate_ticket(ticket_id):
    d = request.get_json()
    return jsonify(_j(escalate_ticket(
        ticket_id=ticket_id,
        escalation_reason=d.get("escalation_reason", ""),
        escalate_to=d.get("escalate_to", "Level 2 Support"),
    )))


@app.route("/api/tickets/sla", methods=["GET"])
def api_sla_all():
    return jsonify(_j(calculate_sla_metrics()))


@app.route("/api/tickets/<ticket_id>/sla", methods=["GET"])
def api_sla_ticket(ticket_id):
    return jsonify(_j(calculate_sla_metrics(ticket_id=ticket_id)))


# ═══════════════════════════════════════════════════════════════════
# 3. KNOWLEDGE BASE
# ═══════════════════════════════════════════════════════════════════

@app.route("/api/kb", methods=["GET"])
def api_search_kb():
    q = request.args.get("q", "")
    if not q:
        return jsonify({"error": "Query parameter 'q' required"}), 400
    return jsonify(_j(search_knowledge_base(query=q)))


@app.route("/api/kb/categories", methods=["GET"])
def api_kb_categories():
    return jsonify(_j(list_kb_categories()))


# ═══════════════════════════════════════════════════════════════════
# 4. SYSTEM MONITORING
# ═══════════════════════════════════════════════════════════════════

@app.route("/api/systems", methods=["GET"])
def api_all_systems():
    return jsonify(_j(get_system_status()))


@app.route("/api/systems/<system_name>", methods=["GET"])
def api_system(system_name):
    return jsonify(_j(get_system_status(system_name=system_name)))


@app.route("/api/systems/<system_name>/performance", methods=["GET"])
def api_system_perf(system_name):
    return jsonify(_j(get_system_performance(system_name=system_name)))


@app.route("/api/incidents", methods=["GET"])
def api_incidents():
    return jsonify(_j(get_active_incidents()))


# ═══════════════════════════════════════════════════════════════════
# 5. EMPLOYEE SERVICES
# ═══════════════════════════════════════════════════════════════════

@app.route("/api/employees", methods=["GET"])
def api_search_employees():
    q = request.args.get("q", "")
    if not q:
        return jsonify({"error": "Query parameter 'q' required"}), 400
    return jsonify(_j(lookup_employee(query=q)))


@app.route("/api/employees/<employee_id>", methods=["GET"])
def api_employee(employee_id):
    return jsonify(_j(lookup_employee(query=employee_id)))


@app.route("/api/employees/<employee_id>/leave", methods=["GET"])
def api_leave(employee_id):
    return jsonify(_j(get_leave_balance(employee_id=employee_id)))


@app.route("/api/departments", methods=["GET"])
def api_departments():
    return jsonify(_j(get_department_directory()))


@app.route("/api/departments/<dept_name>", methods=["GET"])
def api_department(dept_name):
    return jsonify(_j(get_department_directory(department=dept_name)))


@app.route("/api/onboarding", methods=["GET"])
def api_onboarding():
    return jsonify(_j(get_onboarding_checklist()))


# ═══════════════════════════════════════════════════════════════════
# 6. SECURITY OPERATIONS
# ═══════════════════════════════════════════════════════════════════

@app.route("/api/security/alerts", methods=["GET"])
def api_sec_alerts():
    sev = request.args.get("severity", "")
    return jsonify(_j(get_security_alerts(severity=sev)))


@app.route("/api/security/compliance", methods=["GET"])
def api_compliance():
    return jsonify(_j(get_compliance_report()))


@app.route("/api/security/compliance/<policy_name>", methods=["GET"])
def api_compliance_policy(policy_name):
    return jsonify(_j(get_compliance_report(policy_name=policy_name)))


@app.route("/api/security/access-requests", methods=["GET"])
def api_access_requests():
    return jsonify(_j(list_pending_access_requests()))


@app.route("/api/security/access-policy/<access_type>", methods=["GET"])
def api_access_policy(access_type):
    return jsonify(_j(check_access_request_policy(access_type=access_type)))


# ═══════════════════════════════════════════════════════════════════
# META
# ═══════════════════════════════════════════════════════════════════

@app.route("/api/tools", methods=["GET"])
def api_tools():
    modules = {
        "ticket_management": {"description": "Create, search, update, escalate tickets + SLA", "functions": sorted(f.__name__ for f in TICKET_FUNCS)},
        "knowledge_base": {"description": "Search troubleshooting articles", "functions": sorted(f.__name__ for f in KB_FUNCS)},
        "system_monitoring": {"description": "Infrastructure health, performance, incidents", "functions": sorted(f.__name__ for f in MONITORING_FUNCS)},
        "employee_services": {"description": "HR lookup, leave, directory, onboarding", "functions": sorted(f.__name__ for f in EMPLOYEE_FUNCS)},
        "security_operations": {"description": "Alerts, access requests, compliance", "functions": sorted(f.__name__ for f in SECURITY_FUNCS)},
    }
    return jsonify({"total_tools": sum(len(m["functions"]) for m in modules.values()), "modules": modules})


@app.route("/api/time", methods=["GET"])
def api_time():
    return jsonify({"utc": get_current_time()})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "challenge5-backend",
        "tools": "5 MCP modules (19 functions)",
        "cosmos_db": "connected",
    })


# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("BACKEND_PORT", "8000"))
    print(f"[BACKEND] IT Help Desk API starting on http://localhost:{port}")
    print(f"[BACKEND] 5 MCP Modules | 19 Tools | Cosmos DB | Foundry Agent")
    app.run(host="0.0.0.0", port=port, debug=False)
