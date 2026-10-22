"""
verify_call_dates.py
AlphaLens - Date integrity check (PDR 7.1 "filename date != PDF date" ka automated version)

Problem: Infosys aur Wipro ke kai filenames SEBI filing/upload date use karte hain,
asli call date nahi (call 3-5 din pehle hoti hai). TRANSCRIPT_MAP mein wahi date
jaane se return window call ke BAAD shuru hota tha - yaani market reaction miss.

Ye script har transcript ke text se asli call date nikalta hai:
  1. "meeting/call held|conducted on <date>"  (Wipro cover letters, ICICI etc.)
  2. "<Earnings ... Call>" heading ke turant baad wali date line (Infosys)
Agar kuch na mile to filename date hi rakhta hai (source = 'filename').

Output: data/call_dates_verified.json  {file_stem: {"filename_date", "call_date", "source"}}  (JSON, kyunki .gitignore mein *.csv hai)
"""
import re
import json
from pathlib import Path
from datetime import datetime

P = Path("data/processed")
BACKUP = P / "_pre_split_backup"
OUT = Path("data/call_dates_verified.json")

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
DATE = rf"(?:{MONTHS})\s+\d{{1,2}},?\s+\d{{4}}"
HELD = re.compile(rf"(?:held|conducted)\s+on\s+({DATE})", re.IGNORECASE)
HEADING_DATE = re.compile(rf"Earnings\s+(?:Conference\s+)?Call[^\n]*\n\s*({DATE})\s*\n", re.IGNORECASE)


def to_date(s):
    return datetime.strptime(re.sub(r"\s+", " ", s.replace(",", "")), "%B %d %Y").date()


def call_date_from_text(text):
    head = text[:6000]
    m = HELD.search(head)
    if m:
        return to_date(m.group(1)), "held-on"
    m = HEADING_DATE.search(head)
    if m:
        return to_date(m.group(1)), "heading"
    return None, "filename"


def main():
    rows = []
    for f in sorted(P.glob("*_clean.txt")):
        src = (BACKUP / f.name) if (BACKUP / f.name).exists() else f   # split se pehle ka original (heading wahan hai)
        text = src.read_text(encoding="utf-8")
        fname_date = datetime.strptime(f.stem.split("_")[2], "%d%b%Y").date()
        d, source = call_date_from_text(text)
        call = d or fname_date
        if d and abs((fname_date - d).days) > 10:      # sanity: bahut door ki date galat match hai
            call, source = fname_date, "filename(rejected-far)"
        rows.append((f.stem, fname_date, call, source, call != fname_date))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(
        {r[0]: {"filename_date": str(r[1]), "call_date": str(r[2]), "source": r[3]} for r in rows}, indent=1))

    changed = [r for r in rows if r[4]]
    print(f"{len(rows)} files, {len(changed)} call dates differ from filename date")
    for r in changed:
        print(f"  {r[0]:40s} filename={r[1]}  call={r[2]}  ({(r[1]-r[2]).days}d earlier)  [{r[3]}]")
    unver = [r for r in rows if r[3].startswith("filename")]
    print(f"{len(unver)} files fall back to filename date (not verifiable from text): "
          + ", ".join(sorted({r[0].split('_')[0] for r in unver})))


if __name__ == "__main__":
    main()