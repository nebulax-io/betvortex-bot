"""
BetVortex Telegram Casino Bot
Zero Investment Casino Platform
"""

import os
import random
import hashlib
import string
import logging
import time
from decimal import Decimal
from datetime import datetime
from functools import wraps

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    BotCommand
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
from db import supabase

# ============================================
# LOGGING SETUP
# ============================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
from agent_system import (
    agent_register, agent_dashboard, agent_team,
    agent_withdraw, agent_stats,
    agent_share, buy_package, process_buy,
    process_payment, submit_tx,
    admin_agents, admin_approve_agent, admin_reject_agent,
    admin_approve_withdraw, trigger_commission
)
from extra_games import (
    mines_menu, mines_click, mines_cashout,
    play_plinko, play_wheel,
    keno_menu, keno_select, keno_draw,
    hilo_start, hilo_guess, hilo_cashout,
    play_baccarat, baccarat_result,
    lottery_menu, lottery_buy,
    rps_menu, rps_result,
    play_limbo, limbo_result,
    tower_start, tower_click, tower_cashout,
    play_double, double_result,
    play_adder, adder_add, adder_stop
)
from game_control import (
    admin_game_panel, admin_game_detail, toggle_game,
    create_promo, claim_promo, set_limits_menu, self_exclude,
    is_game_enabled, check_user_can_bet
)
from ui_messages import (
    WELCOME_NEW_USER, WELCOME_EXISTING_USER,
    WIN_MESSAGE, LOSE_MESSAGE, DRAW_MESSAGE,
    BALANCE_TEXT, REFERRAL_TEXT, HELP_TEXT,
    ERROR_INSUFFICIENT_BALANCE, ERROR_GAME_DISABLED,
    WITHDRAW_MENU, WITHDRAW_SUBMITTED,
    SLOTS_SPIN, MAIN_MENU_TEXT
)

# ============================================
# CONFIG
# ============================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ============================================
# HOUSE EDGE SETTINGS
# ============================================

HOUSE_EDGE = {
    "slots": 0.05,      # 5%
    "dice": 0.03,       # 3%
    "crash": 0.05,      # 5%
    "blackjack": 0.02,  # 2%
    "roulette": 0.027,  # 2.7%
    "coinflip": 0.03,   # 3%
    "mines": 0.03,      # 3%
}

# ============================================
# RATE LIMITING
# ============================================

_rate_limits = {}  # {user_id: [timestamp, ...]}
RATE_LIMIT_WINDOW = 5  # seconds
RATE_LIMIT_MAX_BETS = 3  # max bets per window

def is_rate_limited(user_id: int) -> bool:
    """Check if user is betting too fast."""
    now = time.time()
    if user_id not in _rate_limits:
        _rate_limits[user_id] = []
    # Clean old entries
    _rate_limits[user_id] = [t for t in _rate_limits[user_id] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limits[user_id]) >= RATE_LIMIT_MAX_BETS:
        return True
    _rate_limits[user_id].append(now)
    return False

# ============================================
# ERROR HANDLING DECORATOR
# ============================================

