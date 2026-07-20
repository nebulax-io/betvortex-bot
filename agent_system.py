"""
BetVortex — Agent System Module (PAID PACKAGES)
Admin → Master Agent → Sub-Agent → User
Agent pays to buy package → earns commission from players
"""

import random
import string
from decimal import Decimal
from datetime import datetime, timedelta

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import ContextTypes
import os
import logging
from db import supabase

logger = logging.getLogger(__name__)
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ============================================
# AGENT PACKAGES (PAID)
# ============================================

AGENT_PACKAGES = {
    "starter": {
        "name": "🟢 Starter",
        "price": 100,            # $100 দিয়ে কিনতে হবে
        "commission": 0.10,      # 10% commission
        "max_users": 50,
        "max_sub_agents": 0,     # Sub-agent রাখতে পারবে না
        "features": [
            "10% player commission",
            "Up to 50 players",
            "Basic dashboard",
            "Referral link",
        ]
    },
    "pro": {
        "name": "🔵 Pro",
        "price": 500,            # $500 দিয়ে কিনতে হবে
        "commission": 0.15,      # 15% commission
        "max_users": 200,
        "max_sub_agents": 5,     # 5টা sub-agent রাখতে পারবে
        "features": [
            "15% player commission",
            "Up to 200 players",
            "5 sub-agents allowed",
            "Advanced analytics",
            "Priority support",
        ]
    },
    "elite": {
        "name": "🟡 Elite",
        "price": 2000,           # $2000 দিয়ে কিনতে হবে
        "commission": 0.20,      # 20% commission
        "max_users": 999999,
        "max_sub_agents": 50,    # 50টা sub-agent রাখতে পারবে
        "features": [
            "20% player commission",
            "Unlimited players",
            "50 sub-agents allowed",
            "Full analytics dashboard",
            "Dedicated support",
            "Custom referral pages",
            "White-label option",
        ]
    },
    "vip": {
        "name": "🔴 VIP",
        "price": 5000,           # $5000 দিয়ে কিনতে হবে
        "commission": 0.25,      # 25% commission
        "max_users": 999999,
        "max_sub_agents": 999,   # Unlimited sub-agents
        "features": [
            "25% player commission",
            "Unlimited everything",
            "Unlimited sub-agents",
            "Full white-label",
            "Revenue sharing with sub-agents",
            "Dedicated account manager",
            "Custom API access",
            "Monthly bonus pool",
        ]
    }
}

# ============================================
# DATABASE SCHEMA
# ============================================

"""
-- Agents table (PAID)
CREATE TABLE agents (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    agent_code TEXT UNIQUE NOT NULL,
    parent_agent_id BIGINT,
    package TEXT DEFAULT NULL,
    package_price DECIMAL(15,2) DEFAULT 0,
    commission_rate DECIMAL(5,2) DEFAULT 0,
    total_referrals INT DEFAULT 0,
    total_commission DECIMAL(15,2) DEFAULT 0,
    total_wagered_by_refs DECIMAL(15,2) DEFAULT 0,
    total_earned_override DECIMAL(15,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT FALSE,
    is_paid BOOLEAN DEFAULT FALSE,
    payment_tx_hash TEXT,
    payment_method TEXT,
    approved_by BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    activated_at TIMESTAMPTZ
);

-- Agent commission log
CREATE TABLE agent_commissions (
    id BIGSERIAL PRIMARY KEY,
    agent_id BIGINT REFERENCES agents(telegram_id),
    from_user_id BIGINT,
    bet_amount DECIMAL(15,2),
    commission_amount DECIMAL(15,2),
    commission_type TEXT DEFAULT 'direct',
    game TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent withdrawals
CREATE TABLE agent_withdrawals (
    id BIGSERIAL PRIMARY KEY,
    agent_id BIGINT REFERENCES agents(telegram_id),
    amount DECIMAL(15,2),
    status TEXT DEFAULT 'pending',
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent package purchases
CREATE TABLE agent_purchases (
    id BIGSERIAL PRIMARY KEY,
    agent_id BIGINT REFERENCES agents(telegram_id),
    package TEXT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    payment_method TEXT,
    tx_hash TEXT,
    status TEXT DEFAULT 'pending',
    approved_by BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    approved_at TIMESTAMPTZ
);
"""

