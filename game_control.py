"""
BetVortex — Admin Game Control Module
Admin can control all game settings, limits, house edge, enable/disable games
"""

import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from supabase import create_client, Client

supabase: Client = create_client(os.getenv("SUPABASE_URL"), ***"SUPABASE_KEY"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ============================================
# DEFAULT GAME SETTINGS
# ============================================

DEFAULT_SETTINGS = {
    "slots":    {"enabled": True, "min_bet": 0.10, "max_bet": 100,   "house_edge": 0.05, "rtp": 0.95},
    "dice":     {"enabled": True, "min_bet": 0.10, "max_bet": 500,   "house_edge": 0.03, "rtp": 0.97},
    "crash":    {"enabled": True, "min_bet": 0.10, "max_bet": 200,   "house_edge": 0.05, "rtp": 0.95},
    "blackjack":{"enabled": True, "min_bet": 0.50, "max_bet": 200,   "house_edge": 0.02, "rtp": 0.98},
    "roulette": {"enabled": True, "min_bet": 0.10, "max_bet": 500,   "house_edge": 0.027,"rtp": 0.973},
    "coinflip": {"enabled": True, "min_bet": 0.10, "max_bet": 100,   "house_edge": 0.03, "rtp": 0.97},
    "mines":    {"enabled": True, "min_bet": 0.10, "max_bet": 100,   "house_edge": 0.03, "rtp": 0.97},
    "plinko":   {"enabled": True, "min_bet": 0.10, "max_bet": 200,   "house_edge": 0.03, "rtp": 0.97},
    "wheel":    {"enabled": True, "min_bet": 0.10, "max_bet": 200,   "house_edge": 0.05, "rtp": 0.95},
    "keno":     {"enabled": True, "min_bet": 0.10, "max_bet": 100,   "house_edge": 0.05, "rtp": 0.95},
    "hilo":     {"enabled": True, "min_bet": 0.10, "max_bet": 200,   "house_edge": 0.03, "rtp": 0.97},
    "baccarat": {"enabled": True, "min_bet": 0.50, "max_bet": 500,   "house_edge": 0.012,"rtp": 0.988},
    "lottery":  {"enabled": True, "min_bet": 1.00, "max_bet": 50,    "house_edge": 0.10, "rtp": 0.90},
    "rps":      {"enabled": True, "min_bet": 0.10, "max_bet": 100,   "house_edge": 0.03, "rtp": 0.97},
    "limbo":    {"enabled": True, "min_bet": 0.10, "max_bet": 200,   "house_edge": 0.03, "rtp": 0.97},
    "tower":    {"enabled": True, "min_bet": 0.10, "max_bet": 100,   "house_edge": 0.03, "rtp": 0.97},
    "double":   {"enabled": True, "min_bet": 0.10, "max_bet": 500,   "house_edge": 0.02, "rtp": 0.98},
    "adder":    {"enabled": True, "min_bet": 0.10, "max_bet": 100,   "house_edge": 0.03, "rtp": 0.97},
}

# ============================================
# DATABASE TABLE
# ============================================

"""
CREATE TABLE game_settings (
    game TEXT PRIMARY KEY,
    enabled BOOLEAN DEFAULT TRUE,
    min_bet DECIMAL(15,2) DEFAULT 0.10,
    max_bet DECIMAL(15,2) DEFAULT 100,
    house_edge DECIMAL(5,4) DEFAULT 0.05,
    rtp DECIMAL(5,4) DEFAULT 0.95,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by BIGINT
);

CREATE TABLE game_promos (
    id BIGSERIAL PRIMARY KEY,
    game TEXT,
    promo_type TEXT,
    multiplier_boost DECIMAL(5,2),
    free_spins INT,
    cashback_percent DECIMAL(5,2),
    min_bet DECIMAL(15,2),
    max_uses INT,
    used_count INT DEFAULT 0,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_limits (
    user_id BIGINT PRIMARY KEY,
    daily_deposit_limit DECIMAL(15,2),
    daily_loss_limit DECIMAL(15,2),
    daily_bet_limit DECIMAL(15,2),
    session_time_limit INT,
    self_excluded BOOLEAN DEFAULT FALSE,
    exclude_until TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
"""

# ============================================
# GAME CONTROL FUNCTIONS
# ============================================

def get_game_settings(game: str = None):
    """Get settings for one or all games"""
    if game:
        result = supabase.table("game_settings").select("*").eq("game", game).execute()
        if result.data:
            return result.data[0]
        return DEFAULT_SETTINGS.get(game, DEFAULT_SETTINGS["slots"])
    else:
        result = supabase.table("game_settings").select("*").execute()
        settings = {}
        for row in (result.data or []):
            settings[row["game"]] = row
        # Fill defaults for missing
        for game_id, default in DEFAULT_SETTINGS.items():
            if game_id not in settings:
                settings[game_id] = default
        return settings

def update_game_setting(game: str, **kwargs):
    """Update a game setting"""
    kwargs["updated_at"] = datetime.utcnow().isoformat()
    kwargs["updated_by"] = ADMIN_ID
    
    existing = supabase.table("game_settings").select("*").eq("game", game).execute()
    
    if existing.data:
        supabase.table("game_settings").update(kwargs).eq("game", game).execute()
    else:
        kwargs["game"] = game
        supabase.table("game_settings").insert(kwargs).execute()

def is_game_enabled(game: str) -> bool:
    """Check if a game is enabled"""
    settings = get_game_settings(game)
    return settings.get("enabled", True)

def get_bet_limits(game: str) -> tuple:
    """Get min/max bet for a game"""
    settings = get_game_settings(game)
    return (settings.get("min_bet", 0.10), settings.get("max_bet", 100))

def get_house_edge(game: str) -> float:
    """Get house edge for a game"""
    settings = get_game_settings(game)
    return settings.get("house_edge", 0.05)

# ============================================
# USER LIMITS
# ============================================

def get_user_limits(user_id: int):
    """Get user's responsible gambling limits"""
    result = supabase.table("user_limits").select("*").eq("user_id", user_id).execute()
    if result.data:
        return result.data[0]
    return None

def set_user_limits(user_id: int, **kwargs):
    """Set user limits"""
    kwargs["updated_at"] = datetime.utcnow().isoformat()
    existing = get_user_limits(user_id)
    
    if existing:
        supabase.table("user_limits").update(kwargs).eq("user_id", user_id).execute()
    else:
        kwargs["user_id"] = user_id
        supabase.table("user_limits").insert(kwargs).execute()

def check_user_can_bet(user_id: int, amount: float, game: str) -> tuple:
    """Check if user is allowed to bet"""
    limits = get_user_limits(user_id)
    
    if not limits:
        return (True, "OK")
    
    if limits.get("self_excluded"):
        if limits.get("exclude_until"):
            until = limits["exclude_until"]
            if datetime.fromisoformat(until) > datetime.utcnow():
                return (False, f"⛔ Self-excluded until {until[:10]}")
        else:
            return (False, "⛔ Self-excluded permanently")
    
    if limits.get("daily_loss_limit"):
        # Check daily losses
        today = datetime.utcnow().strftime("%Y-%m-%d")
        result = supabase.table("bets").select("profit").eq(
            "user_id", user_id
        ).gte("created_at", today).execute()
        
        total_loss = sum(abs(float(b["profit"])) for b in (result.data or []) if float(b["profit"]) < 0)
        
        if total_loss + amount > limits["daily_loss_limit"]:
            return (False, f"⛔ Daily loss limit reached (${limits['daily_loss_limit']:.2f})")
    
    if limits.get("daily_bet_limit"):
        today = datetime.utcnow().strftime("%Y-%m-%d")
        result = supabase.table("bets").select("amount").eq(
            "user_id", user_id
        ).gte("created_at", today).execute()
        
        total_bet = sum(float(b["amount"]) for b in (result.data or []))
        
        if total_bet + amount > limits["daily_bet_limit"]:
            return (False, f"⛔ Daily bet limit reached (${limits['daily_bet_limit']:.2f})")
    
    return (True, "OK")

# ============================================
# ADMIN COMMANDS
# ============================================

async def admin_game_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Game control panel: /games"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    settings = get_game_settings()
    
    keyboard_rows = []
    game_list = list(settings.items())
    
    for i in range(0, len(game_list), 2):
        row = []
        for j in range(2):
            if i + j < len(game_list):
                game_id, s = game_list[i + j]
                status = "✅" if s.get("enabled", True) else "❌"
                row.append(InlineKeyboardButton(
                    f"{status} {game_id}",
                    callback_data=f"admin_game_{game_id}"
                ))
        keyboard_rows.append(row)
    
    keyboard_rows.append([InlineKeyboardButton("🔙 Back", callback_data="admin_main")])
    
    text = "🎮 **Game Control Panel**\n\nClick a game to configure:\n\n"
    
    for game_id, s in settings.items():
        status = "✅" if s.get("enabled", True) else "❌"
        edge = s.get("house_edge", 0.05) * 100
        text += f"{status} **{game_id}** | Edge: {edge}% | ${s.get('min_bet', 0.10)}-${s.get('max_bet', 100)}\n"
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard_rows),
        parse_mode="Markdown"
    )