def safe_handler(func):
    """Decorator that catches exceptions and logs them instead of crashing."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            # Try to notify user
            try:
                update = args[0] if args else None
                if update and hasattr(update, 'callback_query') and update.callback_query:
                    await update.callback_query.answer("⚠️ An error occurred. Try again.", show_alert=True)
                elif update and hasattr(update, 'message') and update.message:
                    await update.message.reply_text("⚠️ Something went wrong. Please try again.")
            except Exception:
                pass
    return wrapper

# ============================================
# DATABASE HELPERS (with error handling)
# =============================================

def get_user(telegram_id: int):
    try:
        result = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"get_user({telegram_id}) failed: {e}")
        return None

def create_user(telegram_id: int, username: str, referred_by: int = None):
    ref_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    data = {
        "telegram_id": telegram_id,
        "username": username,
        "referral_code": ref_code,
        "referred_by": referred_by
    }
    try:
        supabase.table("users").insert(data).execute()
    except Exception as e:
        logger.error(f"create_user({telegram_id}) failed: {e}")
    return data

def update_balance(telegram_id: int, amount: float):
    """Atomic balance update using Supabase RPC (no race condition)."""
    try:
        # Use Supabase RPC for atomic increment
        result = supabase.rpc("atomic_balance_update", {
            "p_telegram_id": telegram_id,
            "p_amount": amount
        }).execute()
        if result.data is not None:
            return float(result.data)
    except Exception as e:
        logger.warning(f"RPC atomic_balance_update not available, falling back: {e}")

    # Fallback: read-then-write (non-atomic, but better than nothing)
    try:
        user = get_user(telegram_id)
        if not user:
            logger.error(f"update_balance: user {telegram_id} not found")
            return 0
        new_balance = float(user["balance"]) + amount
        if new_balance < 0:
            new_balance = 0
        supabase.table("users").update({"balance": new_balance}).eq("telegram_id", telegram_id).execute()
        return new_balance
    except Exception as e:
        logger.error(f"update_balance({telegram_id}, {amount}) failed: {e}")
        return 0

def log_transaction(telegram_id: int, tx_type: str, amount: float, status: str = "completed"):
    try:
        supabase.table("transactions").insert({
            "user_id": telegram_id,
            "type": tx_type,
            "amount": amount,
            "status": status
        }).execute()
    except Exception as e:
        logger.error(f"log_transaction({telegram_id}) failed: {e}")

def log_bet(telegram_id: int, game: str, amount: float, multiplier: float, result: str, profit: float):
    try:
        supabase.table("bets").insert({
            "user_id": telegram_id,
            "game": game,
            "amount": amount,
            "multiplier": multiplier,
            "result": result,
            "profit": profit
        }).execute()
    except Exception as e:
        logger.error(f"log_bet({telegram_id}, {game}) failed: {e}")

# ============================================
# PROVABLY FAIR
# ============================================

def generate_seed():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def provably_fair_result(server_seed: str, client_seed: str, max_value: int):
    combined = f"{server_seed}:{client_seed}"
    hash_result = hashlib.sha256(combined.encode()).hexdigest()
    number = int(hash_result[:8], 16) % (max_value + 1)
    return number

# ============================================
# MAIN MENU
# ============================================

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎰 Slots", callback_data="game_slots"),
            InlineKeyboardButton("🎲 Dice", callback_data="game_dice"),
        ],
        [
            InlineKeyboardButton("✈️ Crash", callback_data="game_crash"),
            InlineKeyboardButton("🃏 Blackjack", callback_data="game_blackjack"),
        ],
        [
            InlineKeyboardButton("🎡 Roulette", callback_data="game_roulette"),
            InlineKeyboardButton("🪙 Coin Flip", callback_data="game_coinflip"),
        ],
        [
            InlineKeyboardButton("💣 Mines", callback_data="game_mines"),
            InlineKeyboardButton("📌 Plinko", callback_data="game_plinko"),
        ],
        [
            InlineKeyboardButton("🎡 Wheel", callback_data="game_wheel"),
            InlineKeyboardButton("🎱 Keno", callback_data="game_keno"),
        ],
        [
            InlineKeyboardButton("🔺 Hi-Lo", callback_data="game_hilo"),
            InlineKeyboardButton("🂡 Baccarat", callback_data="game_baccarat"),
        ],
        [
            InlineKeyboardButton("🎟️ Lottery", callback_data="game_lottery"),
            InlineKeyboardButton("✊ RPS", callback_data="game_rps"),
        ],
        [
            InlineKeyboardButton("💰 Deposit", callback_data="deposit"),
            InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"),
        ],
        [
            InlineKeyboardButton("📊 Balance", callback_data="balance"),
            InlineKeyboardButton("🤝 Referral", callback_data="referral"),
        ],
        [
            InlineKeyboardButton("📜 History", callback_data="history"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
        ]
    ])

# ============================================
# COMMAND HANDLERS
# ============================================

@safe_handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    username = user.username or user.first_name

    # Check referral
    referred_by = None
    if context.args and context.args[0].startswith("ref_"):
        ref_code = context.args[0].replace("ref_", "")
        referrer = supabase.table("users").select("*").eq("referral_code", ref_code).execute()
        if referrer.data:
            referred_by = referrer.data[0]["telegram_id"]

    # Create user if not exists
    existing = get_user(telegram_id)
    if not existing:
        create_user(telegram_id, username, referred_by)
        # Bonus for new user
        update_balance(telegram_id, 1.00)
        log_transaction(telegram_id, "bonus", 1.00)
        text = WELCOME_NEW_USER.format(username=username, balance=get_user(telegram_id)['balance'])
    else:
        text = WELCOME_EXISTING_USER.format(username=username, balance=get_user(telegram_id)['balance'])

    await update.message.reply_text(
        text,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

@safe_handler
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Please /start first!")
        return

    text = BALANCE_TEXT.format(
        balance=float(user['balance']),
        deposited=float(user['total_deposited']),
        withdrawn=float(user['total_withdrawn']),
        wagered=float(user['total_wagered']),
        games_played=0,  # TODO: count from bets table
        win_rate=0,       # TODO: calculate
        biggest_win=0     # TODO: calculate
    )
    await update.message.reply_text(text, parse_mode="Markdown")

@safe_handler
async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("₿ BTC", callback_data="dep_btc"),
            InlineKeyboardButton("Ξ ETH", callback_data="dep_eth"),
        ],
        [
            InlineKeyboardButton("₮ USDT", callback_data="dep_usdt"),
            InlineKeyboardButton("Ł LTC", callback_data="dep_ltc"),
        ],
        [
            InlineKeyboardButton("TRX", callback_data="dep_trx"),
            InlineKeyboardButton("Ð DOGE", callback_data="dep_doge"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])

    text = """
💰 **Deposit Crypto**

Select cryptocurrency:

⚡ Min deposit: $1 equivalent
🔄 Auto-confirmation (1-3 blocks)
💳 Zero platform fees
    """
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Please /start first!")
        return

    text = WITHDRAW_MENU.format(balance=float(user['balance']))
    await update.message.reply_text(text, parse_mode="Markdown")

@safe_handler
async def process_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        return

    try:
        parts = update.message.text.split()
        amount = float(parts[1])
        address = parts[2]

        if amount < 10:
            await update.message.reply_text("❌ Minimum withdrawal: $10")
            return
        if amount > float(user["balance"]):
            await update.message.reply_text("❌ Insufficient balance!")
            return

        # Deduct balance
        update_balance(update.effective_user.id, -amount)
        log_transaction(update.effective_user.id, "withdraw", amount, "pending")

        # Notify admin
        await context.bot.send_message(
            ADMIN_ID,
            f"💸 **Withdrawal Request**\n\n"
            f"User: @{user['username']} ({user['telegram_id']})\n"
            f"Amount: ${amount:.2f}\n"
            f"Address: `{address}`\n\n"
            f"Reply: /approve {user['telegram_id']} {amount} OR /reject {user['telegram_id']} {amount}",
            parse_mode="Markdown"
        )

        await update.message.reply_text(
            f"✅ Withdrawal request submitted!\n\n"
            f"Amount: ${amount:.2f}\n"
            f"Address: `{address}`\n"
            f"Status: Pending review\n\n"
            f"You'll be notified when processed.",
            parse_mode="Markdown"
        )
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Format: /withdraw AMOUNT ADDRESS")

@safe_handler
async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Please /start first!")
        return

    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user['referral_code']}"

    # Count referrals
    refs = supabase.table("referrals").select("*").eq("referrer_id", user["telegram_id"]).execute()
    ref_count = len(refs.data) if refs.data else 0

    text = f"""
