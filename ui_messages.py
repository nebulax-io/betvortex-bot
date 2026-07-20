"""
BetVortex — Complete English UX/UI Messages
All bot text, buttons, and interactions in professional English
"""

# ============================================
# MAIN MENU
# ============================================

MAIN_MENU_TEXT = """
🎰 **Welcome to BetVortex Casino** 🎰

Your balance: **${balance:.2f}**

Select a game to play or manage your account:

🎮 **18 Games Available**
💰 **Instant Deposits & Withdrawals**
🤝 **Agent System — Earn up to 25%**
🎁 **$1 Welcome Bonus**
"""

MAIN_MENU_BUTTONS = [
    # Row 1: Popular Games
    [("🎰 Slots", "game_slots"), ("🎲 Dice", "game_dice")],
    [("✈️ Crash", "game_crash"), ("🃏 Blackjack", "game_blackjack")],
    [("🎡 Roulette", "game_roulette"), ("🪙 Coin Flip", "game_coinflip")],
    
    # Row 2: More Games
    [("💣 Mines", "game_mines"), ("📌 Plinko", "game_plinko")],
    [("🎡 Wheel", "game_wheel"), ("🎱 Keno", "game_keno")],
    [("🔺 Hi-Lo", "game_hilo"), ("🂡 Baccarat", "game_baccarat")],
    
    # Row 3: Extra Games
    [("🎟️ Lottery", "game_lottery"), ("✊ RPS", "game_rps")],
    [("🎯 Limbo", "game_limbo"), ("🏗️ Tower", "game_tower")],
    [("🔴 Double", "game_double"), ("➕ Adder", "game_adder")],
    
    # Row 4: Account
    [("💰 Deposit", "deposit"), ("💸 Withdraw", "withdraw")],
    [("📊 Balance", "balance"), ("🤝 Referral", "referral")],
    [("📜 History", "history"), ("ℹ️ Help", "help")],
]

# ============================================
# WELCOME MESSAGE
# ============================================

WELCOME_NEW_USER = """
🎰 **Welcome to BetVortex Casino!** 🎰

Hello {username}! Ready to play?

🎁 **Welcome Bonus: $1.00 Added!**

💰 Your Balance: **${balance:.2f}**

━━━━━━━━━━━━━━━━━━━━

🎮 **18 Games Available:**
🎰 Slots • 🎲 Dice • ✈️ Crash • 🃏 Blackjack
🎡 Roulette • 🪙 Coin Flip • 💣 Mines • 📌 Plinko
🎡 Wheel • 🎱 Keno • 🔺 Hi-Lo • 🂡 Baccarat
🎟️ Lottery • ✊ RPS • 🎯 Limbo • 🏗️ Tower
🔴 Double • ➕ Adder

━━━━━━━━━━━━━━━━━━━━

💰 **Quick Start:**
1. Tap **Deposit** to add crypto
2. Choose a game
3. Place your bet
4. Win big!

🎁 **Earn More:**
• /referral — Invite friends, earn bonus
• /agent — Become an agent, earn commission

Good luck! 🍀
"""

WELCOME_EXISTING_USER = """
🎰 **Welcome Back to BetVortex!** 🎰

Hello {username}!

💰 Balance: **${balance:.2f}**

Choose a game to play:
"""

# ============================================
# GAME DESCRIPTIONS
# ============================================

