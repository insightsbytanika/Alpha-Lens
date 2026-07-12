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

@st.cache_data
def load_hedging_data():
    """Saari hedging CSVs ek table mein."""
    all_data = []
    for f in DIR_PROCESSED.glob("*_hedging.csv"):
        df = pd.read_csv(f)
        df["source"] = f.stem.replace("_clean_hedging", "")
        all_data.append(df)
    if not all_data:
        return pd.DataFrame()
    return pd.concat(all_data, ignore_index=True)

@st.cache_data
def load_correlation_data():
    """Backtesting results load karo."""
    path = Path("backtesting/results/correlation_results.csv")
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


hedging_df = load_hedging_data()
corr_df    = load_correlation_data()


st.success(f"✓ {len(hedging_df)} sentences loaded across all transcripts")

# ── Section 1: Hedging Comparison ─────────────────
st.header("🔍 Hedging Language — Company Comparison")

if not hedging_df.empty:
    # Har source ka hedging % nikalo
    summary = hedging_df.groupby("source")["is_hedging"].mean().reset_index()
    summary.columns = ["Company / Quarter", "Hedging %"]
    summary["Hedging %"] = (summary["Hedging %"] * 100).round(2)
    summary = summary.sort_values("Hedging %", ascending=False)

    fig1 = px.bar(
        summary,
        x="Company / Quarter",
        y="Hedging %",
        title="Hedging Language % per Earnings Call",
        color="Hedging %",
        color_continuous_scale="RdYlGn_r",  # red = high hedging, green = low
    )
    fig1.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig1, use_container_width=True)

else:
    st.warning("Hedging data nahi mila — pehle hedging_detector.py chalao")

st.divider()

# ── Section 2: Correlation Table ──────────────────
st.header("📊 Backtesting Results")

if not corr_df.empty:
    st.dataframe(
        corr_df.style.background_gradient(
            subset=["return_t1", "return_t3", "return_t7"],
            cmap="RdYlGn"
        ),
        use_container_width=True,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Hedging %",
                f"{corr_df['hedging_pct'].mean()*100:.1f}%")
    col2.metric("Avg T+1 Return",
                f"{corr_df['return_t1'].mean():.2f}%")
    col3.metric("Avg T+3 Return",
                f"{corr_df['return_t3'].mean():.2f}%")
else:
    st.warning("Correlation data nahi mila — pehle signal_correlator.py chalao")

st.divider()

# ── Section 3: Sentiment Explorer ─────────────────
st.header("💬 Sentiment Explorer")

if not hedging_df.empty:
    sources = hedging_df["source"].unique().tolist()
    selected = st.selectbox("Transcript chuno:", sources)

    filtered = hedging_df[hedging_df["source"] == selected]
    hedging_sentences = filtered[filtered["is_hedging"] == True]

    col1, col2 = st.columns(2)
    col1.metric("Total Sentences", len(filtered))
    col2.metric("Hedging Sentences", len(hedging_sentences))

    st.markdown("**Hedging sentences:**")
    for _, row in hedging_sentences.head(10).iterrows():
        st.markdown(f"> {row['sentence']}")
        st.caption(f"Words: {row['hedging_words']}")