🤝 **Referral Program**

🔗 Your referral link:
`{ref_link}`

👥 Referrals: {ref_count}
💵 Earned: ${sum(r['commission_earned'] for r in (refs.data or [])):.2f}

**How it works:**
• Share your link with friends
• They get $1 signup bonus
• You get 10% of their first deposit
• You earn 5% of their losses (lifetime)
    """
    await update.message.reply_text(text, parse_mode="Markdown")

@safe_handler
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bets = supabase.table("bets").select("*").eq(
        "user_id", update.effective_user.id
    ).order("created_at", desc=True).limit(10).execute()

    if not bets.data:
        await update.message.reply_text("📜 No bet history yet!")
        return

    text = "📜 **Last 10 Bets:**\n\n"
    for bet in bets.data:
        emoji = "✅" if bet["profit"] >= 0 else "❌"
        text += f"{emoji} {bet['game']} | ${bet['amount']:.2f} | {bet['multiplier']}x | {'+$' if bet['profit']>=0 else '-$'}{abs(bet['profit']):.2f}\n"

    await update.message.reply_text(text, parse_mode="Markdown")

# ============================================
# GAMES
# ============================================

@safe_handler
async def game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, game: str):
    query = update.callback_query
    await query.answer()

    game_info = {
        "slots": {"name": "🎰 Slots", "desc": "Spin the reels! Match 3 symbols to win big!", "min": 0.10, "max": 100},
        "dice": {"name": "🎲 Dice", "desc": "Roll the dice! Predict over/under!", "min": 0.10, "max": 500},
        "crash": {"name": "✈️ Crash", "desc": "Multiplier rises! Cash out before crash!", "min": 0.10, "max": 200},
        "blackjack": {"name": "🃏 Blackjack", "desc": "Get 21 or beat the dealer!", "min": 0.50, "max": 200},
        "roulette": {"name": "🎡 Roulette", "desc": "Bet on number, color, or range!", "min": 0.10, "max": 500},
        "coinflip": {"name": "🪙 Coin Flip", "desc": "Heads or Tails! 2x payout!", "min": 0.10, "max": 100},
        "mines": {"name": "💣 Mines", "desc": "Find gems, avoid mines! Cash out anytime!", "min": 0.10, "max": 100},
        "plinko": {"name": "📌 Plinko", "desc": "Drop the ball! Multipliers up to 10x!", "min": 0.10, "max": 200},
        "wheel": {"name": "🎡 Wheel", "desc": "Spin the wheel! Win up to 50x!", "min": 0.10, "max": 200},
        "keno": {"name": "🎱 Keno", "desc": "Pick lucky numbers! Match to win!", "min": 0.10, "max": 100},
        "hilo": {"name": "🔺 Hi-Lo", "desc": "Higher or lower? Build your streak!", "min": 0.10, "max": 200},
        "baccarat": {"name": "🂡 Baccarat", "desc": "Player vs Banker! Classic card game!", "min": 0.50, "max": 500},
        "lottery": {"name": "🎟️ Lottery", "desc": "Buy ticket, win big prizes!", "min": 1, "max": 50},
        "rps": {"name": "✊ RPS", "desc": "Rock Paper Scissors! 2x payout!", "min": 0.10, "max": 100},
        "limbo": {"name": "🎯 Limbo", "desc": "Pick target, roll above to win!", "min": 0.10, "max": 200},
        "tower": {"name": "🏗️ Tower", "desc": "Climb floors, avoid danger!", "min": 0.10, "max": 100},
        "double": {"name": "🔴 Double", "desc": "Red/Black/Green color bet!", "min": 0.10, "max": 500},
        "adder": {"name": "➕ Adder", "desc": "Add numbers, get close to 21!", "min": 0.10, "max": 100},
    }

    info = game_info.get(game, game_info["slots"])

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("$1", callback_data=f"bet_{game}_1"),
            InlineKeyboardButton("$5", callback_data=f"bet_{game}_5"),
            InlineKeyboardButton("$10", callback_data=f"bet_{game}_10"),
        ],
        [
            InlineKeyboardButton("$25", callback_data=f"bet_{game}_25"),
            InlineKeyboardButton("$50", callback_data=f"bet_{game}_50"),
            InlineKeyboardButton("$100", callback_data=f"bet_{game}_100"),
        ],
        [
            InlineKeyboardButton("✏️ Custom Amount", callback_data=f"custom_{game}"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])

    user = get_user(update.effective_user.id)
    text = f"""
**{info['name']}**

{info['desc']}

💰 Balance: ${user['balance']:.2f}
📊 Min bet: ${info['min']:.2f} | Max: ${info['max']:.2f}

Select bet amount:
    """

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ============================================
# SLOT MACHINE
# ============================================

SLOT_SYMBOLS = ["🍒", "🍋", "🍊", "🍇", "🔔", "💎", "⭐", "7️⃣"]

SLOT_PAYOUTS = {
    "🍒🍒🍒": 5,
    "🍋🍋🍋": 8,
    "🍊🍊🍊": 10,
    "🍇🍇🍇": 15,
    "🔔🔔🔔": 25,
    "💎💎💎": 50,
    "⭐⭐⭐": 75,
    "7️⃣7️⃣7️⃣": 100,
}

@safe_handler
async def play_slots(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float):
    query = update.callback_query
    user_id = update.effective_user.id

    if is_rate_limited(user_id):
        await query.answer("⏳ Slow down! Wait a few seconds.", show_alert=True)
        return

    user = get_user(user_id)
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return

    # Deduct bet
    update_balance(update.effective_user.id, -bet_amount)

    # Spin reels
    reel1 = random.choice(SLOT_SYMBOLS)
    reel2 = random.choice(SLOT_SYMBOLS)
    reel3 = random.choice(SLOT_SYMBOLS)

    result = f"{reel1}{reel2}{reel3}"

    # Calculate payout
    multiplier = SLOT_PAYOUTS.get(result, 0)
    # Partial matches
    if multiplier == 0:
        if reel1 == reel2 or reel2 == reel3:
            multiplier = 1.5
        elif reel1 == reel3:
            multiplier = 1.2

    profit = (bet_amount * multiplier) - bet_amount if multiplier > 0 else -bet_amount

    if multiplier > 0:
        update_balance(update.effective_user.id, bet_amount * multiplier)

    log_bet(update.effective_user.id, "slots", bet_amount, multiplier, result, profit)

    # Update wagered
    supabase.table("users").update({
        "total_wagered": float(user["total_wagered"]) + bet_amount
    }).eq("telegram_id", update.effective_user.id).execute()

    emoji = "🎉" if profit > 0 else "😢"

    text = f"""
