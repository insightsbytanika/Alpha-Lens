'''
price_featcher.py featches the historical price data of nse listed companies via yfinance
stores 1 csv per ticket inside data/prices
'''

import yfinance as yf
import pandas as pd
from pathlib import path
import datetime 
import time
import logging

''' Config ────────────────────────────────────────────────────────────────────
NSE tickers need ".NS" suffix for Yahoo Finance'''

NSE_TICKERS= [
    "INFY.NS", #infosis
    "tcs.NS" ,
    "HDFCBANK.NS", 
    "RELIANCE.NS" ,
    "WIPRO.NS",
    "ICICIBANK.NS",
    "AXISBANK.NS",
    "LT.NS" #Larsen and tuobro
]

BACKTEST_START="2022-01-01"
BACKTEST_END=datetime.today().strftime("%Y-%m-%d")
OUTPUT_DIR=path("data\price")
SLEEP_BETWEEN=1.5

# Logging setup ─────────────────────────────────────────────────────────────
logging.basic.config(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)
log=logging.getLogger(__name__)

#core function

def featch_price_history(ticker :str ) -> pd.dataframe | None :
    ''' download ohlcv  data for one ticker.
    returns a clean dataframe or none if the download fails 
    '''
    log.info(f"feaching {ticker}....")
    try:
        df=yf.download(
            ticker,
            start = BACKTEST_START,
            auto_adjust=True,
            postgres=False
        )
        if df.empty:
            log.warning(f" No data returned for {ticker} — skipping")
            return None 
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns= df.columns.get_level_values(0)
        
        df.index.name="date"
        df.columns= [c.lower().replace(" ","_") for c in df columns ]
        df["ticker"]=ticker
        log.info(f"  ✓ {len(df)} rows  |  {df.index[0].date()} → {df.index[-1].date()}")
        return df
 
    except Exception as e:
        log.error(f"  ✗ Failed for {ticker}: {e}")
        return None
 
 



