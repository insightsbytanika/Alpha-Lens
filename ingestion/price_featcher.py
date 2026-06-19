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
