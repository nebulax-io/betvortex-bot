-- ============================================
-- BETVORTEX: Atomic Balance Update Function
-- Run this in Supabase SQL Editor AFTER the main setup
-- ============================================

-- Atomic balance update (no race condition)
CREATE OR REPLACE FUNCTION atomic_balance_update(p_telegram_id BIGINT, p_amount DECIMAL)
RETURNS DECIMAL AS $$
DECLARE
    new_balance DECIMAL;
BEGIN
    UPDATE users 
    SET balance = balance + p_amount
    WHERE telegram_id = p_telegram_id
    RETURNING balance INTO new_balance;
    
    IF new_balance IS NULL THEN
        RAISE EXCEPTION 'User not found: %', p_telegram_id;
    END IF;
    
    -- Prevent negative balance
    IF new_balance < 0 THEN
        UPDATE users SET balance = 0 WHERE telegram_id = p_telegram_id;
        RETURN 0;
    END IF;
    
    RETURN new_balance;
END;
$$ LANGUAGE plpgsql;

-- Verify
SELECT 'atomic_balance_update function created! ✅' as status;
