"""
price_fetcher.py
AlphaLens — Week 1 Ingestion
Fetches historical stock price data for NSE-listed companies via yfinance.
Stores one CSV per ticker in data/prices/.
"""

import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import datetime
import time
import logging

# ── Config ────────────────────────────────────────────────────────────────────
# NSE tickers need ".NS" suffix for Yahoo Finance
NSE_TICKERS = [
    "INFY.NS",      # Infosys
    "TCS.NS",       # TCS
    "HDFCBANK.NS",  # HDFC Bank
    "RELIANCE.NS",  # Reliance Industries
    "WIPRO.NS",     # Wipro
    "ICICIBANK.NS", # ICICI Bank
    "AXISBANK.NS",  # Axis Bank
    "LT.NS",        # Larsen & Toubro
]

BACKTEST_START = "2022-01-01"   # 3 years of history
BACKTEST_END   = datetime.today().strftime("%Y-%m-%d")
OUTPUT_DIR     = Path("data/prices")
SLEEP_BETWEEN  = 1.5  # seconds — be polite to Yahoo's servers

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Core function ─────────────────────────────────────────────────────────────
def fetch_price_history(ticker: str) -> pd.DataFrame | None:
    """
    Downloads OHLCV data for one ticker.
    Returns a cleaned DataFrame or None if the download fails.
    """
    log.info(f"Fetching {ticker} ...")
    try:
        df = yf.download(
            ticker,
            start=BACKTEST_START,
            end=BACKTEST_END,
            auto_adjust=True,   # adjusts for splits/dividends automatically
            progress=False,     # no progress bar spam in logs
        )

        if df.empty:
            log.warning(f"  ✗ No data returned for {ticker} — skipping")
            return None

        # Flatten multi-level columns yfinance sometimes returns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Clean up
        df.index.name = "date"
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]
        df["ticker"] = ticker

        log.info(f"  ✓ {len(df)} rows  |  {df.index[0].date()} → {df.index[-1].date()}")
        return df

    except Exception as e:
        log.error(f"  ✗ Failed for {ticker}: {e}")
        return None


def save_prices(df: pd.DataFrame, ticker: str) -> Path:
    """Saves DataFrame to CSV. Returns the file path."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Strip the .NS suffix for clean filenames: INFY.NS → INFY
    clean_name = ticker.replace(".NS", "")
    path = OUTPUT_DIR / f"{clean_name}_prices.csv"
    df.to_csv(path)
    log.info(f"  → Saved to {path}")
    return path


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    log.info("=" * 55)
    log.info("AlphaLens  |  Price Fetcher  |  Week 1")
    log.info("=" * 55)

    success, failed = [], []

    for ticker in NSE_TICKERS:
        df = fetch_price_history(ticker)

        if df is not None:
            save_prices(df, ticker)
            success.append(ticker)
        else:
            failed.append(ticker)

        time.sleep(SLEEP_BETWEEN)  # don't hammer Yahoo Finance

    # ── Summary ───────────────────────────────────────────────────────────────
    log.info("")
    log.info("── Run Summary ──────────────────────────────────────")
    log.info(f"  ✓ Success : {len(success)}  →  {', '.join(success)}")
    if failed:
        log.info(f"  ✗ Failed  : {len(failed)}  →  {', '.join(failed)}")
    log.info(f"  CSVs saved in: {OUTPUT_DIR.resolve()}")
    log.info("────────────────────────────────────────────────────")


if __name__ == "__main__":
    main()