# ============================================
# CORE FUNCTIONS
# ============================================

def get_agent(telegram_id: int):
    try:
        result = supabase.table("agents").select("*").eq("telegram_id", telegram_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"get_agent({telegram_id}) failed: {e}")
        return None

def get_agent_by_code(agent_code: str):
    try:
        result = supabase.table("agents").select("*").eq("agent_code", agent_code).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"get_agent_by_code({agent_code}) failed: {e}")
        return None

def register_agent(telegram_id: int, username: str, parent_code: str = None):
    """Register agent (not paid yet)"""
    try:
        existing = get_agent(telegram_id)
        if existing:
            return existing
        
        agent_code = "AGT" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        parent_id = None
        if parent_code:
            parent = get_agent_by_code(parent_code)
            if parent:
                parent_id = parent["telegram_id"]
        
        data = {
            "telegram_id": telegram_id,
            "username": username,
            "agent_code": agent_code,
            "parent_agent_id": parent_id,
            "is_active": False,
            "is_paid": False,
        }
        
        supabase.table("agents").insert(data).execute()
        return data
    except Exception as e:
        logger.error(f"register_agent({telegram_id}) failed: {e}")
        return None

def activate_agent(telegram_id: int, package: str, payment_method: str, tx_hash: str = None):
    """Activate agent after payment"""
    try:
        pkg = AGENT_PACKAGES[package]
        
        supabase.table("agents").update({
            "package": package,
            "package_price": pkg["price"],
            "commission_rate": pkg["commission"],
            "is_active": True,
            "is_paid": True,
            "payment_method": payment_method,
            "payment_tx_hash": tx_hash,
            "activated_at": datetime.utcnow().isoformat()
        }).eq("telegram_id", telegram_id).execute()
        
        # Log purchase
        supabase.table("agent_purchases").insert({
            "agent_id": telegram_id,
            "package": package,
            "amount": pkg["price"],
            "payment_method": payment_method,
            "tx_hash": tx_hash,
            "status": "completed"
        }).execute()
    except Exception as e:
        logger.error(f"activate_agent({telegram_id}, {package}) failed: {e}")

def get_agent_referrals(agent_id: int):
    try:
        result = supabase.table("users").select("*").eq("referred_by", agent_id).execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"get_agent_referrals({agent_id}) failed: {e}")
        return []

def get_sub_agents(parent_id: int):
    try:
        result = supabase.table("agents").select("*").eq("parent_agent_id", parent_id).execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"get_sub_agents({parent_id}) failed: {e}")
        return []

def calculate_commission(agent_id: int, bet_amount: float, game: str, house_profit: float):
    """Calculate commission on house profit (not bet amount)"""
    try:
        agent = get_agent(agent_id)
        if not agent or not agent["is_active"]:
            return 0
        
        commission = house_profit * float(agent["commission_rate"])
        
        if commission <= 0:
            return 0
        
        supabase.table("agent_commissions").insert({
            "agent_id": agent_id,
            "bet_amount": bet_amount,
            "commission_amount": commission,
            "commission_type": "direct",
            "game": game
        }).execute()
        
        new_total = float(agent["total_commission"]) + commission
        new_wagered = float(agent["total_wagered_by_refs"]) + bet_amount
        supabase.table("agents").update({
            "total_commission": new_total,
            "total_wagered_by_refs": new_wagered
        }).eq("telegram_id", agent_id).execute()
        
        # Override commission for parent agent
        if agent.get("parent_agent_id"):
            parent = get_agent(agent["parent_agent_id"])
            if parent and parent["is_active"]:
                override_rate = float(parent["commission_rate"]) * 0.2  # 20% of their rate as override
                override = house_profit * override_rate
                
                if override > 0:
                    supabase.table("agent_commissions").insert({
                        "agent_id": parent["telegram_id"],
                        "from_user_id": agent_id,
                        "bet_amount": bet_amount,
                        "commission_amount": override,
                        "commission_type": "override",
                        "game": game
                    }).execute()
                    
                    supabase.table("agents").update({
                        "total_earned_override": float(parent["total_earned_override"]) + override,
                        "total_commission": float(parent["total_commission"]) + override
                    }).eq("telegram_id", parent["telegram_id"]).execute()
        
        return commission
    except Exception as e:
        logger.error(f"calculate_commission({agent_id}, {bet_amount}, {game}) failed: {e}")
        return 0

