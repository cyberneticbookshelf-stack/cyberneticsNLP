"""


parse_and_clean_stream.py  —  v2 (JSONL output)
────────────────────────────────────────────────────────────────────────────
Parses and cleans one books_text_XX.csv at a time, appending results to
books_clean.jsonl using JSON Lines format.

JSONL format: one JSON object per line, one book per line.
  {"id": "105", "title": "...", "author": "...", "clean_text": "..."}
  {"id": "121", ...}

Advantages over the previous books_clean.json approach:
  - Append-only: new books are written one line at a time with no read-back
  - Memory use is O(batch_size) — never loads the full corpus into memory
  - Resumable: existing IDs are collected by scanning only the "id" fields,
    not the full text, so the skip-check remains fast even at 600+ books
  - Corruption-safe: a crash mid-write leaves at most one incomplete line,
    which is easily detected and skipped by downstream readers

Usage:
    python3 parse_and_clean_stream.py books_text_01.csv
    python3 parse_and_clean_stream.py books_text_02.csv
    ... (run once per CSV file, in any order)

Downstream scripts read books_clean.jsonl. If any script expects the old
books_clean.json dict format, use the provided convert_jsonl_to_json.py
helper (included at the bottom of this file as a comment).

Input:   books_lang.csv  (metadata)
         books_text_XX.csv  (raw OCR text)
Output:  books_clean.jsonl  (append-only JSON Lines)
"""

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_lang.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


import csv, json, os, re, sys

csv.field_size_limit(10_000_000)
CLEAN_CAP = 300_000

# ── Load metadata ─────────────────────────────────────────────────────────────
meta = {}
with open(str(CSV_DIR / 'books_lang.csv'), encoding='utf-8', errors='replace') as f:
    for row in csv.DictReader(f, delimiter='\t'):
        bid = row['id'].strip()
        last, _, first = row['author_sort'].partition(',')
        author = f'{first.strip()} {last.strip()}'.strip() if first else last.strip()
        meta[bid] = {
            'title':   row['title'].strip(),
            'author':  author,
            'pubdate': row['pubdate'][:4],
        }

# ── Minimal regex-based cleaner (no Hunspell dependency) ─────────────────────
_INLINE = re.compile(
    r'(?i)(isbn[\s\-]?\d[\d\-]{8,})'          # ISBN
    r'|(\b10\.\d{4,}/\S+)'                     # DOI
    r'|(https?://\S+|www\.\S+)'                # URLs
    r'|(\bpage\s+intentionally\s+left\s+blank\b)'
)
_SECTION_HDR = re.compile(
    r'(?im)^[\s]*(?:table\s+of\s+contents?|list\s+of\s+(?:tables?|figures?)'
    r'|(?:author[\'\s]s?\s+)?preface|foreword|prologue|acknowledgements?'
    r'|dedication|about\s+the\s+author|contributors?|bibliography'
    r'|references?|works\s+cited|further\s+reading|index)[\s]*$'
)
_CHAPTER = re.compile(
    r'(?im)^[\s]*(?:CHAPTER|Chapter|PART|Part)\s+[\dIVXivx]'
)
# OCR line-break dehyphenation — joins "feed-\nback" → "feedback"
_DEHYPHEN = re.compile(r'([a-zA-Z])-\n([a-zA-Z])')

def clean(text):
    # 1. Rejoin OCR line-break hyphens
    text = _DEHYPHEN.sub(r'\1\2', text)
    # 2. Normalise whitespace
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 3. Strip inline boilerplate
    text = _INLINE.sub(' ', text)
    # 4. Remove boilerplate sections (state machine)
    lines = text.split('\n')
    out, skip, budget = [], False, 0
    for line in lines:
        s = line.strip()
        if skip and _CHAPTER.match(s):
            skip = False; budget = 0; out.append(line); continue
        if not skip and _SECTION_HDR.match(s):
            skip = True; budget = 500; continue
        if skip:
            budget -= 1
            if budget <= 0: skip = False
            continue
        out.append(line)
    text = '\n'.join(out)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# ── Collect already-processed IDs from JSONL (id field only, no text read) ───
out_path = str(JSON_DIR / 'books_clean.jsonl')
done_ids = set()
if os.path.exists(out_path):
    with open(out_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                # Fast partial parse — only extract "id" field
                m = re.search(r'"id"\s*:\s*"([^"]+)"', line)
                if m:
                    done_ids.add(m.group(1))
            except Exception:
                pass
    print(f'Already cleaned: {len(done_ids)} books')
else:
    print('Starting fresh')

# ── Process the requested CSV file ───────────────────────────────────────────
csv_file = sys.argv[1] if len(sys.argv) > 1 else None
if not csv_file:
    print('Usage: python3 parse_and_clean_stream.py books_text_01.csv')
    sys.exit(1)

print(f'Processing {csv_file}...')
n_new = n_skip = n_nometa = 0

# Open output file in append mode — never reads existing content
with open(out_path, 'a', encoding='utf-8') as out_f, \
     open(csv_file, encoding='utf-8', errors='replace') as in_f:

    for row in csv.DictReader(in_f):
        bid = row['id'].strip()

        if bid in done_ids:
            n_skip += 1
            continue
        if bid not in meta:
            n_nometa += 1
            continue

        raw   = row['searchable_text'][:CLEAN_CAP]
        clean_text = clean(raw)

        record = {
            'id':         bid,
            'title':      meta[bid]['title'],
            'author':     meta[bid]['author'],
            'pubdate':    meta[bid]['pubdate'],
            'clean_text': clean_text,
        }

        # Write one JSON line — no read-back required
        out_f.write(json.dumps(record, ensure_ascii=False) + '\n')
        out_f.flush()   # ensure it's on disk immediately (crash-safe)
        done_ids.add(bid)
        n_new += 1

        print(f'  [{bid}] {meta[bid]["title"][:45]:45s} '
              f'{len(raw):>7,} → {len(clean_text):>7,}')

print(f'\nDone. New: {n_new}  Skipped: {n_skip}  No-meta: {n_nometa}')
print(f'Total in {out_path}: {len(done_ids)} books')

# ── JSONL → JSON conversion helper ───────────────────────────────────────────
# If any downstream script still expects the old dict-format books_clean.json,
# run this once after all 25 CSV files are processed:
#
#   python3 - << 'EOF'
#   import json
#   books = {}
#   with open(str(JSON_DIR / 'books_clean.jsonl')) as f:
#       for line in f:
#           if line.strip():
#               r = json.loads(line)
#               books[r['id']] = {k:v for k,v in r.items() if k != 'id'}
#   with open(str(JSON_DIR / 'books_clean.json'),'w') as f:
#       json.dump(books, f, ensure_ascii=False)
#   print(f'Converted {len(books)} books to books_clean.json')
#   EOF