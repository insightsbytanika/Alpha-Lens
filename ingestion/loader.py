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


print("functions working")


