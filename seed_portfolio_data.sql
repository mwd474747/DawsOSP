-- =============================================================================
-- DawsOS Portfolio Database Seed Script
-- Purpose: Seed comprehensive transaction and holdings data for admin user
-- User: michael@dawsos.com
-- Portfolio: 64ff3be6-0ed1-4990-a32b-4ded17f0320c
-- Date: October 30, 2025
-- =============================================================================

-- Clear existing data for this portfolio (optional, comment out if you want to append)
DELETE FROM holdings WHERE portfolio_id = '64ff3be6-0ed1-4990-a32b-4ded17f0320c';
DELETE FROM lots WHERE portfolio_id = '64ff3be6-0ed1-4990-a32b-4ded17f0320c';
DELETE FROM transactions WHERE portfolio_id = '64ff3be6-0ed1-4990-a32b-4ded17f0320c';

-- =============================================================================
-- 1. INSERT SECURITIES (Skip BRK.B as it already exists)
-- =============================================================================

INSERT INTO securities (id, symbol, name, security_type, exchange, trading_currency, dividend_currency, domicile_country, active)
VALUES
    (gen_random_uuid(), 'CNR', 'Canadian National Railway', 'equity', 'TSX', 'CAD', 'CAD', 'CA', true),
    (gen_random_uuid(), 'BAM', 'Brookfield Asset Management', 'equity', 'NYSE', 'USD', 'USD', 'CA', true),
    (gen_random_uuid(), 'BBUC', 'BlackRock USD Cash Fund', 'etf', 'NYSE', 'USD', 'USD', 'US', true),
    (gen_random_uuid(), 'BTI', 'British American Tobacco', 'equity', 'NYSE', 'USD', 'USD', 'GB', true),
    (gen_random_uuid(), 'EVO', 'Evolution Gaming', 'equity', 'NASDAQ', 'EUR', 'EUR', 'SE', true),
    (gen_random_uuid(), 'NKE', 'Nike Inc', 'equity', 'NYSE', 'USD', 'USD', 'US', true),
    (gen_random_uuid(), 'PYPL', 'PayPal Holdings', 'equity', 'NASDAQ', 'USD', 'USD', 'US', true),
    (gen_random_uuid(), 'HHC', 'Howard Hughes Corporation', 'equity', 'NYSE', 'USD', 'USD', 'US', true)
ON CONFLICT (symbol) DO NOTHING;

-- =============================================================================
-- 2. INSERT TRANSACTIONS (Historical, dating back 1-2 years)
-- =============================================================================

-- CNR - Canadian National Railway (CAD)
-- Initial purchase - Jan 2024
INSERT INTO transactions (portfolio_id, transaction_type, security_id, symbol, transaction_date, settlement_date, quantity, price, amount, currency, fee, source)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BUY', 
     (SELECT id FROM securities WHERE symbol = 'CNR'), 'CNR', '2024-01-15', '2024-01-17', 
     200, 155.00, -31000.00, 'CAD', 10.00, 'manual'),
    
    -- Dividend payments
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'DIVIDEND', 
     (SELECT id FROM securities WHERE symbol = 'CNR'), 'CNR', '2024-03-31', '2024-03-31', 
     NULL, NULL, 158.00, 'CAD', 0.00, 'manual'),
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'DIVIDEND', 
     (SELECT id FROM securities WHERE symbol = 'CNR'), 'CNR', '2024-06-30', '2024-06-30', 
     NULL, NULL, 158.00, 'CAD', 0.00, 'manual'),
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'DIVIDEND', 
     (SELECT id FROM securities WHERE symbol = 'CNR'), 'CNR', '2024-09-30', '2024-09-30', 
     NULL, NULL, 158.00, 'CAD', 0.00, 'manual'),
    
    -- Additional purchase - Aug 2024
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BUY', 
     (SELECT id FROM securities WHERE symbol = 'CNR'), 'CNR', '2024-08-10', '2024-08-12', 
     100, 162.00, -16200.00, 'CAD', 10.00, 'manual');