# ============================================
# AGENT COMMANDS
# ============================================

async def agent_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register as agent: /agent or /agent PARENT_CODE"""
    user = update.effective_user
    telegram_id = user.id
    username = user.username or user.first_name
    
    existing = get_agent(telegram_id)
    
    if existing:
        if existing["is_active"]:
            pkg = AGENT_PACKAGES.get(existing["package"], {})
            await update.message.reply_text(
                f"✅ আপনি একজন Active Agent!\n\n"
                f"🆔 Code: `{existing['agent_code']}`\n"
                f"📦 Package: {pkg.get('name', 'N/A')}\n"
                f"💰 Commission: {existing['commission_rate']*100}%\n"
                f"👥 Players: {existing['total_referrals']}\n"
                f"💵 Earned: ${existing['total_commission']:.2f}\n\n"
                f"Commands:\n"
                f"/agent_dashboard · /agent_team · /agent_withdraw",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"⏳ আপনার registration pending!\n\n"
                f"🆔 Code: `{existing['agent_code']}`\n"
                f"❌ Package এখনো কেনা হয়নি\n\n"
                f"Package কিনতে /buy_package ব্যবহার করুন",
                parse_mode="Markdown"
            )
        return
    
    # New registration
    parent_code = context.args[0] if context.args else None
    
    if parent_code:
        parent = get_agent_by_code(parent_code)
        if not parent or not parent["is_active"]:
            await update.message.reply_text("❌ Invalid or inactive agent code!")
            return
    
    agent = register_agent(telegram_id, username, parent_code)
    
    bot_username = (await context.bot.get_me()).username
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 View Packages", callback_data="view_packages")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
    ])
    
    await update.message.reply_text(
        f"🎉 **Agent Registration Complete!**\n\n"
        f"🆔 Your Code: `{agent['agent_code']}`\n"
        f"👤 Username: @{username}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"⚠️ **এখনো Active নন!**\n\n"
        f"Agent হিসেবে কাজ করতে হলে **Package কিনতে হবে।**\n"
        f"নিচের Package গুলো দেখুন:\n\n"
        f"🟢 Starter — $100 (10% commission)\n"
        f"🔵 Pro — $500 (15% commission)\n"
        f"🟡 Elite — $2,000 (20% commission)\n"
        f"🔴 VIP — $5,000 (25% commission)\n\n"
        f"📦 /buy_package দিয়ে কিনুন",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def buy_package(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show packages to buy: /buy_package"""
    agent = get_agent(update.effective_user.id)
    
    if not agent:
        await update.message.reply_text("❌ আগে /agent দিয়ে register করুন!")
        return
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🟢 Starter $100", callback_data="buy_starter"),
            InlineKeyboardButton("🔵 Pro $500", callback_data="buy_pro"),
        ],
        [
            InlineKeyboardButton("🟡 Elite $2,000", callback_data="buy_elite"),
            InlineKeyboardButton("🔴 VIP $5,000", callback_data="buy_vip"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    text = """
📦 **Agent Packages — এজেন্ট প্যাকেজ**

একটি Package কিনুন এবং Agent হিসেবে কাজ শুরু করুন!

━━━━━━━━━━━━━━━━━━━━━

🟢 **Starter — $100**
• 10% player commission
• Up to 50 players
• Basic dashboard
• No sub-agents

🔵 **Pro — $500**
• 15% player commission
• Up to 200 players
• 5 sub-agents allowed
• Advanced analytics

🟡 **Elite — $2,000**
• 20% player commission
• Unlimited players
• 50 sub-agents allowed
• Full dashboard + priority support

🔴 **VIP — $5,000**
• 25% player commission
• Unlimited everything
• Unlimited sub-agents
• White-label + dedicated support

━━━━━━━━━━━━━━━━━━━━━

💰 **কিভাবে আয় হবে:**
Player যত বেট করবে → House edge থেকে আপনি commission পাবেন

Example: Starter agent, 20 players, প্রতিদিন $30 bet
→ $30 × 20 players × 5% edge × 10% commission = **$3/day = $90/month**

━━━━━━━━━━━━━━━━━━━━━

Payment methods:
• 💰 Crypto (BTC/ETH/USDT)
• 💳 Manual (Admin approval)
    """
    
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def process_buy(update: Update, context: ContextTypes.DEFAULT_TYPE, package: str):
    """Process package purchase"""
    query = update.callback_query
    agent = get_agent(update.effective_user.id)
    
    if not agent:
        await query.answer("❌ Register first with /agent", show_alert=True)
        return
    
    if agent["is_active"]:
        await query.answer("✅ আপনি ইতিমধ্যে active agent!", show_alert=True)
        return
    
    pkg = AGENT_PACKAGES[package]
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("₿ Pay with Crypto", callback_data=f"pay_crypto_{package}"),
            InlineKeyboardButton("💳 Manual Payment", callback_data=f"pay_manual_{package}"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="view_packages")]
    ])
    
    await query.edit_message_text(
        f"📦 **{pkg['name']} Package — ${pkg['price']:,}**\n\n"
        f"✅ Features:\n" + "\n".join(f"  • {f}" for f in pkg["features"]) + f"\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 Payment Method বাছুন:\n\n"
        f"**₿ Crypto:** Auto-confirmation (NOWPayments)\n"
        f"**💳 Manual:** Admin approve করবেন\n"
        f"  → Crypto পাঠান: `YOUR_WALLET_ADDRESS`\n"
        f"  → TX Hash দিন: /submit_tx HASH\n"
        f"  → Admin verify করে activate করবেন",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, package: str, method: str):
    """Process payment for package"""
    query = update.callback_query
    agent = get_agent(update.effective_user.id)
    pkg = AGENT_PACKAGES[package]
    
    if method == "crypto":
        # In production: integrate NOWPayments API
        await query.edit_message_text(
            f"₿ **Crypto Payment — {pkg['name']}**\n\n"
            f"Amount: **${pkg['price']:,}**\n\n"
            f"Send payment to:\n"
            f"`YOUR_CRYPTO_ADDRESS_HERE`\n\n"
            f"Supported: BTC, ETH, USDT (TRC20), LTC\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚡ Payment confirm হলে auto-activate হবে\n"
            f"📧 অথবা TX Hash পাঠান: `/submit_tx YOUR_HASH`\n\n"
            f"⏳ Processing time: 1-3 confirmations",
            parse_mode="Markdown"
        )
    elif method == "manual":
        # Notify admin
        await context.bot.send_message(
            ADMIN_ID,
            f"💳 **New Agent Package Request**\n\n"
            f"User: @{agent.get('username', 'N/A')} ({agent['telegram_id']})\n"
            f"Agent Code: {agent['agent_code']}\n"
            f"Package: {pkg['name']} — ${pkg['price']:,}\n\n"
            f"Payment Method: Manual\n\n"
            f"Commands:\n"
            f"/approve_agent {agent['telegram_id']} {package}\n"
            f"/reject_agent {agent['telegram_id']}",
            parse_mode="Markdown"
        )
        
        await query.edit_message_text(
            f"💳 **Manual Payment — {pkg['name']}**\n\n"
            f"Amount: **${pkg['price']:,}**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📋 **Instructions:**\n\n"
            f"1. Send ${pkg['price']:,} to admin\n"
            f"   Crypto: `YOUR_WALLET_ADDRESS`\n"
            f"   Or contact: @AdminUsername\n\n"
            f"2. After payment, send:\n"
            f"   `/submit_tx TRANSACTION_HASH`\n\n"
            f"3. Admin will verify & activate your account\n\n"
            f"⏳ Usually processed within 1-24 hours\n\n"
            f"✅ Admin has been notified!",
            parse_mode="Markdown"
        )