GAME_DESCRIPTIONS = {
    "slots": {
        "name": "🎰 Slots",
        "description": "Spin the reels and match symbols to win!",
        "how_to_play": """
**How to Play:**
1. Select your bet amount
2. Tap Spin
3. Match 3 symbols to win!

**Payouts:**
🍒🍒🍒 = 5x | 🍋🍋🍋 = 8x | 🍊🍊🍊 = 10x
🍇🍇🍇 = 15x | 🔔🔔🔔 = 25x | 💎💎💎 = 50x
⭐⭐⭐ = 75x | 7️⃣7️⃣7️⃣ = 100x

**Partial Match:**
2 matching = 1.2x - 1.5x
""",
        "min_bet": 0.10,
        "max_bet": 100,
    },
    "dice": {
        "name": "🎲 Dice",
        "description": "Roll the dice and predict the outcome!",
        "how_to_play": """
**How to Play:**
1. Select your bet amount
2. Choose Over or Under
3. Dice rolls 0-100

**Payouts:**
Over 50 = 2x | Under 50 = 2x
Over 75 = 4x | Under 25 = 4x
Over 90 = 10x | Under 10 = 10x
""",
        "min_bet": 0.10,
        "max_bet": 500,
    },
    "crash": {
        "name": "✈️ Crash",
        "description": "Multiplier rises — cash out before it crashes!",
        "how_to_play": """
**How to Play:**
1. Place your bet
2. Watch the multiplier rise
3. Cash out before it crashes!

**Example:**
Multiplier: 1.00x → 1.50x → 2.00x → 3.00x → 💥 CRASH
If you cash out at 2.00x, you win 2x your bet!

**Risk:** Higher wait = Higher reward = Higher risk
""",
        "min_bet": 0.10,
        "max_bet": 200,
    },
    "blackjack": {
        "name": "🃏 Blackjack",
        "description": "Get 21 or beat the dealer!",
        "how_to_play": """
**How to Play:**
1. You get 2 cards
2. Dealer gets 2 cards (1 hidden)
3. Get closer to 21 than dealer

**Actions:**
🃏 Hit — Take another card
✋ Stand — Keep your hand
💰 Double — Double bet, take 1 card

**Payouts:**
Win = 2x | Blackjack = 2.5x | Push = Refund
""",
        "min_bet": 0.50,
        "max_bet": 200,
    },
    "roulette": {
        "name": "🎡 Roulette",
        "description": "Bet on number, color, or range!",
        "how_to_play": """
**How to Play:**
1. Choose your bet type
2. Place your bet
3. Wheel spins!

**Bet Types:**
🔴 Red = 2x | ⚫ Black = 2x
🟢 Green (0) = 36x
1-12 = 3x | 13-24 = 3x | 25-36 = 3x
1-18 = 2x | 19-36 = 2x
""",
        "min_bet": 0.10,
        "max_bet": 500,
    },
    "coinflip": {
        "name": "🪙 Coin Flip",
        "description": "Heads or Tails — simple 2x payout!",
        "how_to_play": """
**How to Play:**
1. Choose Heads or Tails
2. Coin flips
3. Match = Win 2x!

**Payouts:**
Correct = 2x | Wrong = Lose
""",
        "min_bet": 0.10,
        "max_bet": 100,
    },
    "mines": {
        "name": "💣 Mines",
        "description": "Find gems, avoid mines! Cash out anytime!",
        "how_to_play": """
**How to Play:**
1. Grid has hidden gems and mines
2. Tap tiles to reveal
3. Gem = Multiplier increases
4. Mine = Game over!

**Strategy:**
• More mines = Higher risk = Higher reward
• Cash out anytime to secure winnings
""",
        "min_bet": 0.10,
        "max_bet": 100,
    },
    "plinko": {
        "name": "📌 Plinko",
        "description": "Drop the ball — land on multiplier!",
        "how_to_play": """
**How to Play:**
1. Place your bet
2. Ball drops through pegs
3. Lands on multiplier slot

**Multipliers:**
Edge slots = 10x
Middle slots = 0.5x - 1.5x
""",
        "min_bet": 0.10,
        "max_bet": 200,
    },
    "wheel": {
        "name": "🎡 Wheel",
        "description": "Spin the wheel of fortune!",
        "how_to_play": """
**How to Play:**
1. Place your bet
2. Spin the wheel
3. Land on multiplier!

**Segments:**
🍒 2x | 🍋 3x | 🍊 5x | 🍇 10x
🔔 0x | 💎 15x | ⭐ 25x | 7️⃣ 50x
""",
        "min_bet": 0.10,
        "max_bet": 200,
    },
    "keno": {
        "name": "🎱 Keno",
        "description": "Pick numbers, match to win!",
        "how_to_play": """
**How to Play:**
1. Pick 1-10 numbers (1-40)
2. 10 numbers drawn
3. More matches = Bigger win!

**Payouts (10 picked):**
10/10 = 5000x | 9/10 = 500x
8/10 = 100x | 7/10 = 20x
6/10 = 5x | 5/10 = 1x
""",
        "min_bet": 0.10,
        "max_bet": 100,
    },
    "hilo": {
        "name": "🔺 Hi-Lo",
        "description": "Higher or lower? Build your streak!",
        "how_to_play": """
**How to Play:**
1. Card is shown
2. Guess: Next card Higher or Lower?
3. Correct = Multiplier increases!
4. Wrong = Game over

**Strategy:**
• Build streak for bigger multiplier
• Cash out anytime
""",
        "min_bet": 0.10,
        "max_bet": 200,
    },
    "baccarat": {
        "name": "🂡 Baccarat",
        "description": "Player vs Banker — classic card game!",
        "how_to_play": """
**How to Play:**
1. Bet on Player, Banker, or Tie
2. Cards dealt
3. Closest to 9 wins

**Payouts:**
Player = 2x | Banker = 1.95x | Tie = 8x
""",
        "min_bet": 0.50,
        "max_bet": 500,
    },
    "lottery": {
        "name": "🎟️ Lottery",
        "description": "Buy ticket, win big prizes!",
        "how_to_play": """
**How to Play:**
1. Buy a ticket ($1-$50)
2. 6 random numbers generated
3. Match to win!

**Prizes:**
6/6 = $10,000 | 5/6 = $500
4/6 = $50 | 3/6 = $5
""",
        "min_bet": 1,
        "max_bet": 50,
    },
    "rps": {
        "name": "✊ RPS",
        "description": "Rock Paper Scissors — 2x payout!",
        "how_to_play": """
**How to Play:**
1. Choose Rock, Paper, or Scissors
2. Bot chooses
3. Standard rules apply

**Payouts:**
Win = 2x | Draw = Refund | Lose = 0x
""",
        "min_bet": 0.10,
        "max_bet": 100,
    },
    "limbo": {
        "name": "🎯 Limbo",
        "description": "Pick target — roll above to win!",
        "how_to_play": """
**How to Play:**
1. Choose target multiplier
2. Roll happens
3. Above target = Win!

**Example:**
Target: 2x
Roll: 3.5x = ✅ WIN
Roll: 1.2x = ❌ LOSE
""",
        "min_bet": 0.10,
        "max_bet": 200,
    },
    "tower": {
        "name": "🏗️ Tower",
        "description": "Climb floors, avoid danger!",
        "how_to_play": """
**How to Play:**
1. Each floor has 3 tiles (1 danger)
2. Pick a tile
3. Safe = Climb higher = Multiplier up
4. Danger = Game over!

**Strategy:**
• Cash out anytime
• Higher floor = Bigger multiplier
""",
        "min_bet": 0.10,
        "max_bet": 100,
    },
    "double": {
        "name": "🔴 Double",
        "description": "Red/Black/Green color bet!",
        "how_to_play": """
**How to Play:**
1. Choose Red, Black, or Green
2. Color is drawn
3. Match = Win!

**Payouts:**
🔴 Red = 2x (47.5%)
⚫ Black = 2x (47.5%)
🟢 Green = 14x (5%)
""",
        "min_bet": 0.10,
        "max_bet": 500,
    },
    "adder": {
        "name": "➕ Adder",
        "description": "Add numbers — get close to 21!",
        "how_to_play": """
**How to Play:**
1. Number appears (1-10)
2. Choose: Add or Stop
3. Get close to 21 without going over

**Payouts:**
Closer to 21 = Higher multiplier
Over 21 = Bust = Lose
""",
        "min_bet": 0.10,
        "max_bet": 100,
    },
}

