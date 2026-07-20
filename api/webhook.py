# api/webhook.py — Vercel Serverless Function
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "bot": "BetVortex"}).encode())

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            import asyncio
            from telegram import Update
            import os
            
            TOKEN = ***"BOT_TOKEN")
            SUPABASE_URL = ***"SUPABASE_URL")
            SUPABASE_KEY = os.getenv("SUPABASE_KEY")
            
            from telegram.ext import Application, CommandHandler, CallbackQueryHandler
            
            app = Application.builder().token(TOKEN).build()
            
            from bot import (
                start, balance, deposit, process_withdraw, 
                referral, history, admin_panel, broadcast, 
                callback_handler
            )
            from agent_system import (
                agent_register, agent_dashboard, agent_team,
                agent_withdraw, agent_stats, agent_share,
                buy_package, submit_tx, admin_agents,
                admin_approve_agent, admin_reject_agent,
                admin_approve_withdraw
            )
            from game_control import (
                admin_game_panel, create_promo, claim_promo,
                set_limits_menu, self_exclude
            )
            
            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("balance", balance))
            app.add_handler(CommandHandler("deposit", deposit))
            app.add_handler(CommandHandler("withdraw", process_withdraw))
            app.add_handler(CommandHandler("referral", referral))
            app.add_handler(CommandHandler("history", history))
            app.add_handler(CommandHandler("admin", admin_panel))
            app.add_handler(CommandHandler("broadcast", broadcast))
            app.add_handler(CommandHandler("agent", agent_register))
            app.add_handler(CommandHandler("buy_package", buy_package))
            app.add_handler(CommandHandler("submit_tx", submit_tx))
            app.add_handler(CommandHandler("agent_dashboard", agent_dashboard))
            app.add_handler(CommandHandler("agent_team", agent_team))
            app.add_handler(CommandHandler("agent_withdraw", agent_withdraw))
            app.add_handler(CommandHandler("agent_stats", agent_stats))
            app.add_handler(CommandHandler("agent_share", agent_share))
            app.add_handler(CommandHandler("admin_agents", admin_agents))
            app.add_handler(CommandHandler("approve_agent", admin_approve_agent))
            app.add_handler(CommandHandler("reject_agent", admin_reject_agent))
            app.add_handler(CommandHandler("approve_withdraw", admin_approve_withdraw))
            app.add_handler(CommandHandler("games", admin_game_panel))
            app.add_handler(CommandHandler("promo", create_promo))
            app.add_handler(CommandHandler("claim", claim_promo))
            app.add_handler(CommandHandler("limits", set_limits_menu))
            app.add_handler(CommandHandler("exclude", self_exclude))
            app.add_handler(CallbackQueryHandler(callback_handler))
            
            update = Update.de_json(data, app.bot)
            asyncio.run(app.process_update(update))
        except Exception as e:
            print(f"Error: {e}")
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())