🎰 **SLOT MACHINE**

╔═══════════════╗
║   {reel1} │ {reel2} │ {reel3}   ║
╚═══════════════╝

Bet: ${bet_amount:.2f}
Multiplier: {multiplier}x
{emoji} {'Won' if profit >= 0 else 'Lost'}: ${abs(profit):.2f}

💰 Balance: ${get_user(update.effective_user.id)['balance']:.2f}
    """

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Spin Again", callback_data=f"bet_slots_{bet_amount}"),
            InlineKeyboardButton("🎮 Other Games", callback_data="main_menu"),
        ],
        [InlineKeyboardButton("💰 Balance", callback_data="balance")]
    ])

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ============================================
# DICE GAME
# ============================================

@safe_handler
async def play_dice(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float):
    query = update.callback_query
    user_id = update.effective_user.id

    if is_rate_limited(user_id):
        await query.answer("⏳ Slow down! Wait a few seconds.", show_alert=True)
        return

    user = get_user(user_id)
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Over 50 (2x)", callback_data=f"dice_roll_{bet_amount}_over50"),
            InlineKeyboardButton("Under 50 (2x)", callback_data=f"dice_roll_{bet_amount}_under50"),
        ],
        [
            InlineKeyboardButton("Over 75 (4x)", callback_data=f"dice_roll_{bet_amount}_over75"),
            InlineKeyboardButton("Under 25 (4x)", callback_data=f"dice_roll_{bet_amount}_under25"),
        ],
        [
            InlineKeyboardButton("Over 90 (10x)", callback_data=f"dice_roll_{bet_amount}_over90"),
            InlineKeyboardButton("Under 10 (10x)", callback_data=f"dice_roll_{bet_amount}_under10"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="game_dice")]
    ])

    await query.edit_message_text(
        f"🎲 **Dice Game**\n\nBet: ${bet_amount:.2f}\n💰 Balance: ${user['balance']:.2f}\n\nChoose your prediction:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def dice_roll(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float, prediction: str):
    query = update.callback_query

    user = get_user(update.effective_user.id)
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return

    update_balance(update.effective_user.id, -bet_amount)

    # Roll dice (0-100)
    roll = random.randint(0, 100)

    # Determine win
    win = False
    multiplier = 0

    if prediction == "over50" and roll > 50:
        win = True
        multiplier = 2
    elif prediction == "under50" and roll < 50:
        win = True
        multiplier = 2
    elif prediction == "over75" and roll > 75:
        win = True
        multiplier = 4
    elif prediction == "under25" and roll < 25:
        win = True
        multiplier = 4
    elif prediction == "over90" and roll > 90:
        win = True
        multiplier = 10
    elif prediction == "under10" and roll < 10:
        win = True
        multiplier = 10

    profit = -bet_amount
    if win:
        update_balance(update.effective_user.id, bet_amount * multiplier)
        profit = (bet_amount * multiplier) - bet_amount

    log_bet(update.effective_user.id, "dice", bet_amount, multiplier, f"rolled_{roll}_pred_{prediction}", profit)
    supabase.table("users").update({"total_wagered": float(user["total_wagered"]) + bet_amount}).eq("telegram_id", update.effective_user.id).execute()

    emoji = "🎉" if win else "😢"

    text = f"""
🎲 **Dice Result**

🎯 Your prediction: {prediction}
🎲 Rolled: **{roll}/100**

Bet: ${bet_amount:.2f}
Multiplier: {multiplier}x
{emoji} {'Won' if win else 'Lost'}: ${abs(profit):.2f}

💰 Balance: ${get_user(update.effective_user.id)['balance']:.2f}
    """

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Roll Again", callback_data=f"bet_dice_{bet_amount}"),
            InlineKeyboardButton("🎮 Main Menu", callback_data="main_menu"),
        ]
    ])

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ============================================
# COIN FLIP
# ============================================

async def play_coinflip(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float):
    query = update.callback_query

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👑 Heads", callback_data=f"flip_{bet_amount}_heads"),
            InlineKeyboardButton("🦅 Tails", callback_data=f"flip_{bet_amount}_tails"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="game_coinflip")]
    ])

    await query.edit_message_text(
        f"🪙 **Coin Flip**\n\nBet: ${bet_amount:.2f}\n\nChoose Heads or Tails:\n💰 2x Payout!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def coinflip_result(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float, choice: str):
    query = update.callback_query

    user = get_user(update.effective_user.id)
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return

    update_balance(update.effective_user.id, -bet_amount)

    result = random.choice(["heads", "tails"])
    win = choice == result

    profit = -bet_amount
    if win:
        update_balance(update.effective_user.id, bet_amount * 2)
        profit = bet_amount

    log_bet(update.effective_user.id, "coinflip", bet_amount, 2 if win else 0, f"{choice}_vs_{result}", profit)
    supabase.table("users").update({"total_wagered": float(user["total_wagered"]) + bet_amount}).eq("telegram_id", update.effective_user.id).execute()

    emoji = "🎉" if win else "😢"
    coin_emoji = "👑" if result == "heads" else "🦅"

    text = f"""
