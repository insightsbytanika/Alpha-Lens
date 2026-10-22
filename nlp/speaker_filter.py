"""
speaker_filter.py
AlphaLens - Text-based speaker attribution (PDR Section 4.3)

Sirf EXECUTIVE (management) ki lines rakhta hai; moderator, analysts aur
boilerplate hata deta hai. Alag-alag companies ke transcript formats alag
hain, isliye ye module sab handle karta hai:

  Axis/HDFC/Wipro : "MANAGEMENT:" block, dialogue "NAAM:" format mein
  Infosys         : "CORPORATE PARTICIPANTS" block, speaker naam apni alag line pe
  Reliance        : "Call Participants:" list, speaker tag "Sh Naam HH:MM:SS"
  TCS / ICICI     : koi clean list nahi - naam Moderator ke inline intro mein

Analyst pehchaan ke liye moderator ka "next question is from the line of
X from Y" pattern use hota hai (sab companies mein consistent).
"""
import re

TITLE_KEYWORDS = (r'Chief|Managing Director|Executive Director|President|Chairman|'
                  r'Whole[- ]?time Director|CFO\b|CEO\b|COO\b|CHRO\b|CTO\b|Head')

MGMT_BLOCK = re.compile(r'MANAGEMENT:(.*?)(?:Moderator:|Ladies and gentlemen)', re.DOTALL | re.IGNORECASE)
MGMT_NAME = re.compile(r'(?:MR\.|MS\.|DR\.)\s+([A-Z][A-Z\s.]+?)\s*[–—-]', re.IGNORECASE)

CORP_BLOCK = re.compile(r'C\s?O\s?R\s?P\s?O\s?R\s?A\s?T\s?E\s+P\s?A\s?R\s?T\s?I\s?C\s?I\s?P\s?A\s?N\s?T\s?S:?(.*?)'
                        r'(?:\n\s*(?:ANALYSTS|JOURNALISTS?|MODERATOR)\b)', re.DOTALL | re.IGNORECASE)
NAME_LINE = re.compile(r'^[A-Z][a-zA-Z.]*(\s+[A-Z][a-zA-Z.]+){0,3}$')

CALL_PARTICIPANTS_BLOCK = re.compile(r'Call Participants:(.*?)Duration:', re.DOTALL | re.IGNORECASE)
BULLET_NAME = re.compile(r'(?:Sh|Smt|Dr)\.?\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,3})')

INLINE_NAME_TITLE = re.compile(
    r'(?:Mr\.|Ms\.|Dr\.)\s+([A-Z][A-Za-z.]*(?:\s+[A-Z][A-Za-z.]+){0,3})\s*[,–—-]\s*'
    r'(?=[^.\n]{0,70}?(?:' + TITLE_KEYWORDS + r'))')

ANALYST_INTRO = re.compile(r'next question (?:is\s+)?from(?:\s+the\s+line\s+of)?\s+'
                           r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z.]+){0,3})\s+from', re.IGNORECASE)

COLON_SPEAKER = re.compile(r'^([A-Za-z][A-Za-z .]{1,40}):\s*(?:\S|$)')
TIMESTAMP_SPEAKER = re.compile(r'^(?:Sh|Smt|Ms|Mr|Dr)\.?\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,3})\s+\d{1,2}:\d{2}:\d{2}')
BARE_NAME_LINE = re.compile(r'^[A-Z][A-Za-z.]*(?:\s+[A-Z][a-zA-Z.]+){0,3}$')

# ICICI: prepared remarks "Mr. Bakhshi's opening remarks" / "Anindya's opening remarks" header ke neeche aate hain (colon nahi)
OPENING_REMARKS_HDR = re.compile(r"^(?:Mr\.|Ms\.|Dr\.)?\s*[A-Z][\w.]*(?:\s+[A-Z][\w.]*)?[’']s opening remarks\s*$")

NON_EXEC_LABELS = {'moderator', 'operator'}
HEADER_WORDS = {'sub', 'note', 'encl', 'ref', 'to', 'from', 'date', 'subject', 'transcript',
                'duration', 'presentation link', 'meeting audio', 'call participants'}


def _dedupe(names):
    seen, out = set(), []
    for n in names:
        n = re.sub(r'\s+', ' ', n).strip('. ')
        if n and n.lower() not in seen:
            seen.add(n.lower())
            out.append(n)
    return out


