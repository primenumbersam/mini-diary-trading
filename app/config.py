from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "diary.db"

# Benchmark presets
BENCHMARK_PRESETS = ["SPY", "DIA", "QQQ"]
DEFAULT_BENCHMARK = "SPY"

# Base currency
BASE_CURRENCY = "USD"