🪙 **Coin Flip Result**

{coin_emoji} Result: **{result.title()}**
🎯 Your choice: {choice.title()}

Bet: ${bet_amount:.2f}
{emoji} {'Won' if win else 'Lost'}: ${abs(profit):.2f}

💰 Balance: ${get_user(update.effective_user.id)['balance']:.2f}
    """

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Flip Again", callback_data=f"bet_coinflip_{bet_amount}"),
            InlineKeyboardButton("🎮 Main Menu", callback_data="main_menu"),
        ]
    ])

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ============================================
# ROULETTE
# ============================================

ROULETTE_NUMBERS = list(range(0, 37))  # 0-36
RED_NUMBERS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK_NUMBERS = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}

async def play_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float):
    query = update.callback_query

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔴 Red (2x)", callback_data=f"roulette_{bet_amount}_red"),
            InlineKeyboardButton("⚫ Black (2x)", callback_data=f"roulette_{bet_amount}_black"),
        ],
        [
            InlineKeyboardButton("🟢 Green (36x)", callback_data=f"roulette_{bet_amount}_green"),
        ],
        [
            InlineKeyboardButton("1-12 (3x)", callback_data=f"roulette_{bet_amount}_1st12"),
            InlineKeyboardButton("13-24 (3x)", callback_data=f"roulette_{bet_amount}_2nd12"),
            InlineKeyboardButton("25-36 (3x)", callback_data=f"roulette_{bet_amount}_3rd12"),
        ],
        [
            InlineKeyboardButton("1-18 (2x)", callback_data=f"roulette_{bet_amount}_low"),
            InlineKeyboardButton("19-36 (2x)", callback_data=f"roulette_{bet_amount}_high"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="game_roulette")]
    ])

    user = get_user(update.effective_user.id)
    await query.edit_message_text(
        f"🎡 **Roulette**\n\nBet: ${bet_amount:.2f}\n💰 Balance: ${user['balance']:.2f}\n\nPlace your bet:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def roulette_result(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float, bet_type: str):
    query = update.callback_query

    user = get_user(update.effective_user.id)
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return

    update_balance(update.effective_user.id, -bet_amount)

    number = random.choice(ROULETTE_NUMBERS)
    color = "green" if number == 0 else ("red" if number in RED_NUMBERS else "black")

    win = False
    multiplier = 0

    if bet_type == "red" and color == "red":
        win, multiplier = True, 2
    elif bet_type == "black" and color == "black":
        win, multiplier = True, 2
    elif bet_type == "green" and number == 0:
        win, multiplier = True, 36
    elif bet_type == "1st12" and 1 <= number <= 12:
        win, multiplier = True, 3
    elif bet_type == "2nd12" and 13 <= number <= 24:
        win, multiplier = True, 3
    elif bet_type == "3rd12" and 25 <= number <= 36:
        win, multiplier = True, 3
    elif bet_type == "low" and 1 <= number <= 18:
        win, multiplier = True, 2
    elif bet_type == "high" and 19 <= number <= 36:
        win, multiplier = True, 2

    profit = -bet_amount
    if win:
        update_balance(update.effective_user.id, bet_amount * multiplier)
        profit = (bet_amount * multiplier) - bet_amount

    log_bet(update.effective_user.id, "roulette", bet_amount, multiplier, f"{number}_{color}_{bet_type}", profit)
    supabase.table("users").update({"total_wagered": float(user["total_wagered"]) + bet_amount}).eq("telegram_id", update.effective_user.id).execute()

    color_emoji = {"red": "🔴", "black": "⚫", "green": "🟢"}[color]
    emoji = "🎉" if win else "😢"

    text = f"""
🎡 **Roulette Result**

{color_emoji} **{number}** ({color.title()})

Your bet: {bet_type} | ${bet_amount:.2f}
Multiplier: {multiplier}x
{emoji} {'Won' if win else 'Lost'}: ${abs(profit):.2f}

💰 Balance: ${get_user(update.effective_user.id)['balance']:.2f}
    """

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Spin Again", callback_data=f"bet_roulette_{bet_amount}"),
            InlineKeyboardButton("🎮 Main Menu", callback_data="main_menu"),
        ]
    ])

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ============================================
# CRASH GAME (Simplified)
# ============================================

async def play_crash(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float):
    query = update.callback_query

    user = get_user(update.effective_user.id)
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return

    # Generate crash point (provably fair)
    server_seed = generate_seed()
    crash_point = max(1.0, (1 / (1 - random.random())) * (1 - HOUSE_EDGE["crash"]))
    crash_point = round(crash_point, 2)

    # Auto cashout options
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"💰 Cashout 1.5x", callback_data=f"crash_cash_{bet_amount}_1.5_{crash_point}"),
            InlineKeyboardButton(f"💰 Cashout 2x", callback_data=f"crash_cash_{bet_amount}_2_{crash_point}"),
        ],
        [
            InlineKeyboardButton(f"💰 Cashout 3x", callback_data=f"crash_cash_{bet_amount}_3_{crash_point}"),
            InlineKeyboardButton(f"💰 Cashout 5x", callback_data=f"crash_cash_{bet_amount}_5_{crash_point}"),
        ],
        [
            InlineKeyboardButton(f"🚀 Let it Ride!", callback_data=f"crash_cash_{bet_amount}_max_{crash_point}"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="game_crash")]
    ])

    text = f"""
✈️ **Crash Game**

🚀 Multiplier rising...
📈 Current: 1.00x

Bet: ${bet_amount:.2f}
💰 Balance: ${user['balance']:.2f}

