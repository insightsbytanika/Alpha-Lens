"""
hedging_detector.py
AlphaLens - Week 3 (updated: executive-only + word-boundary matching)
Transcript mein uncertain/hedging language dhundta hai - SIRF management ki lines mein.
Input: data/processed/ ki _clean.txt files
Output: data/processed/ mein _hedging.csv   (same schema as before)

Changes vs purana version:
  1. speaker_filter se sirf executive lines score hoti hain (moderator/analyst nahi)
  2. matching word-boundary se hoti hai - pehle "may" jaise words kisi bhi shabd ke
     andar match ho jaate the, aur "expect" ke saath "expected" double count hota tha
  3. purana `[20:]` slice hata diya (wo pehle 20 sentences blindly skip karta tha);
     boilerplate ab speaker filter hata deta hai
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import re
import pandas as pd
from config import DIR_PROCESSED
from nlp.speaker_filter import filter_executive_text
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Hedging words aur phrases ki list (lexicon unchanged)
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
HEDGING_PATTERNS = [(w, re.compile(r"\b" + re.escape(w) + r"\b")) for w in HEDGING_WORDS]


def split_sentences(text: str) -> list:
    """Simple split (sentiment_pipeline jaisa hi) taaki dono scripts same sentences dekhein."""
    return [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 20]


def detect_hedging(sentence: str) -> dict:
    """Ek sentence mein hedging words dhundta hai."""
    sentence_lower = sentence.lower()
    matched = [w for w, pat in HEDGING_PATTERNS if pat.search(sentence_lower)]
    word_count = len(sentence.split())
    score = round(len(matched) / max(word_count, 1), 4)
    return {
        "hedging_count": len(matched),
        "hedging_score": score,
        "hedging_words": ", ".join(matched) if matched else "none",
        "is_hedging":    len(matched) > 0,
    }


def process_file(txt_path: Path) -> Path:
    """Ek transcript file uthao, executive text nikalo, hedging detect karo, CSV save karo."""
    log.info(f"Processing: {txt_path.name}")
    text = txt_path.read_text(encoding="utf-8")
    exec_text = filter_executive_text(text)
    sentences = split_sentences(exec_text)
    log.info(f"  {len(sentences)} executive sentences ({len(exec_text) / max(len(text), 1):.0%} of text)")

    results = []
    for i, sent in enumerate(sentences):
        results.append({"sentence_id": i, "sentence": sent, **detect_hedging(sent)})

    df = pd.DataFrame(results)
    out_path = DIR_PROCESSED / (txt_path.stem + "_hedging.csv")
    df.to_csv(out_path, index=False)
    log.info(f"  {int(df['is_hedging'].sum())} hedging sentences / {len(df)}  -> {out_path.name}")
    return out_path


def main():
    log.info("=" * 55)
    log.info("AlphaLens  |  Hedging Detector (executive-only)")
    log.info("=" * 55)

    files = sorted(DIR_PROCESSED.glob("*_clean.txt"))
    if not files:
        log.warning("Koi _clean.txt file nahi mili — pehle loader.py chalao!")
        return

    log.info(f"  {len(files)} transcript(s) mili")
    for f in files:
        process_file(f)

    log.info("-- Done " + "-" * 47)


if __name__ == "__main__":
    main()