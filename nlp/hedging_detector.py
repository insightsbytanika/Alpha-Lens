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

