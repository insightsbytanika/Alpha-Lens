"""
split_media_earnings.py
AlphaLens - Data Quality Fix

Infosys (aur kuch ICICI) filings mein Media/Press call aur Analyst Earnings
call dono transcripts ek hi PDF mein aate hain. loader.py dono ko ek
_clean.txt mein daal deta hai, isliye journalists ke sawaal bhi "earnings
call" ki tarah score ho rahe the.

Ye script har _clean.txt se sirf analyst earnings-call wala hissa rakhta
hai. Order file-to-file alag hota hai (INFY_Q4FY22 mein earnings pehle),
isliye journalist/analyst participant list dekh ke section pehchanta hai.
Originals data/processed/_pre_split_backup/ mein backup hote hain.

Run once, hedging/sentiment se pehle.
"""
import re
import shutil
from pathlib import Path
import logging

DIR_PROCESSED = Path("data/processed")
BACKUP_DIR = DIR_PROCESSED / "_pre_split_backup"

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

# Section-start headings (Infosys: CORPORATE PARTICIPANTS, kabhi spaced "C O R P O R A T E ...")
SECTION_HEADINGS = [
    re.compile(r'^\s*C\s?O\s?R\s?P\s?O\s?R\s?A\s?T\s?E\s+P\s?A\s?R\s?T\s?I\s?C\s?I\s?P\s?A\s?N\s?T\s?S:?\s*$',
               re.IGNORECASE | re.MULTILINE),
    re.compile(r'^Media conference call for quarter ended.*$', re.IGNORECASE | re.MULTILINE),
    re.compile(r'^Earnings conference call\s*-\s*Quarter ended.*$', re.IGNORECASE | re.MULTILINE),
]

JOURNALIST_RE = re.compile(r'\bJOURNALISTS?\b', re.IGNORECASE)
MEDIA_TITLE_RE = re.compile(r'Media conference call|Press Conference Call', re.IGNORECASE)
# Kabhi press section ki list "ANALYSTS" label hoti hai par naam media outlets ke hote hain
OUTLET_RE = re.compile(r'CNBC|Moneycontrol|NDTV|Economic Times|ET Now|BQ Prime|Zee Business|Times of India|'
                       r'Hindu BusinessLine|Financial Express|Reuters|\bMint\b|Business Standard|Fortune India',
                       re.IGNORECASE)
LOOKAHEAD = 1200         # participant list ke andar journalist marker dhundo
MERGE_WINDOW = 400        # media title ke turant baad ka heading = same section


def classify_sections(text):
    """Returns list of (start, kind) sorted; kind in {'media','earnings'}."""
    starts = sorted({m.start() for p in SECTION_HEADINGS for m in p.finditer(text)})
    # media title ke 400 chars ke andar wala heading usi section ka hissa hai
    media_titles = [m.start() for m in MEDIA_TITLE_RE.finditer(text)]
    merged = []
    for pos in starts:
        if any(0 <= pos - t <= MERGE_WINDOW for t in media_titles) and merged and \
           any(0 <= merged[-1] - t <= MERGE_WINDOW for t in media_titles):
            continue
        merged.append(pos)

    sections = []
    for pos in merged:
        window = text[pos:pos + LOOKAHEAD]
        near_media_title = any(0 <= pos - t <= MERGE_WINDOW or 0 <= t - pos <= 60 for t in media_titles)
        outlets = len(OUTLET_RE.findall(window))
        kind = 'media' if (JOURNALIST_RE.search(window) or near_media_title or outlets >= 3) else 'earnings'
        sections.append((pos, kind))
    return sections


def earnings_span(text):
    sections = classify_sections(text)
    kinds = {k for _, k in sections}
    if 'media' not in kinds or 'earnings' not in kinds:
        return None  # already clean (ya pehchaan nahi hui) - touch mat karo
    for i, (pos, kind) in enumerate(sections):
        if kind == 'earnings':
            end = sections[i + 1][0] if i + 1 < len(sections) else len(text)
            return pos, end
    return None


def process_file(path):
    text = path.read_text(encoding="utf-8")
    span = earnings_span(text)
    if span is None:
        return False
    start, end = span
    kept = text[start:end].strip()
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if not (BACKUP_DIR / path.name).exists():
        shutil.copy(path, BACKUP_DIR / path.name)
    path.write_text(kept, encoding="utf-8")
    log.info(f"{path.name}: kept [{start}:{end}] {len(kept)} chars (was {len(text)})")
    return True


def main():
    files = sorted(DIR_PROCESSED.glob("*_clean.txt"))
    fixed = [f.name for f in files if process_file(f)]
    log.info(f"{len(fixed)}/{len(files)} files split. Backups: {BACKUP_DIR}")


if __name__ == "__main__":
    main()