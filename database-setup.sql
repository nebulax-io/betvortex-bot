-- ============================================
-- BETVORTEX DATABASE - একসাথে সব tables
-- Supabase SQL Editor এ paste করুন এবং Run করুন
-- ============================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    balance DECIMAL(15,2) DEFAULT 0,
    total_deposited DECIMAL(15,2) DEFAULT 0,
    total_withdrawn DECIMAL(15,2) DEFAULT 0,
    total_wagered DECIMAL(15,2) DEFAULT 0,
    referral_code TEXT UNIQUE,
    referred_by BIGINT,
    is_banned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bets table
CREATE TABLE IF NOT EXISTS bets (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(telegram_id),
    game TEXT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    multiplier DECIMAL(10,2),
    result TEXT,
    profit DECIMAL(15,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(telegram_id),
    type TEXT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    status TEXT DEFAULT 'pending',
    tx_hash TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
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
    created_at TIMESTAMPTZ DEFAULT NOW(),
    activated_at TIMESTAMPTZ
);

-- Agent commissions
CREATE TABLE IF NOT EXISTS agent_commissions (
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
CREATE TABLE IF NOT EXISTS agent_withdrawals (
    id BIGSERIAL PRIMARY KEY,
    agent_id BIGINT REFERENCES agents(telegram_id),
    amount DECIMAL(15,2),
    status TEXT DEFAULT 'pending',
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Referrals
CREATE TABLE IF NOT EXISTS referrals (
    id BIGSERIAL PRIMARY KEY,
    referrer_id BIGINT REFERENCES users(telegram_id),
    referred_id BIGINT REFERENCES users(telegram_id),
    commission_earned DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Game settings
CREATE TABLE IF NOT EXISTS game_settings (
    game TEXT PRIMARY KEY,
    enabled BOOLEAN DEFAULT TRUE,
    min_bet DECIMAL(15,2) DEFAULT 0.10,
    max_bet DECIMAL(15,2) DEFAULT 100,
    house_edge DECIMAL(5,4) DEFAULT 0.05,
    rtp DECIMAL(5,4) DEFAULT 0.95,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by BIGINT
);

-- User limits
CREATE TABLE IF NOT EXISTS user_limits (
    user_id BIGINT PRIMARY KEY,
    daily_deposit_limit DECIMAL(15,2),
    daily_loss_limit DECIMAL(15,2),
    daily_bet_limit DECIMAL(15,2),
    session_time_limit INT,
    self_excluded BOOLEAN DEFAULT FALSE,
    exclude_until TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Game promos
CREATE TABLE IF NOT EXISTS game_promos (
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

-- Agent purchases
CREATE TABLE IF NOT EXISTS agent_purchases (
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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_telegram ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_referral ON users(referral_code);
CREATE INDEX IF NOT EXISTS idx_bets_user ON bets(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_agents_code ON agents(agent_code);
CREATE INDEX IF NOT EXISTS idx_agents_parent ON agents(parent_agent_id);

-- Success message
SELECT 'BetVortex Database Setup Complete! 🎰' as status;