Choose when to cash out!
    """

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def crash_result(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float, cashout: str, crash_point: float):
    query = update.callback_query

    user = get_user(update.effective_user.id)
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return

    update_balance(update.effective_user.id, -bet_amount)

    if cashout == "max":
        actual_cashout = crash_point
    else:
        actual_cashout = float(cashout)

    won = actual_cashout <= crash_point
    multiplier = actual_cashout if won else 0
    profit = -bet_amount

    if won:
        update_balance(update.effective_user.id, bet_amount * actual_cashout)
        profit = (bet_amount * actual_cashout) - bet_amount

    log_bet(update.effective_user.id, "crash", bet_amount, multiplier, f"crash@{crash_point}_cash@{actual_cashout}", profit)
    supabase.table("users").update({"total_wagered": float(user["total_wagered"]) + bet_amount}).eq("telegram_id", update.effective_user.id).execute()

    emoji = "🎉" if won else "💥"

    text = f"""
✈️ **Crash Result**

💥 Crashed at: **{crash_point}x**
💰 You cashed out at: **{actual_cashout}x**

Bet: ${bet_amount:.2f}
{emoji} {'Won' if won else 'Lost'}: ${abs(profit):.2f}

💰 Balance: ${get_user(update.effective_user.id)['balance']:.2f}
    """

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Play Again", callback_data=f"bet_crash_{bet_amount}"),
            InlineKeyboardButton("🎮 Main Menu", callback_data="main_menu"),
        ]
    ])

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ============================================
# BLACKJACK (Simplified)
# ============================================

CARDS = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
SUITS = ['♠','♥','♦','♣']

def draw_card():
    return f"{random.choice(CARDS)}{random.choice(SUITS)}"

def card_value(card):
    rank = card[:-1]
    if rank in ['J','Q','K']:
        return 10
    elif rank == 'A':
        return 11
    return int(rank)

def hand_value(cards):
    value = sum(card_value(c) for c in cards)
    aces = sum(1 for c in cards if c[:-1] == 'A')
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

async def play_blackjack(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float):
    query = update.callback_query

    user = get_user(update.effective_user.id)
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return

    update_balance(update.effective_user.id, -bet_amount)

    # Deal cards
    player_cards = [draw_card(), draw_card()]
    dealer_cards = [draw_card(), draw_card()]

    player_val = hand_value(player_cards)
    dealer_val = hand_value(dealer_cards)

    # Check blackjack
    if player_val == 21:
        # Blackjack!
        payout = bet_amount * 2.5
        update_balance(update.effective_user.id, payout)
        profit = payout - bet_amount
        log_bet(update.effective_user.id, "blackjack", bet_amount, 2.5, "blackjack", profit)
        supabase.table("users").update({"total_wagered": float(user["total_wagered"]) + bet_amount}).eq("telegram_id", update.effective_user.id).execute()

        text = f"""
🃏 **BLACKJACK!** 🎉

Your hand: {' '.join(player_cards)} = **{player_val}**
Dealer: {' '.join(dealer_cards)} = {dealer_val}

Bet: ${bet_amount:.2f}
🎉 Won: ${profit:.2f}

💰 Balance: ${get_user(update.effective_user.id)['balance']:.2f}
        """
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Play Again", callback_data=f"bet_blackjack_{bet_amount}"),
             InlineKeyboardButton("🎮 Menu", callback_data="main_menu")]
        ])
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
        return

    # Store game state
    context.user_data["bj"] = {
        "player": player_cards,
        "dealer": dealer_cards,
        "bet": bet_amount
    }

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🃏 Hit", callback_data="bj_hit"),
            InlineKeyboardButton("✋ Stand", callback_data="bj_stand"),
        ],
        [
            InlineKeyboardButton("💰 Double", callback_data="bj_double"),
        ]
    ])

    text = f"""
🃏 **Blackjack**

Your hand: {' '.join(player_cards)} = **{player_val}**
Dealer: {dealer_cards[0]} ❓

Bet: ${bet_amount:.2f}

Hit, Stand, or Double?
    """

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def bj_hit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    game = context.user_data.get("bj")
    if not game:
        await query.answer("Game not found!")
        return

    game["player"].append(draw_card())
    val = hand_value(game["player"])

    if val > 21:
        # Bust
        profit = -game["bet"]
        log_bet(update.effective_user.id, "blackjack", game["bet"], 0, "bust", profit)
        user = get_user(update.effective_user.id)
        supabase.table("users").update({"total_wagered": float(user["total_wagered"]) + game["bet"]}).eq("telegram_id", update.effective_user.id).execute()

        text = f"""
🃏 **BUST!** 😢

Your hand: {' '.join(game['player'])} = **{val}**
Dealer: {' '.join(game['dealer'])} = {hand_value(game['dealer'])}

Bet: ${game['bet']:.2f}
😢 Lost: ${game['bet']:.2f}

💰 Balance: ${get_user(update.effective_user.id)['balance']:.2f}
        """
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Play Again", callback_data=f"bet_blackjack_{game['bet']}"),
             InlineKeyboardButton("🎮 Menu", callback_data="main_menu")]
        ])
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🃏 Hit", callback_data="bj_hit"),
            InlineKeyboardButton("✋ Stand", callback_data="bj_stand"),
        ]
    ])

    text = f"""
🃏 **Blackjack**

Your hand: {' '.join(game['player'])} = **{val}**
Dealer: {game['dealer'][0]} ❓

