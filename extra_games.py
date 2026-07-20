"""
BetVortex — Extra Games Module
Mines, Plinko, Wheel, Keno, Hi-Lo, Baccarat, Lottery, Rock Paper Scissors
"""

import random
import string
import math
import logging
from decimal import Decimal
from datetime import datetime

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import ContextTypes
import os
from db import supabase

logger = logging.getLogger(__name__)

SLOT_SYMBOLS = ["🍒", "🍋", "🍊", "🍇", "🔔", "💎", "⭐", "7️⃣"]

def get_user(tid):
    try:
        r = supabase.table("users").select("*").eq("telegram_id", tid).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        logger.error(f"get_user({tid}) failed: {e}")
        return None

def update_balance(tid, amount):
    try:
        u = get_user(tid)
        if not u:
            return 0
        nb = float(u["balance"]) + amount
        if nb < 0:
            nb = 0
        supabase.table("users").update({"balance": nb}).eq("telegram_id", tid).execute()
        return nb
    except Exception as e:
        logger.error(f"update_balance({tid}, {amount}) failed: {e}")
        return 0

def log_bet(tid, game, amount, mult, result, profit):
    try:
        supabase.table("bets").insert({
            "user_id": tid, "game": game, "amount": amount,
            "multiplier": mult, "result": result, "profit": profit
        }).execute()
        u = get_user(tid)
        if u:
            supabase.table("users").update({
                "total_wagered": float(u["total_wagered"]) + amount
            }).eq("telegram_id", tid).execute()
    except Exception as e:
        logger.error(f"log_bet({tid}, {game}) failed: {e}")

# ============================================
# GAME 7: MINES 💣
# ============================================

