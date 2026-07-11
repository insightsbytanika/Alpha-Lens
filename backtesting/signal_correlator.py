"""
signal_correlator.py
AlphaLens - Week 5
Hedging scores aur stock price movement ko correlate karta hai.
Pearson correlation + p-value nikalta hai.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from scipy import stats
from config import DIR_PROCESSED, DIR_PRICES
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

TRANSCRIPT_MAP = {
    "earningscallinfosys_clean": ("INFY.NS", "2024-01-11"),
    "infosys limited earnings confrence call july 18 2024_clean": ("INFY.NS", "2024-07-18"),
    "infosys limited q2 fy24 earnings confrence call oct 12 2023_clean": ("INFY.NS", "2023-10-12"),
    "reliance19012024-Q3-FY2023-24-Transcript_clean": ("RELIANCE.NS", "2024-01-19"),
    "Transcript of the Q2 2024-25 Earnings Conference Call held on Oct 10, 2024_clean": ("HDFCBANK.NS", "2024-10-10"),
    "Transcript of the Q3 2023-24 Earnings Conference Call held on January 11, 2023_clean": ("HDFCBANK.NS", "2023-01-11"),
    "transcript---q3-fy24--earnings-call_clean": ("TCS.NS", "2024-01-11"),
    "transcript--q2-fy24-analyst-earnings-call_clean": ("TCS.NS", "2023-10-11"),
    "wipro q3fy24-earnings-transcript_clean": ("WIPRO.NS", "2024-01-17"),
}

def get_hedging_score(file_stem: str) -> float:
    """Transcript ki hedging CSV padhke overall hedging % nikalta hai."""
    hedging_path = DIR_PROCESSED / (file_stem + "_hedging.csv")
    if not hedging_path.exists():
        log.warning(f"  Hedging file nahi mili: {hedging_path}")
        return None

    df = pd.read_csv(hedging_path)
    score = round(df["is_hedging"].sum() / len(df), 4)
    return score

def get_price_return(ticker: str, call_date: str, days: int) -> float:
    """
    Call ke baad kitne din mein stock kitna gaya.
    days = 1, 3, ya 7
    """
    price_file = DIR_PRICES / f"{ticker.replace('.NS', '')}_prices.csv"
    if not price_file.exists():
        log.warning(f"  Price file nahi mili: {price_file}")
        return None

    df = pd.read_csv(price_file, index_col="date", parse_dates=True)
    df = df.sort_index()
    try:
        # Call date ke baad ki prices
        future = df[df.index > call_date]
        if len(future) < days:
            log.warning(f"  {ticker} ke paas {days} din ka data nahi")
            return None

        price_day0 = df[df.index <= call_date]["close"].iloc[-1]
        price_dayN = future["close"].iloc[days - 1]
        return_pct = round((price_dayN - price_day0) / price_day0 * 100, 4)
        return return_pct

    except Exception as e:
        log.warning(f"  Price return error {ticker}: {e}")
        return None
    
def build_dataset() -> pd.DataFrame:
    """Saare transcripts ka hedging score aur price returns ek table mein."""
    rows = []

    for file_stem, (ticker, call_date) in TRANSCRIPT_MAP.items():
        log.info(f"Processing: {file_stem[:40]}...")

        hedging = get_hedging_score(file_stem)
        if hedging is None:
            continue

        r1 = get_price_return(ticker, call_date, 1)
        r3 = get_price_return(ticker, call_date, 3)
        r7 = get_price_return(ticker, call_date, 7)

        rows.append({
            "file":         file_stem[:40],
            "ticker":       ticker,
            "call_date":    call_date,
            "hedging_pct":  hedging,
            "return_t1":    r1,
            "return_t3":    r3,
            "return_t7":    r7,
        })

    return pd.DataFrame(rows)


