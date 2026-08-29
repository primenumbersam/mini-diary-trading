from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


# --- Assets ---
class AssetBase(BaseModel):
    asset_id: str
    asset_class: Literal["cash", "stock", "derivative", "bond"] = "cash"
    asset_country: str
    asset_name: str
    asset_description: Optional[str] = None
    asset_memo: Optional[str] = None


class AssetCreate(AssetBase):
    pass


class AssetOut(AssetBase):
    asset_status: Literal["active", "inactive", "pending"] = "pending"
    current_price: Optional[float] = None
    holding_qty: Optional[float] = None
    created_at: Optional[datetime] = None


# --- Plans ---
class PlanBase(BaseModel):
    plan_id: str
    asset_id: str
    plan_date: date
    position_side: Literal["long", "short"]
    instrument_type: Literal["spot", "future", "option"] = "spot"
    plan_entry_price: float = Field(gt=0)
    plan_tp_price: float = Field(gt=0)
    plan_sl_price: float = Field(gt=0)
    plan_qty: float = Field(gt=0)
    plan_confidence: Literal["high", "medium", "low"] = "medium"
    plan_memo: Optional[str] = None


class PlanCreate(PlanBase):
    pass


class PlanOut(PlanBase):
    plan_status: Literal["active", "pending"] = "pending"
    plan_target_value: Optional[float] = None
    plan_rrr: Optional[float] = None
    created_at: Optional[datetime] = None


# --- Trades ---
class TradeBase(BaseModel):
    trade_id: str
    plan_id: Optional[str] = None
    asset_id: str
    trade_datetime: datetime
    position_side: Literal["long", "short", "neutral"]
    trade_action: Literal["deposit", "withdraw", "open", "add", "reduce", "close"]
    trade_price: float = Field(gt=0)
    trade_qty: float = Field(gt=0)
    trade_fee: float = Field(default=0.0, ge=0)
    trade_tp_price: Optional[float] = None
    trade_sl_price: Optional[float] = None
    trade_status: Literal["active", "inactive"] = "active"
    trade_memo: Optional[str] = None


class TradeCreate(TradeBase):
    pass


class TradeOut(TradeBase):
    trade_amount: Optional[float] = None
    instrument_type: Optional[str] = None
    created_at: Optional[datetime] = None


# --- Internal Portfolio (Daily NAV & Snapshot) ---
class InternalPfoOut(BaseModel):
    nav_date: date
    cash_balance: float
    market_value: float
    total_nav: float
    external_flow: float
    daily_twr: Optional[float] = None
    cumulative_twr_index: Optional[float] = None
    usd_krw_rate: Optional[float] = None
    total_nav_krw: Optional[float] = None

# Backward compatibility alias
DailyNavOut = InternalPfoOut
