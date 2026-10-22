"""
signal_correlator.py
AlphaLens - Week 5 (v2)
Hedging / sentiment signals aur stock price movement ko correlate karta hai.

v2 changes:
  * call date: data/call_dates_verified.json se (filename date nahi - Infosys/Wipro
    ke filenames filing date the, call se 1-5 din baad) -> ingestion/verify_call_dates.py
  * ABNORMAL returns = stock return - Nifty 50 return (same window). Raw return mostly
    market move hota hai.
  * hedging_z / net_sentiment_z : company ke apne average ke relative (TCS naturally
    Axis se zyada hedge kar sakta hai - hum company identity nahi, "us company ke liye
    unusual" signal naapna chahte hain). Note: mean poore sample se liya hai.
  * Pearson + Spearman dono (returns mein outliers hote hain)
  * Primary test PEHLE se fixed: hedging_z -> abn_t3. Baaki sab exploratory hain aur
    Bonferroni threshold ke saath report hote hain (24 tests mein se kuch p<0.05 aana
    chance se bhi normal hai).

Return window: close-to-close. Day0 = call date (ya uske pehle ka last trading close,
weekend/holiday ho to). T+N = Day0 ke baad N-th trading day ka close. Zyadatar calls
market ke baad hoti hain, isliye T+1 pehla tradable reaction day hota hai.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
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
    "AXISBANK_Q1FY23_25Jul2022_clean": ("AXISBANK.NS", "2022-07-25"),
    "AXISBANK_Q1FY24_26Jul2023_clean": ("AXISBANK.NS", "2023-07-26"),
    "AXISBANK_Q1FY25_24Jul2024_clean": ("AXISBANK.NS", "2024-07-24"),
    "AXISBANK_Q1FY26_17Jul2025_clean": ("AXISBANK.NS", "2025-07-17"),
    "AXISBANK_Q1FY27_18Jul2026_clean": ("AXISBANK.NS", "2026-07-18"),
    "AXISBANK_Q2FY24_25Oct2023_clean": ("AXISBANK.NS", "2023-10-25"),
    "AXISBANK_Q2FY25_17Oct2024_clean": ("AXISBANK.NS", "2024-10-17"),
    "AXISBANK_Q2FY26_15Oct2025_clean": ("AXISBANK.NS", "2025-10-15"),
    "AXISBANK_Q3FY23_23Jan2023_clean": ("AXISBANK.NS", "2023-01-23"),
    "AXISBANK_Q3FY24_23Jan2024_clean": ("AXISBANK.NS", "2024-01-23"),
    "AXISBANK_Q3FY25_16Jan2025_clean": ("AXISBANK.NS", "2025-01-16"),
    "AXISBANK_Q3FY26_26Jan2026_clean": ("AXISBANK.NS", "2026-01-26"),
    "AXISBANK_Q4FY23_27Apr2023_clean": ("AXISBANK.NS", "2023-04-27"),
    "AXISBANK_Q4FY24_24Apr2024_clean": ("AXISBANK.NS", "2024-04-24"),
    "AXISBANK_Q4FY25_25Apr2025_clean": ("AXISBANK.NS", "2025-04-25"),
    "AXISBANK_Q4FY26_25Apr2026_clean": ("AXISBANK.NS", "2026-04-25"),
    "HDFCBANK_Q1FY24_17Jul2023_clean": ("HDFCBANK.NS", "2023-07-17"),
    "HDFCBANK_Q1FY27_18Jul2026_clean": ("HDFCBANK.NS", "2026-07-18"),
    "HDFCBANK_Q2FY24_16Oct2023_clean": ("HDFCBANK.NS", "2023-10-16"),
    "HDFCBANK_Q3FY24_16Jan2024_clean": ("HDFCBANK.NS", "2024-01-16"),
    "HDFCBANK_Q4FY24_20Apr2024_clean": ("HDFCBANK.NS", "2024-04-20"),
    "ICICIBANK_Q1FY23_23Jul2022_clean": ("ICICIBANK.NS", "2022-07-23"),
    "ICICIBANK_Q1FY24_22Jul2023_clean": ("ICICIBANK.NS", "2023-07-22"),
    "ICICIBANK_Q1FY25_27Jul2024_clean": ("ICICIBANK.NS", "2024-07-27"),
    "ICICIBANK_Q1FY26_19Jul2025_clean": ("ICICIBANK.NS", "2025-07-19"),
    "ICICIBANK_Q1FY27_18Jul2026_clean": ("ICICIBANK.NS", "2026-07-18"),
    "ICICIBANK_Q2FY23_22Oct2022_clean": ("ICICIBANK.NS", "2022-10-22"),
    "ICICIBANK_Q2FY24_21Oct2023_clean": ("ICICIBANK.NS", "2023-10-21"),
    "ICICIBANK_Q2FY25_26Oct2024_clean": ("ICICIBANK.NS", "2024-10-26"),
    "ICICIBANK_Q3FY23_21Jan2023_clean": ("ICICIBANK.NS", "2023-01-21"),
    "ICICIBANK_Q3FY24_20Jan2024_clean": ("ICICIBANK.NS", "2024-01-20"),
    "ICICIBANK_Q3FY25_25Jan2025_clean": ("ICICIBANK.NS", "2025-01-25"),
    "ICICIBANK_Q3FY26_17Jan2026_clean": ("ICICIBANK.NS", "2026-01-17"),
    "ICICIBANK_Q4FY22_23Apr2022_clean": ("ICICIBANK.NS", "2022-04-23"),
    "ICICIBANK_Q4FY23_22Apr2023_clean": ("ICICIBANK.NS", "2023-04-22"),
    "ICICIBANK_Q4FY24_27Apr2024_clean": ("ICICIBANK.NS", "2024-04-27"),
    "ICICIBANK_Q4FY26_18Apr2026_clean": ("ICICIBANK.NS", "2026-04-18"),
    "INFY_Q1FY23_25Jul2022_clean": ("INFY.NS", "2022-07-25"),
    "INFY_Q1FY24_25Jul2023_clean": ("INFY.NS", "2023-07-25"),
    "INFY_Q1FY25_18Jul2024_clean": ("INFY.NS", "2024-07-18"),
    "INFY_Q1FY26_28Jul2025_clean": ("INFY.NS", "2025-07-28"),
    "INFY_Q1FY27_28Jul2026_clean": ("INFY.NS", "2026-07-28"),
    "INFY_Q2FY23_17Oct2022_clean": ("INFY.NS", "2022-10-17"),
    "INFY_Q2FY24_12Oct2023_clean": ("INFY.NS", "2023-10-12"),
    "INFY_Q2FY25_22Oct2024_clean": ("INFY.NS", "2024-10-22"),
    "INFY_Q2FY26_21Oct2025_clean": ("INFY.NS", "2025-10-21"),
    "INFY_Q3FY23_17Jan2023_clean": ("INFY.NS", "2023-01-17"),
    "INFY_Q3FY24_11Jan2024_clean": ("INFY.NS", "2024-01-11"),
    "INFY_Q3FY25_21Jan2025_clean": ("INFY.NS", "2025-01-21"),
    "INFY_Q3FY26_19Jan2026_clean": ("INFY.NS", "2026-01-19"),
    "INFY_Q4FY22_19Apr2022_clean": ("INFY.NS", "2022-04-19"),
    "INFY_Q4FY23_18Apr2023_clean": ("INFY.NS", "2023-04-18"),
    "INFY_Q4FY24_18Apr2024_clean": ("INFY.NS", "2024-04-18"),
    "INFY_Q4FY25_22Apr2025_clean": ("INFY.NS", "2025-04-22"),
    "INFY_Q4FY26_27Apr2026_clean": ("INFY.NS", "2026-04-27"),
    "RELIANCE_Q1FY26_18Jul2025_clean": ("RELIANCE.NS", "2025-07-18"),
    "RELIANCE_Q2FY24_27Oct2023_clean": ("RELIANCE.NS", "2023-10-27"),
    "RELIANCE_Q2FY26_17Oct2025_clean": ("RELIANCE.NS", "2025-10-17"),
    "RELIANCE_Q3FY24_19Jan2024_clean": ("RELIANCE.NS", "2024-01-19"),
    "RELIANCE_Q3FY26_16Jan2026_clean": ("RELIANCE.NS", "2026-01-16"),
    "RELIANCE_Q4FY26_24Apr2026_clean": ("RELIANCE.NS", "2026-04-24"),
    "TCS_Q1FY23_08Jul2022_clean": ("TCS.NS", "2022-07-08"),
    "TCS_Q1FY24_12Jul2023_clean": ("TCS.NS", "2023-07-12"),
    "TCS_Q1FY25_11Jul2024_clean": ("TCS.NS", "2024-07-11"),
    "TCS_Q1FY26_10Jul2025_clean": ("TCS.NS", "2025-07-10"),
    "TCS_Q1FY27_09Jul2026_clean": ("TCS.NS", "2026-07-09"),
    "TCS_Q2FY23_10Oct2022_clean": ("TCS.NS", "2022-10-10"),
    "TCS_Q2FY24_11Oct2023_clean": ("TCS.NS", "2023-10-11"),
    "TCS_Q2FY25_10Oct2024_clean": ("TCS.NS", "2024-10-10"),
    "TCS_Q2FY26_09Oct2025_clean": ("TCS.NS", "2025-10-09"),
    "TCS_Q3FY23_09Jan2023_clean": ("TCS.NS", "2023-01-09"),
    "TCS_Q3FY24_11Jan2024_clean": ("TCS.NS", "2024-01-11"),
    "TCS_Q3FY25_09Jan2025_clean": ("TCS.NS", "2025-01-09"),
    "TCS_Q3FY26_12Jan2026_clean": ("TCS.NS", "2026-01-12"),
    "TCS_Q4FY22_11Apr2022_clean": ("TCS.NS", "2022-04-11"),
    "TCS_Q4FY23_12Apr2023_clean": ("TCS.NS", "2023-04-12"),
    "TCS_Q4FY24_12Apr2024_clean": ("TCS.NS", "2024-04-12"),
    "TCS_Q4FY25_10Apr2025_clean": ("TCS.NS", "2025-04-10"),
    "TCS_Q4FY26_09Apr2026_clean": ("TCS.NS", "2026-04-09"),
    "WIPRO_Q1FY23_22Jul2022_clean": ("WIPRO.NS", "2022-07-22"),
    "WIPRO_Q1FY24_15Jul2023_clean": ("WIPRO.NS", "2023-07-15"),
    "WIPRO_Q1FY25_22Jul2024_clean": ("WIPRO.NS", "2024-07-22"),
    "WIPRO_Q1FY26_18Jul2025_clean": ("WIPRO.NS", "2025-07-18"),
    "WIPRO_Q1FY27_17Jul2026_clean": ("WIPRO.NS", "2026-07-17"),
    "WIPRO_Q2FY23_15Oct2022_clean": ("WIPRO.NS", "2022-10-15"),
    "WIPRO_Q2FY24_18Oct2023_clean": ("WIPRO.NS", "2023-10-18"),
    "WIPRO_Q2FY25_18Oct2024_clean": ("WIPRO.NS", "2024-10-18"),
    "WIPRO_Q2FY26_17Oct2025_clean": ("WIPRO.NS", "2025-10-17"),
    "WIPRO_Q3FY23_16Jan2023_clean": ("WIPRO.NS", "2023-01-16"),
    "WIPRO_Q3FY24_12Jan2024_clean": ("WIPRO.NS", "2024-01-12"),
    "WIPRO_Q3FY25_20Jan2025_clean": ("WIPRO.NS", "2025-01-20"),
    "WIPRO_Q3FY26_19Jan2026_clean": ("WIPRO.NS", "2026-01-19"),
    "WIPRO_Q4FY24_19Apr2024_clean": ("WIPRO.NS", "2024-04-19"),
    "WIPRO_Q4FY25_17Apr2025_clean": ("WIPRO.NS", "2025-04-17"),
    "WIPRO_Q4FY26_17Apr2026_clean": ("WIPRO.NS", "2026-04-17"),
}

BENCHMARK_FILE  = "NIFTY50"   # data/prices/NIFTY50_prices.csv  (price_fetcher.py banata hai, ^NSEI se)
CALL_DATES_FILE = Path("data/call_dates_verified.json")
HORIZONS        = (1, 3, 7)
PRIMARY_SIGNAL, PRIMARY_RETURN = "hedging_z", "abn_t3"

_PRICE_CACHE = {}


def load_call_dates() -> dict:
    """Verified call dates (stem -> 'YYYY-MM-DD'). Missing ho to filename date fallback."""
    if not CALL_DATES_FILE.exists():
        log.warning("  data/call_dates_verified.json nahi mili - filename dates use ho rahi hain!")
        log.warning("  Pehle chalao: python ingestion/verify_call_dates.py")
        return {}
    return {k: v["call_date"] for k, v in json.loads(CALL_DATES_FILE.read_text()).items()}


def load_prices(name: str):
    """data/prices/{name}_prices.csv, date-sorted, tz-naive. Cached."""
    if name in _PRICE_CACHE:
        return _PRICE_CACHE[name]
    path = DIR_PRICES / f"{name}_prices.csv"
    df = None
    if path.exists():
        df = pd.read_csv(path, index_col="date", parse_dates=True).sort_index()
        if getattr(df.index, "tz", None) is not None:
            df.index = df.index.tz_localize(None)
    else:
        log.warning(f"  Price file nahi mili: {path}")
    _PRICE_CACHE[name] = df
    return df


def get_hedging_score(file_stem: str):
    """Executive sentences mein se hedging wale sentences ka fraction."""
    path = DIR_PROCESSED / (file_stem + "_hedging.csv")
    if not path.exists():
        log.warning(f"  Hedging file nahi mili: {path}")
        return None
    df = pd.read_csv(path)
    return round(df["is_hedging"].sum() / len(df), 4) if len(df) else None


def get_net_sentiment(file_stem: str):
    """Mean(positive) - mean(negative) FinBERT probability. Sentiment CSV na ho to None."""
    path = DIR_PROCESSED / (file_stem + "_sentiment.csv")
    if not path.exists():
        return None
    df = pd.read_csv(path)
    return round(df["positive"].mean() - df["negative"].mean(), 4) if len(df) else None


def window_return(df, call_date: str, days: int):
    """Close-to-close % return: last close on/before call_date -> days-th trading close after."""
    if df is None or "close" not in df:
        return None
    ts = pd.Timestamp(call_date)
    past, future = df[df.index <= ts], df[df.index > ts]
    if past.empty or len(future) < days:
        return None
    p0, pn = past["close"].iloc[-1], future["close"].iloc[days - 1]
    return round((pn / p0 - 1) * 100, 4)


def build_dataset() -> pd.DataFrame:
    """Har transcript: signals + raw returns + Nifty-relative (abnormal) returns."""
    call_dates = load_call_dates()
    bench = load_prices(BENCHMARK_FILE)
    if bench is None:
        log.warning("  Nifty 50 prices nahi mile -> abnormal returns NaN rahenge. "
                    "Chalao: python ingestion/price_fetcher.py (ab ^NSEI bhi fetch karta hai)")

    n_files = len(list(DIR_PROCESSED.glob("*_clean.txt")))
    if n_files != len(TRANSCRIPT_MAP):
        log.warning(f"  MISMATCH: {n_files} transcript files vs {len(TRANSCRIPT_MAP)} TRANSCRIPT_MAP entries")

    rows = []
    for stem, (ticker, fname_date) in TRANSCRIPT_MAP.items():
        hedging = get_hedging_score(stem)
        if hedging is None:
            continue
        call_date = call_dates.get(stem, fname_date)
        stock = load_prices(ticker.replace(".NS", ""))

        row = {"file": stem[:40], "ticker": ticker, "call_date": call_date,
               "filename_date": fname_date, "hedging_pct": hedging,
               "net_sentiment": get_net_sentiment(stem)}
        for n in HORIZONS:
            r = window_return(stock, call_date, n)
            b = window_return(bench, call_date, n)
            row[f"return_t{n}"] = r
            row[f"abn_t{n}"] = round(r - b, 4) if (r is not None and b is not None) else None
        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    def zscore(s):
        sd = s.std(ddof=0)
        return (s - s.mean()) / sd if sd and sd > 0 else s * np.nan

    df["hedging_z"] = df.groupby("ticker")["hedging_pct"].transform(zscore)
    df["net_sentiment_z"] = df.groupby("ticker")["net_sentiment"].transform(zscore)
    return df


def correlate(df: pd.DataFrame, signal: str, ret: str) -> dict:
    sub = df[[signal, ret]].dropna()
    if len(sub) < 10 or sub[signal].nunique() < 3:
        return {"signal": signal, "return": ret, "n": len(sub)}
    r, p = stats.pearsonr(sub[signal], sub[ret])
    rho, sp = stats.spearmanr(sub[signal], sub[ret])
    return {"signal": signal, "return": ret, "n": len(sub),
            "pearson_r": round(r, 4), "pearson_p": round(p, 4),
            "spearman_rho": round(rho, 4), "spearman_p": round(sp, 4)}


def main():
    log.info("=" * 55)
    log.info("AlphaLens  |  Signal Correlator v2")
    log.info("=" * 55)

    df = build_dataset()
    if df.empty:
        log.error("Koi data nahi mila — TRANSCRIPT_MAP / hedging CSVs check karo")
        return

    n_changed = int((df["call_date"] != df["filename_date"]).sum())
    log.info(f"  {len(df)} transcripts | {n_changed} mein verified call date filename se alag")

    signals = ["hedging_pct", "hedging_z"]
    if df["net_sentiment"].notna().sum() >= 10:
        signals += ["net_sentiment", "net_sentiment_z"]
    else:
        log.info("  (sentiment CSVs nahi mile - sirf hedging signals; pehle sentiment_pipeline.py chalao)")
    returns = [f"abn_t{n}" for n in HORIZONS] + [f"return_t{n}" for n in HORIZONS]
    returns = [r for r in returns if df[r].notna().sum() >= 10]
    if not any(r.startswith("abn_") for r in returns):
        log.warning("  Abnormal returns available nahi - sirf raw returns pe test ho raha hai")

    res = pd.DataFrame([correlate(df, s, r) for s in signals for r in returns])
    k = len(res.dropna(subset=["pearson_p"])) if "pearson_p" in res else 0
    bonf = 0.05 / max(k, 1)

    log.info("\n-- PRIMARY test (pehle se fixed) " + "-" * 22)
    prim = res[(res.signal == PRIMARY_SIGNAL) & (res["return"] == PRIMARY_RETURN)]
    if prim.empty or "pearson_p" not in prim or prim["pearson_p"].isna().all():
        log.info("  Primary test ke liye data nahi (Nifty prices missing?)")
    else:
        row = prim.iloc[0]
        log.info(f"  {PRIMARY_SIGNAL} -> {PRIMARY_RETURN}: n={int(row.n)}  Pearson r={row.pearson_r} (p={row.pearson_p})"
                 f"  Spearman rho={row.spearman_rho} (p={row.spearman_p})")
        log.info("  " + ("SIGNIFICANT at 0.05" if row.pearson_p < 0.05 else "Not significant at 0.05"))

    log.info(f"\n-- Exploratory ({k} tests; Bonferroni threshold p < {bonf:.4f}) " + "-" * 6)
    log.info("\n" + res.to_string(index=False))
    if "pearson_p" in res:
        hits = res[(res.pearson_p < bonf)]
        log.info("  Bonferroni ke baad survive: " + (", ".join(f"{a}->{b}" for a, b in zip(hits.signal, hits['return'])) or "koi nahi"))

    out_dir = Path("backtesting/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "correlation_results.csv", index=False)
    res.to_csv(out_dir / "correlation_stats.csv", index=False)
    log.info(f"\n  Saved: {out_dir.resolve()}/correlation_results.csv , correlation_stats.csv")
    log.info("-" * 55)


if __name__ == "__main__":
    main()