-- BAM - Brookfield Asset Management
-- Initial purchase - Feb 2024
INSERT INTO transactions (portfolio_id, transaction_type, security_id, symbol, transaction_date, settlement_date, quantity, price, amount, currency, fee, source)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BUY', 
     (SELECT id FROM securities WHERE symbol = 'BAM'), 'BAM', '2024-02-05', '2024-02-07', 
     500, 42.00, -21000.00, 'USD', 10.00, 'manual'),
    
    -- Additional purchase - May 2024
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BUY', 
     (SELECT id FROM securities WHERE symbol = 'BAM'), 'BAM', '2024-05-20', '2024-05-22', 
     300, 45.00, -13500.00, 'USD', 10.00, 'manual'),
    
    -- Partial sell - Sept 2024
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'SELL', 
     (SELECT id FROM securities WHERE symbol = 'BAM'), 'BAM', '2024-09-15', '2024-09-17', 
     200, 52.00, 10400.00, 'USD', 10.00, 'manual'),
    
    -- Dividend
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'DIVIDEND', 
     (SELECT id FROM securities WHERE symbol = 'BAM'), 'BAM', '2024-06-15', '2024-06-15', 
     NULL, NULL, 180.00, 'USD', 0.00, 'manual');

-- BBUC - BlackRock USD Cash Fund (Money Market)
-- Large position for cash management
INSERT INTO transactions (portfolio_id, transaction_type, security_id, symbol, transaction_date, settlement_date, quantity, price, amount, currency, fee, source)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BUY', 
     (SELECT id FROM securities WHERE symbol = 'BBUC'), 'BBUC', '2024-01-10', '2024-01-10', 
     50000, 1.00, -50000.00, 'USD', 0.00, 'manual'),
    
    -- Monthly interest/dividends
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'DIVIDEND', 
     (SELECT id FROM securities WHERE symbol = 'BBUC'), 'BBUC', '2024-02-29', '2024-02-29', 
     NULL, NULL, 208.33, 'USD', 0.00, 'manual'),
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'DIVIDEND', 
     (SELECT id FROM securities WHERE symbol = 'BBUC'), 'BBUC', '2024-03-31', '2024-03-31', 
     NULL, NULL, 208.33, 'USD', 0.00, 'manual'),
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'DIVIDEND', 
     (SELECT id FROM securities WHERE symbol = 'BBUC'), 'BBUC', '2024-04-30', '2024-04-30', 
     NULL, NULL, 208.33, 'USD', 0.00, 'manual');

-- BRK.B - Berkshire Hathaway B
-- Large value position
INSERT INTO transactions (portfolio_id, transaction_type, security_id, symbol, transaction_date, settlement_date, quantity, price, amount, currency, fee, source)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BUY', 
     (SELECT id FROM securities WHERE symbol = 'BRK.B'), 'BRK.B', '2023-12-01', '2023-12-03', 
     100, 330.00, -33000.00, 'USD', 10.00, 'manual'),
    
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BUY', 
     (SELECT id FROM securities WHERE symbol = 'BRK.B'), 'BRK.B', '2024-03-15', '2024-03-17', 
     50, 345.00, -17250.00, 'USD', 10.00, 'manual'),
    
    -- Small sell to lock in gains
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'SELL', 
     (SELECT id FROM securities WHERE symbol = 'BRK.B'), 'BRK.B', '2024-10-01', '2024-10-03', 
     20, 365.00, 7300.00, 'USD', 10.00, 'manual');

-- BTI - British American Tobacco (High dividend yield)
INSERT INTO transactions (portfolio_id, transaction_type, security_id, symbol, transaction_date, settlement_date, quantity, price, amount, currency, fee, source)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BUY', 
     (SELECT id FROM securities WHERE symbol = 'BTI'), 'BTI', '2024-01-20', '2024-01-22', 
     500, 32.00, -16000.00, 'USD', 10.00, 'manual'),
    
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BUY', 
     (SELECT id FROM securities WHERE symbol = 'BTI'), 'BTI', '2024-04-15', '2024-04-17', 
     300, 33.50, -10050.00, 'USD', 10.00, 'manual'),
    
    -- Quarterly dividends (high yield ~8%)
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'DIVIDEND', 
     (SELECT id FROM securities WHERE symbol = 'BTI'), 'BTI', '2024-02-15', '2024-02-15', 
     NULL, NULL, 360.00, 'USD', 0.00, 'manual'),
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'DIVIDEND', 
     (SELECT id FROM securities WHERE symbol = 'BTI'), 'BTI', '2024-05-15', '2024-05-15', 
     NULL, NULL, 360.00, 'USD', 0.00, 'manual'),
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'DIVIDEND', 
     (SELECT id FROM securities WHERE symbol = 'BTI'), 'BTI', '2024-08-15', '2024-08-15', 
     NULL, NULL, 360.00, 'USD', 0.00, 'manual');

