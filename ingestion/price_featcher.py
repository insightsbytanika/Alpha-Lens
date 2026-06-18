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