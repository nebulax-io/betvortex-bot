from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "running",
            "bot": "BetVortex Casino",
            "message": "Bot is running! Set webhook to use this URL."
        }).encode())

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        data = json.loads(body)
        
        try:
            import asyncio
            from bot import get_application
            
            app = get_application()
            from telegram import Update
            update = Update.de_json(data, app.bot)
            asyncio.run(app.process_update(update))
        except Exception as e:
            print(f"Error: {e}")
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())