async def mines_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float):
    query = update.callback_query
    # Generate board: 5x5, 3-5 mines
    num_mines = random.randint(3, 7)
    mines = set()
    while len(mines) < num_mines:
        mines.add((random.randint(0, 4), random.randint(0, 4)))
    
    context.user_data["mines"] = {
        "bet": bet_amount,
        "mines": mines,
        "revealed": set(),
        "num_mines": num_mines,
        "multiplier": 1.0,
        "game_over": False
    }
    
    keyboard = mines_keyboard(mines, set(), False, bet_amount, 1.0)
    
    await query.edit_message_text(
        f"💣 **Mines**\n\n"
        f"Bet: ${bet_amount:.2f} | Mines: {num_mines}\n"
        f"Multiplier: 1.00x\n\n"
        f"Find gems, avoid mines!\n"
        f"Each safe tile increases multiplier.\n"
        f"Cash out anytime!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def mines_keyboard(mines, revealed, game_over, bet, mult):
    rows = []
    for r in range(5):
        row = []
        for c in range(5):
            if (r, c) in revealed:
                if (r, c) in mines:
                    row.append(InlineKeyboardButton("💥", callback_data="mines_ignore"))
                else:
                    row.append(InlineKeyboardButton("💎", callback_data="mines_ignore"))
            elif game_over:
                if (r, c) in mines:
                    row.append(InlineKeyboardButton("💣", callback_data="mines_ignore"))
                else:
                    row.append(InlineKeyboardButton("⬜", callback_data="mines_ignore"))
            else:
                row.append(InlineKeyboardButton("⬜", callback_data=f"mines_{r}_{c}"))
        rows.append(row)
    
    if not game_over and len(revealed) > 0:
        rows.append([
            InlineKeyboardButton(f"💰 Cash Out ${bet * mult:.2f}", callback_data="mines_cashout"),
        ])
    
    if game_over:
        rows.append([
            InlineKeyboardButton("🔄 Play Again", callback_data=f"bet_mines_{bet}"),
            InlineKeyboardButton("🎮 Menu", callback_data="main_menu"),
        ])
    
    return InlineKeyboardMarkup(rows)

async def mines_click(update: Update, context: ContextTypes.DEFAULT_TYPE, row: int, col: int):
    query = update.callback_query
    game = context.user_data.get("mines")
    
    if not game or game["game_over"]:
        await query.answer("Game over!")
        return
    
    if (row, col) in game["revealed"]:
        await query.answer("Already revealed!")
        return
    
    tid = update.effective_user.id
    
    if (row, col) in game["mines"]:
        # HIT A MINE!
        game["game_over"] = True
        profit = -game["bet"]
        log_bet(tid, "mines", game["bet"], 0, "mine_hit", profit)
        
        keyboard = mines_keyboard(game["mines"], game["revealed"], True, game["bet"], 0)
        
        await query.edit_message_text(
            f"💣 **BOOM! Mine Hit!** 💥\n\n"
            f"Bet: ${game['bet']:.2f}\n"
            f"😢 Lost: ${game['bet']:.2f}\n\n"
            f"💰 Balance: ${get_user(tid)['balance']:.2f}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        # SAFE TILE
        game["revealed"].add((row, col))
        safe_tiles = 25 - game["num_mines"]
        tiles_found = len(game["revealed"])
        
        # Calculate multiplier
        game["multiplier"] = round(1.0 * (25 / (25 - tiles_found)) * 0.97, 2)
        
        if tiles_found >= safe_tiles:
            # ALL SAFE TILES FOUND - AUTO WIN!
            game["game_over"] = True
            mult = game["multiplier"]
            payout = game["bet"] * mult
            update_balance(tid, payout)
            profit = payout - game["bet"]
            log_bet(tid, "mines", game["bet"], mult, "all_found", profit)
            
            keyboard = mines_keyboard(game["mines"], game["revealed"], True, game["bet"], mult)
            await query.edit_message_text(
                f"💣 **ALL GEMS FOUND!** 🎉\n\n"
                f"Multiplier: {mult}x\n"
                f"🎉 Won: ${profit:.2f}\n\n"
                f"💰 Balance: ${get_user(tid)['balance']:.2f}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            keyboard = mines_keyboard(game["mines"], game["revealed"], False, game["bet"], game["multiplier"])
            await query.edit_message_text(
                f"💣 **Mines**\n\n"
                f"Bet: ${game['bet']:.2f} | Mines: {game['num_mines']}\n"
                f"Gems found: {tiles_found}/{safe_tiles}\n"
                f"Multiplier: {game['multiplier']}x\n\n"
                f"Cash out or keep going!",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )

async def mines_cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    game = context.user_data.get("mines")
    
    if not game or game["game_over"]:
        await query.answer("Game over!")
        return
    
    tid = update.effective_user.id
    game["game_over"] = True
    
    mult = game["multiplier"]
    payout = game["bet"] * mult
    update_balance(tid, payout)
    profit = payout - game["bet"]
    
    log_bet(tid, "mines", game["bet"], mult, "cashout", profit)
    
    keyboard = mines_keyboard(game["mines"], game["revealed"], True, game["bet"], mult)
    await query.edit_message_text(
        f"💣 **Mines Cashout!** 🎉\n\n"
        f"Gems found: {len(game['revealed'])}\n"
        f"Multiplier: {mult}x\n"
        f"🎉 Won: ${profit:.2f}\n\n"
        f"💰 Balance: ${get_user(tid)['balance']:.2f}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# ============================================
# GAME 8: PLINKO 📌
# ============================================

async def play_plinko(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float):
    query = update.callback_query
    tid = update.effective_user.id
    user = get_user(tid)
    
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return
    
    update_balance(tid, -bet_amount)
    
    # Simulate ball path (8 rows)
    path = []
    position = 4  # Start center (0-8)
    for _ in range(8):
        direction = random.choice([-1, 1])
        position += direction
        position = max(0, min(8, position))
        path.append(direction)
    
    # Multipliers for slots (9 slots)
    multipliers = [10, 3, 1.5, 1, 0.5, 1, 1.5, 3, 10]
    mult = multipliers[position]
    
    payout = bet_amount * mult
    profit = payout - bet_amount
    
    if mult >= 1:
        update_balance(tid, payout)
    
    log_bet(tid, "plinko", bet_amount, mult, f"slot_{position}", profit)
    
    emoji = "🎉" if profit >= 0 else "😢"
    
    # Visual path
    visual = ""
    for i, d in enumerate(path):
        visual += "  " * (position - sum(1 for x in path[:i] if x == -1) + sum(1 for x in path[:i] if x == 1))
        visual += "📌\n"
    
    text = f"""
📌 **Plinko Result**

Ball landed in slot **{position + 1}**
Multiplier: **{mult}x**

Bet: ${bet_amount:.2f}
{emoji} {'Won' if profit >= 0 else 'Lost'}: ${abs(profit):.2f}

💰 Balance: ${get_user(tid)['balance']:.2f}
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Play Again", callback_data=f"bet_plinko_{bet_amount}"),
            InlineKeyboardButton("🎮 Menu", callback_data="main_menu"),
        ]
    ])
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ============================================
# GAME 9: WHEEL OF FORTUNE 🎡
# ============================================

WHEEL_SEGMENTS = [
    {"label": "🍒", "mult": 2, "color": "🔴"},
    {"label": "🍋", "mult": 3, "color": "🟡"},
    {"label": "🍊", "mult": 5, "color": "🟠"},
    {"label": "🍇", "mult": 10, "color": "🟣"},
    {"label": "🔔", "mult": 0, "color": "⚫"},  # Lose
    {"label": "💎", "mult": 15, "color": "🔵"},
    {"label": "⭐", "mult": 25, "color": "🟢"},
    {"label": "7️⃣", "mult": 50, "color": "🔴"},
    {"label": "💰", "mult": 0.5, "color": "🟡"},
    {"label": "🎁", "mult": 3, "color": "🟠"},
]

async def play_wheel(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float):
    query = update.callback_query
    tid = update.effective_user.id
    user = get_user(tid)
    
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return
    
    update_balance(tid, -bet_amount)
    
    # Spin
    result_idx = random.randint(0, len(WHEEL_SEGMENTS) - 1)
    segment = WHEEL_SEGMENTS[result_idx]
    mult = segment["mult"]
    
    payout = bet_amount * mult
    profit = payout - bet_amount
    
    if mult > 0:
        update_balance(tid, payout)
    
    log_bet(tid, "wheel", bet_amount, mult, f"seg_{result_idx}", profit)
    
    emoji = "🎉" if profit > 0 else ("🤝" if profit == 0 else "😢")
    
    text = f"""
🎡 **Wheel of Fortune**

🎯 Landed on: {segment['color']} {segment['label']}
Multiplier: **{mult}x**

Bet: ${bet_amount:.2f}
{emoji} {'Won' if profit > 0 else ('Push' if profit == 0 else 'Lost')}: ${abs(profit):.2f}

💰 Balance: ${get_user(tid)['balance']:.2f}
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Spin Again", callback_data=f"bet_wheel_{bet_amount}"),
            InlineKeyboardButton("🎮 Menu", callback_data="main_menu"),
        ]
    ])
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ============================================
# GAME 10: KENO 🎱
# ============================================

async def keno_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float):
    query = update.callback_query
    
    # Generate 40 numbers, player picks up to 10
    context.user_data["keno"] = {
        "bet": bet_amount,
        "selected": set(),
        "drawn": None,
        "max_pick": 10
    }
    
    keyboard = keno_number_keyboard(set(), set(), False)
    
    await query.edit_message_text(
        f"🎱 **Keno**\n\n"
        f"Bet: ${bet_amount:.2f}\n\n"
        f"Pick 1-10 numbers (1-40)\n"
        f"Then draw 10 random numbers.\n"
        f"More matches = bigger win!\n\n"
        f"Selected: 0/{10}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def keno_number_keyboard(selected, drawn, done):
    rows = []
    for row_start in range(0, 40, 8):
        row = []
        for n in range(row_start + 1, min(row_start + 9, 41)):
            if n in drawn:
                if n in selected:
                    label = f"✅{n}"  # Match!
                else:
                    label = f"❌{n}"  # Drawn but not picked
            elif n in selected:
                label = f"🔵{n}"
            else:
                label = str(n)
            
            if done:
                row.append(InlineKeyboardButton(label, callback_data="keno_ignore"))
            else:
                row.append(InlineKeyboardButton(label, callback_data=f"keno_{n}"))
        rows.append(row)
    
    if not done and len(selected) > 0:
        rows.append([
            InlineKeyboardButton(f"🎱 Draw! ({len(selected)} numbers)", callback_data="keno_draw"),
        ])
    
    if done:
        rows.append([
            InlineKeyboardButton("🔄 Play Again", callback_data=f"bet_keno_{bet_amount}"),
            InlineKeyboardButton("🎮 Menu", callback_data="main_menu"),
        ])
    
    return InlineKeyboardMarkup(rows)

async def keno_select(update: Update, context: ContextTypes.DEFAULT_TYPE, number: int):
    query = update.callback_query
    game = context.user_data.get("keno")
    
    if not game:
        return
    
    if number in game["selected"]:
        game["selected"].remove(number)
    else:
        if len(game["selected"]) >= game["max_pick"]:
            await query.answer("Max 10 numbers!", show_alert=True)
            return
        game["selected"].add(number)
    
    keyboard = keno_number_keyboard(game["selected"], set() if not game["drawn"] else game["drawn"], False)
    
    await query.edit_message_text(
        f"🎱 **Keno**\n\n"
        f"Bet: ${game['bet']:.2f}\n\n"
        f"Pick 1-10 numbers (1-40)\n"
        f"Selected: {len(game['selected'])}/{game['max_pick']}\n\n"
        f"Then press Draw!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def keno_draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    game = context.user_data.get("keno")
    
    if not game or len(game["selected"]) == 0:
        await query.answer("Pick at least 1 number!", show_alert=True)
        return
    
    tid = update.effective_user.id
    user = get_user(tid)
    
    if float(user["balance"]) < game["bet"]:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return
    
    update_balance(tid, -game["bet"])
    
    # Draw 10 random numbers
    drawn = set(random.sample(range(1, 41), 10))
    game["drawn"] = drawn
    
    # Count matches
    matches = game["selected"] & drawn
    num_matches = len(matches)
    picked = len(game["selected"])
    
    # Payout table based on matches/picked
    payout_table = {
        1: {1: 2},
        2: {1: 0.5, 2: 5},
        3: {1: 0, 2: 2, 3: 20},
        4: {1: 0, 2: 1, 3: 5, 4: 50},
        5: {1: 0, 2: 0.5, 3: 2, 4: 15, 5: 100},
        6: {1: 0, 2: 0, 3: 1, 4: 5, 5: 25, 6: 200},
        7: {1: 0, 2: 0, 3: 0.5, 4: 2, 5: 10, 6: 50, 7: 500},
        8: {1: 0, 2: 0, 3: 0, 4: 1, 5: 5, 6: 20, 7: 100, 8: 1000},
        9: {1: 0, 2: 0, 3: 0, 4: 0.5, 5: 2, 6: 10, 7: 50, 8: 200, 9: 2000},
        10: {1: 0, 2: 0, 3: 0, 4: 0, 5: 1, 6: 5, 7: 20, 8: 100, 9: 500, 10: 5000},
    }
    
    mult = payout_table.get(picked, {}).get(num_matches, 0)
    payout = game["bet"] * mult
    profit = payout - game["bet"]
    
    if mult > 0:
        update_balance(tid, payout)
    
    log_bet(tid, "keno", game["bet"], mult, f"{num_matches}_of_{picked}", profit)
    
    emoji = "🎉" if profit > 0 else "😢"
    
    keyboard = keno_number_keyboard(game["selected"], drawn, True)
    
    await query.edit_message_text(
        f"🎱 **Keno Result**\n\n"
        f"Your numbers: {sorted(game['selected'])}\n"
        f"Drawn: {sorted(drawn)}\n"
        f"Matches: **{num_matches}** / {picked}\n\n"
        f"Multiplier: {mult}x\n"
        f"Bet: ${game['bet']:.2f}\n"
        f"{emoji} {'Won' if profit >= 0 else 'Lost'}: ${abs(profit):.2f}\n\n"
        f"💰 Balance: ${get_user(tid)['balance']:.2f}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# ============================================
# GAME 11: HI-LO 🔺🔻
# ============================================

CARDS = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
SUITS = ['♠','♥','♦','♣']

def card_rank(card):
    rank = card[:-1]
    if rank == 'A': return 14
    if rank == 'K': return 13
    if rank == 'Q': return 12
    if rank == 'J': return 11
    return int(rank)

async def hilo_start(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float):
    query = update.callback_query
    tid = update.effective_user.id
    user = get_user(tid)
    
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return
    
    update_balance(tid, -bet_amount)
    
    current = f"{random.choice(CARDS)}{random.choice(SUITS)}"
    
    context.user_data["hilo"] = {
        "bet": bet_amount,
        "current": current,
        "streak": 0,
        "multiplier": 1.0,
        "game_over": False
    }
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔺 Higher", callback_data="hilo_higher"),
            InlineKeyboardButton("🔻 Lower", callback_data="hilo_lower"),
        ],
        [InlineKeyboardButton("💰 Cash Out", callback_data="hilo_cashout")]
    ])
    
    await query.edit_message_text(
        f"🔺🔻 **Hi-Lo**\n\n"
        f"Current Card: **{current}**\n\n"
        f"Bet: ${bet_amount:.2f}\n"
        f"Streak: 0 | Multiplier: 1.00x\n\n"
        f"Next card will be Higher or Lower?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def hilo_guess(update: Update, context: ContextTypes.DEFAULT_TYPE, guess: str):
    query = update.callback_query
    game = context.user_data.get("hilo")
    
    if not game or game["game_over"]:
        await query.answer("Game over!")
        return
    
    tid = update.effective_user.id
    
    current_rank = card_rank(game["current"])
    next_card = f"{random.choice(CARDS)}{random.choice(SUITS)}"
    next_rank = card_rank(next_card)
    
    correct = False
    if guess == "higher" and next_rank > current_rank:
        correct = True
    elif guess == "lower" and next_rank < current_rank:
        correct = True
    elif next_rank == current_rank:
        # Push - same rank
        pass
    
    if correct:
        game["streak"] += 1
        game["multiplier"] = round(1.0 + (game["streak"] * 0.5), 2)
        game["current"] = next_card
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔺 Higher", callback_data="hilo_higher"),
                InlineKeyboardButton("🔻 Lower", callback_data="hilo_lower"),
            ],
            [InlineKeyboardButton(f"💰 Cash Out ${game['bet'] * game['multiplier']:.2f}", callback_data="hilo_cashout")]
        ])
        
        await query.edit_message_text(
            f"🔺🔻 **Hi-Lo**\n\n"
            f"Previous: **{game['current']}** → **{next_card}**\n\n"
            f"Bet: ${game['bet']:.2f}\n"
            f"Streak: {game['streak']} | Multiplier: {game['multiplier']}x\n\n"
            f"✅ Correct! Keep going or cash out!",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        # Wrong guess
        game["game_over"] = True
        profit = -game["bet"]
        log_bet(tid, "hilo", game["bet"], 0, f"wrong_{guess}", profit)
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Play Again", callback_data=f"bet_hilo_{game['bet']}"),
                InlineKeyboardButton("🎮 Menu", callback_data="main_menu"),
            ]
        ])
        
        await query.edit_message_text(
            f"🔺🔻 **Hi-Lo — Wrong!** 😢\n\n"
            f"Card was: **{game['current']}**\n"
            f"Next was: **{next_card}**\n"
            f"You guessed: {guess}\n\n"
            f"Bet: ${game['bet']:.2f}\n"
            f"😢 Lost: ${game['bet']:.2f}\n\n"
            f"💰 Balance: ${get_user(tid)['balance']:.2f}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

async def hilo_cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    game = context.user_data.get("hilo")
    
    if not game or game["game_over"]:
        await query.answer("Game over!")
        return
    
    tid = update.effective_user.id
    game["game_over"] = True
    
    mult = game["multiplier"]
    payout = game["bet"] * mult
    update_balance(tid, payout)
    profit = payout - game["bet"]
    
    log_bet(tid, "hilo", game["bet"], mult, f"cashout_streak_{game['streak']}", profit)
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Play Again", callback_data=f"bet_hilo_{game['bet']}"),
            InlineKeyboardButton("🎮 Menu", callback_data="main_menu"),
        ]
    ])
    
    await query.edit_message_text(
        f"🔺🔻 **Hi-Lo Cashout!** 🎉\n\n"
        f"Streak: {game['streak']}\n"
        f"Multiplier: {mult}x\n"
        f"🎉 Won: ${profit:.2f}\n\n"
        f"💰 Balance: ${get_user(tid)['balance']:.2f}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# ============================================
# GAME 12: BACCARAT 🂡
# ============================================

async def play_baccarat(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float):
    query = update.callback_query
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👤 Player (2x)", callback_data=f"baccarat_{bet_amount}_player"),
            InlineKeyboardButton("🏦 Banker (1.95x)", callback_data=f"baccarat_{bet_amount}_banker"),
        ],
        [
            InlineKeyboardButton("🤝 Tie (8x)", callback_data=f"baccarat_{bet_amount}_tie"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="game_baccarat")]
    ])
    
    user = get_user(update.effective_user.id)
    await query.edit_message_text(
        f"🂡 **Baccarat**\n\n"
        f"Bet: ${bet_amount:.2f}\n"
        f"💰 Balance: ${user['balance']:.2f}\n\n"
        f"Who will win?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def baccarat_hand_value(cards):
    total = sum(min(card_rank(c[:-1] if len(c) > 2 else c[0]), 10) for c in cards)
    return total % 10

async def baccarat_result(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float, choice: str):
    query = update.callback_query
    tid = update.effective_user.id
    user = get_user(tid)
    
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return
    
    update_balance(tid, -bet_amount)
    
    # Deal cards
    player_cards = [f"{random.choice(CARDS)}{random.choice(SUITS)}", f"{random.choice(CARDS)}{random.choice(SUITS)}"]
    banker_cards = [f"{random.choice(CARDS)}{random.choice(SUITS)}", f"{random.choice(CARDS)}{random.choice(SUITS)}"]
    
    player_val = baccarat_hand_value(player_cards)
    banker_val = baccarat_hand_value(banker_cards)
    
    # Determine winner
    if player_val > banker_val:
        winner = "player"
    elif banker_val > player_val:
        winner = "banker"
    else:
        winner = "tie"
    
    # Calculate payout
    if choice == winner:
        if choice == "player":
            mult = 2.0
        elif choice == "banker":
            mult = 1.95
        else:  # tie
            mult = 8.0
        payout = bet_amount * mult
        profit = payout - bet_amount
        update_balance(tid, payout)
    else:
        mult = 0
        profit = -bet_amount
    
    log_bet(tid, "baccarat", bet_amount, mult, f"{choice}_vs_{winner}", profit)
    
    emoji = "🎉" if profit > 0 else "😢"
    winner_text = {"player": "Player", "banker": "Banker", "tie": "Tie"}[winner]
    
    text = f"""
🂡 **Baccarat Result**

👤 Player: {' '.join(player_cards)} = **{player_val}**
🏦 Banker: {' '.join(banker_cards)} = **{banker_val}**

Winner: **{winner_text}**
Your bet: {choice.title()}

Bet: ${bet_amount:.2f}
{emoji} {'Won' if profit > 0 else 'Lost'}: ${abs(profit):.2f}

💰 Balance: ${get_user(tid)['balance']:.2f}
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Play Again", callback_data=f"bet_baccarat_{bet_amount}"),
            InlineKeyboardButton("🎮 Menu", callback_data="main_menu"),
        ]
    ])
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ============================================
# GAME 13: LOTTERY 🎟️
# ============================================

async def lottery_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    tid = update.effective_user.id
    user = get_user(tid)
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎟️ $1 Ticket", callback_data="lottery_1"),
            InlineKeyboardButton("🎟️ $5 Ticket", callback_data="lottery_5"),
        ],
        [
            InlineKeyboardButton("🎟️ $10 Ticket", callback_data="lottery_10"),
            InlineKeyboardButton("🎟️ $50 Ticket", callback_data="lottery_50"),
        ],
        [
            InlineKeyboardButton("🏆 View Winners", callback_data="lottery_winners"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
    ])
    
    await query.edit_message_text(
        f"🎟️ **Lottery**\n\n"
        f"💰 Balance: ${user['balance']:.2f}\n\n"
        f"Buy a ticket and win big!\n\n"
        f"**Prizes:**\n"
        f"🎯 6/6 numbers: **$10,000**\n"
        f"🎯 5/6 numbers: **$500**\n"
        f"🎯 4/6 numbers: **$50**\n"
        f"🎯 3/6 numbers: **$5**\n\n"
        f"Draw every 24 hours!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def lottery_buy(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: float):
    query = update.callback_query
    tid = update.effective_user.id
    user = get_user(tid)
    
    if float(user["balance"]) < amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return
    
    update_balance(tid, -amount)
    
    # Generate ticket numbers
    numbers = sorted(random.sample(range(1, 50), 6))
    
    # Instant draw (simplified - in production, use scheduled draw)
    drawn = sorted(random.sample(range(1, 50), 6))
    matches = len(set(numbers) & set(drawn))
    
    prizes = {6: 10000, 5: 500, 4: 50, 3: 5}
    prize = prizes.get(matches, 0) * (amount / 1)  # Scale by ticket price
    
    if prize > 0:
        update_balance(tid, prize)
        profit = prize - amount
        emoji = "🎉"
    else:
        profit = -amount
        emoji = "😢"
    
    log_bet(tid, "lottery", amount, prize / amount if amount > 0 else 0, f"{matches}_match", profit)
    
    text = f"""
🎟️ **Lottery Result**

Your numbers: **{' '.join(f'{n:02d}' for n in numbers)}**
Drawn numbers: **{' '.join(f'{n:02d}' for n in drawn)}**

Matches: **{matches}/6**

Ticket: ${amount:.2f}
{emoji} {'Won $' + f'{prize:.2f}' if prize > 0 else 'No prize'}

💰 Balance: ${get_user(tid)['balance']:.2f}
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎟️ Buy Again", callback_data="game_lottery"),
            InlineKeyboardButton("🎮 Menu", callback_data="main_menu"),
        ]
    ])
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ============================================
# GAME 14: ROCK PAPER SCISSORS ✊✌️🖐️
# ============================================