def extract_exec_names(text: str) -> list:
    names = []
    m = MGMT_BLOCK.search(text)
    if m:
        names += MGMT_NAME.findall(m.group(1))

    m = CORP_BLOCK.search(text)
    if m:
        lines = [l.strip() for l in m.group(1).split('\n') if l.strip()]
        for i in range(len(lines) - 1):
            if (re.search(TITLE_KEYWORDS, lines[i + 1], re.IGNORECASE)
                    and not re.search(TITLE_KEYWORDS, lines[i], re.IGNORECASE)
                    and NAME_LINE.match(lines[i])):
                names.append(lines[i])

    m = CALL_PARTICIPANTS_BLOCK.search(text)
    if m:
        for line in m.group(1).split('\n'):
            if re.search(TITLE_KEYWORDS, line, re.IGNORECASE):
                names += BULLET_NAME.findall(line)

    if not names:  # TCS / ICICI fallback
        names = INLINE_NAME_TITLE.findall(text[:8000])
    return _dedupe(names)


def extract_analyst_names(text: str) -> list:
    return _dedupe(ANALYST_INTRO.findall(text))


def _lasts(names):
    return {n.split()[-1].lower() for n in names if n.split()}


def tag_speaker_lines(text, exec_names, analyst_names):
    """(tag, line) list. Continuation lines pichhla tag carry karti hain."""
    exec_last, analyst_last = _lasts(exec_names), _lasts(analyst_names)
    # analyst list mil gayi to unknown multi-word speaker ko executive maano
    # (call mein sirf moderator/management/analyst bolte hain); warna safe default non-exec
    unknown_default = 'executive' if analyst_last else 'non-executive'

    tagged, tag, started = [], 'non-executive', False
    for line in text.split('\n'):
        stripped = line.strip()
        speaker = None
        if OPENING_REMARKS_HDR.match(stripped):
            tag, started = 'executive', True
            tagged.append((tag, line))
            continue
        m = COLON_SPEAKER.match(line)
        if m and m.group(1).strip().lower() not in HEADER_WORDS:
            speaker = m.group(1).strip()
        else:
            m2 = TIMESTAMP_SPEAKER.match(line)
            if m2:
                speaker = m2.group(1).strip()
            elif stripped.lower() in NON_EXEC_LABELS:
                speaker = stripped
            elif BARE_NAME_LINE.match(stripped) and len(stripped.split()) >= 2:
                last = stripped.split()[-1].lower()
                if last in exec_last or last in analyst_last:  # Infosys: sirf known naam
                    speaker = stripped

        if speaker:
            label = speaker.lower()
            last = speaker.split()[-1].lower()
            if label in NON_EXEC_LABELS:
                tag, started = 'non-executive', True
            elif last in exec_last:
                tag, started = 'executive', True
            elif last in analyst_last:
                tag, started = 'non-executive', True
            elif started or TIMESTAMP_SPEAKER.match(line):
                # single-word ya unknown => conservative; multi-word + analyst list => executive
                tag = unknown_default if len(speaker.split()) >= 2 else 'non-executive'
                started = True
        tagged.append((tag if started else 'non-executive', line))
    return tagged


def filter_executive_text(text: str) -> str:
    """Executive lines ka text. Agar koi signal hi na mile to original text (filter skip)."""
    exec_names = extract_exec_names(text)
    analyst_names = extract_analyst_names(text)
    if not exec_names and not analyst_names:
        return text
    tagged = tag_speaker_lines(text, exec_names, analyst_names)
    return '\n'.join(line for tag, line in tagged if tag == 'executive')


if __name__ == "__main__":
    # Quick audit: har file mein executive share dikhata hai
    from pathlib import Path
    rows = []
    for f in sorted(Path("data/processed").glob("*_clean.txt")):
        t = f.read_text(encoding="utf-8")
        ex = filter_executive_text(t)
        rows.append((f.name, len(extract_exec_names(t)), len(extract_analyst_names(t)), len(ex) / max(len(t), 1)))
    for name, ne, na, share in rows:
        flag = "  <-- CHECK" if share < 0.30 or share > 0.95 else ""
        print(f"{name:45s} execs={ne} analysts={na:2d} exec_share={share:5.1%}{flag}")