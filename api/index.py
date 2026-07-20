"""
BetVortex — Vercel Webhook Entry Point
Handles Telegram updates via webhook (not polling)
"""

import os
import json
from http.server import BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Import bot modules
from bot import (
    start, balance, deposit, process_withdraw, referral, history,
    admin_panel, broadcast, callback_handler, main_menu_keyboard,
    get_user
)
from agent_system import (
    agent_register, agent_dashboard, agent_team, agent_withdraw,
    agent_stats, agent_share, buy_package, process_buy, process_payment,
    submit_tx, admin_agents, admin_approve_agent, admin_reject_agent,
    admin_approve_withdraw
)
from extra_games import (
    mines_menu, mines_click, mines_cashout, play_plinko, play_wheel,
    keno_menu, keno_select, keno_draw, hilo_start, hilo_guess, hilo_cashout,
    play_baccarat, baccarat_result, lottery_menu, lottery_buy,
    rps_menu, rps_result, play_limbo, limbo_result,
    tower_start, tower_click, tower_cashout,
    play_double, double_result, play_adder, adder_add, adder_stop
)
from game_control import (
    admin_game_panel, admin_game_detail, toggle_game,
    create_promo, claim_promo, set_limits_menu, self_exclude
)

# Global application instance
application = None

def get_application():
    global application
    if application is None:
        BOT_TOKEN = ***"BOT_TOKEN")
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Register all handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("balance", balance))
        application.add_handler(CommandHandler("deposit", deposit))
        application.add_handler(CommandHandler("withdraw", process_withdraw))
        application.add_handler(CommandHandler("referral", referral))
        application.add_handler(CommandHandler("history", history))
        application.add_handler(CommandHandler("admin", admin_panel))
        application.add_handler(CommandHandler("broadcast", broadcast))
        application.add_handler(CommandHandler("agent", agent_register))
        application.add_handler(CommandHandler("buy_package", buy_package))
        application.add_handler(CommandHandler("submit_tx", submit_tx))
        application.add_handler(CommandHandler("agent_dashboard", agent_dashboard))
        application.add_handler(CommandHandler("agent_team", agent_team))
        application.add_handler(CommandHandler("agent_withdraw", agent_withdraw))
        application.add_handler(CommandHandler("agent_stats", agent_stats))
        application.add_handler(CommandHandler("agent_share", agent_share))
        application.add_handler(CommandHandler("admin_agents", admin_agents))
        application.add_handler(CommandHandler("approve_agent", admin_approve_agent))
        application.add_handler(CommandHandler("reject_agent", admin_reject_agent))
        application.add_handler(CommandHandler("approve_withdraw", admin_approve_withdraw))
        application.add_handler(CommandHandler("games", admin_game_panel))
        application.add_handler(CommandHandler("promo", create_promo))
        application.add_handler(CommandHandler("claim", claim_promo))
        application.add_handler(CommandHandler("limits", set_limits_menu))
        application.add_handler(CommandHandler("exclude", self_exclude))
        application.add_handler(CallbackQueryHandler(callback_handler))
    
    return application


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        data = json.loads(body)
        
        app = get_application()
        update = Update.de_json(data, app.bot)
        
        import asyncio
        asyncio.run(app.process_update(update))
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "running",
            "bot": "BetVortex Casino",
            "games": 18
        }).encode())