async def submit_tx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Submit transaction hash: /submit_tx HASH"""
    agent = get_agent(update.effective_user.id)
    
    if not agent:
        await update.message.reply_text("❌ আগে /agent দিয়ে register করুন!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 Usage: `/submit_tx YOUR_TRANSACTION_HASH`\n\n"
            "Example: `/submit_tx abc123def456...`",
            parse_mode="Markdown"
        )
        return
    
    tx_hash = context.args[0]
    
    # Update agent record
    supabase.table("agents").update({
        "payment_tx_hash": tx_hash,
        "payment_method": "crypto"
    }).eq("telegram_id", agent["telegram_id"]).execute()
    
    # Notify admin
    await context.bot.send_message(
        ADMIN_ID,
        f"₿ **Crypto Payment Submitted**\n\n"
        f"User: @{agent.get('username', 'N/A')} ({agent['telegram_id']})\n"
        f"Agent Code: {agent['agent_code']}\n"
        f"TX Hash: `{tx_hash}`\n\n"
        f"Verify and activate:\n"
        f"/approve_agent {agent['telegram_id']} PACKAGE\n\n"
        f"Reject:\n"
        f"/reject_agent {agent['telegram_id']}",
        parse_mode="Markdown"
    )
    
    await update.message.reply_text(
        f"✅ **TX Hash Submitted!**\n\n"
        f"Hash: `{tx_hash}`\n\n"
        f"Admin verify করে activate করবেন।\n"
        f"⏳ Usually 1-24 hours.",
        parse_mode="Markdown"
    )

async def agent_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Agent dashboard: /agent_dashboard"""
    agent = get_agent(update.effective_user.id)
    
    if not agent:
        await update.message.reply_text("❌ আপনি Agent নন! /agent দিয়ে register করুন.")
        return
    
    if not agent["is_active"]:
        await update.message.reply_text(
            f"⏳ আপনার account inactive!\n\n"
            f"Package কিনতে /buy_package ব্যবহার করুন.",
            parse_mode="Markdown"
        )
        return
    
    refs = get_agent_referrals(agent["telegram_id"])
    sub_agents = get_sub_agents(agent["telegram_id"])
    pkg = AGENT_PACKAGES.get(agent["package"], {})
    
    recent = supabase.table("agent_commissions").select("*").eq(
        "agent_id", agent["telegram_id"]
    ).order("created_at", desc=True).limit(5).execute()
    
    text = f"""
📊 **Agent Dashboard**

🆔 Code: `{agent['agent_code']}`
📦 Package: {pkg.get('name', 'N/A')}
💰 Commission: {agent['commission_rate']*100}%

━━━━━━━━━━━━━━━━━━━━━

💵 **Earnings**
Direct Commission: **${agent['total_commission']:.2f}**
Override Commission: **${agent['total_earned_override']:.2f}**
Available to Withdraw: **${agent['total_commission']:.2f}**

👥 **Team**
Players: {len(refs)} / {pkg.get('max_users', 0)}
Sub-Agents: {len(sub_agents)} / {pkg.get('max_sub_agents', 0)}
Total Wagered by Refs: ${agent['total_wagered_by_refs']:.2f}

━━━━━━━━━━━━━━━━━━━━━

📈 **Recent Commissions:**
"""
    
    if recent.data:
        for c in recent.data:
            ctype = "🔗" if c.get("commission_type") == "override" else "💰"
            text += f"  {ctype} ${c['commission_amount']:.2f} from {c['game']} ({c['created_at'][:10]})\n"
    else:
        text += "  No commissions yet — share your link!\n"
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👥 My Team", callback_data="agent_team"),
            InlineKeyboardButton("💸 Withdraw", callback_data="agent_withdraw"),
        ],
        [
            InlineKeyboardButton("📊 Stats", callback_data="agent_stats"),
            InlineKeyboardButton("📤 Share Link", callback_data="agent_share"),
        ],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
    ])
    
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def agent_team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show agent's team"""
    agent = get_agent(update.effective_user.id)
    
    if not agent or not agent["is_active"]:
        await update.message.reply_text("❌ আপনি active Agent নন!")
        return
    
    refs = get_agent_referrals(agent["telegram_id"])
    sub_agents = get_sub_agents(agent["telegram_id"])
    pkg = AGENT_PACKAGES.get(agent["package"], {})
    
    text = f"👥 **Your Team**\n\n"
    
    text += f"**Sub-Agents ({len(sub_agents)}/{pkg.get('max_sub_agents', 0)}):**\n"
    if sub_agents:
        for sa in sub_agents[:10]:
            sa_pkg = AGENT_PACKAGES.get(sa.get("package", "starter"), {})
            status = "✅" if sa["is_active"] else "⏳"
            text += f"  {status} @{sa.get('username', 'N/A')} | {sa['agent_code']} | {sa_pkg.get('name', 'N/A')} | ${sa['total_commission']:.2f}\n"
    else:
        text += "  No sub-agents yet\n"
    
    text += f"\n**Players ({len(refs)}/{pkg.get('max_users', 0)}):**\n"
    if refs:
        for u in refs[:10]:
            text += f"  👤 @{u.get('username', 'N/A')} | Wagered: ${u['total_wagered']:.2f}\n"
        if len(refs) > 10:
            text += f"  ... and {len(refs)-10} more\n"
    else:
        text += "  No players yet — share your link!\n"
    
    bot_username = (await context.bot.get_me()).username
    text += f"\n📤 **Invite Links:**\n"
    text += f"Player: `https://t.me/{bot_username}?start=ref_{agent['agent_code']}`\n"
    if pkg.get('max_sub_agents', 0) > 0:
        text += f"Sub-Agent: `https://t.me/{bot_username}?start=agt_{agent['agent_code']}`\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def agent_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Agent withdrawal"""
    agent = get_agent(update.effective_user.id)
    
    if not agent or not agent["is_active"]:
        await update.message.reply_text("❌ আপনি active Agent নন!")
        return
    
    available = float(agent["total_commission"])
    
    if not context.args:
        await update.message.reply_text(
            f"💸 **Withdraw Commission**\n\n"
            f"Available: **${available:.2f}**\n\n"
            f"Usage: `/agent_withdraw AMOUNT`\n"
            f"Min: $20",
            parse_mode="Markdown"
        )
        return
    
    try:
        amount = float(context.args[0])
    except:
        await update.message.reply_text("❌ Invalid amount!")
        return
    
    if amount < 20:
        await update.message.reply_text("❌ Minimum withdrawal: $20")
        return
    
    if amount > available:
        await update.message.reply_text(f"❌ Insufficient! Available: ${available:.2f}")
        return
    
    supabase.table("agent_withdrawals").insert({
        "agent_id": agent["telegram_id"],
        "amount": amount,
        "status": "pending"
    }).execute()
    
    supabase.table("agents").update({
        "total_commission": available - amount
    }).eq("telegram_id", agent["telegram_id"]).execute()
    
    await context.bot.send_message(
        ADMIN_ID,
        f"💸 **Agent Withdrawal Request**\n\n"
        f"Agent: @{agent.get('username', 'N/A')} ({agent['agent_code']})\n"
        f"Package: {AGENT_PACKAGES.get(agent['package'], {}).get('name', 'N/A')}\n"
        f"Amount: ${amount:.2f}\n\n"
        f"/approve_withdraw {agent['telegram_id']} {amount}",
        parse_mode="Markdown"
    )
    
    await update.message.reply_text(
        f"✅ **Withdrawal Requested!**\n\n"
        f"Amount: ${amount:.2f}\n"
        f"Status: Pending\n\n"
        f"Admin approve করবেন।",
        parse_mode="Markdown"
    )