-- EVO - Evolution Gaming (EUR denominated)
INSERT INTO transactions (portfolio_id, transaction_type, security_id, symbol, transaction_date, settlement_date, quantity, price, amount, currency, fee, source)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BUY', 
     (SELECT id FROM securities WHERE symbol = 'EVO'), 'EVO', '2024-02-10', '2024-02-12', 
     150, 95.00, -14250.00, 'EUR', 15.00, 'manual'),
    
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BUY', 
     (SELECT id FROM securities WHERE symbol = 'EVO'), 'EVO', '2024-06-05', '2024-06-07', 
     100, 102.00, -10200.00, 'EUR', 15.00, 'manual'),
    
    -- Small dividend
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'DIVIDEND', 
     (SELECT id FROM securities WHERE symbol = 'EVO'), 'EVO', '2024-05-20', '2024-05-20', 
     NULL, NULL, 125.00, 'EUR', 0.00, 'manual');

-- NKE - Nike
INSERT INTO transactions (portfolio_id, transaction_type, security_id, symbol, transaction_date, settlement_date, quantity, price, amount, currency, fee, source)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BUY', 
     (SELECT id FROM securities WHERE symbol = 'NKE'), 'NKE', '2024-03-01', '2024-03-03', 
     200, 95.00, -19000.00, 'USD', 10.00, 'manual'),
    
    -- Sell on weakness
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'SELL', 
     (SELECT id FROM securities WHERE symbol = 'NKE'), 'NKE', '2024-07-15', '2024-07-17', 
     100, 82.00, 8200.00, 'USD', 10.00, 'manual'),
    
    -- Buy back lower
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BUY', 
     (SELECT id FROM securities WHERE symbol = 'NKE'), 'NKE', '2024-09-10', '2024-09-12', 
     150, 73.00, -10950.00, 'USD', 10.00, 'manual'),
    
    -- Quarterly dividends
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'DIVIDEND', 
     (SELECT id FROM securities WHERE symbol = 'NKE'), 'NKE', '2024-04-01', '2024-04-01', 
     NULL, NULL, 74.00, 'USD', 0.00, 'manual'),
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'DIVIDEND', 
     (SELECT id FROM securities WHERE symbol = 'NKE'), 'NKE', '2024-07-01', '2024-07-01', 
     NULL, NULL, 37.00, 'USD', 0.00, 'manual'),
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'DIVIDEND', 
     (SELECT id FROM securities WHERE symbol = 'NKE'), 'NKE', '2024-10-01', '2024-10-01', 
     NULL, NULL, 55.50, 'USD', 0.00, 'manual');

-- PYPL - PayPal (Growth/Tech)
INSERT INTO transactions (portfolio_id, transaction_type, security_id, symbol, transaction_date, settlement_date, quantity, price, amount, currency, fee, source)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BUY', 
     (SELECT id FROM securities WHERE symbol = 'PYPL'), 'PYPL', '2024-01-25', '2024-01-27', 
     300, 55.00, -16500.00, 'USD', 10.00, 'manual'),
    
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BUY', 
     (SELECT id FROM securities WHERE symbol = 'PYPL'), 'PYPL', '2024-05-10', '2024-05-12', 
     200, 58.00, -11600.00, 'USD', 10.00, 'manual'),
    
    -- Partial profit taking
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'SELL', 
     (SELECT id FROM securities WHERE symbol = 'PYPL'), 'PYPL', '2024-08-20', '2024-08-22', 
     100, 65.00, 6500.00, 'USD', 10.00, 'manual');

