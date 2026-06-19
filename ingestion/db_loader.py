"""
ingestion/db_loader.py
------------------------
Pushes processed transcripts and price data into Postgres.
 
SCHEMA ASSUMPTION:
  No schema existed yet in this project, so this module defines and creates
  a minimal one on first run (see SCHEMA_SQL below):
    - companies(symbol PK, name)
    - transcripts(id PK, symbol FK, call_date, source, file_path, raw_text)
    - prices(symbol FK, date, open, high, low, close, volume) — matches a
      typical yfinance-style CSV. If price_fetcher.py's actual CSV columns
      differ, adjust COLUMN MAPPING in load_prices_csv() below — that's the
      one place column names are assumed.
 
Requires: psycopg2-binary, pandas
"""
 
import logging
from datetime import date
from pathlib import Path
from typing import Optional
 
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
 
from config import DATABASE_URL
 
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
 
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS companies (
    symbol      TEXT PRIMARY KEY,
    name        TEXT
);
 
CREATE TABLE IF NOT EXISTS transcripts (
    id          SERIAL PRIMARY KEY,
    symbol      TEXT REFERENCES companies(symbol),
    call_date   DATE,
    source      TEXT,           -- 'nse' or 'seeking_alpha'
    file_path   TEXT,           -- path to raw file on disk
    raw_text    TEXT,
    UNIQUE (symbol, call_date, source)
);
 
CREATE TABLE IF NOT EXISTS prices (
    symbol      TEXT REFERENCES companies(symbol),
    date        DATE,
    open        NUMERIC,
    high        NUMERIC,
    low         NUMERIC,
    close       NUMERIC,
    volume      BIGINT,
    PRIMARY KEY (symbol, date)
);
"""
 
 
def get_connection():
    """
    Opens a new psycopg2 connection using DATABASE_URL from config.py
    (built from .env values — never hardcode credentials here).
    """
    return psycopg2.connect(DATABASE_URL)
 
 
def init_schema() -> None:
    """Creates tables if they don't already exist. Safe to call repeatedly."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        conn.commit()
    logger.info("Schema verified/created.")
 
 
def upsert_company(symbol: str, name: Optional[str] = None) -> None:
    """Ensures a row exists in companies before transcripts/prices reference it."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO companies (symbol, name)
                VALUES (%s, %s)
                ON CONFLICT (symbol) DO UPDATE
                    SET name = COALESCE(EXCLUDED.name, companies.name)
                """,
                (symbol.upper(), name),
            )
        conn.commit()
 
 
def load_transcript(symbol: str, call_date: date, source: str, file_path: str, raw_text: str) -> None:
    """
    Inserts one transcript record. Uses ON CONFLICT to make re-runs
    idempotent — re-loading the same (symbol, call_date, source) updates
    rather than duplicates.
    """
    upsert_company(symbol)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO transcripts (symbol, call_date, source, file_path, raw_text)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (symbol, call_date, source) DO UPDATE
                    SET file_path = EXCLUDED.file_path,
                        raw_text = EXCLUDED.raw_text
                """,
                (symbol.upper(), call_date, source, file_path, raw_text),
            )
        conn.commit()
    logger.info("Loaded transcript: %s / %s / %s", symbol, call_date, source)
 
 
def load_prices_csv(csv_path: str, symbol: Optional[str] = None) -> int:
    """
    Bulk-loads a price CSV (as produced by price_fetcher.py) into the
    prices table. Idempotent via ON CONFLICT on (symbol, date).
 
    COLUMN MAPPING (adjust here if price_fetcher.py's actual headers differ):
      Expects either yfinance-default columns (Date, Open, High, Low, Close,
      Volume) or already-lowercased equivalents. 'symbol' is taken from a
      'Symbol'/'symbol' column if present in the CSV, otherwise from the
      `symbol` argument — at least one of the two must supply it.
 
    Returns number of rows loaded.
    """
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().lower() for c in df.columns]
 
    required = {"date", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"{csv_path}: missing expected columns {missing}. "
            "Check price_fetcher.py's output format and update the COLUMN "
            "MAPPING note in load_prices_csv() if its headers differ."
        )
 
    if "symbol" in df.columns:
        df["symbol"] = df["symbol"].str.upper()
    elif symbol:
        df["symbol"] = symbol.upper()
    else:
        raise ValueError(
            f"{csv_path} has no 'symbol' column and no symbol was passed in — "
            "can't load without knowing which ticker this is."
        )
 
    df["date"] = pd.to_datetime(df["date"]).dt.date
 
    for sym in df["symbol"].unique():
        upsert_company(sym)
 
    rows = list(
        df[["symbol", "date", "open", "high", "low", "close", "volume"]]
        .itertuples(index=False, name=None)
    )
 
    with get_connection() as conn:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO prices (symbol, date, open, high, low, close, volume)
                VALUES %s
                ON CONFLICT (symbol, date) DO UPDATE
                    SET open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume
                """,
                rows,
            )
        conn.commit()
 
    logger.info("Loaded %d price rows from %s", len(rows), csv_path)
    return len(rows)
 
 
def load_transcript_file(file_path: str, symbol: str, call_date: date, source: str) -> None:
    """Convenience wrapper: reads a .txt transcript off disk and loads it."""
    text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    load_transcript(symbol, call_date, source, str(file_path), text)
 
 
if __name__ == "__main__":
    init_schema()
    logger.info("db_loader ready. Call load_prices_csv(...) / load_transcript_file(...) as needed.")