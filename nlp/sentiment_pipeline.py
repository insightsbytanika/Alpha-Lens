"""
sentiment_pipeline.py
AlphaLens - Week 3
FinBERT se har sentence ka sentiment score nikalta hai.
Input: data/processed/ ki clean .txt files
Output: data/processed/ mein _sentiment.csv
"""

from transformers import BertTokenizer, BertForSequenceClassification
from transformers import pipeline
from pathlib import Path
import pandas as pd
import logging

# Config
INPUT_DIR  = Path("data/processed")
OUTPUT_DIR = Path("data/processed")
MODEL_NAME = "ProsusAI/finbert"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

print("imports working")