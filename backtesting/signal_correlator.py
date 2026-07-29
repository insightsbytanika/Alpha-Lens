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
    "AXISBANK_Q2FY25_17Oct2024_clean": ("AXISBANK.NS", "2024-10-17"),
    "AXISBANK_Q3FY24_23Jan2024_clean": ("AXISBANK.NS", "2024-01-23"),
    "HDFCBANK_Q1FY24_17Jul2023_clean": ("HDFCBANK.NS", "2023-07-17"),
    "HDFCBANK_Q2FY24_16Oct2023_clean": ("HDFCBANK.NS", "2023-10-16"),
    "HDFCBANK_Q3FY24_16Jan2024_clean": ("HDFCBANK.NS", "2024-01-16"),
    "HDFCBANK_Q4FY24_20Apr2024_clean": ("HDFCBANK.NS", "2024-04-20"),
    "ICICIBANK_Q2FY24_27Oct2023_clean": ("ICICIBANK.NS", "2023-10-27"),
    "ICICIBANK_Q3FY24_20Jan2024_clean": ("ICICIBANK.NS", "2024-01-20"),
    "INFY_Q1FY23_25Jul2022_clean": ("INFY.NS", "2022-07-25"),
    "INFY_Q1FY25_18Jul2024_clean": ("INFY.NS", "2024-07-18"),
    "INFY_Q2FY24_12Oct2023_clean": ("INFY.NS", "2023-10-12"),
    "INFY_Q3FY24_11Jan2024_clean": ("INFY.NS", "2024-01-11"),
    "INFY_Q4FY24_18Apr2024_clean": ("INFY.NS", "2024-04-18"),
    "RELIANCE_Q2FY24_27Oct2023_clean": ("RELIANCE.NS", "2023-10-27"),
    "RELIANCE_Q3FY24_19Jan2024_clean": ("RELIANCE.NS", "2024-01-19"),
    "TCS_Q1FY25_11Jul2024_clean": ("TCS.NS", "2024-07-11"),
    "TCS_Q2FY25_10Oct2024_clean": ("TCS.NS", "2024-10-10"),
    "TCS_Q3FY24_11Jan2024_clean": ("TCS.NS", "2024-01-11"),
    "TCS_Q4FY25_10Apr2025_clean": ("TCS.NS", "2025-04-10"),
    "WIPRO_Q2FY24_18Oct2023_clean": ("WIPRO.NS", "2023-10-18"),
    "WIPRO_Q3FY24_12Jan2024_clean": ("WIPRO.NS", "2024-01-12"),
    "WIPRO_Q4FY24_19Apr2024_clean": ("WIPRO.NS", "2024-04-19"),
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


def run_correlation(df: pd.DataFrame, return_col: str):
    """Hedging % aur stock return ka Pearson correlation nikalta hai."""
    clean = df[["hedging_pct", return_col]].dropna()

    if len(clean) < 3:
        log.warning(f"  {return_col}: kam data hai — skip")
        return

    corr, pvalue = stats.pearsonr(clean["hedging_pct"], clean[return_col])

    log.info(f"  {return_col}:")
    log.info(f"    Correlation : {round(corr, 4)}")
    log.info(f"    P-value     : {round(pvalue, 4)}")
    if pvalue < 0.05:
        log.info(f"    ✓ SIGNIFICANT — signal real hai!")
    else:
        log.info(f"    ✗ Not significant yet — aur data chahiye")


def main():
    log.info("=" * 55)
    log.info("AlphaLens  |  Signal Correlator  |  Week 5")
    log.info("=" * 55)

    df = build_dataset()

    if df.empty:
        log.error("Koi data nahi mila — TRANSCRIPT_MAP check karo")
        return

    log.info(f"\n  {len(df)} transcripts ka data ready\n")
    log.info(df[["ticker", "call_date", "hedging_pct",
                 "return_t1", "return_t3", "return_t7"]].to_string())

    log.info("\n-- Correlation Results " + "-" * 32)
    run_correlation(df, "return_t1")
    run_correlation(df, "return_t3")
    run_correlation(df, "return_t7")

    out = Path("backtesting/results/correlation_results.csv")
    out.parent.mkdir(exist_ok=True)
    df.to_csv(out, index=False)
    log.info(f"\n  Results saved: {out.resolve()}")
    log.info("-" * 55)


if __name__ == "__main__":
    main()
