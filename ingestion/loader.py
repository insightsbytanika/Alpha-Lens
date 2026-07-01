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