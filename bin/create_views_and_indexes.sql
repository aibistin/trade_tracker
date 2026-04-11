-- =============================================================================
-- Schema improvements: indexes and views for the Trading app
-- Created: 2026-04-07
--
-- Run with:  sqlite3 data/stock_trades.db < bin/create_views_and_indexes.sql
--
-- Safe to re-run: uses CREATE INDEX IF NOT EXISTS and CREATE VIEW with
-- DROP VIEW IF EXISTS (views are virtual, no data loss).
-- Does NOT modify existing tables or triggers.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- INDEXES
-- ---------------------------------------------------------------------------

-- Covers get_raw_trade_data / get_trade_data_for_analysis:
--   WHERE symbol = ? AND action IN (...) ORDER BY trade_date
CREATE INDEX IF NOT EXISTS idx_trade_symbol_action_date
    ON trade_transaction (symbol, action, trade_date);

-- Covers the buy/sell aggregation CTEs in get_current_holdings:
--   WHERE action IN (...) GROUP BY symbol, trade_type
CREATE INDEX IF NOT EXISTS idx_trade_action_symbol_type
    ON trade_transaction (action, symbol, trade_type);

-- Covers ORDER BY trade_date across multiple queries
CREATE INDEX IF NOT EXISTS idx_trade_date
    ON trade_transaction (trade_date);

-- Covers get_all_traded_symbols:
--   SELECT DISTINCT symbol ORDER BY symbol
CREATE INDEX IF NOT EXISTS idx_trade_symbol
    ON trade_transaction (symbol);

-- Covers filtered queries by account
CREATE INDEX IF NOT EXISTS idx_trade_account
    ON trade_transaction (account);


-- ---------------------------------------------------------------------------
-- VIEWS
-- ---------------------------------------------------------------------------

-- Buy-side aggregation per symbol and trade_type
-- Sums quantity and absolute amount for buy-type actions (B, RS, BO)
DROP VIEW IF EXISTS v_buy_summary;
CREATE VIEW v_buy_summary AS
SELECT
    symbol,
    trade_type,
    SUM(quantity)          AS total_buy_qty,
    ABS(SUM(amount))       AS total_buy_cost,
    CASE
        WHEN SUM(quantity) > 0
        THEN ROUND(ABS(SUM(amount)) / SUM(quantity), 2)
        ELSE 0
    END                    AS avg_buy_price,
    COUNT(*)               AS buy_trade_count,
    MIN(trade_date)        AS first_buy_date,
    MAX(trade_date)        AS last_buy_date
FROM trade_transaction
WHERE action IN ('B', 'RS', 'BO')
GROUP BY symbol, trade_type;


-- Sell-side aggregation per symbol and trade_type
-- Sums quantity and amount for sell-type actions (S, SC, EXP, EE)
DROP VIEW IF EXISTS v_sell_summary;
CREATE VIEW v_sell_summary AS
SELECT
    symbol,
    trade_type,
    SUM(quantity)          AS total_sell_qty,
    SUM(amount)            AS total_sell_proceeds,
    CASE
        WHEN SUM(quantity) > 0
        THEN ROUND(SUM(amount) / SUM(quantity), 2)
        ELSE 0
    END                    AS avg_sell_price,
    COUNT(*)               AS sell_trade_count,
    MIN(trade_date)        AS first_sell_date,
    MAX(trade_date)        AS last_sell_date
FROM trade_transaction
WHERE action IN ('S', 'SC', 'EXP', 'EE')
GROUP BY symbol, trade_type;


-- Open positions: buy qty exceeds sell qty
-- Joins with security table for the security name
DROP VIEW IF EXISTS v_open_positions;
CREATE VIEW v_open_positions AS
SELECT
    b.symbol,
    b.trade_type,
    s.name                                           AS security_name,
    (b.total_buy_qty - COALESCE(sl.total_sell_qty, 0))  AS open_qty,
    b.avg_buy_price,
    b.total_buy_cost,
    COALESCE(sl.total_sell_proceeds, 0)               AS sell_proceeds,
    ROUND(COALESCE(sl.total_sell_proceeds, 0) - b.total_buy_cost, 2) AS unrealized_cost_basis,
    b.first_buy_date,
    b.last_buy_date
FROM v_buy_summary b
LEFT JOIN v_sell_summary sl
    ON b.symbol = sl.symbol AND b.trade_type = sl.trade_type
JOIN security s
    ON b.symbol = s.symbol
WHERE (b.total_buy_qty - COALESCE(sl.total_sell_qty, 0)) > 0.0001;


