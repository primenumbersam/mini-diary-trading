import sqlite3
from contextlib import contextmanager
from app.config import DB_PATH

DDL_STATEMENTS = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- 1. 자산 및 현금 마스터 테이블
CREATE TABLE IF NOT EXISTS assets (
    asset_id TEXT NOT NULL,
    user_id TEXT NOT NULL DEFAULT 'default_user',
    asset_class TEXT NOT NULL DEFAULT 'cash' CHECK (asset_class IN ('cash', 'stock', 'derivative', 'bond')),
    asset_country TEXT NOT NULL DEFAULT 'US',
    asset_name TEXT NOT NULL,
    asset_description TEXT,
    asset_memo TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, asset_id)
);

-- 2. 사전 매매 계획 테이블
CREATE TABLE IF NOT EXISTS plans (
    plan_id TEXT NOT NULL,
    user_id TEXT NOT NULL DEFAULT 'default_user',
    asset_id TEXT NOT NULL,
    plan_date DATE NOT NULL,
    position_side TEXT NOT NULL CHECK (position_side IN ('long', 'short')),
    instrument_type TEXT NOT NULL CHECK (instrument_type IN ('spot', 'future', 'option')),
    plan_entry_price REAL NOT NULL,
    plan_tp_price REAL NOT NULL,
    plan_sl_price REAL NOT NULL,
    plan_qty REAL NOT NULL,
    plan_target_value REAL GENERATED ALWAYS AS (plan_entry_price * plan_qty) STORED,
    plan_rrr REAL GENERATED ALWAYS AS (
        ABS(plan_tp_price - plan_entry_price) / NULLIF(ABS(plan_entry_price - plan_sl_price), 0)
    ) STORED,
    plan_confidence TEXT NOT NULL CHECK (plan_confidence IN ('high', 'medium', 'low')),
    plan_memo TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, plan_id),
    FOREIGN KEY (user_id, asset_id) REFERENCES assets(user_id, asset_id)
);

-- 3. 체결 및 현금 흐름 원장 테이블 (Fact Table)
CREATE TABLE IF NOT EXISTS trades (
    trade_id TEXT NOT NULL,
    user_id TEXT NOT NULL DEFAULT 'default_user',
    plan_id TEXT,
    asset_id TEXT NOT NULL,
    trade_datetime DATETIME NOT NULL,
    position_side TEXT NOT NULL CHECK (position_side IN ('long', 'short', 'neutral')),
    trade_action TEXT NOT NULL CHECK (trade_action IN ('deposit', 'withdraw', 'open', 'add', 'reduce', 'close')),
    trade_price REAL NOT NULL,
    trade_qty REAL NOT NULL,
    trade_amount REAL GENERATED ALWAYS AS (trade_price * trade_qty) STORED,
    trade_fee REAL NOT NULL DEFAULT 0.0,
    trade_tp_price REAL,
    trade_sl_price REAL,
    trade_status TEXT NOT NULL DEFAULT 'active' CHECK (trade_status IN ('active', 'inactive')),
    trade_memo TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, trade_id),
    FOREIGN KEY (user_id, asset_id) REFERENCES assets(user_id, asset_id)
);

-- 4. 일별 NAV 스냅샷 테이블 (TWR 계산용 및 다중 통화 지원)
CREATE TABLE IF NOT EXISTS internal_pfo (
    user_id TEXT NOT NULL DEFAULT 'default_user',
    nav_date DATE NOT NULL,
    cash_balance REAL NOT NULL,
    market_value REAL NOT NULL,
    total_nav REAL NOT NULL,
    external_flow REAL NOT NULL DEFAULT 0.0,
    daily_twr REAL,
    cumulative_twr_index REAL,
    usd_krw_rate REAL,
    total_nav_krw REAL GENERATED ALWAYS AS (total_nav * usd_krw_rate) STORED,
    PRIMARY KEY (user_id, nav_date)
);

-- 5. 현재가 및 시장 데이터 캐시 테이블 (공용 글로벌 데이터)
CREATE TABLE IF NOT EXISTS external_data (
    asset_id TEXT PRIMARY KEY,
    current_price REAL NOT NULL,
    price_currency TEXT NOT NULL DEFAULT 'USD',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_db():
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript(DDL_STATEMENTS)


if __name__ == "__main__":
    init_db()
    print(f"Database initialized successfully at {DB_PATH}")