# ============================================
# GAME RESULT MESSAGES
# ============================================

WIN_MESSAGE = """
🎉 **YOU WON!**

{game_name}

Bet: **${bet:.2f}**
Multiplier: **{multiplier}x**
Won: **+${profit:.2f}**

💰 Balance: **${balance:.2f}**
"""

LOSE_MESSAGE = """
😢 **You Lost**

{game_name}

Bet: **${bet:.2f}**
Lost: **-${loss:.2f}**

💰 Balance: **${balance:.2f}**

Better luck next time! 🍀
"""

DRAW_MESSAGE = """
🤝 **Draw!**

{game_name}

Bet: **${bet:.2f}**
Result: **Refunded**

💰 Balance: **${balance:.2f}**
"""

# ============================================
# DEPOSIT MESSAGES
# ============================================

DEPOSIT_MENU = """
💰 **Deposit Crypto**

Select a cryptocurrency:

⚡ **Instant confirmation**
💳 **Zero platform fees**
🔒 **Secure & Anonymous**

Min deposit: **$1 equivalent**
"""

DEPOSIT_INSTRUCTIONS = """
💰 **Deposit {coin}**

Send **{coin}** to this address:

`{address}`

━━━━━━━━━━━━━━━━━━━━

⚡ **Network:** {network}
💵 **Min deposit:** $1 equivalent
🔄 **Confirmations:** 1-3 blocks
💳 **Fee:** Zero

━━━━━━━━━━━━━━━━━━━━

⚠️ **Important:**
• Send only **{coin}** to this address
• Sending other coins may result in loss
• Balance updates automatically after confirmation

📞 Need help? Contact support
"""

