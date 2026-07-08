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

def process_file(txt_path: Path) -> Path:
    """Ek transcript file uthao, hedging detect karo, CSV save karo."""
    log.info(f"Processing: {txt_path.name}")
    text = txt_path.read_text(encoding="utf-8")

    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 20]
    log.info(f"  {len(sentences)} sentences mile")

    results = []
    for i, sent in enumerate(sentences):
        hedging = detect_hedging(sent)
        results.append({
            "sentence_id":   i,
            "sentence":      sent,
            **hedging,
        })

    df = pd.DataFrame(results)
    out_path = DIR_PROCESSED / (txt_path.stem + "_hedging.csv")
    df.to_csv(out_path, index=False)

    hedging_count = df["is_hedging"].sum()
    log.info(f"  {hedging_count} hedging sentences mile {len(df)} mein se")
    log.info(f"  -> Saved: {out_path}")
    return out_path

def main():
    log.info("=" * 55)
    log.info("AlphaLens  |  Hedging Detector  |  Week 3")
    log.info("=" * 55)

    files = list(DIR_PROCESSED.glob("*_clean.txt"))
    if not files:
        log.warning("Koi _clean.txt file nahi mili — pehle loader.py chalao!")
        return

    log.info(f"  {len(files)} transcript(s) mili")
    for f in files:
        process_file(f)

    log.info("")
    log.info("-- Done " + "-" * 47)
    log.info(f"  Results yahan hain: {DIR_PROCESSED.resolve()}")
    log.info("-" * 55)


if __name__ == "__main__":
    main()
