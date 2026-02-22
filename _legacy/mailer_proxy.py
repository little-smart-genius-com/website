#!/usr/bin/env python3
"""
MAILER_PROXY.PY — Local development proxy for MailerLite
=========================================================
Run this while testing forms locally. It acts as a mini HTTP server
that receives form data from the browser and forwards it to MailerLite API.

Usage:
    python mailer_proxy.py          # Starts on http://localhost:5555
    python mailer_proxy.py --port 8888

Endpoints:
    POST /subscribe   → Add subscriber to MailerLite newsletter group
    POST /contact     → Add contact message as subscriber with tag
    GET  /health      → Health check

Then open index.html or contact.html with Live Server / browser.
"""

import os
import json
import argparse
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

load_dotenv()

API_KEY   = os.getenv("MAILERLITE_API_KEY", "")
GROUP_ID  = os.getenv("MAILERLITE_GROUP_ID", "")
ML_BASE   = "https://connect.mailerlite.com/api"
PORT      = 5555

# ─── MailerLite API helpers ────────────────────────────────
def ml_request(method: str, path: str, body: dict = None):
    url = f"{ML_BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return e.code, json.loads(body) if body else {}


def add_subscriber(email: str, name: str = "", fields: dict = None):
    """Add or update a subscriber and assign to group."""
    payload = {
        "email": email,
        "groups": [GROUP_ID],
    }
    if name:
        payload["fields"] = {"name": name}
    if fields:
        payload.setdefault("fields", {}).update(fields)

    return ml_request("POST", "/subscribers", payload)


# ─── HTTP Handler ───────────────────────────────────────────
class ProxyHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"  [proxy] {self.address_string()} — {format % args}")

    def send_json(self, status: int, body: dict):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        # CORS — allow local file:// and any localhost
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self.send_json(200, {"status": "ok", "group_id": GROUP_ID, "api_key_set": bool(API_KEY)})
        else:
            self.send_json(404, {"error": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8")

        # Parse JSON or form-encoded
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            qs = parse_qs(raw)
            data = {k: v[0] for k, v in qs.items()}

        print(f"  [proxy] {path} => {data}")

        if path == "/subscribe":
            email = data.get("email", "").strip()
            if not email:
                self.send_json(400, {"error": "Email is required"})
                return
            status, resp = add_subscriber(email)
            if status in (200, 201):
                self.send_json(200, {"success": True, "message": "Subscribed! Check your inbox."})
            elif status == 422:
                self.send_json(200, {"success": True, "message": "You're already subscribed!"})
            else:
                self.send_json(500, {"error": f"MailerLite error {status}", "details": resp})

        elif path == "/contact":
            email   = data.get("email", "").strip()
            name    = data.get("name", "").strip()
            subject = data.get("subject", "").strip()
            message = data.get("message", "").strip()

            if not email or not message:
                self.send_json(400, {"error": "Email and message are required"})
                return

            # Store contact as subscriber with custom fields + tag
            status, resp = add_subscriber(
                email=email,
                name=name,
                fields={"last_message": f"[{subject}] {message[:500]}"},
            )
            if status in (200, 201, 422):
                self.send_json(200, {"success": True, "message": "Message sent! We'll reply within 24h."})
            else:
                self.send_json(500, {"error": f"MailerLite error {status}", "details": resp})

        else:
            self.send_json(404, {"error": "Unknown endpoint"})


# ─── Entry point ───────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="MailerLite local proxy")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: MAILERLITE_API_KEY not set in .env")
        return
    if not GROUP_ID:
        print("ERROR: MAILERLITE_GROUP_ID not set in .env")
        return

    server = HTTPServer(("localhost", args.port), ProxyHandler)
    print(f"\n  MailerLite Proxy running on http://localhost:{args.port}")
    print(f"  Group ID : {GROUP_ID}")
    print(f"  API Key  : {API_KEY[:20]}...")
    print(f"\n  Endpoints:")
    print(f"    POST  http://localhost:{args.port}/subscribe")
    print(f"    POST  http://localhost:{args.port}/contact")
    print(f"    GET   http://localhost:{args.port}/health")
    print(f"\n  Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Proxy stopped.")

if __name__ == "__main__":
    main()