async def agent_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get shareable links"""
    agent = get_agent(update.effective_user.id)
    
    if not agent or not agent["is_active"]:
        await update.message.reply_text("❌ আপনি active Agent নন!")
        return
    
    bot_username = (await context.bot.get_me()).username
    pkg = AGENT_PACKAGES.get(agent["package"], {})
    
    text = f"""
📤 **Your Share Links**

👤 **Player Link** (players join under you):
`https://t.me/{bot_username}?start=ref_{agent['agent_code']}`

"""
    
    if pkg.get("max_sub_agents", 0) > 0:
        text += f"""🤝 **Sub-Agent Link** (others become your sub-agent):
`https://t.me/{bot_username}?start=agt_{agent['agent_code']}`

"""
    
    text += f"""━━━━━━━━━━━━━━━━━━━━━

💡 **Tips:**
• Player link share করুন → Players আসবে
• প্রতিটা player এর bet থেকে আপনি commission পাবেন
• Sub-agent link দিয়ে team বানান → তাদের players থেকেও আয়
"""
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def agent_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detailed stats"""
    agent = get_agent(update.effective_user.id)
    
    if not agent or not agent["is_active"]:
        await update.message.reply_text("❌ আপনি active Agent নন!")
        return
    
    commissions = supabase.table("agent_commissions").select("*").eq(
        "agent_id", agent["telegram_id"]
    ).execute()
    
    direct = [c for c in (commissions.data or []) if c.get("commission_type") == "direct"]
    override = [c for c in (commissions.data or []) if c.get("commission_type") == "override"]
    
    by_game = {}
    for c in direct:
        game = c["game"]
        by_game[game] = by_game.get(game, 0) + float(c["commission_amount"])
    
    text = f"""
📈 **Detailed Stats**

🆔 Agent: `{agent['agent_code']}`
📦 Package: {AGENT_PACKAGES.get(agent['package'], {}).get('name', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━

💰 **Direct Commission Breakdown:**
"""
    for game, amount in by_game.items():
        text += f"  🎰 {game}: ${amount:.2f}\n"
    
    text += f"""
━━━━━━━━━━━━━━━━━━━━━

🔗 **Override Commission:**
Total from sub-agents: ${agent['total_earned_override']:.2f}

━━━━━━━━━━━━━━━━━━━━━

📊 **Performance:**
Total Bets Processed: {len(direct)}
Direct Commission: ${sum(float(c['commission_amount']) for c in direct):.2f}
Override Commission: ${sum(float(c['commission_amount']) for c in override):.2f}
Total Wagered by Refs: ${agent['total_wagered_by_refs']:.2f}
Avg Commission per Bet: ${sum(float(c['commission_amount']) for c in direct) / max(len(direct), 1):.2f}
"""
    
    await update.message.reply_text(text, parse_mode="Markdown")

