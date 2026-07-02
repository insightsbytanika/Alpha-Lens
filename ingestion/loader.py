"""
loader.py
AlphaLens - Week 1
PDF transcripts padhta hai data/transcripts/ se,
clean text banata hai aur data/processed/ mein save karta hai.
"""

import pdfplumber
import re
from pathlib import Path
import logging

# Config
INPUT_DIR  = Path("data/transcripts")
OUTPUT_DIR = Path("data/processed")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: Path) -> str:
    """PDF se raw text nikalti hai page by page."""
    log.info(f"Reading PDF: {pdf_path.name}")
    full_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                full_text += text + "\n"
            else:
                log.warning(f"  Page {i+1} mein kuch nahi mila — skip")

    log.info(f"  Total characters extracted: {len(full_text)}")
    return full_text


def clean_text(raw: str) -> str:
    """Junk hata do — extra spaces, page numbers, etc."""
    # Multiple blank lines ko ek blank line karo
    text = re.sub(r'\n{3,}', '\n\n', raw)
    # 3+ spaces ko single space karo
    text = re.sub(r' {3,}', ' ', text)
    # Page number patterns hata do jaise "Page 1 of 12"
    text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
    return text.strip()


def process_transcript(pdf_path: Path) -> Path:
    """Ek PDF uthao, clean karo, processed folder mein save karo."""
    raw_text   = extract_text_from_pdf(pdf_path)
    clean      = clean_text(raw_text)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / (pdf_path.stem + "_clean.txt")
    out_path.write_text(clean, encoding="utf-8")
    log.info(f"  -> Saved to {out_path}")
    return out_path


def main():
    log.info("=" * 55)
    log.info("AlphaLens  |  Loader  |  Week 1")
    log.info("=" * 55)

    pdfs = list(INPUT_DIR.glob("*.pdf"))

    if not pdfs:
        log.warning(f"Koi PDF nahi mili {INPUT_DIR} mein — kuch dalo pehle!")
        return

    log.info(f"  {len(pdfs)} PDF mili/milin")

    for pdf_path in pdfs:
        process_transcript(pdf_path)

    log.info("")
    log.info("-- Done " + "-" * 47)
    log.info(f"  Clean files yahan hain: {OUTPUT_DIR.resolve()}")
    log.info("-" * 55)


if __name__ == "__main__":
    main()