-- HHC - Howard Hughes Corporation (Real Estate)
INSERT INTO transactions (portfolio_id, transaction_type, security_id, symbol, transaction_date, settlement_date, quantity, price, amount, currency, fee, source)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BUY', 
     (SELECT id FROM securities WHERE symbol = 'HHC'), 'HHC', '2024-02-20', '2024-02-22', 
     200, 65.00, -13000.00, 'USD', 10.00, 'manual'),
    
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BUY', 
     (SELECT id FROM securities WHERE symbol = 'HHC'), 'HHC', '2024-07-05', '2024-07-07', 
     100, 72.00, -7200.00, 'USD', 10.00, 'manual');

-- =============================================================================
-- 3. INSERT LOTS (Tax lot accounting)
-- =============================================================================

-- CNR Lots
INSERT INTO lots (portfolio_id, security_id, symbol, acquisition_date, quantity, cost_basis, cost_basis_per_share, currency, is_open)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', (SELECT id FROM securities WHERE symbol = 'CNR'), 'CNR', 
     '2024-01-15', 200, 31010.00, 155.05, 'CAD', true),
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', (SELECT id FROM securities WHERE symbol = 'CNR'), 'CNR', 
     '2024-08-10', 100, 16210.00, 162.10, 'CAD', true);

-- BAM Lots (600 shares remaining after selling 200)
INSERT INTO lots (portfolio_id, security_id, symbol, acquisition_date, quantity, cost_basis, cost_basis_per_share, currency, is_open)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', (SELECT id FROM securities WHERE symbol = 'BAM'), 'BAM', 
     '2024-02-05', 300, 12610.00, 42.03, 'USD', true),  -- 500 bought, 200 sold
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', (SELECT id FROM securities WHERE symbol = 'BAM'), 'BAM', 
     '2024-05-20', 300, 13510.00, 45.03, 'USD', true);

-- BBUC Lot
INSERT INTO lots (portfolio_id, security_id, symbol, acquisition_date, quantity, cost_basis, cost_basis_per_share, currency, is_open)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', (SELECT id FROM securities WHERE symbol = 'BBUC'), 'BBUC', 
     '2024-01-10', 50000, 50000.00, 1.00, 'USD', true);

-- BRK.B Lots (130 shares remaining after selling 20)
INSERT INTO lots (portfolio_id, security_id, symbol, acquisition_date, quantity, cost_basis, cost_basis_per_share, currency, is_open)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', (SELECT id FROM securities WHERE symbol = 'BRK.B'), 'BRK.B', 
     '2023-12-01', 80, 26410.00, 330.13, 'USD', true),  -- 100 bought, 20 sold
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', (SELECT id FROM securities WHERE symbol = 'BRK.B'), 'BRK.B', 
     '2024-03-15', 50, 17260.00, 345.20, 'USD', true);

-- BTI Lots
INSERT INTO lots (portfolio_id, security_id, symbol, acquisition_date, quantity, cost_basis, cost_basis_per_share, currency, is_open)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', (SELECT id FROM securities WHERE symbol = 'BTI'), 'BTI', 
     '2024-01-20', 500, 16010.00, 32.02, 'USD', true),
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', (SELECT id FROM securities WHERE symbol = 'BTI'), 'BTI', 
     '2024-04-15', 300, 10060.00, 33.53, 'USD', true);

-- EVO Lots
INSERT INTO lots (portfolio_id, security_id, symbol, acquisition_date, quantity, cost_basis, cost_basis_per_share, currency, is_open)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', (SELECT id FROM securities WHERE symbol = 'EVO'), 'EVO', 
     '2024-02-10', 150, 14265.00, 95.10, 'EUR', true),
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', (SELECT id FROM securities WHERE symbol = 'EVO'), 'EVO', 
     '2024-06-05', 100, 10215.00, 102.15, 'EUR', true);

