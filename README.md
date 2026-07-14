# AlphaLens 📊
### Earnings Call Intelligence System for NSE-Listed Indian Companies

> A financial NLP pipeline that processes earnings call transcripts, scores executive sentiment with FinBERT, detects hedging language, and backtests those signals against real stock price movement — built specifically for the Indian markets, where no comparable open-source tool exists.

**Status: 🚧 Active Development** — this is a real, working pipeline, not a mockup. Numbers below are current and updated as the dataset grows.

---

## Why This Exists

Every quarter, NSE-listed companies hold earnings calls. Research from Stanford and MIT has shown that *how* executives speak — confident vs. hedging, specific vs. vague — carries predictive signal beyond the numbers themselves. That kind of language-intelligence pipeline exists inside firms like Goldman Sachs and Morgan Stanley. It doesn't exist, openly, for retail investors or students — and every comparable open-source project is built on US S&P 500 data, not Indian markets.

AlphaLens is our attempt to close that gap: an end-to-end, statistically rigorous pipeline built from scratch for NSE earnings calls.

---

## Current Progress

| Metric | Status |
|---|---|
| Transcripts processed | **24** NSE earnings calls |
| Sentiment scoring | FinBERT pipeline live, generating real (non-simulated) scores |
| Dashboard | Live and functional |
| Speaker diarisation | Implemented (pyannote.audio) |
| Hedging detector | Implemented — rule layer + classifier |
| Backtesting | Running — T+3 Pearson correlation: **0.27**, p-value: **0.24** |

**Honest read on the stats:** a correlation of 0.27 with p = 0.24 is not statistically significant yet — at this sample size (24 transcripts), it's an early signal, not proof. We know the difference between "found a correlation" and "found a real correlation," and we're not claiming the latter until the numbers earn it. Scaling toward 200+ transcripts (per our build plan) is the next milestone specifically to get p below 0.05 with confidence, one way or the other.

---

## What It Does

1. **Fetches transcripts** — from NSE investor relations pages and Seeking Alpha
2. **Separates speakers** — diarisation isolates CEO, CFO, and analyst voices
3. **Scores sentiment** — FinBERT run per speaker, per section of the call
4. **Detects hedging language** — flags markers like "we expect," "subject to," "potentially"
5. **Tracks tone trajectory** — does confidence rise or fall across the call?
6. **Compares across quarters** — is a company's language improving or deteriorating over time?
7. **Backtests the signal** — correlates language patterns with actual next-day (and T+3) price movement
8. **Outputs a credibility score** — how strongly a company's language predicts its own stock behaviour

---

## System Architecture

| Layer | What it does | Stack |
|---|---|---|
| Data Ingestion | Scrapes NSE IR pages, Seeking Alpha, fetches price history | Python, BeautifulSoup, yfinance |
| Transcription | Converts call audio to timestamped text, runs locally | OpenAI Whisper |
| Speaker Diarisation | Separates CEO / CFO / analyst voices | pyannote.audio |
| NLP Pipeline | Domain-specific financial sentiment | FinBERT, HuggingFace Transformers |
| Hedging Detector | Flags uncertainty markers, vague language | Custom rule layer + BERT classifier |
| Backtesting Engine | Correlates sentiment with T+1 / T+3 price movement | pandas, scipy, statsmodels |
| Storage | Structured data + raw files | PostgreSQL, AWS S3 |
| Dashboard | Sentiment timeline, hedging heatmap, comparisons | Streamlit / Plotly |
| MLOps | Experiment tracking, versioning | MLflow, Docker, GitHub Actions |

---

## Data Sources (All Free, All Public)

- **NSE India Investor Relations** — earnings call transcripts, quarterly results for NSE 500 companies
- **Seeking Alpha** — pre-cleaned English transcripts
- **Yahoo Finance (`yfinance`)** — historical price data, 20+ years, no API key required
- **BSE Corporate Filings** — backup transcript source
- **Company IR audio pages** — recordings published publicly under SEBI regulation

---

## Tech Stack

```
NLP            FinBERT, HuggingFace Transformers, PEFT/LoRA
Transcription  OpenAI Whisper (local), pyannote.audio
Data Collection BeautifulSoup, requests, yfinance, pandas
Statistics     scipy, statsmodels, numpy
Storage        PostgreSQL, AWS S3, parquet
Dashboard      Streamlit, Plotly
Cloud          AWS EC2, S3, Lambda
MLOps          MLflow, Docker, GitHub Actions
```

---

## Failure Log

Documenting what broke and how it got fixed — because that's the actual engineering.

**FinBERT misread Indian financial phrasing.** General-purpose FinBERT, trained on US filings, scored neutral-to-positive on phrases like "subdued demand environment." Fine-tuning on manually labelled Indian earnings-call sentences is in progress to close this gap.

**Whisper mangled financial jargon.** Terms like "EBITDA" and "capex" were transcribed as nonsense ("E better," "Cape X"). A post-processing correction layer using a financial-term dictionary was added to catch and fix known errors.

**Backtest signal isn't significant yet.** At 24 transcripts, T+3 correlation sits at 0.27 with p = 0.24 — an early, unproven signal. This is being tracked honestly rather than dressed up, and is the core reason the dataset is being scaled up next.

---

## Roadmap

- [ ] Scale dataset from 24 → 200+ transcripts
- [ ] Re-run backtest at scale to determine if signal reaches p < 0.05
- [ ] Fine-tune FinBERT on Indian earnings-call vocabulary
- [ ] Deploy dashboard to Streamlit Cloud
- [ ] Move storage/compute to AWS (S3, EC2, Lambda for scheduled scraping)
- [ ] Set up MLflow experiment tracking

---

## Team

| | Focus |
|---|---|
| **Tanika** | FinBERT fine-tuning, hedging detector, sentiment scoring, backtesting engine, MLflow tracking |
| **Manav** | Audio transcription (Whisper), speaker diarisation, data scraping pipeline, AWS deployment, dashboard |

---
## Why This Is Different

- No open-source tool currently targets NSE earnings calls specifically — every comparable project uses US S&P 500 data.
- The backtesting is built on real historical price data with proper temporal train/test splits — not simulated.
- The pipeline handles a problem most student projects skip entirely: speaker-level attribution (CEO sentiment ≠ analyst-question sentiment ≠ overall call sentiment).

---

This README reflects the project's actual current state and will be updated as the dataset and results grow.

