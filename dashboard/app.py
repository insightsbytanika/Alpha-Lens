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

#Page config
st.set_page_config(
    page_title="AlphaLens",
    page_icon="📈",
    layout="wide",
)

# ── Header ────────────────────────────────────────
st.title("📈 AlphaLens")
st.subheader("Earnings Call Intelligence System — NSE Listed Companies")
st.divider()

# ── Sidebar ───────────────────────────────────────
st.sidebar.title("Controls")
st.sidebar.markdown("AlphaLens v1.0")
