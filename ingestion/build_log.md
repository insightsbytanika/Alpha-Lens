<!--
WHAT THIS FILE IS:
A private, running diary of the AlphaLens build — not a polished doc, not
for recruiters. Every time something breaks and gets fixed, or a real
decision gets made, it gets logged here, dated, in the moment.

WHY IT EXISTS:
1. Memory fades fast. The exact error message and the reasoning behind a
   fix are clearest right when it happens — not 6 weeks later in an
   interview prep session.
2. This is the raw material for the README's "Failure Log" section and
   for interview answers. Polished lines like "we fine-tuned FinBERT and
   went from 61% to 84% accuracy" start as messy notes like this one.
3. It's proof of process. A messy, honest log with real timestamps is
   more convincing evidence of real work than a clean README alone.

HOW TO USE IT:
- Add a new dated entry every time you: fix a bug, hit something
  confusing, make a design decision, or finish a script.
- Don't polish it. Write it like you're talking to yourself.
- Keep it short — bullet points, not essays.
- This file is NOT meant to be shown to recruiters as-is. When the
  project is done, you'll mine this log to write the actual README and
  your interview answers.
-->

# AlphaLens — Build Log

---

## 2026-06-28 — Week 1: Price Fetcher

**What I built:**
`ingestion/price_fetcher.py` — pulls 3 years of historical OHLCV price
data for 8 NSE-listed tickers via yfinance, saves one CSV per ticker to
`data/prices/`.

**Bugs I hit while writing it by hand:**
- `path("data\price")` → should be `Path("data/prices")`. Mixed up
  lowercase `path` vs the imported `Path` class, used a backslash
  instead of forward slash, and singular `price` instead of `prices`.
- `postgress=False` → should be `progress=False` in `yf.download()`.
  One-letter typo, nothing to do with the database.
- `exits_ok=True` → should be `exist_ok=True` in `.mkdir()`.
- Function defined as `featch_price_history` but called as
  `fetch_price_history` elsewhere — name mismatch from a typo in the
  definition.
- Forgot to pass `end=BACKTEST_END` into `yf.download()` even though the
  variable was defined.
- Indentation bug: the "CSVs saved in" and closing summary lines were
  nested inside `if failed:`, so they'd only print on failure instead of
  every run.

**Lesson:** typing ML/data code by hand (vs pasting) surfaces a lot of
small case-sensitivity and one-letter typos. Running the script in small
steps catches these faster than writing the whole thing first.

**Result:**
7 out of 8 tickers succeeded. `WIPRO.NS` failed with:
```
$WIPRO.NS: possibly delisted; no price data found (1d 2022-01-01 -> 2026-06-29)
```

**Investigating:** Wipro is definitely still listed on NSE, so this is
likely a transient yfinance/Yahoo API hiccup, not a real delisting.
Next step: test `yf.Ticker('WIPRO.NS').history()` directly to confirm,
then consider adding retry logic with backoff for transient failures
like this — real production scrapers handle this rather than just
logging a failure and moving on.

**Possible future Failure Log entry (for README):**
> "Price fetcher succeeded on 7/8 tickers in first run — WIPRO.NS failed
> with a transient API error. Added retry logic with exponential backoff
> so single bad API responses don't kill confidence in an otherwise
> working pipeline."

---
