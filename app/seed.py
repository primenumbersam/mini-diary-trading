from datetime import date
from app.database import get_db

MOCK_ASSETS = [
    ("CASH_USD", "default_user", "cash", "US", "US Dollar Cash", "Base cash denomination in USD", None),
    ("CASH_KRW", "default_user", "cash", "KR", "Korean Won Cash", "Cash balance in KRW", None),
    ("GOOG", "default_user", "stock", "US", "Alphabet Inc. Class C", "Tech Giant - Search & Cloud", None),
    ("META", "default_user", "stock", "US", "Meta Platforms Inc.", "Social & AI Leader", None),
    ("NVDA", "default_user", "stock", "US", "NVIDIA Corporation", "Semiconductor & AI Hardware", None),
    ("AAPL", "default_user", "stock", "US", "Apple Inc.", "Consumer Tech Leader", None),
    ("TSLA", "default_user", "stock", "US", "Tesla Inc.", "EV & Robotics", None),
]

MOCK_EXTERNAL_DATA = [
    ("CASH_USD", 1.0, "USD"),
    ("CASH_KRW", 0.00074, "USD"),
    ("GOOG", 182.50, "USD"),
    ("META", 515.00, "USD"),
    ("NVDA", 128.20, "USD"),
    ("AAPL", 224.50, "USD"),
    ("TSLA", 218.00, "USD"),
]

MOCK_PLANS = [
    ("GOOG_20260720_01", "default_user", "GOOG", "2026-07-20", "long", "spot", 175.0, 195.0, 165.0, 10.0, "high", "Earnings momentum & Cloud growth"),
    ("META_20260721_01", "default_user", "META", "2026-07-21", "long", "spot", 490.0, 540.0, 465.0, 5.0, "medium", "Breakout above $480 resistance"),
    ("NVDA_20260722_01", "default_user", "NVDA", "2026-07-22", "long", "spot", 120.0, 140.0, 110.0, 20.0, "low", "Key support retest entry"),
    ("AAPL_20260715_01", "default_user", "AAPL", "2026-07-15", "long", "spot", 215.0, 230.0, 205.0, 10.0, "high", "AI feature cycle anticipation"),
]

MOCK_TRADES = [
    # 1. Initial Deposit: $10,000
    ("TR_20260720_001", "default_user", None, "CASH_USD", "2026-07-20 09:00:00", "neutral", "deposit", 1.0, 10000.0, 0.0, None, None, "active", "Initial Capital Deposit"),
    # 2. GOOG Buy: 10 shares @ $175.00
    ("TR_20260720_002", "default_user", "GOOG_20260720_01", "GOOG", "2026-07-20 10:30:00", "long", "open", 175.0, 10.0, 1.5, 195.0, 165.0, "active", "GOOG entry"),
    # 3. META Buy: 5 shares @ $490.00
    ("TR_20260721_001", "default_user", "META_20260721_01", "META", "2026-07-21 11:15:00", "long", "open", 490.0, 5.0, 1.5, 540.0, 465.0, "active", "META entry"),
    # 4. NVDA Buy: 20 shares @ $120.00
    ("TR_20260723_001", "default_user", "NVDA_20260722_01", "NVDA", "2026-07-23 14:00:00", "long", "open", 120.0, 20.0, 2.0, 140.0, 110.0, "active", "NVDA entry"),
    # 5. AAPL Closed Trade (Round trip for Realized PnL Review)
    ("TR_20260715_001", "default_user", "AAPL_20260715_01", "AAPL", "2026-07-15 09:45:00", "long", "open", 215.0, 10.0, 1.5, 230.0, 205.0, "active", "AAPL entry"),
    ("TR_20260719_001", "default_user", "AAPL_20260715_01", "AAPL", "2026-07-19 15:30:00", "short", "close", 228.0, 10.0, 1.5, None, None, "active", "AAPL TP exit"),
]

# Daily NAV & TWR Index Time Series for Performance Chart
MOCK_INTERNAL_PFO = [
    ("default_user", "2026-07-20", 8248.50, 1750.00, 9998.50, 10000.0, 0.0000, 100.00, 1350.0),
    ("default_user", "2026-07-21", 5797.00, 4260.00, 10057.00, 0.0, 0.0059, 100.59, 1352.0),
    ("default_user", "2026-07-22", 5797.00, 4340.00, 10137.00, 0.0, 0.0080, 101.39, 1351.5),
    ("default_user", "2026-07-23", 3395.00, 6815.00, 10210.00, 0.0, 0.0072, 102.12, 1349.0),
    ("default_user", "2026-07-24", 3395.00, 6780.00, 10175.00, 0.0, -0.0034, 101.77, 1348.0),
    ("default_user", "2026-07-25", 3395.00, 6860.00, 10255.00, 0.0, 0.0079, 102.57, 1348.5),
    ("default_user", "2026-07-26", 3395.00, 6890.00, 10285.00, 0.0, 0.0029, 102.87, 1350.0),
    ("default_user", "2026-07-27", 3395.00, 6990.00, 10385.00, 0.0, 0.0097, 103.87, 1353.0),
    ("default_user", "2026-07-28", 3395.00, 7065.00, 10460.00, 0.0, 0.0072, 104.62, 1355.0),
    ("default_user", "2026-07-29", 3395.00, 7150.00, 10545.00, 0.0, 0.0081, 105.47, 1352.0),
    ("default_user", "2026-07-30", 3395.00, 7120.00, 10515.00, 0.0, -0.0028, 105.17, 1350.5),
    ("default_user", "2026-07-31", 3395.00, 7234.00, 10629.00, 0.0, 0.0108, 106.31, 1350.0),
]


def seed_mock_data():
    with get_db() as conn:
        cursor = conn.cursor()

        # Clear existing tables cleanly
        for tbl in ["trades", "plans", "assets", "external_data", "internal_pfo"]:
            cursor.execute(f"DELETE FROM {tbl}")

        # 1. Seed Assets
        cursor.executemany(
            """
            INSERT OR REPLACE INTO assets 
            (asset_id, user_id, asset_class, asset_country, asset_name, asset_description, asset_memo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            MOCK_ASSETS,
        )

        # 2. Seed External Market Prices Cache
        cursor.executemany(
            """
            INSERT OR REPLACE INTO external_data (asset_id, current_price, price_currency)
            VALUES (?, ?, ?)
            """,
            MOCK_EXTERNAL_DATA,
        )

        # 3. Seed Plans
        cursor.executemany(
            """
            INSERT OR REPLACE INTO plans 
            (plan_id, user_id, asset_id, plan_date, position_side, instrument_type, plan_entry_price, plan_tp_price, plan_sl_price, plan_qty, plan_confidence, plan_memo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            MOCK_PLANS,
        )

        # 4. Seed Trades
        cursor.executemany(
            """
            INSERT OR REPLACE INTO trades 
            (trade_id, user_id, plan_id, asset_id, trade_datetime, position_side, trade_action, trade_price, trade_qty, trade_fee, trade_tp_price, trade_sl_price, trade_status, trade_memo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            MOCK_TRADES,
        )

        # 5. Seed Daily NAV & TWR Snapshots
        cursor.executemany(
            """
            INSERT OR REPLACE INTO internal_pfo
            (user_id, nav_date, cash_balance, market_value, total_nav, external_flow, daily_twr, cumulative_twr_index, usd_krw_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            MOCK_INTERNAL_PFO,
        )


if __name__ == "__main__":
    seed_mock_data()
    print("✓ Full mock dataset (Assets, Prices, Plans, Trades, NAV & Benchmark Chart Series) seeded successfully.")