async def rps_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float):
    query = update.callback_query
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✊ Rock", callback_data=f"rps_{bet_amount}_rock"),
            InlineKeyboardButton("✌️ Scissors", callback_data=f"rps_{bet_amount}_scissors"),
            InlineKeyboardButton("🖐️ Paper", callback_data=f"rps_{bet_amount}_paper"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="game_rps")]
    ])
    
    user = get_user(update.effective_user.id)
    await query.edit_message_text(
        f"✊✌️🖐️ **Rock Paper Scissors**\n\n"
        f"Bet: ${bet_amount:.2f}\n"
        f"💰 Balance: ${user['balance']:.2f}\n\n"
        f"Win: 2x | Draw: Refund | Lose: 0x\n\n"
        f"Choose your weapon!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def rps_result(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float, player_choice: str):
    query = update.callback_query
    tid = update.effective_user.id
    user = get_user(tid)
    
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return
    
    update_balance(tid, -bet_amount)
    
    bot_choice = random.choice(["rock", "scissors", "paper"])
    
    emojis = {"rock": "✊", "scissors": "✌️", "paper": "🖐️"}
    
    # Determine winner
    if player_choice == bot_choice:
        result = "draw"
        mult = 1.0
        update_balance(tid, bet_amount)  # Refund
        profit = 0
    elif (player_choice == "rock" and bot_choice == "scissors") or \
         (player_choice == "scissors" and bot_choice == "paper") or \
         (player_choice == "paper" and bot_choice == "rock"):
        result = "win"
        mult = 2.0
        payout = bet_amount * 2
        update_balance(tid, payout)
        profit = bet_amount
    else:
        result = "lose"
        mult = 0
        profit = -bet_amount
    
    log_bet(tid, "rps", bet_amount, mult, f"{player_choice}_vs_{bot_choice}", profit)
    
    result_emoji = {"win": "🎉", "lose": "😢", "draw": "🤝"}[result]
    result_text = {"win": "You Win!", "lose": "You Lose!", "draw": "Draw!"}[result]
    
    text = f"""
✊✌️🖐️ **Rock Paper Scissors**

You: {emojis[player_choice]} {player_choice.title()}
Bot: {emojis[bot_choice]} {bot_choice.title()}

{result_emoji} **{result_text}**

Bet: ${bet_amount:.2f}
{'Won' if profit > 0 else ('Draw' if profit == 0 else 'Lost')}: ${abs(profit):.2f}

💰 Balance: ${get_user(tid)['balance']:.2f}
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Play Again", callback_data=f"bet_rps_{bet_amount}"),
            InlineKeyboardButton("🎮 Menu", callback_data="main_menu"),
        ]
    ])
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ============================================
# GAME 15: LIMBO 🎯
# ============================================

async def play_limbo(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float):
    """Limbo: Pick a target multiplier, ball rolls, if it lands above target you win"""
    query = update.callback_query
    tid = update.effective_user.id
    user = get_user(tid)
    
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1.5x", callback_data=f"limbo_{bet_amount}_1.5"),
            InlineKeyboardButton("2x", callback_data=f"limbo_{bet_amount}_2"),
            InlineKeyboardButton("3x", callback_data=f"limbo_{bet_amount}_3"),
        ],
        [
            InlineKeyboardButton("5x", callback_data=f"limbo_{bet_amount}_5"),
            InlineKeyboardButton("10x", callback_data=f"limbo_{bet_amount}_10"),
            InlineKeyboardButton("100x", callback_data=f"limbo_{bet_amount}_100"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="game_limbo")]
    ])
    
    await query.edit_message_text(
        f"🎯 **Limbo**\n\n"
        f"Bet: ${bet_amount:.2f}\n"
        f"💰 Balance: ${user['balance']:.2f}\n\n"
        f"Pick a target multiplier!\n"
        f"If the roll lands above your target, you win!\n"
        f"Higher target = bigger risk = bigger reward",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def limbo_result(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float, target: float):
    query = update.callback_query
    tid = update.effective_user.id
    user = get_user(tid)
    
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return
    
    update_balance(tid, -bet_amount)
    
    # Generate roll (0 to high, weighted)
    roll = round(random.uniform(0.01, 100.0), 2)
    
    win = roll >= target
    
    if win:
        # Calculate payout (adjusted for house edge)
        payout = bet_amount * target * 0.97  # 3% house edge
        update_balance(tid, payout)
        profit = payout - bet_amount
        mult = target
    else:
        profit = -bet_amount
        mult = 0
    
    log_bet(tid, "limbo", bet_amount, mult, f"roll_{roll}_target_{target}", profit)
    
    emoji = "🎉" if win else "😢"
    
    text = f"""
🎯 **Limbo Result**

🎯 Target: {target}x
🎲 Rolled: **{roll}x**

{'✅ Above target!' if win else '❌ Below target!'}

Bet: ${bet_amount:.2f}
{emoji} {'Won' if win else 'Lost'}: ${abs(profit):.2f}

💰 Balance: ${get_user(tid)['balance']:.2f}
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Play Again", callback_data=f"bet_limbo_{bet_amount}"),
            InlineKeyboardButton("🎮 Menu", callback_data="main_menu"),
        ]
    ])
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ============================================
# GAME 16: TOWER 🏗️
# ============================================

