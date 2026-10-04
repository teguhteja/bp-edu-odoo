"""Pecah keluaran export_mysql.sh menjadi data/<tabel>.jsonl.

    python scripts/labapp_import/split_dump.py dump.txt
"""
import json
import pathlib
import sys

src = pathlib.Path(sys.argv[1])
out_dir = pathlib.Path(__file__).parent / 'data'
out_dir.mkdir(exist_ok=True)

tables = {}
current = None
for line in src.read_text(encoding='utf-8').splitlines():
    if line.startswith('### '):
        current = line[4:].strip()
        tables[current] = []
    elif line.strip() and current:
        json.loads(line)  # validasi
        tables[current].append(line)

for name, rows in tables.items():
    (out_dir / f'{name}.jsonl').write_text('\n'.join(rows) + ('\n' if rows else ''), encoding='utf-8')
    print(f'{name:24} {len(rows)}')
