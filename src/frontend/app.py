"""
IT Help Desk - Web Frontend
Serves the chat UI and proxies API calls to the backend server (port 8000).

The backend handles:
  - Foundry Agent chat + function-call loop
  - All 5 MCP tool REST endpoints (Cosmos DB)

The frontend handles:
  - Serving the HTML/CSS/JS chat UI
  - Proxying /api/* requests to the backend
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response
from dotenv import load_dotenv
import requests as http_requests

# Load .env
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

app = Flask(__name__)

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy_api(path):
    """Proxy all /api/* requests to the backend server."""
    backend = f"{BACKEND_URL}/api/{path}"
    try:
        if request.method == "GET":
            resp = http_requests.get(backend, params=request.args, timeout=120)
        elif request.method == "POST":
            resp = http_requests.post(backend, json=request.get_json(silent=True), timeout=120)
        elif request.method == "PUT":
            resp = http_requests.put(backend, json=request.get_json(silent=True), timeout=120)
        elif request.method == "DELETE":
            resp = http_requests.delete(backend, timeout=120)
        else:
            return jsonify({"error": "Method not allowed"}), 405

        return Response(resp.content, status=resp.status_code, content_type=resp.headers.get("Content-Type", "application/json"))
    except http_requests.exceptions.ConnectionError:
        return jsonify({"error": "Backend server unavailable. Ensure backend is running on port 8000."}), 502
    except http_requests.exceptions.Timeout:
        return jsonify({"error": "Backend request timed out."}), 504


@app.route("/health")
def health():
    """Health check — also checks backend connectivity."""
    try:
        r = http_requests.get(f"{BACKEND_URL}/health", timeout=5)
        backend_status = r.json()
    except Exception:
        backend_status = {"status": "unreachable"}
    return jsonify({
        "status": "healthy",
        "service": "challenge5-frontend",
        "backend": backend_status,
    })


if __name__ == "__main__":
    port = int(os.environ.get("FRONTEND_PORT", "5000"))
    print(f"[FRONTEND] IT Help Desk UI on http://localhost:{port}")
    print(f"[FRONTEND] Backend proxy -> {BACKEND_URL}")
    app.run(host="0.0.0.0", port=port, debug=False)
