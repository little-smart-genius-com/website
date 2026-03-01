import os
import sys
import json
import asyncio
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
DASHBOARD_FILE = "audit_dashboard.html"

from audit_dashboard import main as generate_dashboard_func, analyze_article

class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PROJECT_ROOT, **kwargs)

    def do_GET(self):
        # Always serve index if trying to hit the root
        if self.path == '/':
            self.path = '/' + DASHBOARD_FILE
        return super().do_GET()

    def do_POST(self):
        if self.path == '/api/repair':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                slug = data.get('slug')
                action = data.get('action')
                
                if slug and action:
                    import subprocess
                    result = subprocess.run([sys.executable, "scripts/repair_article.py", "--slug", slug, "--action", action], capture_output=True, text=True)
                    logs = result.stdout + "\\n" + result.stderr
                    if result.returncode == 0:
                        self._send_json({"success": True, "message": f"Repaired {slug}", "logs": logs})
                    else:
                        self._send_json({"success": False, "message": f"Failed {slug}", "logs": logs})
                else:
                    self._send_json({"success": False, "message": "Missing slug or action", "logs": ""})

            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"[SERVER GET ERROR] {e}")
                self._send_json({"success": False, "message": str(e), "logs": error_trace})

        elif self.path == '/api/repair_bulk':
            print("\n[SERVER] Bulk Repair Requested!")
            try:
                bulk_logs = ""
                html_files = [f for f in os.listdir(ARTICLES_DIR) if f.endswith('.html')]
                for filename in html_files:
                    filepath = os.path.join(ARTICLES_DIR, filename)
                    stats = analyze_article(filepath)
                    errors = stats.get('Errors', [])
                    slug = stats['Slug']
                    
                    for error in errors:
                        if error not in ["Missing TOC", "Missing <main> tag"]:
                            print(f" -> Fixing {error} on {slug}...")
                            import subprocess
                            res = subprocess.run([sys.executable, "scripts/repair_article.py", "--slug", slug, "--action", error], capture_output=True, text=True)
                            bulk_logs += f"\\n--- {slug} | {error} ---\\n" + res.stdout + "\\n" + res.stderr

                print("[SERVER] Regenerating Dashboard...")
                res_dash = subprocess.run([sys.executable, "scripts/audit_dashboard.py"], capture_output=True, text=True)
                bulk_logs += "\\n--- Dashboard Regeneration ---\\n" + res_dash.stdout + "\\n" + res_dash.stderr
                self._send_json({"success": True, "message": "Bulk repair finished", "logs": bulk_logs})
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"[SERVER BULK ERROR] {e}")
                self._send_json({"success": False, "message": str(e), "logs": bulk_logs + "\\n" + error_trace})
                
        elif self.path == '/api/scan':
            print("\n[SERVER] Scan All Articles Requested!")
            try:
                import subprocess
                res = subprocess.run([sys.executable, "scripts/audit_dashboard.py"], capture_output=True, text=True)
                logs = res.stdout + "\\n" + res.stderr
                if res.returncode == 0:
                    self._send_json({"success": True, "message": "Scan completed", "logs": logs})
                else:
                    self._send_json({"success": False, "message": "Scan crashed", "logs": logs})
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"[SERVER SCAN ERROR] {e}")
                self._send_json({"success": False, "message": str(e), "logs": error_trace})
                
        else:
            self.send_response(404)
            self.end_headers()

    def _send_json(self, response_data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

    # Suppress verbose HTTP log output
    def log_message(self, format, *args):
        pass

def run(port=8081):
    print("="*60)
    print("Generating fresh dashboard before starting server...")
    generate_dashboard_func()
    print("="*60)
    
    with socketserver.TCPServer(("", port), DashboardHandler) as httpd:
        print(f"🚀 Dashboard Server is running at: http://localhost:{port}")
        print("Press Ctrl+C to stop the server.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == '__main__':
    run()
