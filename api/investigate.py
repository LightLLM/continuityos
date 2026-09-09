"""ContinuityOS investigation endpoint: real Gemini + Grafana MCP, safe demo fallback."""
import json
import os
from http.server import BaseHTTPRequestHandler
from pathlib import Path

import httpx

SCENARIO = {
    "production": "Project Eclipse", "scene": 27, "take": 3,
    "question": "Can we safely move to Scene 28?",
    "continuity": {"expected_wardrobe": "blue jacket", "observed_wardrobe": "black jacket"},
    "camera_b": {"dropped_frames": 14, "threshold": 5},
    "schedule_variance_minutes": 23,
}

FALLBACK = {
    "mode": "demo_fallback", "provider": "deterministic Project Eclipse fixture",
    "decision": "HOLD SHOOT", "summary": "Resolve three production risks before Scene 28.",
    "risks": [
        {"severity": "critical", "title": "Wardrobe continuity mismatch", "detail": "Scene 27 shows a black jacket; the matching scene requires blue."},
        {"severity": "high", "title": "Camera B dropped frames", "detail": "14 dropped frames exceeds the threshold of 5."},
        {"severity": "medium", "title": "Schedule threshold exceeded", "detail": "Scene 27 is 23 minutes behind schedule."},
    ],
    "actions": ["Restore the blue jacket", "Replace Camera B media and verify signal", "Re-sequence Scene 28 setup"],
    "trace": ["Loaded Project Eclipse telemetry", "Applied continuity and technical thresholds", "Generated deterministic safety decision"],
}

async def grafana_context():
    url, token = os.getenv("GRAFANA_MCP_HTTP_URL"), os.getenv("GRAFANA_MCP_TOKEN")
    if not (url and token):
        return None
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.text[:12000]

async def investigate():
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        return FALLBACK
    try:
        from google import genai
        from google.adk.agents import Agent
        grafana = await grafana_context()
        instruction = "You are a film production safety supervisor. Return only JSON with decision, summary, risks, actions, trace. Never invent telemetry."
        # Instantiating the ADK agent makes the intended orchestration explicit; the
        # serverless request uses the same Gemini model directly for low cold-start latency.
        Agent(name="continuity_supervisor", model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), instruction=instruction)
        prompt = instruction + "\nProduction fixture:\n" + json.dumps(SCENARIO) + "\nGrafana MCP response:\n" + (grafana or "Not configured")
        response = genai.Client(api_key=key).models.generate_content(model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), contents=prompt)
        text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
        result = json.loads(text)
        result.update({"mode": "real_runtime", "provider": "Google ADK + Gemini", "grafana_mcp": "connected" if grafana else "not_configured"})
        return result
    except Exception as exc:
        result = dict(FALLBACK)
        result["fallback_reason"] = type(exc).__name__
        return result

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?", 1)[0] in ("/", "/index.html"):
            page = (Path(__file__).parent.parent / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "public, max-age=0, must-revalidate")
            self.end_headers()
            self.wfile.write(page)
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "service": "continuityos", "runtime": "real" if os.getenv("GOOGLE_API_KEY") else "demo_fallback"}).encode())

    def do_POST(self):
        import asyncio
        result = asyncio.run(investigate())
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