DEPOSIT_CONFIRMED = """
✅ **Deposit Confirmed!**

Amount: **+${amount:.2f}**
TX: `{tx_hash}`

💰 New Balance: **${balance:.2f}**

Ready to play! 🎰
"""

# ============================================
# WITHDRAWAL MESSAGES
# ============================================

WITHDRAW_MENU = """
💸 **Withdraw Winnings**

💰 Available: **${balance:.2f}**

━━━━━━━━━━━━━━━━━━━━

To withdraw, send:

`/withdraw AMOUNT ADDRESS`

**Example:**
`/withdraw 50 TRC20_ADDRESS_HERE`

━━━━━━━━━━━━━━━━━━━━

⚡ **Min withdrawal:** $10
🕐 **Processing:** 1-24 hours
💳 **Network fee:** Deducted from amount
"""

WITHDRAW_SUBMITTED = """
✅ **Withdrawal Requested**

Amount: **${amount:.2f}**
Address: `{address}`
Status: **Pending Review**

━━━━━━━━━━━━━━━━━━━━

🕐 Processing time: 1-24 hours
📱 You'll be notified when processed

📞 Questions? Contact support
"""

WITHDRAW_APPROVED = """
✅ **Withdrawal Processed!**

Amount: **${amount:.2f}**
TX: `{tx_hash}`

Sent to: `{address}`

Thank you for playing! 🎰
"""

WITHDRAW_REJECTED = """
❌ **Withdrawal Rejected**

Amount: **${amount:.2f}**
Reason: {reason}

Your balance has been refunded.

📞 Contact support for assistance
"""

# ============================================
# BALANCE MESSAGE
# ============================================

BALANCE_TEXT = """
💰 **Your Wallet**

━━━━━━━━━━━━━━━━━━━━

💵 Balance: **${balance:.2f}**
📥 Total Deposited: **${deposited:.2f}**
📤 Total Withdrawn: **${withdrawn:.2f}**
🎰 Total Wagered: **${wagered:.2f}**

━━━━━━━━━━━━━━━━━━━━

📊 **Quick Stats:**
Games Played: {games_played}
Win Rate: {win_rate}%
Biggest Win: ${biggest_win:.2f}

━━━━━━━━━━━━━━━━━━━━

/actions — Quick actions
"""

# ============================================
# REFERRAL MESSAGES
# ============================================

REFERRAL_TEXT = """
🤝 **Referral Program**

━━━━━━━━━━━━━━━━━━━━

🔗 **Your Referral Link:**
`{link}`

👥 **Your Referrals:** {count}
💵 **Earned:** ${earned:.2f}

━━━━━━━━━━━━━━━━━━━━

**How It Works:**
1. Share your link with friends
2. They join and play
3. You earn **10% of their first deposit**
4. You earn **5% of their losses (lifetime)**

━━━━━━━━━━━━━━━━━━━━

💡 **Tips:**
• Share on social media
• Post in Telegram groups
• Tell your friends
"""

