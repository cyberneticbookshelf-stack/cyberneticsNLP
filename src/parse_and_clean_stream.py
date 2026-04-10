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

Input:   books_metadata_full.csv  (metadata)
         books_text_XX.csv  (raw OCR text)
Output:  books_clean.jsonl  (append-only JSON Lines)
"""

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_metadata_full.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


import csv, datetime, json, os, re, sys

csv.field_size_limit(10_000_000)
CLEAN_CAP = 300_000

# ── Load metadata (with language filter) ─────────────────────────────────────
ENGLISH_CODES = {'eng'}   # ISO 639-2 codes accepted as English

# Manual exclusion list — repo-tracked, Calibre-sync-independent.
# Overrides lang_code from books_metadata_full.csv (unreliable across
# machines sharing a Calibre library via OneDrive).
_excl_path = CSV_DIR / 'lang_exclusions.csv'
manual_exclusions = {}   # bid → lang_code
if _excl_path.exists():
    with open(str(_excl_path), encoding='utf-8') as _ef:
        for _row in csv.DictReader(_ef):
            manual_exclusions[_row['id'].strip()] = _row['lang_code'].strip()

meta = {}
lang_excluded = []   # (bid, title, lang_code) for reporting
meta_path = CSV_DIR / 'books_metadata_full.csv'
if not meta_path.exists():
    print(f"ERROR: {meta_path} not found.")
    print("Run: python3 src/00_export_calibre.py")
    sys.exit(1)
with open(str(meta_path), encoding='utf-8', errors='replace') as f:
    for row in csv.DictReader(f, delimiter='\t'):
        bid       = row['id'].strip()
        lang_code = row.get('lang_code', '').strip().lower()
        # Manual exclusion list takes precedence over Calibre lang_code.
        if bid in manual_exclusions:
            lang_excluded.append((bid, row['title'].strip(), manual_exclusions[bid]))
            continue
        # Exclude books explicitly tagged as non-English in Calibre.
        # Books with no lang_code set pass through (metadata gap ≠ exclusion).
        if lang_code and lang_code not in ENGLISH_CODES:
            lang_excluded.append((bid, row['title'].strip(), lang_code))
            continue
        last, _, first = row['author_sort'].partition(',')
        author = f'{first.strip()} {last.strip()}'.strip() if first else last.strip()
        meta[bid] = {
            'title':   row['title'].strip(),
            'author':  author,
            'pubdate': row['pubdate'][:4],
        }
if lang_excluded:
    n_manual = sum(1 for b,t,l in lang_excluded if b in manual_exclusions)
    n_calibre = len(lang_excluded) - n_manual
    print(f"Language filter: excluded {len(lang_excluded)} non-English books "
          f"({n_manual} from exclusion list, {n_calibre} from Calibre lang_code):")
    for bid, title, lang in sorted(lang_excluded, key=lambda x: x[2]):
        src = 'list' if bid in manual_exclusions else 'calibre'
        print(f"  [{bid}] ({lang},{src}) {title}")
else:
    print("Language filter: no non-English books found (or lang_code not set in Calibre)")

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

# ── runlog.csv: append lang exclusions from this CSV file ────────────────────
# Only written once per script invocation (i.e. when processing the first
# CSV file in the batch), to avoid duplicating the 17-row exclusion list 25×.
# Duplication guard: skip if a row with this run_timestamp + step already exists.
_runlog_path = CSV_DIR / 'runlog.csv'
_run_ts  = datetime.datetime.now().isoformat(timespec='seconds')
_logrows = []
for bid, title, lang in lang_excluded:
    src = 'list' if bid in manual_exclusions else 'calibre'
    _logrows.append({'run_timestamp': _run_ts, 'step': 'parse_and_clean_stream',
                     'action': 'lang_excluded', 'book_id': bid,
                     'title': title, 'lang_code': lang, 'source': src})
_log_fields = ['run_timestamp', 'step', 'action', 'book_id', 'title', 'lang_code', 'source']
# Check if we've already logged this exclusion set in a previous CSV file for
# this same run: look for our timestamp in the last N rows.
_already_logged = False
if _runlog_path.exists() and _logrows:
    with open(str(_runlog_path), encoding='utf-8') as _chk:
        _last = _chk.read()
    if _run_ts in _last:
        _already_logged = True
if _logrows and not _already_logged:
    _write_header = not _runlog_path.exists()
    with open(str(_runlog_path), 'a', encoding='utf-8', newline='') as _lf:
        _writer = csv.DictWriter(_lf, fieldnames=_log_fields)
        if _write_header:
            _writer.writeheader()
        _writer.writerows(_logrows)
    print(f"runlog.csv: appended {len(_logrows)} row(s)")

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