# ============================================
# ADMIN COMMANDS
# ============================================

async def admin_approve_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Approve agent: /approve_agent TELEGRAM_ID PACKAGE"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        agent_id = int(context.args[0])
        package = context.args[1].lower()
    except:
        await update.message.reply_text("Usage: /approve_agent TELEGRAM_ID PACKAGE")
        return
    
    if package not in AGENT_PACKAGES:
        await update.message.reply_text("❌ Invalid package!")
        return
    
    activate_agent(agent_id, package, "manual", approved_by=ADMIN_ID)
    pkg = AGENT_PACKAGES[package]
    
    await context.bot.send_message(
        agent_id,
        f"🎉 **Account Activated!**\n\n"
        f"📦 Package: {pkg['name']}\n"
        f"💰 Commission: {pkg['commission']*100}%\n"
        f"👥 Max Players: {pkg['max_users']}\n\n"
        f"আপনি এখন থেকে Agent হিসেবে কাজ করতে পারবেন!\n\n"
        f"Commands:\n"
        f"/agent_dashboard — Stats\n"
        f"/agent_share — Get referral links\n"
        f"/agent_team — View team",
        parse_mode="Markdown"
    )
    
    await update.message.reply_text(f"✅ Agent {agent_id} activated as {pkg['name']}!")