# ============================================
# AGENT MESSAGES
# ============================================

AGENT_REGISTER = """
🎉 **Agent Registration Complete!**

━━━━━━━━━━━━━━━━━━━━

🆔 Your Agent Code: **`{code}`**
👤 Username: @{username}

━━━━━━━━━━━━━━━━━━━━

⚠️ **Not Active Yet!**

To start earning, buy a package:

🟢 **Starter** — $100 (10% commission)
🔵 **Pro** — $500 (15% commission)
🟡 **Elite** — $2,000 (20% commission)
🔴 **VIP** — $5,000 (25% commission)

━━━━━━━━━━━━━━━━━━━━

📦 /buy_package — View & Buy Packages
"""

AGENT_DASHBOARD = """
📊 **Agent Dashboard**

━━━━━━━━━━━━━━━━━━━━

🆔 Code: **`{code}`**
📦 Package: **{package}**
💰 Commission Rate: **{rate}%**

━━━━━━━━━━━━━━━━━━━━

💵 **Earnings**
• Direct: **${direct:.2f}**
• Override: **${override:.2f}**
• Available: **${available:.2f}**

👥 **Team**
• Players: **{players}** / {max_players}
• Sub-Agents: **{sub_agents}** / {max_subs}
• Total Wagered: **${wagered:.2f}**

━━━━━━━━━━━━━━━━━━━━

📈 **Recent Commissions:**
{recent_commissions}
"""

AGENT_PACKAGE_INFO = """
📦 **Agent Packages**

━━━━━━━━━━━━━━━━━━━━

🟢 **Starter — $100**
• 10% commission on player losses
• Up to 50 players
• Basic dashboard
• No sub-agents

🔵 **Pro — $500**
• 15% commission on player losses
• Up to 200 players
• 5 sub-agents allowed
• Advanced analytics

🟡 **Elite — $2,000**
• 20% commission on player losses
• Unlimited players
• 50 sub-agents allowed
• Full dashboard + priority support

🔴 **VIP — $5,000**
• 25% commission on player losses
• Unlimited everything
• Unlimited sub-agents
• White-label + dedicated support

━━━━━━━━━━━━━━━━━━━━

💰 **How You Earn:**
Player bets $100 → House edge 5% → $5 profit
Your commission (10-25%): $0.50 - $1.25 per $100 bet

━━━━━━━━━━━━━━━━━━━━

💳 /buy_package — Purchase Now
"""

# ============================================
# HELP MESSAGE
# ============================================

HELP_TEXT = """
ℹ️ **BetVortex Casino — Help**

━━━━━━━━━━━━━━━━━━━━

🎮 **Games (18 Available):**
🎰 Slots — Spin & match symbols
🎲 Dice — Predict over/under
✈️ Crash — Cash out before crash
🃏 Blackjack — Get 21
🎡 Roulette — Bet on color/number
🪙 Coin Flip — Heads or Tails
💣 Mines — Find gems, avoid mines
📌 Plinko — Drop ball, win prizes
🎡 Wheel — Spin the wheel
🎱 Keno — Pick lucky numbers
🔺 Hi-Lo — Higher or lower
🂡 Baccarat — Player vs Banker
🎟️ Lottery — Win big prizes
✊ RPS — Rock Paper Scissors
🎯 Limbo — Roll above target
🏗️ Tower — Climb floors
🔴 Double — Color bet
➕ Adder — Add to 21

━━━━━━━━━━━━━━━━━━━━

💰 **Commands:**
/start — Main menu
/balance — Check balance
/deposit — Add crypto
/withdraw — Cash out
/games — View all games
/referral — Earn by referring
/agent — Become an agent
/claim CODE — Claim promo code
/limits — Set gambling limits
/exclude — Self-exclude
/help — This message

━━━━━━━━━━━━━━━━━━━━

🤝 **Earn Money:**
/referral — Get referral link
/agent — Register as agent
/buy_package — Buy agent package
/agent_dashboard — Agent stats

━━━━━━━━━━━━━━━━━━━━

📞 **Support:**
@YourSupportUsername

🌐 **Website:**
https://betvortex.io
"""

