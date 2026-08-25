from pathlib import Path
from datetime import datetime

files = sorted(Path('data/transcripts').glob('*.pdf'))
print('TRANSCRIPT_MAP = {')
for f in files:
    parts = f.stem.split('_')
    ticker = parts[0]
    date_str = parts[2]
    date_obj = datetime.strptime(date_str, '%d%b%Y')
    formatted_date = date_obj.strftime('%Y-%m-%d')
    print(f'    "{f.stem}_clean": ("{ticker}.NS", "{formatted_date}"),')
print('}')