-- NKE Lots (250 shares after trades)
INSERT INTO lots (portfolio_id, security_id, symbol, acquisition_date, quantity, cost_basis, cost_basis_per_share, currency, is_open)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', (SELECT id FROM securities WHERE symbol = 'NKE'), 'NKE', 
     '2024-03-01', 100, 9510.00, 95.10, 'USD', true),  -- 200 bought, 100 sold
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', (SELECT id FROM securities WHERE symbol = 'NKE'), 'NKE', 
     '2024-09-10', 150, 10960.00, 73.07, 'USD', true);

-- PYPL Lots (400 shares after trades)
INSERT INTO lots (portfolio_id, security_id, symbol, acquisition_date, quantity, cost_basis, cost_basis_per_share, currency, is_open)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', (SELECT id FROM securities WHERE symbol = 'PYPL'), 'PYPL', 
     '2024-01-25', 200, 11010.00, 55.05, 'USD', true),  -- 300 bought, 100 sold
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', (SELECT id FROM securities WHERE symbol = 'PYPL'), 'PYPL', 
     '2024-05-10', 200, 11610.00, 58.05, 'USD', true);

-- HHC Lots
INSERT INTO lots (portfolio_id, security_id, symbol, acquisition_date, quantity, cost_basis, cost_basis_per_share, currency, is_open)
VALUES
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', (SELECT id FROM securities WHERE symbol = 'HHC'), 'HHC', 
     '2024-02-20', 200, 13010.00, 65.05, 'USD', true),
    ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', (SELECT id FROM securities WHERE symbol = 'HHC'), 'HHC', 
     '2024-07-05', 100, 7210.00, 72.10, 'USD', true);

-- =============================================================================
-- 4. INSERT/UPDATE HOLDINGS (Current positions)
-- =============================================================================

-- CNR - 300 shares @ current price ~160 CAD
INSERT INTO holdings (portfolio_id, symbol, quantity, cost_basis, current_price, market_value)
VALUES ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'CNR', 300, 47220.00, 160.00, 48000.00)
ON CONFLICT (portfolio_id, symbol) DO UPDATE 
SET quantity = EXCLUDED.quantity, 
    cost_basis = EXCLUDED.cost_basis,
    current_price = EXCLUDED.current_price,
    market_value = EXCLUDED.market_value;

-- BAM - 600 shares @ current price ~50 USD
INSERT INTO holdings (portfolio_id, symbol, quantity, cost_basis, current_price, market_value)
VALUES ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BAM', 600, 26120.00, 50.00, 30000.00)
ON CONFLICT (portfolio_id, symbol) DO UPDATE 
SET quantity = EXCLUDED.quantity, 
    cost_basis = EXCLUDED.cost_basis,
    current_price = EXCLUDED.current_price,
    market_value = EXCLUDED.market_value;

-- BBUC - 50,000 shares @ $1 (money market)
INSERT INTO holdings (portfolio_id, symbol, quantity, cost_basis, current_price, market_value)
VALUES ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BBUC', 50000, 50000.00, 1.00, 50000.00)
ON CONFLICT (portfolio_id, symbol) DO UPDATE 
SET quantity = EXCLUDED.quantity, 
    cost_basis = EXCLUDED.cost_basis,
    current_price = EXCLUDED.current_price,
    market_value = EXCLUDED.market_value;

-- BRK.B - 130 shares @ current price ~358 USD
INSERT INTO holdings (portfolio_id, symbol, quantity, cost_basis, current_price, market_value)
VALUES ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BRK.B', 130, 43670.00, 358.00, 46540.00)
ON CONFLICT (portfolio_id, symbol) DO UPDATE 
SET quantity = EXCLUDED.quantity, 
    cost_basis = EXCLUDED.cost_basis,
    current_price = EXCLUDED.current_price,
    market_value = EXCLUDED.market_value;

-- BTI - 800 shares @ current price ~35 USD
INSERT INTO holdings (portfolio_id, symbol, quantity, cost_basis, current_price, market_value)
VALUES ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'BTI', 800, 26070.00, 35.00, 28000.00)
ON CONFLICT (portfolio_id, symbol) DO UPDATE 
SET quantity = EXCLUDED.quantity, 
    cost_basis = EXCLUDED.cost_basis,
    current_price = EXCLUDED.current_price,
    market_value = EXCLUDED.market_value;

