# AlphaLens - run order (after Oct 2026 data-quality + signal fixes)
Run from the repo root.
pip install -r requirements.txt

python ingestion/split_media_earnings.py   # 1. Infosys/ICICI: media/press call hatao, sirf analyst call rakho (idempotent, backup banata hai)
python ingestion/verify_call_dates.py      # 2. asli call dates -> data/call_dates_verified.json (Infosys/Wipro filenames filing date the)
python ingestion/price_fetcher.py          # 3. prices + Nifty 50 (^NSEI -> data/prices/NIFTY50_prices.csv)
python nlp/hedging_detector.py             # 4. executive-only hedging (seconds)
python nlp/sentiment_pipeline.py           # 5. FinBERT, executive-only (~20-30 min CPU) - optional for the primary hedging test
python backtesting/signal_correlator.py    # 6. Pearson + Spearman, abnormal returns, primary test + exploratory table
 
 
Audit helper: `python nlp/speaker_filter.py` prints the executive share of every transcript
(anything flagged `<-- CHECK` is below 30% or above 95%; WIPRO_Q1FY23 is known to be ~44% because no analyst intros are found).

## What the correlator reports
- **Primary test (fixed in advance):** `hedging_z -> abn_t3` (company-normalised hedging vs Nifty-relative 3-day return).
- **Exploratory table:** every other signal x horizon, with a Bonferroni threshold. Do not pick a winner from this table and report it as the result.
- Raw-return rows are kept only for comparison with the earlier baseline (r = 0.02, p = 0.82).

## Known limitations
- 24 files (Axis, ICICI, Reliance, TCS, some Wipro) have no call date inside the text, so the filename date is used. Spot-check a few against the PDFs.
- Z-scores use each company's full-sample mean (fine for correlation, not for a live trading rule).
- WIPRO_Q1FY23 and the 6 Reliance files use weaker speaker detection (no analyst intro lines).