async def tower_start(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float):
    """Tower: Climb floors, each floor has safe/danger tiles"""
    query = update.callback_query
    tid = update.effective_user.id
    user = get_user(tid)
    
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return
    
    update_balance(tid, -bet_amount)
    
    # Generate tower (8 floors, 3 tiles each, 1 danger per floor)
    tower = []
    for _ in range(8):
        danger = random.randint(0, 2)
        tower.append(danger)
    
    context.user_data["tower"] = {
        "bet": bet_amount,
        "tower": tower,
        "floor": 0,
        "multiplier": 1.0,
        "game_over": False
    }
    
    keyboard = tower_keyboard(tower, 0, False, bet_amount, 1.0)
    
    await query.edit_message_text(
        f"🏗️ **Tower**\n\n"
        f"Bet: ${bet_amount:.2f}\n"
        f"Floor: 0/8 | Multiplier: 1.00x\n\n"
        f"Climb floors to increase multiplier!\n"
        f"Each floor has 3 tiles (1 danger).\n"
        f"Cash out anytime!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

def tower_keyboard(tower, floor, game_over, bet, mult):
    rows = []
    
    if not game_over and floor < 8:
        danger = tower[floor]
        for i in range(3):
            if game_over:
                label = "💥" if i == danger else "🟢"
            else:
                label = f"Tile {i+1}"
            rows.append(InlineKeyboardButton(label, callback_data=f"tower_{i}"))
    
    if floor > 0 and not game_over:
        rows.append(InlineKeyboardButton(f"💰 Cash Out ${bet * mult:.2f}", callback_data="tower_cashout"))
    
    if game_over or floor >= 8:
        rows.append(InlineKeyboardButton("🔄 Play Again", callback_data=f"bet_tower_{bet}"))
        rows.append(InlineKeyboardButton("🎮 Menu", callback_data="main_menu"))
    
    return InlineKeyboardMarkup([rows]) if rows else InlineKeyboardMarkup([[InlineKeyboardButton("🔄", callback_data="main_menu")]])

async def tower_click(update: Update, context: ContextTypes.DEFAULT_TYPE, tile: int):
    query = update.callback_query
    game = context.user_data.get("tower")
    
    if not game or game["game_over"]:
        return
    
    tid = update.effective_user.id
    danger = game["tower"][game["floor"]]
    
    if tile == danger:
        # HIT DANGER
        game["game_over"] = True
        profit = -game["bet"]
        log_bet(tid, "tower", game["bet"], 0, f"floor_{game['floor']}", profit)
        
        keyboard = tower_keyboard(game["tower"], game["floor"], True, game["bet"], 0)
        await query.edit_message_text(
            f"🏗️ **Tower — Crashed!** 💥\n\n"
            f"Fell at floor {game['floor'] + 1}\n"
            f"Bet: ${game['bet']:.2f}\n"
            f"😢 Lost: ${game['bet']:.2f}\n\n"
            f"💰 Balance: ${get_user(tid)['balance']:.2f}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        # SAFE
        game["floor"] += 1
        game["multiplier"] = round(1.0 + (game["floor"] * 0.4), 2)
        
        if game["floor"] >= 8:
            # TOP FLOOR - AUTO WIN
            game["game_over"] = True
            mult = game["multiplier"]
            payout = game["bet"] * mult
            update_balance(tid, payout)
            profit = payout - game["bet"]
            log_bet(tid, "tower", game["bet"], mult, "top", profit)
            
            keyboard = tower_keyboard(game["tower"], game["floor"], True, game["bet"], mult)
            await query.edit_message_text(
                f"🏗️ **Tower — TOP FLOOR!** 🎉\n\n"
                f"Multiplier: {mult}x\n"
                f"🎉 Won: ${profit:.2f}\n\n"
                f"💰 Balance: ${get_user(tid)['balance']:.2f}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            keyboard = tower_keyboard(game["tower"], game["floor"], False, game["bet"], game["multiplier"])
            await query.edit_message_text(
                f"🏗️ **Tower**\n\n"
                f"Floor: {game['floor']}/8 | Multiplier: {game['multiplier']}x\n\n"
                f"✅ Safe! Keep climbing or cash out!",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )

async def tower_cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    game = context.user_data.get("tower")
    
    if not game or game["game_over"]:
        return
    
    tid = update.effective_user.id
    game["game_over"] = True
    
    mult = game["multiplier"]
    payout = game["bet"] * mult
    update_balance(tid, payout)
    profit = payout - game["bet"]
    
    log_bet(tid, "tower", game["bet"], mult, f"cashout_floor_{game['floor']}", profit)
    
    keyboard = tower_keyboard(game["tower"], game["floor"], True, game["bet"], mult)
    await query.edit_message_text(
        f"🏗️ **Tower Cashout!** 🎉\n\n"
        f"Floor: {game['floor']}/8 | Multiplier: {mult}x\n"
        f"🎉 Won: ${profit:.2f}\n\n"
        f"💰 Balance: ${get_user(tid)['balance']:.2f}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# ============================================
# GAME 17: DOUBLE (Color Bet) 🔴⚫🟢
# ============================================

async def play_double(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float):
    query = update.callback_query
    tid = update.effective_user.id
    user = get_user(tid)
    
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔴 Red (2x)", callback_data=f"double_{bet_amount}_red"),
            InlineKeyboardButton("⚫ Black (2x)", callback_data=f"double_{bet_amount}_black"),
        ],
        [
            InlineKeyboardButton("🟢 Green (14x)", callback_data=f"double_{bet_amount}_green"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="game_double")]
    ])
    
    await query.edit_message_text(
        f"🔴⚫🟢 **Double**\n\n"
        f"Bet: ${bet_amount:.2f}\n"
        f"💰 Balance: ${user['balance']:.2f}\n\n"
        f"🔴 Red = 2x (47.5%)\n"
        f"⚫ Black = 2x (47.5%)\n"
        f"🟢 Green = 14x (5%)\n\n"
        f"Pick a color!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def double_result(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float, choice: str):
    query = update.callback_query
    tid = update.effective_user.id
    user = get_user(tid)
    
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return
    
    update_balance(tid, -bet_amount)
    
    # Weighted random: 47.5% red, 47.5% black, 5% green
    roll = random.random()
    if roll < 0.475:
        result = "red"
    elif roll < 0.95:
        result = "black"
    else:
        result = "green"
    
    color_emoji = {"red": "🔴", "black": "⚫", "green": "🟢"}[result]
    
    if choice == result:
        if choice == "green":
            mult = 14
        else:
            mult = 2
        payout = bet_amount * mult
        update_balance(tid, payout)
        profit = payout - bet_amount
    else:
        mult = 0
        profit = -bet_amount
    
    log_bet(tid, "double", bet_amount, mult, f"{choice}_vs_{result}", profit)
    
    emoji = "🎉" if profit > 0 else "😢"
    
    text = f"""
🔴⚫🟢 **Double Result**

{color_emoji} **{result.upper()}**

Your bet: {choice.title()}
Bet: ${bet_amount:.2f}
{emoji} {'Won' if profit > 0 else 'Lost'}: ${abs(profit):.2f}

💰 Balance: ${get_user(tid)['balance']:.2f}
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Play Again", callback_data=f"bet_double_{bet_amount}"),
            InlineKeyboardButton("🎮 Menu", callback_data="main_menu"),
        ]
    ])
    
    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

# ============================================
# GAME 18: ADDER ➕
# ============================================

async def play_adder(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: float):
    """Adder: Numbers appear, decide to add or skip. Get as close to 21 as possible."""
    query = update.callback_query
    tid = update.effective_user.id
    user = get_user(tid)
    
    if float(user["balance"]) < bet_amount:
        await query.answer("❌ Insufficient balance!", show_alert=True)
        return
    
    update_balance(tid, -bet_amount)
    
    first_num = random.randint(1, 10)
    
    context.user_data["adder"] = {
        "bet": bet_amount,
        "total": first_num,
        "numbers": [first_num],
        "game_over": False
    }
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add", callback_data="adder_add"),
            InlineKeyboardButton("🛑 Stop", callback_data="adder_stop"),
        ]
    ])
    
    await query.edit_message_text(
        f"➕ **Adder**\n\n"
        f"Bet: ${bet_amount:.2f}\n\n"
        f"Current: **{first_num}**\n"
        f"Target: 21 (without going over!)\n\n"
        f"Add or Stop?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def adder_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    game = context.user_data.get("adder")
    
    if not game or game["game_over"]:
        return
    
    tid = update.effective_user.id
    
    new_num = random.randint(1, 10)
    game["total"] += new_num
    game["numbers"].append(new_num)
    
    if game["total"] > 21:
        # BUST!
        game["game_over"] = True
        profit = -game["bet"]
        log_bet(tid, "adder", game["bet"], 0, f"bust_{game['total']}", profit)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Play Again", callback_data=f"bet_adder_{game['bet']}"),
             InlineKeyboardButton("🎮 Menu", callback_data="main_menu")]
        ])
        
        await query.edit_message_text(
            f"➕ **BUST!** 💥\n\n"
            f"Numbers: {' + '.join(map(str, game['numbers']))} = **{game['total']}**\n"
            f"Over 21!\n\n"
            f"Bet: ${game['bet']:.2f}\n"
            f"😢 Lost: ${game['bet']:.2f}\n\n"
            f"💰 Balance: ${get_user(tid)['balance']:.2f}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        # Safe - continue
        # Calculate current multiplier
        mult = round(1.0 + (game["total"] / 21) * 3, 2)
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("➕ Add", callback_data="adder_add"),
                InlineKeyboardButton(f"🛑 Stop ${game['bet'] * mult:.2f}", callback_data="adder_stop"),
            ]
        ])
        
        await query.edit_message_text(
            f"➕ **Adder**\n\n"
            f"Numbers: {' + '.join(map(str, game['numbers']))} = **{game['total']}**\n"
            f"Current Multiplier: {mult}x\n\n"
            f"Add or Stop?",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

async def adder_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    game = context.user_data.get("adder")
    
    if not game or game["game_over"]:
        return
    
    tid = update.effective_user.id
    game["game_over"] = True
    
    mult = round(1.0 + (game["total"] / 21) * 3, 2)
    payout = game["bet"] * mult
    update_balance(tid, payout)
    profit = payout - game["bet"]
    
    log_bet(tid, "adder", game["bet"], mult, f"stop_{game['total']}", profit)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Play Again", callback_data=f"bet_adder_{game['bet']}"),
         InlineKeyboardButton("🎮 Menu", callback_data="main_menu")]
    ])
    
    await query.edit_message_text(
        f"➕ **Adder Stopped!** 🎉\n\n"
        f"Numbers: {' + '.join(map(str, game['numbers']))} = **{game['total']}**\n"
        f"Multiplier: {mult}x\n"
        f"🎉 Won: ${profit:.2f}\n\n"
        f"💰 Balance: ${get_user(tid)['balance']:.2f}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
