"""
config.py
AlphaLens - Central Configuration
Saari settings ek jagah — kisi bhi file mein
directly mat likho, yahan se import karo.
"""

from pathlib import Path
from datetime import datetime

# ── Folders ──────────────────────────────────────
DIR_TRANSCRIPTS = Path("data/transcripts")
DIR_PRICES      = Path("data/prices")
DIR_PROCESSED   = Path("data/processed")
DIR_AUDIO       = Path("data/audio")

# ── Model ─────────────────────────────────────────
FINBERT_MODEL = "ProsusAI/finbert"

# ── Tickers ───────────────────────────────────────
NSE_TICKERS = [
    "INFY.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "RELIANCE.NS",
    "WIPRO.NS",
    "ICICIBANK.NS",
    "AXISBANK.NS",
    "LT.NS",
]

# ── Backtest ──────────────────────────────────────
BACKTEST_START = "2022-01-01"
BACKTEST_END   = datetime.today().strftime("%Y-%m-%d")
SLEEP_BETWEEN  = 1.5