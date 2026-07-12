"""
app.py
AlphaLens - Week 6
Streamlit dashboard — sentiment, hedging, correlation visualize karta hai.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
from config import DIR_PROCESSED, DIR_PRICES