async def admin_game_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, game: str):
    """Show game detail for admin"""
    query = update.callback_query
    settings = get_game_settings(game)
    
    enabled = settings.get("enabled", True)
    status = "✅ Enabled" if enabled else "❌ Disabled"
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "❌ Disable" if enabled else "✅ Enable",
                callback_data=f"toggle_{game}"
            ),
        ],
        [
            InlineKeyboardButton("💰 Set Limits", callback_data=f"setlimits_{game}"),
            InlineKeyboardButton("📊 Set Edge", callback_data=f"setedge_{game}"),
        ],
        [
            InlineKeyboardButton("🎁 Create Promo", callback_data=f"promo_{game}"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_games")]
    ])
    
    await query.edit_message_text(
        f"🎮 **{game.upper()} Settings**\n\n"
        f"Status: {status}\n"
        f"Min Bet: ${settings.get('min_bet', 0.10):.2f}\n"
        f"Max Bet: ${settings.get('max_bet', 100):.2f}\n"
        f"House Edge: {settings.get('house_edge', 0.05)*100:.1f}%\n"
        f"RTP: {settings.get('rtp', 0.95)*100:.1f}%\n",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def toggle_game(update: Update, context: ContextTypes.DEFAULT_TYPE, game: str):
    """Toggle game on/off"""
    query = update.callback_query
    settings = get_game_settings(game)
    new_state = not settings.get("enabled", True)
    
    update_game_setting(game, enabled=new_state)
    
    status = "enabled" if new_state else "disabled"
    await query.answer(f"✅ {game} {status}!", show_alert=True)
    
    # Refresh
    await admin_game_detail(update, context, game)

# ============================================
# PROMOS
# ============================================

async def create_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Create promo code: /promo CODE AMOUNT"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        code = context.args[0].upper()
        amount = float(context.args[1])
        max_uses = int(context.args[2]) if len(context.args) > 2 else 100
    except:
        await update.message.reply_text(
            "Usage: `/promo CODE AMOUNT [max_uses]`\n"
            "Example: `/promo WELCOME 5 100`",
            parse_mode="Markdown"
        )
        return
    
    supabase.table("game_promos").insert({
        "promo_type": "code",
        "game": code,
        "multiplier_boost": 0,
        "cashback_percent": 0,
        "free_spins": 0,
        "min_bet": amount,
        "max_uses": max_uses,
        "is_active": True
    }).execute()
    
    await update.message.reply_text(
        f"✅ **Promo Created!**\n\n"
        f"Code: `{code}`\n"
        f"Bonus: ${amount}\n"
        f"Max uses: {max_uses}",
        parse_mode="Markdown"
    )

async def claim_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User: Claim promo: /claim CODE"""
    if not context.args:
        await update.message.reply_text("Usage: `/claim CODE`", parse_mode="Markdown")
        return
    
    code = context.args[0].upper()
    tid = update.effective_user.id
    
    result = supabase.table("game_promos").select("*").eq("game", code).eq("is_active", True).execute()
    
    if not result.data:
        await update.message.reply_text("❌ Invalid or expired promo code!")
        return
    
    promo = result.data[0]
    
    if promo["used_count"] >= promo["max_uses"]:
        await update.message.reply_text("❌ Promo code fully used!")
        return
    
    # Check if already claimed
    user = supabase.table("users").select("*").eq("telegram_id", tid).execute()
    if not user.data:
        await update.message.reply_text("❌ Please /start first!")
        return
    
    # Add bonus
    bonus = promo["min_bet"]  # Using min_bet field as bonus amount
    from extra_games import update_balance
    update_balance(tid, bonus)
    
    # Update used count
    supabase.table("game_promos").update({
        "used_count": promo["used_count"] + 1
    }).eq("id", promo["id"]).execute()
    
    await update.message.reply_text(
        f"🎁 **Promo Claimed!**\n\n"
        f"Code: `{code}`\n"
        f"Bonus: +${bonus:.2f}\n\n"
        f"💰 Balance: ${user.data[0]['balance'] + bonus:.2f}",
        parse_mode="Markdown"
    )

# ============================================
# RESPONSIBLE GAMBLING COMMANDS
# ============================================

async def set_limits_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User: Set gambling limits: /limits"""
    tid = update.effective_user.id
    limits = get_user_limits(tid)
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 Daily Deposit Limit", callback_data="limit_deposit"),
            InlineKeyboardButton("📉 Daily Loss Limit", callback_data="limit_loss"),
        ],
        [
            InlineKeyboardButton("🎰 Daily Bet Limit", callback_data="limit_bet"),
            InlineKeyboardButton("⏰ Session Time Limit", callback_data="limit_time"),
        ],
        [
            InlineKeyboardButton("🚫 Self-Exclude", callback_data="limit_exclude"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    current = ""
    if limits:
        current = f"""
**Current Limits:**
💰 Daily Deposit: {'$'+str(limits['daily_deposit_limit']) if limits.get('daily_deposit_limit') else 'Not set'}
📉 Daily Loss: {'$'+str(limits['daily_loss_limit']) if limits.get('daily_loss_limit') else 'Not set'}
🎰 Daily Bet: {'$'+str(limits['daily_bet_limit']) if limits.get('daily_bet_limit') else 'Not set'}
⏰ Session: {str(limits['session_time_limit'])+'min' if limits.get('session_time_limit') else 'Not set'}
🚫 Self-Excluded: {'Yes' if limits.get('self_excluded') else 'No'}
"""
    
    await update.message.reply_text(
        f"⚙️ **Responsible Gambling**\n\n"
        f"Set limits to control your gambling.\n"
        f"{current}\n"
        f"Choose a limit to set:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def self_exclude(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User: Self exclude: /exclude DAYS"""
    tid = update.effective_user.id
    
    days = 7  # Default 7 days
    if context.args:
        try:
            days = int(context.args[0])
        except:
            pass
    
    from datetime import timedelta
    until = (datetime.utcnow() + timedelta(days=days)).isoformat()
    
    set_user_limits(tid, self_excluded=True, exclude_until=until)
    
    await update.message.reply_text(
        f"🚫 **Self-Exclusion Activated**\n\n"
        f"Duration: {days} days\n"
        f"Until: {until[:10]}\n\n"
        f"You won't be able to play until then.\n"
        f"Take care of yourself! 💚",
        parse_mode="Markdown"
    )