# ============================================
# RESPONSIBLE GAMBLING
# ============================================

LIMITS_MENU = """
⚙️ **Responsible Gambling**

Set limits to control your gambling:

━━━━━━━━━━━━━━━━━━━━

**Current Limits:**
💰 Daily Deposit: {deposit_limit}
📉 Daily Loss: {loss_limit}
🎰 Daily Bet: {bet_limit}
⏰ Session Time: {time_limit}
🚫 Self-Excluded: {excluded}

━━━━━━━━━━━━━━━━━━━━

**Set a Limit:**
"""

SELF_EXCLUDE_CONFIRMED = """
🚫 **Self-Exclusion Activated**

Duration: **{days} days**
Until: **{until}**

━━━━━━━━━━━━━━━━━━━━

You won't be able to play until then.

Take care of yourself! 💚

If you need help with gambling addiction:
📞 GamCare: www.gamcare.org.uk
📞 Gamblers Anonymous: www.gamblersanonymous.org
"""

# ============================================
# ERROR MESSAGES
# ============================================

ERROR_INSUFFICIENT_BALANCE = """
❌ **Insufficient Balance**

Your balance: **${balance:.2f}**
Required: **${required:.2f}**

💰 /deposit — Add funds
"""

ERROR_GAME_DISABLED = """
❌ **Game Temporarily Unavailable**

This game is currently disabled.
Please try another game or check back later.

🎮 /games — View available games
"""

ERROR_INVALID_AMOUNT = """
❌ **Invalid Amount**

Please enter a valid bet amount.

Min: ${min:.2f}
Max: ${max:.2f}

Example: `{example}`
"""

ERROR_SELF_EXCLUDED = """
🚫 **Account Restricted**

You have self-excluded until **{until}**.

If you need help:
📞 GamCare: www.gamcare.org.uk
"""

# ============================================
# ADMIN MESSAGES
# ============================================

ADMIN_PANEL = """
👑 **Admin Panel**

━━━━━━━━━━━━━━━━━━━━

📊 **Platform Stats:**
👥 Total Users: {users}
💰 Total Balance: ${balance:.2f}
🎰 Total Wagered: ${wagered:.2f}
💵 Total Revenue: ${revenue:.2f}
📥 Pending Deposits: {deposits}
📤 Pending Withdrawals: {withdrawals}
🤝 Active Agents: {agents}

━━━━━━━━━━━━━━━━━━━━

**Commands:**
/games — Game control panel
/admin_agents — View agents
/promo CODE AMT — Create promo
/approve ID AMT — Approve withdrawal
/broadcast MSG — Message all users
/stats — Detailed statistics
"""

# ============================================
# PROMO MESSAGES
# ============================================

PROMO_CLAIMED = """
🎁 **Promo Code Claimed!**

Code: **{code}**
Bonus: **+${amount:.2f}**

💰 New Balance: **${balance:.2f}**

Play now! 🎰
"""

PROMO_INVALID = """
❌ **Invalid Promo Code**

Code: **{code}**

This code is invalid or expired.

💡 Check the code and try again
"""

# ============================================
# BET CONFIRMATION
# ============================================

BET_PLACED = """
🎰 **Bet Placed!**

Game: {game}
Amount: **${bet:.2f}**

Good luck! 🍀
"""

# ============================================
# LOADING / PROCESSING
# ============================================

PROCESSING = """
⏳ **Processing...**

Please wait.
"""

SPINNING = """
🎰 **Spinning...**

🎲🎲🎲
"""

# ============================================
# GAME SPECIFIC MESSAGES
# ============================================

SLOTS_SPIN = """
🎰 **SLOT MACHINE**

╔═══════════════╗
║   {r1} │ {r2} │ {r3}   ║
╚═══════════════╝

Bet: **${bet:.2f}**
Multiplier: **{mult}x**
{result}

💰 Balance: **${balance:.2f}**
"""