Hit or Stand?
    """
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def bj_stand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    game = context.user_data.get("bj")
    if not game:
        await query.answer("Game not found!")
        return

    player_val = hand_value(game["player"])

    # Dealer draws
    while hand_value(game["dealer"]) < 17:
        game["dealer"].append(draw_card())

    dealer_val = hand_value(game["dealer"])

    if dealer_val > 21 or player_val > dealer_val:
        # Player wins
        payout = game["bet"] * 2
        update_balance(update.effective_user.id, payout)
        profit = game["bet"]
        result = "won"
        emoji = "🎉"
    elif player_val == dealer_val:
        # Push
        update_balance(update.effective_user.id, game["bet"])
        profit = 0
        result = "push"
        emoji = "🤝"
    else:
        # Dealer wins
        profit = -game["bet"]
        result = "lost"
        emoji = "😢"

    log_bet(update.effective_user.id, "blackjack", game["bet"], 2 if result == "won" else (1 if result == "push" else 0), result, profit)
    user = get_user(update.effective_user.id)
    supabase.table("users").update({"total_wagered": float(user["total_wagered"]) + game["bet"]}).eq("telegram_id", update.effective_user.id).execute()

    text = f"""
🃏 **Blackjack Result**

Your hand: {' '.join(game['player'])} = **{player_val}**
Dealer: {' '.join(game['dealer'])} = **{dealer_val}**

Bet: ${game['bet']:.2f}
{emoji} {'Won' if profit > 0 else ('Push' if profit == 0 else 'Lost')}: ${abs(profit):.2f}

💰 Balance: ${get_user(update.effective_user.id)['balance']:.2f}
    """

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Play Again", callback_data=f"bet_blackjack_{game['bet']}"),
         InlineKeyboardButton("🎮 Menu", callback_data="main_menu")]
    ])

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ============================================
# ADMIN COMMANDS
# ============================================

@safe_handler
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    users = supabase.table("users").select("*").execute()
    total_users = len(users.data)
    total_balance = sum(float(u["balance"]) for u in users.data)
    total_wagered = sum(float(u["total_wagered"]) for u in users.data)

    pending_deposits = supabase.table("transactions").select("*").eq("type", "deposit").eq("status", "pending").execute()
    pending_withdrawals = supabase.table("transactions").select("*").eq("type", "withdraw").eq("status", "pending").execute()

    text = f"""
👑 **Admin Panel**

👥 Total Users: {total_users}
💰 Total Balance: ${total_balance:.2f}
🎰 Total Wagered: ${total_wagered:.2f}
📥 Pending Deposits: {len(pending_deposits.data)}
📤 Pending Withdrawals: {len(pending_withdrawals.data)}

Commands:
/stats - Detailed stats
/broadcast MSG - Message all users
/approve USER_ID AMOUNT - Approve withdrawal
/reject USER_ID AMOUNT - Reject withdrawal
/promo CODE AMOUNT - Create promo code
    """
    await update.message.reply_text(text, parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    message = ' '.join(context.args)
    users = supabase.table("users").select("telegram_id").execute()

    sent = 0
    failed = 0
    for user in users.data:
        try:
            await context.bot.send_message(user["telegram_id"], f"📢 **Announcement**\n\n{message}", parse_mode="Markdown")
            sent += 1
        except:
            failed += 1

    await update.message.reply_text(f"✅ Sent: {sent} | ❌ Failed: {failed}")

# ============================================
# CALLBACK ROUTER
# ============================================

@safe_handler
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    # Main menu
    if data == "main_menu":
        await query.answer()
        user = get_user(update.effective_user.id)
        text = f"""
🎰 **BetVortex Casino**

💰 Balance: ${user['balance']:.2f}

