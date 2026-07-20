from http.server import BaseHTTPRequestHandler
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "bot": "BetVortex Casino",
            "message": "Bot is running!"
        }).encode())

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            
            import asyncio
            from telegram import Update
            
            # Import bot modules
            from bot import get_application
            
            app = get_application()
            update = Update.de_json(data, app.bot)
            asyncio.run(app.process_update(update))
        except Exception as e:
            print(f"Error: {e}")
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())