CRASH_GAME = """
✈️ **CRASH GAME**

🚀 Current Multiplier: **{multiplier:.2f}x**

Bet: **${bet:.2f}**
💰 Balance: **${balance:.2f}**

Cash out before it crashes!
"""

CRASH_RESULT = """
✈️ **Crash Result**

💥 Crashed at: **{crash_point:.2f}x**
💰 You cashed out at: **{cashout:.2f}x**

Bet: **${bet:.2f}**
{result}

💰 Balance: **${balance:.2f}**
"""

BLACKJACK_HAND = """
🃏 **BLACKJACK**

Your Hand: {player_cards} = **{player_val}**
Dealer: {dealer_cards} = **{dealer_val}**

Bet: **${bet:.2f}**

{action}
"""

DICE_ROLL = """
🎲 **DICE RESULT**

🎯 Your Prediction: **{prediction}**
🎲 Rolled: **{roll}/100**

Bet: **${bet:.2f}**
{result}

💰 Balance: **${balance:.2f}**
"""

ROULETTE_RESULT = """
🎡 **ROULETTE RESULT**

{color_emoji} **{number}** ({color})

Your Bet: **{bet_type}**
Bet: **${bet:.2f}**
{result}

💰 Balance: **${balance:.2f}**
"""

MINES_BOARD = """
💣 **MINES**

Bet: **${bet:.2f}** | Mines: **{mines}**
Gems Found: **{found}/{safe}**
Multiplier: **{mult:.2f}x**

{board}

{action}
"""

WHEEL_RESULT = """
🎡 **WHEEL OF FORTUNE**

🎯 Landed on: {segment}
Multiplier: **{mult}x**

Bet: **${bet:.2f}**
{result}

💰 Balance: **${balance:.2f}**
"""

KENO_RESULT = """
🎱 **KENO RESULT**

Your Numbers: **{picked}**
Drawn: **{drawn}**

Matches: **{matches}/{total}**

Bet: **${bet:.2f}**
Multiplier: **{mult}x**
{result}

💰 Balance: **${balance:.2f}**
"""

HILO_ROUND = """
🔺 **HI-LO**

Current Card: **{card}**
Streak: **{streak}**
Multiplier: **{mult:.2f}x**

Bet: **${bet:.2f}**

Higher or Lower?
"""

BACCARAT_RESULT = """
🂡 **BACCARAT RESULT**

👤 Player: {player_cards} = **{player_val}**
🏦 Banker: {banker_cards} = **{banker_val}**

Winner: **{winner}**
Your Bet: **{choice}**

Bet: **${bet:.2f}**
{result}

💰 Balance: **${balance:.2f}**
"""

COINFLIP_RESULT = """
🪙 **COIN FLIP RESULT**

{coin_emoji} Result: **{result}**
Your Choice: **{choice}**

Bet: **${bet:.2f}**
{outcome}

💰 Balance: **${balance:.2f}**
"""

LOTTERY_RESULT = """
🎟️ **LOTTERY RESULT**

Your Numbers: **{numbers}**
Drawn: **{drawn}**

Matches: **{matches}/6**

Ticket: **${bet:.2f}**
{result}

💰 Balance: **${balance:.2f}**
"""

RPS_RESULT = """
✊✌️🖐️ **ROCK PAPER SCISSORS**

You: {player_emoji} **{player}**
Bot: {bot_emoji} **{bot}**

{result}

Bet: **${bet:.2f}**
{outcome}

💰 Balance: **${balance:.2f}**
"""

LIMBO_RESULT = """
🎯 **LIMBO RESULT**

🎯 Target: **{target:.2f}x**
🎲 Rolled: **{roll:.2f}x**

{result}

Bet: **${bet:.2f}**
{outcome}

💰 Balance: **${balance:.2f}**
"""

TOWER_FLOOR = """
🏗️ **TOWER**

Floor: **{floor}/8**
Multiplier: **{mult:.2f}x**

Bet: **${bet:.2f}**

{action}
"""

