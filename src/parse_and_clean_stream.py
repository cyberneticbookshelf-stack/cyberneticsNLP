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

Language filtering:
  Language is detected from each book's actual text using langdetect.
  A book is excluded if its top-detected language is not English with
  confidence ≥ 0.7.  Uncertain detections pass through (safe default).

  For edge cases (mixed-language books, parallel translations, OCR noise),
  csv/lang_override.csv provides per-book overrides:
    action=include  → force-include regardless of detected language
    action=exclude  → force-exclude regardless of detected language

  Requires: langdetect (pip install langdetect)
  If not installed, all books pass through with a warning.

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

# ── Language detection setup ──────────────────────────────────────────────────
try:
    from langdetect import detect_langs, DetectorFactory, LangDetectException
    DetectorFactory.seed = 0   # reproducible results
    _LANGDETECT_AVAILABLE = True
except ImportError:
    _LANGDETECT_AVAILABLE = False
    print("WARNING: langdetect not installed — language filter disabled.")
    print("         Run: pip install langdetect")

# Minimum confidence for a non-English detection to trigger exclusion.
_LANG_CONF_THRESHOLD = 0.70


def detect_book_language(text: str, sample_chars: int = 1000) -> tuple:
    """
    Detect the primary language of a book by sampling start, middle, and end.
    Returns (lang_code, confidence) using ISO 639-1 codes ('en', 'de', 'fr', …).
    Returns ('en', 0.0) if detection fails or langdetect is not available.
    """
    if not _LANGDETECT_AVAILABLE or len(text) < 50:
        return ('en', 0.0)
    n = len(text)
    mid = n // 2
    sample = (text[:sample_chars]
              + ' ' + text[mid: mid + sample_chars]
              + ' ' + text[max(0, n - sample_chars):])
    try:
        results = detect_langs(sample)
        top = results[0]
        return (top.lang, round(top.prob, 3))
    except Exception:
        return ('en', 0.0)


# ── Load lang_override.csv (optional per-book overrides) ─────────────────────
# Columns: id, action (include|exclude), lang_code, note
_override_path = CSV_DIR / 'lang_override.csv'
lang_override = {}   # bid → 'include' | 'exclude'
if _override_path.exists():
    with open(str(_override_path), encoding='utf-8') as _of:
        for _row in csv.DictReader(_of):
            _bid    = _row['id'].strip()
            _action = _row.get('action', '').strip().lower()
            if _bid and _action in ('include', 'exclude'):
                lang_override[_bid] = _action
    if lang_override:
        print(f"lang_override.csv: {len(lang_override)} manual overrides loaded "
              f"({sum(1 for v in lang_override.values() if v=='include')} include, "
              f"{sum(1 for v in lang_override.values() if v=='exclude')} exclude)")

# ── Load metadata ─────────────────────────────────────────────────────────────
meta = {}
meta_path = CSV_DIR / 'books_metadata_full.csv'
if not meta_path.exists():
    print(f"ERROR: {meta_path} not found.")
    print("Run: python3 src/00_export_calibre.py")
    sys.exit(1)
with open(str(meta_path), encoding='utf-8', errors='replace') as f:
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
lang_excluded_this_run = []   # (bid, title, lang, conf, source)

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

        raw        = row['searchable_text'][:CLEAN_CAP]
        title      = meta[bid]['title']

        # Manual override takes absolute precedence
        override = lang_override.get(bid)
        if override == 'exclude':
            lang_excluded_this_run.append((bid, title, 'override', 1.0, 'override'))
            continue
        if override != 'include':
            # Auto-detect language from text
            detected_lang, confidence = detect_book_language(raw)
            if detected_lang != 'en' and confidence >= _LANG_CONF_THRESHOLD:
                lang_excluded_this_run.append(
                    (bid, title, detected_lang, confidence, 'auto'))
                continue
        # else: override == 'include' → skip detection, fall through

        clean_text = clean(raw)

        record = {
            'id':         bid,
            'title':      title,
            'author':     meta[bid]['author'],
            'pubdate':    meta[bid]['pubdate'],
            'clean_text': clean_text,
        }

        # Write one JSON line — no read-back required
        out_f.write(json.dumps(record, ensure_ascii=False) + '\n')
        out_f.flush()   # ensure it's on disk immediately (crash-safe)
        done_ids.add(bid)
        n_new += 1

        print(f'  [{bid}] {title[:45]:45s} '
              f'{len(raw):>7,} → {len(clean_text):>7,}')

if lang_excluded_this_run:
    print(f'\nLanguage filter: excluded {len(lang_excluded_this_run)} books from {csv_file}:')
    for bid, title, lang, conf, src in lang_excluded_this_run:
        print(f'  [{bid}] ({lang} {conf:.2f}, {src}) {title}')

print(f'\nDone. New: {n_new}  Skipped: {n_skip}  No-meta: {n_nometa}')
print(f'Total in {out_path}: {len(done_ids)} books')

# ── runlog.csv: append per-book drops ────────────────────────────────────────
# The exclusion list is detected once per invocation (one CSV file).
# For a 25-CSV batch, the same 17 books would be detected each time — guard
# against duplicate rows by checking for a matching run_timestamp before appending.
_runlog_path = CSV_DIR / 'runlog.csv'
_run_ts  = datetime.datetime.now().isoformat(timespec='seconds')
_logrows = []
for bid, title, lang, conf, src in lang_excluded_this_run:
    _logrows.append({'run_timestamp': _run_ts,
                     'step': f'parse_and_clean_stream ({os.path.basename(csv_file)})',
                     'action': 'lang_excluded', 'book_id': bid,
                     'title': title, 'lang_code': lang,
                     'confidence': conf, 'source': src})
_log_fields = ['run_timestamp', 'step', 'action', 'book_id', 'title',
               'lang_code', 'confidence', 'source']
if _logrows:
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