-- Closed trades P&L: buy qty equals sell qty (fully closed positions)
DROP VIEW IF EXISTS v_closed_trades_pnl;
CREATE VIEW v_closed_trades_pnl AS
SELECT
    b.symbol,
    b.trade_type,
    s.name                                           AS security_name,
    b.total_buy_qty                                  AS qty,
    b.avg_buy_price,
    sl.avg_sell_price,
    b.total_buy_cost,
    sl.total_sell_proceeds,
    ROUND(sl.total_sell_proceeds - b.total_buy_cost, 2) AS realized_pnl,
    CASE
        WHEN b.total_buy_cost > 0
        THEN ROUND((sl.total_sell_proceeds - b.total_buy_cost) / b.total_buy_cost * 100, 2)
        ELSE 0
    END                                              AS pnl_percent,
    CASE
        WHEN ROUND(sl.total_sell_proceeds - b.total_buy_cost, 2) > 0 THEN 'W'
        WHEN ROUND(sl.total_sell_proceeds - b.total_buy_cost, 2) < 0 THEN 'L'
        ELSE 'E'
    END                                              AS win_lose,
    b.first_buy_date,
    sl.last_sell_date                                AS closed_date
FROM v_buy_summary b
JOIN v_sell_summary sl
    ON b.symbol = sl.symbol AND b.trade_type = sl.trade_type
JOIN security s
    ON b.symbol = s.symbol
WHERE ABS(b.total_buy_qty - sl.total_sell_qty) < 0.0001;


-- Enriched trade activity: each transaction joined with security name
-- Useful for the frontend trade history table and sparkline data
DROP VIEW IF EXISTS v_trade_activity;
CREATE VIEW v_trade_activity AS
SELECT
    t.id,
    t.symbol,
    s.name                  AS security_name,
    t.action,
    t.trade_type,
    t.label,
    t.trade_date,
    t.expiration_date,
    t.quantity,
    t.price,
    t.amount,
    t.target_price,
    t.initial_stop_price,
    t.projected_sell_price,
    t.reason,
    t.account,
    CASE
        WHEN t.action IN ('B', 'RS', 'BO') THEN 'BUY'
        WHEN t.action IN ('S', 'SC', 'EXP', 'EE') THEN 'SELL'
        ELSE 'OTHER'
    END                     AS action_side
FROM trade_transaction t
JOIN security s ON t.symbol = s.symbol
WHERE t.action IN ('B', 'BO', 'EE', 'EXP', 'RS', 'S', 'SC')
ORDER BY t.trade_date, t.symbol;


-- Per-account open positions (same as v_open_positions but broken out by account)
DROP VIEW IF EXISTS v_open_positions_by_account;
CREATE VIEW v_open_positions_by_account AS
SELECT
    t.symbol,
    t.trade_type,
    t.account,
    s.name                                         AS security_name,
    SUM(CASE WHEN t.action IN ('B', 'RS', 'BO') THEN t.quantity ELSE 0 END)
      - SUM(CASE WHEN t.action IN ('S', 'SC', 'EXP', 'EE') THEN t.quantity ELSE 0 END)
                                                   AS open_qty,
    CASE
        WHEN SUM(CASE WHEN t.action IN ('B', 'RS', 'BO') THEN t.quantity ELSE 0 END) > 0
        THEN ROUND(
            ABS(SUM(CASE WHEN t.action IN ('B', 'RS', 'BO') THEN t.amount ELSE 0 END))
            / SUM(CASE WHEN t.action IN ('B', 'RS', 'BO') THEN t.quantity ELSE 0 END), 2)
        ELSE 0
    END                                            AS avg_buy_price,
    ABS(SUM(CASE WHEN t.action IN ('B', 'RS', 'BO') THEN t.amount ELSE 0 END))
                                                   AS total_buy_cost,
    SUM(CASE WHEN t.action IN ('S', 'SC', 'EXP', 'EE') THEN t.amount ELSE 0 END)
                                                   AS sell_proceeds
FROM trade_transaction t
JOIN security s ON t.symbol = s.symbol
WHERE t.action IN ('B', 'BO', 'RS', 'S', 'SC', 'EXP', 'EE')
GROUP BY t.symbol, t.trade_type, t.account
HAVING (
    SUM(CASE WHEN t.action IN ('B', 'RS', 'BO') THEN t.quantity ELSE 0 END)
    - SUM(CASE WHEN t.action IN ('S', 'SC', 'EXP', 'EE') THEN t.quantity ELSE 0 END)
) > 0.0001;


-- Monthly P&L summary from closed sell transactions
-- Groups sell-side proceeds and corresponding buy costs by month
DROP VIEW IF EXISTS v_monthly_pnl;
CREATE VIEW v_monthly_pnl AS
SELECT
    strftime('%Y-%m', sl.last_sell_date) AS period,
    SUM(sl.total_sell_proceeds - b.total_buy_cost) AS pnl_dollars,
    COUNT(*) AS trade_count,
    SUM(CASE WHEN (sl.total_sell_proceeds - b.total_buy_cost) > 0 THEN 1 ELSE 0 END) AS winning_trades,
    SUM(CASE WHEN (sl.total_sell_proceeds - b.total_buy_cost) < 0 THEN 1 ELSE 0 END) AS losing_trades
FROM v_buy_summary b
JOIN v_sell_summary sl
    ON b.symbol = sl.symbol AND b.trade_type = sl.trade_type
WHERE ABS(b.total_buy_qty - sl.total_sell_qty) < 0.0001
GROUP BY strftime('%Y-%m', sl.last_sell_date)
ORDER BY period;