async def admin_reject_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Reject agent: /reject_agent TELEGRAM_ID"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        agent_id = int(context.args[0])
    except:
        await update.message.reply_text("Usage: /reject_agent TELEGRAM_ID")
        return
    
    await context.bot.send_message(
        agent_id,
        "❌ **Payment Rejected**\n\n"
        "আপনার payment verify করা যায়নি।\n"
        "অনুগ্রহ করে আবার চেষ্টা করুন বা support এ যোগাযোগ করুন।\n\n"
        "/buy_package — আবার চেষ্টা করুন",
        parse_mode="Markdown"
    )
    
    await update.message.reply_text(f"❌ Agent {agent_id} rejected.")

async def admin_agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: View all agents: /admin_agents"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    agents = supabase.table("agents").select("*").order("created_at", desc=True).execute()
    
    active = [a for a in agents.data if a["is_active"]]
    pending = [a for a in agents.data if not a["is_active"]]
    
    text = f"👑 **All Agents**\n\n"
    text += f"✅ Active: {len(active)} | ⏳ Pending: {len(pending)}\n\n"
    
    text += "**Active Agents:**\n"
    for a in active[:15]:
        pkg = AGENT_PACKAGES.get(a.get("package", ""), {})
        text += f"  ✅ `{a['agent_code']}` | @{a.get('username', 'N/A')} | {pkg.get('name', 'N/A')} | ${a['total_commission']:.2f}\n"
    
    if pending:
        text += f"\n**Pending (unpaid):**\n"
        for a in pending[:10]:
            text += f"  ⏳ `{a['agent_code']}` | @{a.get('username', 'N/A')} | {a['telegram_id']}\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def admin_approve_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Approve withdrawal: /approve_withdraw AGENT_ID AMOUNT"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        agent_id = int(context.args[0])
        amount = float(context.args[1])
    except:
        await update.message.reply_text("Usage: /approve_withdraw AGENT_ID AMOUNT")
        return
    
    supabase.table("agent_withdrawals").update({
        "status": "completed",
        "processed_at": datetime.utcnow().isoformat()
    }).eq("agent_id", agent_id).eq("amount", amount).eq("status", "pending").execute()
    
    try:
        await context.bot.send_message(
            agent_id,
            f"✅ **Withdrawal Approved!**\n\nAmount: ${amount:.2f}\n\nProcessed successfully!",
            parse_mode="Markdown"
        )
    except:
        pass
    
    await update.message.reply_text(f"✅ Approved ${amount:.2f} for agent {agent_id}")

