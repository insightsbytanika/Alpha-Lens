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
def extract_management_names(text: str) -> list:
    """Transcript ke shuru se Management list ke naam nikalta hai."""
    match = re.search(r'MANAGEMENT:(.*?)Moderator:', text, re.DOTALL | re.IGNORECASE)
    if not match:
        return []
    block = match.group(1)
    names = []
    for line in block.split('\n'):
        name_match = re.search(r'(?:MR\.|MS\.|DR\.)\s+([A-Z\s]+?)\s*[\u2013\u2014-]', line, re.IGNORECASE)
        if name_match:
            names.append(name_match.group(1).strip())
    return names

def tag_speaker_lines(text: str, mgmt_names: list) -> list:
    """
    Har line ko 'executive' ya 'non-executive' tag karta hai,
    speaker ke naam ke basis pe. Continuation lines (bina naye
    speaker ke) pichhle tag ko carry karti hain.
    """
    mgmt_last_names = set(name.split()[-1].lower() for name in mgmt_names)
    lines = text.split('\n')
    tagged_lines = []
    current_tag = 'non-executive'  # default jab tak pehla speaker na mile

    for line in lines:
        speaker_match = re.match(r'^([A-Za-z\s]+):\s', line)
        if speaker_match:
            speaker = speaker_match.group(1).strip()
            speaker_last = speaker.split()[-1].lower() if speaker else ''
            current_tag = 'executive' if speaker_last in mgmt_last_names else 'non-executive'
        tagged_lines.append((current_tag, line))

    return tagged_lines

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

    # Speaker tagging — kaun executive hai, kaun nahi
    mgmt_names = extract_management_names(text)
    tagged_lines = tag_speaker_lines(text, mgmt_names)

    # Tagged lines ko wapas text mein jodo, lekin tag info sath rakho
    # Har line ke saath uska tag jod ke ek naya text banate hain,
    # phir sentence split karte hain, aur tag ko sentence ke sath map karte hain
    combined = []
    for tag, line in tagged_lines:
        for part in line.split('.'):
            part = part.strip()
            if len(part) > 20:
                combined.append((tag, part))

    # Pehle 20 (boilerplate) skip karo, jaisa pehle karte the
    combined = combined[20:]
    log.info(f"  {len(combined)} sentences mile ({len(mgmt_names)} management names mile)")

    results = []
    for i, (tag, sent) in enumerate(combined):
        hedging = detect_hedging(sent)
        results.append({
            "sentence_id":   i,
            "sentence":      sent,
            "speaker_tag":   tag,
            **hedging,
        })

    df = pd.DataFrame(results)
    out_path = DIR_PROCESSED / (txt_path.stem + "_hedging.csv")
    df.to_csv(out_path, index=False)

    hedging_count = df["is_hedging"].sum()
    exec_hedging_count = df[df["speaker_tag"] == "executive"]["is_hedging"].sum()
    exec_total = (df["speaker_tag"] == "executive").sum()
    log.info(f"  {hedging_count} hedging sentences (all speakers) mile {len(df)} mein se")
    log.info(f"  {exec_hedging_count} hedging sentences (executive-only) mile {exec_total} mein se")
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
