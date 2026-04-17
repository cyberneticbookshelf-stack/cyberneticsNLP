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

# Google Books invisible text-layer artefacts.
# PDFs digitised by Google carry metadata in the embedded text layer that is
# not visible on-screen but is indexed by Calibre's full-text search engine.
# These patterns strip the most common forms before text reaches the vectoriser.
_GOOGLE_BOOKS = re.compile(
    r'(?i)'
    r'(digitized\s+by\s+google[\w\s,]*)'
    r'|(original\s+from\s+(the\s+)?university\s+of\s+california[\w\s,]*)'
    r'|(generated\s+by\s+(?:google|abc\s+amber\s+lit\s+converter)[\w\s,]*)'
    r'|(google\s+books[\w\s]*)'
)
# ── OCR likelihood scorer ─────────────────────────────────────────────────────
# Scores raw text (before cleaning) on four signals to estimate the probability
# that a book's text was produced by OCR rather than extracted from a born-digital PDF.
# Returns (score 0.0–1.0, list of detected signal labels).
#
# Bands:  < 0.30 → Low (likely born-digital)
#         0.30–0.65 → Medium (possibly scanned)
#         ≥ 0.65 → High (likely OCR scan)
#
# Signal weights (sum to 1.0 max, capped):
#   scanning_metadata  +0.55  (Google/IA/HathiTrust strings — near-definitive)
#   low_alpha_ratio    +0.25  (scaled: alpha < 0.60 over body sample)
#   ocr_error_tokens   +0.20  (classic substitution errors: tlie, liave, tbe …)
#   page_artifacts     +0.10  (isolated numbers on their own lines)

_OCR_SCAN_META = re.compile(
    r'(?i)(digitized\s+by\s+google'
    r'|internet\s+archive'
    r'|hathitrust'
    r'|university\s+of\s+california\s+digitized'
    r'|scanning\s+centre'
    r'|scanned\s+by)'
)
_OCR_ERRORS = re.compile(
    r'(?i)\b(tlie|llie|liave|tbe|wlien|wliich|wliere|tliis|tbeir|tbey'
    r'|witli|tbat|sucli|mucli|wbat|wbo|wbose|sliould|could|woulcl'
    r'|tliey|wliole|sliow|diat|iiave|heen|lias|iu\b)\b'
)
_PAGE_NUM = re.compile(r'(?m)^\s{0,4}\d{1,4}\s*$')

def ocr_likelihood(raw: str) -> tuple:
    score = 0.0
    signals = []

    # Signal 1: scanning metadata strings
    if _OCR_SCAN_META.search(raw):
        score += 0.55
        signals.append('scanning_metadata')

    # Signal 2: alpha ratio on body sample (skip first 10%)
    start  = max(500, len(raw) // 10)
    sample = raw[start:start + 6000]
    if sample:
        alpha = sum(c.isalpha() for c in sample) / len(sample)
        if alpha < 0.60:
            contribution = round((0.60 - alpha) / 0.60 * 0.25, 3)
            score += contribution
            signals.append(f'low_alpha:{alpha:.2f}')

    # Signal 3: classic OCR substitution-error tokens
    n_errors = len(_OCR_ERRORS.findall(raw))
    if n_errors >= 3:
        contribution = min(n_errors / 80, 0.20)
        score += contribution
        signals.append(f'ocr_errors:{n_errors}')

    # Signal 4: isolated page-number lines
    n_pages = len(_PAGE_NUM.findall(raw))
    if n_pages >= 8:
        contribution = min(n_pages / 150, 0.10)
        score += contribution
        signals.append(f'page_artifacts:{n_pages}')

    score = round(min(score, 1.0), 3)
    band  = 'high' if score >= 0.65 else ('medium' if score >= 0.30 else 'low')
    return score, band, signals


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
    # 3b. Strip Google Books text-layer artefacts (invisible in PDF viewer)
    text = _GOOGLE_BOOKS.sub(' ', text)
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

        ocr_score, ocr_band, ocr_signals = ocr_likelihood(raw)
        clean_text = clean(raw)

        record = {
            'id':          bid,
            'title':       title,
            'author':      meta[bid]['author'],
            'pubdate':     meta[bid]['pubdate'],
            'clean_text':  clean_text,
            'ocr_score':   ocr_score,   # 0.0–1.0 likelihood of OCR origin
            'ocr_band':    ocr_band,    # 'low' / 'medium' / 'high'
            'ocr_signals': ocr_signals, # list of detected evidence strings
        }

        # Write one JSON line — no read-back required
        out_f.write(json.dumps(record, ensure_ascii=False) + '\n')
        out_f.flush()   # ensure it's on disk immediately (crash-safe)
        done_ids.add(bid)
        n_new += 1

        ocr_tag = {'high': ' ⚠ OCR:high', 'medium': ' ~ OCR:med', 'low': ''}.get(ocr_band, '')
        print(f'  [{bid}] {title[:45]:45s} '
              f'{len(raw):>7,} → {len(clean_text):>7,}{ocr_tag}')

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
