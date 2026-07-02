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

print("imports working")


