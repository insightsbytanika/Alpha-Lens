"""
hedging_detector.py
AlphaLens - Week 3
Transcript mein uncertain/hedging language dhundta hai.
Input: data/processed/ ki _clean.txt files
Output: data/processed/ mein _hedging.csv
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import re
import pandas as pd
from pathlib import Path
from config import DIR_PROCESSED
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Hedging words aur phrases ki list
HEDGING_WORDS = [
    "expect", "expected", "expecting",
    "potentially", "potential",
    "possibly", "possible",
    "approximately", "roughly",
    "may", "might", "could", "should",
    "subject to", "depending on",
    "if conditions", "we believe",
    "we anticipate", "we hope",
    "going forward", "remain cautious",
    "uncertainty", "uncertain",
    "challenges", "headwinds",
    "volatile", "volatility",
    "monitor", "monitoring",
    "cautious", "caution",
]

def detect_hedging(sentence: str) -> dict:
    """
    Ek sentence mein hedging words dhundta hai.
    Returns dict with score and matched words.
    """
    sentence_lower = sentence.lower()
    matched = []

    for phrase in HEDGING_WORDS:
        if phrase in sentence_lower:
            matched.append(phrase)
    # Score = kitne hedging words mile / total words
    word_count = len(sentence.split())
    score = round(len(matched) / max(word_count, 1), 4)
    return {
        "hedging_count": len(matched),
        "hedging_score": score,
        "hedging_words": ", ".join(matched) if matched else "none",
        "is_hedging":    len(matched) > 0,
    }


print("functions ready")