# ============================================
# CALLBACK HANDLERS (add to main bot.py callback_handler)
# ============================================

"""
Add these to bot.py callback_handler:

elif data == "view_packages":
    await buy_package(update, context)

elif data.startswith("buy_"):
    package = data.replace("buy_", "")
    await process_buy(update, context, package)

elif data.startswith("pay_crypto_"):
    package = data.replace("pay_crypto_", "")
    await process_payment(update, context, package, "crypto")

elif data.startswith("pay_manual_"):
    package = data.replace("pay_manual_", "")
    await process_payment(update, context, package, "manual")

elif data == "agent_team":
    await agent_team(update, context)

elif data == "agent_withdraw":
    await agent_withdraw(update, context)

elif data == "agent_stats":
    await agent_stats(update, context)

elif data == "agent_share":
    await agent_share(update, context)
"""

# ============================================
# COMMISSION TRIGGER (call from game engine)
# ============================================

async def trigger_commission(user_id: int, bet_amount: float, game: str, house_edge_rate: float):
    """
    Call this after every bet.
    house_edge_rate: e.g. 0.05 for 5% house edge
    """
    user = supabase.table("users").select("*").eq("telegram_id", user_id).execute()
    
    if not user.data:
        return
    
    referred_by = user.data[0].get("referred_by")
    if not referred_by:
        return
    
    agent = get_agent(referred_by)
    if not agent or not agent["is_active"]:
        return
    
    house_profit = bet_amount * house_edge_rate
    
    commission = calculate_commission(referred_by, bet_amount, game, house_profit)
    
    return commission