DOUBLE_RESULT = """
🔴⚫🟢 **DOUBLE RESULT**

{color_emoji} **{color}**

Your Bet: **{choice}**
Bet: **${bet:.2f}**
{result}

💰 Balance: **${balance:.2f}**
"""

ADDER_ROUND = """
➕ **ADDER**

Numbers: {numbers} = **{total}**
Multiplier: **{mult:.2f}x**

Bet: **${bet:.2f}**

Add or Stop?
"""

# ============================================
# BUTTON LABELS
# ============================================

BUTTONS = {
    # Navigation
    "back": "🔙 Back",
    "main_menu": "🏠 Main Menu",
    "cancel": "❌ Cancel",
    
    # Games
    "spin": "🎰 Spin",
    "roll": "🎲 Roll",
    "hit": "🃏 Hit",
    "stand": "✋ Stand",
    "double_down": "💰 Double",
    "cashout": "💰 Cash Out",
    "play_again": "🔄 Play Again",
    
    # Bets
    "bet_1": "$1",
    "bet_5": "$5",
    "bet_10": "$10",
    "bet_25": "$25",
    "bet_50": "$50",
    "bet_100": "$100",
    "custom_bet": "✏️ Custom Amount",
    
    # Dice
    "over_50": "Over 50 (2x)",
    "under_50": "Under 50 (2x)",
    "over_75": "Over 75 (4x)",
    "under_25": "Under 25 (4x)",
    "over_90": "Over 90 (10x)",
    "under_10": "Under 10 (10x)",
    
    # Roulette
    "red": "🔴 Red (2x)",
    "black": "⚫ Black (2x)",
    "green": "🟢 Green (36x)",
    "first_12": "1-12 (3x)",
    "second_12": "13-24 (3x)",
    "third_12": "25-36 (3x)",
    "low": "1-18 (2x)",
    "high": "19-36 (2x)",
    
    # Coin Flip
    "heads": "👑 Heads",
    "tails": "🦅 Tails",
    
    # Baccarat
    "player": "👤 Player (2x)",
    "banker": "🏦 Banker (1.95x)",
    "tie": "🤝 Tie (8x)",
    
    # Hi-Lo
    "higher": "🔺 Higher",
    "lower": "🔻 Lower",
    
    # RPS
    "rock": "✊ Rock",
    "scissors": "✌️ Scissors",
    "paper": "🖐️ Paper",
    
    # Crash
    "let_ride": "🚀 Let it Ride!",
    
    # Mines/Tower
    "tile_1": "⬜ 1",
    "tile_2": "⬜ 2",
    "tile_3": "⬜ 3",
    
    # Adder
    "add": "➕ Add",
    "stop": "🛑 Stop",
    
    # Double
    "double_red": "🔴 Red (2x)",
    "double_black": "⚫ Black (2x)",
    "double_green": "🟢 Green (14x)",
    
    # Wallet
    "deposit_btc": "₿ BTC",
    "deposit_eth": "Ξ ETH",
    "deposit_usdt": "₮ USDT",
    "deposit_ltc": "Ł LTC",
    "deposit_trx": "TRX",
    "deposit_doge": "Ð DOGE",
    
    # Agent
    "view_packages": "📦 View Packages",
    "buy_starter": "🟢 Starter $100",
    "buy_pro": "🔵 Pro $500",
    "buy_elite": "🟡 Elite $2,000",
    "buy_vip": "🔴 VIP $5,000",
    "pay_crypto": "₿ Pay with Crypto",
    "pay_manual": "💳 Manual Payment",
    
    # Agent Dashboard
    "my_team": "👥 My Team",
    "withdraw_commission": "💸 Withdraw",
    "agent_stats": "📊 Stats",
    "share_link": "📤 Share Link",
    "upgrade_package": "⬆️ Upgrade",
    
    # Limits
    "limit_deposit": "💰 Daily Deposit Limit",
    "limit_loss": "📉 Daily Loss Limit",
    "limit_bet": "🎰 Daily Bet Limit",
    "limit_time": "⏰ Session Time Limit",
    "self_exclude": "🚫 Self-Exclude",
}
