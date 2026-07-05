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

def load_finbert():
    """FinBERT model load karta hai HuggingFace se."""
    log.info("Loading FinBERT model — pehli baar mein download hoga (~400MB)...")
    nlp = pipeline(
        "text-classification",
        model=MODEL_NAME,
        tokenizer=MODEL_NAME,
        top_k=None,        # teenon scores chahiye — positive, negative, neutral
    )
    log.info("FinBERT ready.")
    return nlp


def score_sentences(nlp, text: str) -> list:
    """
    Text ko sentences mein todta hai aur har sentence ko score karta hai.
    Returns list of dicts.
    """
    # Simple sentence split — full stop ya newline pe
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 20]

    log.info(f"  {len(sentences)} sentences mile scoring ke liye")
    results = []

    for i, sent in enumerate(sentences):
        try:
            scores = nlp(sent[:512])[0]  # FinBERT max 512 tokens leta hai
            # scores ek list hai — [{label, score}, {label, score}, {label, score}]
            score_dict = {s["label"]: round(s["score"], 4) for s in scores}
            results.append({
                "sentence_id": i,
                "sentence":    sent,
                "positive":    score_dict.get("positive", 0),
                "negative":    score_dict.get("negative", 0),
                "neutral":     score_dict.get("neutral",  0),
                "label":       max(score_dict, key=score_dict.get),
            })
        except Exception as e:
            log.warning(f"  Sentence {i} skip — {e}")

    return results

def process_file(nlp, txt_path: Path) -> Path:
    """Ek transcript file uthao, score karo, CSV save karo."""
    log.info(f"Processing: {txt_path.name}")
    text = txt_path.read_text(encoding="utf-8")
    results = score_sentences(nlp, text)

    if not results:
        log.warning("  Koi sentences nahi mile — skip")
        return None
    df = pd.DataFrame(results)
    out_path = OUTPUT_DIR / (txt_path.stem + "_sentiment.csv")
    df.to_csv(out_path, index=False)
    log.info(f"  -> {len(df)} sentences scored")
    log.info(f"  -> Saved: {out_path}")
    return out_path

def main():
    log.info("=" * 55)
    log.info("AlphaLens  |  Sentiment Pipeline  |  Week 3")
    log.info("=" * 55)

    #FinBERT loading
    nlp = load_finbert()

    #finding all the clean files
    files = list(INPUT_DIR.glob("*_clean.txt"))
    if not files:
        log.warning(f"Koi _clean.txt file nahi mili {INPUT_DIR} mein")
        log.warning("Pehle loader.py chalao!")
        return

    log.info(f"  {len(files)} transcript(s) mili")

    for f in files:
        process_file(nlp, f)
        log.info("")
    log.info("-- Done " + "-" * 47)
    log.info(f"  Results yahan hain: {OUTPUT_DIR.resolve()}")
    log.info("-" * 55)


if __name__ == "__main__":
    main()