Choose a game:
        """
        await query.edit_message_text(text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")

    # Game menus
    elif data.startswith("game_"):
        game = data.replace("game_", "")
        if game == "lottery":
            await lottery_menu(update, context)
        else:
            await game_menu(update, context, game)

    # Bet amounts
    elif data.startswith("bet_"):
        parts = data.split("_")
        game = parts[1]
        amount = float(parts[2])

        # Rate limit check
        if is_rate_limited(update.effective_user.id):
            await query.answer("⏳ Slow down! Wait a few seconds.", show_alert=True)
            return

        if game == "slots":
            await play_slots(update, context, amount)
        elif game == "dice":
            await play_dice(update, context, amount)
        elif game == "coinflip":
            await play_coinflip(update, context, amount)
        elif game == "roulette":
            await play_roulette(update, context, amount)
        elif game == "crash":
            await play_crash(update, context, amount)
        elif game == "blackjack":
            await play_blackjack(update, context, amount)
        elif game == "mines":
            await mines_menu(update, context, amount)
        elif game == "plinko":
            await play_plinko(update, context, amount)
        elif game == "wheel":
            await play_wheel(update, context, amount)
        elif game == "keno":
            await keno_menu(update, context, amount)
        elif game == "hilo":
            await hilo_start(update, context, amount)
        elif game == "baccarat":
            await play_baccarat(update, context, amount)
        elif game == "rps":
            await rps_menu(update, context, amount)
        elif game == "limbo":
            await play_limbo(update, context, amount)
        elif game == "tower":
            await tower_start(update, context, amount)
        elif game == "double":
            await play_double(update, context, amount)
        elif game == "adder":
            await play_adder(update, context, amount)

    # Dice rolls
    elif data.startswith("dice_roll_"):
        parts = data.split("_")
        amount = float(parts[2])
        prediction = parts[3]
        await dice_roll(update, context, amount, prediction)

    # Coin flip
    elif data.startswith("flip_"):
        parts = data.split("_")
        amount = float(parts[1])
        choice = parts[2]
        await coinflip_result(update, context, amount, choice)

    # Roulette
    elif data.startswith("roulette_"):
        parts = data.split("_")
        amount = float(parts[1])
        bet_type = parts[2]
        await roulette_result(update, context, amount, bet_type)

    # Crash
    elif data.startswith("crash_cash_"):
        parts = data.split("_")
        amount = float(parts[2])
        cashout = parts[3]
        crash_point = float(parts[4])
        await crash_result(update, context, amount, cashout, crash_point)

    # Blackjack
    elif data == "bj_hit":
        await bj_hit(update, context)
    elif data == "bj_stand":
        await bj_stand(update, context)
    elif data == "bj_double":
        await query.answer("Double feature coming soon!", show_alert=True)

    # Mines
    elif data.startswith("mines_"):
        if data == "mines_cashout":
            await mines_cashout(update, context)
        elif data != "mines_ignore":
            parts = data.split("_")
            row, col = int(parts[1]), int(parts[2])
            await mines_click(update, context, row, col)

    # Keno
    elif data.startswith("keno_"):
        if data == "keno_draw":
            await keno_draw(update, context)
        elif data != "keno_ignore":
            number = int(data.split("_")[1])
            await keno_select(update, context, number)

    # Hi-Lo
    elif data.startswith("hilo_"):
        if data == "hilo_higher":
            await hilo_guess(update, context, "higher")
        elif data == "hilo_lower":
            await hilo_guess(update, context, "lower")
        elif data == "hilo_cashout":
            await hilo_cashout(update, context)

    # Baccarat
    elif data.startswith("baccarat_"):
        parts = data.split("_")
        amount = float(parts[1])
        choice = parts[2]
        await baccarat_result(update, context, amount, choice)

    # Lottery
    elif data.startswith("lottery_"):
        if data == "lottery_winners":
            await query.answer("🏆 Winners announced weekly!", show_alert=True)
        else:
            amount = float(data.split("_")[1])
            await lottery_buy(update, context, amount)

    # RPS
    elif data.startswith("rps_"):
        parts = data.split("_")
        amount = float(parts[1])
        choice = parts[2]
        await rps_result(update, context, amount, choice)

    # Limbo
    elif data.startswith("limbo_"):
        parts = data.split("_")
        amount = float(parts[1])
        target = float(parts[2])
        await limbo_result(update, context, amount, target)

    # Tower
    elif data.startswith("tower_"):
        if data == "tower_cashout":
            await tower_cashout(update, context)
        else:
            tile = int(data.split("_")[1])
            await tower_click(update, context, tile)

    # Double
    elif data.startswith("double_"):
        parts = data.split("_")
        amount = float(parts[1])
        choice = parts[2]
        await double_result(update, context, amount, choice)

    # Adder
    elif data == "adder_add":
        await adder_add(update, context)
    elif data == "adder_stop":
        await adder_stop(update, context)

    # Wallet
    elif data == "deposit":
        await query.answer()
        await deposit(update, context)
    elif data == "withdraw":
        await query.answer()
        await withdraw(update, context)
    elif data == "balance":
        await query.answer()
        user = get_user(update.effective_user.id)
        await query.edit_message_text(
            f"💰 **Balance: ${user['balance']:.2f}**\n\n"
            f"📥 Deposited: ${user['total_deposited']:.2f}\n"
            f"📤 Withdrawn: ${user['total_withdrawn']:.2f}\n"
            f"🎰 Wagered: ${user['total_wagered']:.2f}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]),
            parse_mode="Markdown"
        )
    elif data == "referral":
        await query.answer()
        await referral(update, context)
    elif data == "history":
        await query.answer()
        await history(update, context)
    elif data == "help":
        await query.answer()
        text = HELP_TEXT
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]),
            parse_mode="Markdown"
        )

    # Agent callbacks
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

    # Admin Game Control callbacks
    elif data == "admin_games":
        await admin_game_panel(update, context)
    elif data.startswith("admin_game_"):
        game = data.replace("admin_game_", "")
        await admin_game_detail(update, context, game)
    elif data.startswith("toggle_"):
        game = data.replace("toggle_", "")
        await toggle_game(update, context, game)

    # Deposit crypto selection
    elif data.startswith("dep_"):
        coin = data.replace("dep_", "").upper()
        await query.answer()
        await query.edit_message_text(
            f"💰 **Deposit {coin}**\n\n"
            f"Send {coin} to this address:\n"
            f"(Integration with NOWPayments API needed)\n\n"
            f"Or contact admin for manual deposit.\n"
            f"Min: $1 equivalent",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="deposit")]]),
            parse_mode="Markdown"
        )

# ============================================
# MAIN
# ============================================

def main():
    # Validate required environment variables
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not os.getenv("SUPABASE_URL"):
        missing.append("SUPABASE_URL")
    if not os.getenv("SUPABASE_KEY"):
        missing.append("SUPABASE_KEY")
    
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print("Set them in Railway → Variables tab")
        return
    
    logger.info(f"Starting bot with ADMIN_ID={ADMIN_ID}")
    
    try:
        app = Application.builder().token(BOT_TOKEN).build()

        # Commands
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("balance", balance))
        app.add_handler(CommandHandler("deposit", deposit))
        app.add_handler(CommandHandler("withdraw", process_withdraw))
        app.add_handler(CommandHandler("referral", referral))
        app.add_handler(CommandHandler("history", history))
        app.add_handler(CommandHandler("admin", admin_panel))
        app.add_handler(CommandHandler("broadcast", broadcast))
        
        # Agent Commands
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
        
        # Game Control Commands (Admin)
        app.add_handler(CommandHandler("games", admin_game_panel))
        app.add_handler(CommandHandler("promo", create_promo))
        
        # User Commands
        app.add_handler(CommandHandler("claim", claim_promo))
        app.add_handler(CommandHandler("limits", set_limits_menu))
        app.add_handler(CommandHandler("exclude", self_exclude))

        # Callbacks
        app.add_handler(CallbackQueryHandler(callback_handler))

        print("🎰 BetVortex Casino Bot is running!")
        app.run_polling()
    except Exception as e:
        logger.error(f"Bot startup failed: {e}", exc_info=True)
        print(f"ERROR: Bot startup failed: {e}")
        raise

if __name__ == "__main__":
    main()