-- EVO - 250 shares @ current price ~100 EUR
INSERT INTO holdings (portfolio_id, symbol, quantity, cost_basis, current_price, market_value)
VALUES ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'EVO', 250, 24480.00, 100.00, 25000.00)
ON CONFLICT (portfolio_id, symbol) DO UPDATE 
SET quantity = EXCLUDED.quantity, 
    cost_basis = EXCLUDED.cost_basis,
    current_price = EXCLUDED.current_price,
    market_value = EXCLUDED.market_value;

-- NKE - 250 shares @ current price ~75 USD
INSERT INTO holdings (portfolio_id, symbol, quantity, cost_basis, current_price, market_value)
VALUES ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'NKE', 250, 20470.00, 75.00, 18750.00)
ON CONFLICT (portfolio_id, symbol) DO UPDATE 
SET quantity = EXCLUDED.quantity, 
    cost_basis = EXCLUDED.cost_basis,
    current_price = EXCLUDED.current_price,
    market_value = EXCLUDED.market_value;

-- PYPL - 400 shares @ current price ~60 USD
INSERT INTO holdings (portfolio_id, symbol, quantity, cost_basis, current_price, market_value)
VALUES ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'PYPL', 400, 22620.00, 60.00, 24000.00)
ON CONFLICT (portfolio_id, symbol) DO UPDATE 
SET quantity = EXCLUDED.quantity, 
    cost_basis = EXCLUDED.cost_basis,
    current_price = EXCLUDED.current_price,
    market_value = EXCLUDED.market_value;

-- HHC - 300 shares @ current price ~70 USD
INSERT INTO holdings (portfolio_id, symbol, quantity, cost_basis, current_price, market_value)
VALUES ('64ff3be6-0ed1-4990-a32b-4ded17f0320c', 'HHC', 300, 20220.00, 70.00, 21000.00)
ON CONFLICT (portfolio_id, symbol) DO UPDATE 
SET quantity = EXCLUDED.quantity, 
    cost_basis = EXCLUDED.cost_basis,
    current_price = EXCLUDED.current_price,
    market_value = EXCLUDED.market_value;

-- =============================================================================
-- 5. VERIFICATION QUERIES
-- =============================================================================

-- Verify securities were created
SELECT 'Securities created:' as status, COUNT(*) as count 
FROM securities 
WHERE symbol IN ('CNR', 'BAM', 'BBUC', 'BRK.B', 'BTI', 'EVO', 'NKE', 'PYPL', 'HHC');

-- Verify transactions
SELECT 'Transactions created:' as status, COUNT(*) as count, 
       SUM(CASE WHEN transaction_type = 'BUY' THEN 1 ELSE 0 END) as buys,
       SUM(CASE WHEN transaction_type = 'SELL' THEN 1 ELSE 0 END) as sells,
       SUM(CASE WHEN transaction_type = 'DIVIDEND' THEN 1 ELSE 0 END) as dividends
FROM transactions 
WHERE portfolio_id = '64ff3be6-0ed1-4990-a32b-4ded17f0320c';

-- Verify lots
SELECT 'Lots created:' as status, COUNT(*) as count, SUM(quantity) as total_shares
FROM lots 
WHERE portfolio_id = '64ff3be6-0ed1-4990-a32b-4ded17f0320c';

-- Verify holdings
SELECT 'Holdings overview:' as status, 
       COUNT(*) as positions,
       SUM(market_value) as total_market_value,
       SUM(cost_basis) as total_cost_basis,
       SUM(market_value) - SUM(cost_basis) as unrealized_pnl
FROM holdings 
WHERE portfolio_id = '64ff3be6-0ed1-4990-a32b-4ded17f0320c';

-- Display current holdings
SELECT symbol, quantity, cost_basis, current_price, market_value, 
       ROUND((market_value - cost_basis) / NULLIF(cost_basis, 0) * 100, 2) as return_pct
FROM holdings 
WHERE portfolio_id = '64ff3be6-0ed1-4990-a32b-4ded17f0320c'
ORDER BY market_value DESC;

-- =============================================================================
-- DONE! Portfolio seeded with comprehensive data
-- =============================================================================