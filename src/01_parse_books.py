"""


01_parse_books.py
─────────────────────────────────────────────────────────────────────────────
Step 1 of the Book NLP Pipeline.

Auto-detects every books_text_*.csv in the current directory, merges them
into a single collection, and joins with metadata from books_metadata_full.csv.
Duplicate book IDs resolved by keeping the FIRST occurrence (alphabetical order).

A lightweight preprocess_raw_text() pass is applied to each book's raw text
before it is written to books_parsed.json.  This removes:
  - Null / control characters
  - Dense OCR symbol garble (4+ consecutive non-alphanumeric chars)
  - Standalone page-number lines
  - Repeated punctuation runs (OCR scanning artefacts)
  - All-caps short header lines (soft-normalised to title-case)
Heavy semantic cleaning (boilerplate sections, dictionary filtering,
case normalisation) remains in step 02.

NOTE FOR LARGE CORPORA (>~300 books):
  This script produces books_parsed.json which can exceed 500 MB.
  Step 02 must then load that entire file, which can time out in constrained
  environments. For large corpora, use parse_and_clean_stream.py instead —
  it processes one CSV at a time and writes directly to books_clean.json,
  bypassing steps 01 and 02 entirely:

      for f in books_text_*.csv; do
          python3 src/parse_and_clean_stream.py "$f"
      done

Input:  books_metadata_full.csv (tab-sep), books_text_*.csv (CSV, auto-detected)
Output: books_parsed.json

Language filtering:
  Language is detected from the book's actual text content using langdetect.
  A book is excluded if its top-detected language is not English with
  confidence ≥ 0.7.  Books that are ambiguous or where detection fails
  are included by default (metadata gap ≠ exclusion).

  For edge cases (mixed-language books, parallel translations, OCR noise),
  csv/lang_override.csv provides per-book overrides:
    action=include  → force-include regardless of detected language
    action=exclude  → force-exclude regardless of detected language
  This file is optional and starts empty; add rows only when auto-detection
  gets it wrong.

  Requires: langdetect (pip install langdetect)
  If langdetect is not installed, all books pass through with a warning.
"""

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_metadata_full.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


import csv, datetime, glob, json, os, re
csv.field_size_limit(10_000_000)

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
# Books below this threshold are included (safe default for ambiguous/short texts).
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


# ── Lightweight raw-text preprocessing ───────────────────────────────────────
# Applied before books_parsed.json is written.  Goal: remove the worst noise
# categories so that 02_clean_text.py works on a much cleaner input.
# Deliberately conservative — heavy semantic cleaning belongs in step 02.

# Null / control characters (except tab and newline)
_CTRL_RE    = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
# Runs of 4+ non-alphanumeric, non-whitespace characters (OCR symbol garble)
_SYMBOL_RE  = re.compile(r'[^a-zA-Z0-9\s\'\-]{4,}')
# Standalone numbers-only tokens on their own line (page numbers, footnote refs)
_PAGENUM_RE = re.compile(r'(?m)^\s*\d{1,4}\s*$')
# Repeated punctuation (OCR scanning artefacts: ". . . . ." or "— — — —")
_REPEAT_PUNCT_RE = re.compile(r'([^\w\s])\1{2,}')
# Lines that are purely uppercase and very short (≤4 words) → likely headers
# that leaked into body text; collapse to title-case so they don't inflate caps
_ALLCAPS_LINE_RE = re.compile(r'(?m)^([A-Z][A-Z\s]{0,40}[A-Z])$')
# Excessive whitespace runs
_WS_RE = re.compile(r'[ \t]{3,}')


def preprocess_raw_text(text: str) -> str:
    """
    Light-touch noise removal applied at parse time (step 01).
    Does NOT touch semantic content — boilerplate section removal,
    dictionary filtering, and case normalisation happen in step 02.
    """
    # Normalise line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Strip null / control characters
    text = _CTRL_RE.sub('', text)
    # Remove dense symbol runs (OCR garble)
    text = _SYMBOL_RE.sub(' ', text)
    # Remove standalone page-number lines
    text = _PAGENUM_RE.sub('', text)
    # Collapse repeated punctuation to a single instance
    text = _REPEAT_PUNCT_RE.sub(r'\1', text)
    # Soft-normalise all-caps short lines to title-case
    text = _ALLCAPS_LINE_RE.sub(lambda m: m.group(1).title(), text)
    # Collapse excessive horizontal whitespace
    text = _WS_RE.sub(' ', text)
    # Collapse 3+ blank lines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ── Load lang_override.csv (optional per-book overrides) ─────────────────────
# Columns: id, action (include|exclude), lang_code, note
# 'include'  → force-keep regardless of detected language
# 'exclude'  → force-drop regardless of detected language
# File is optional; no rows needed for a clean corpus.
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
valid_book_ids = set()
books_meta = {}
meta_path = CSV_DIR / 'books_metadata_full.csv'
if not meta_path.exists():
    raise FileNotFoundError(
        f"{meta_path} not found.\n"
        "Run: python3 src/00_export_calibre.py")
with open(str(meta_path), encoding='utf-8') as f:
    for row in csv.DictReader(f, delimiter='\t'):
        bid = row['id'].strip()
        raw = row['author_sort'].strip()
        parts = raw.split(',', 1)
        author = (parts[1].strip() + ' ' + parts[0].strip()).strip() if len(parts)==2 else raw
        valid_book_ids.add(bid)
        books_meta[bid] = {'title': row['title'].strip(), 'author': author,
                           'pubdate': row['pubdate'].strip()[:4]}

# ── Load text and apply language filter ───────────────────────────────────────
text_files = sorted(glob.glob(str(CSV_DIR / 'books_text_*.csv')))
books_data   = {}
skipped_dupe = []
lang_excluded = []   # (bid, title, detected_lang, confidence, source)

for fpath in text_files:
    fname = os.path.basename(fpath)
    n_new = 0
    with open(fpath, encoding='utf-8', errors='replace') as f:
        for row in csv.DictReader(f):
            bid = row['id'].strip()
            if bid not in valid_book_ids:
                continue
            if bid in books_data:
                skipped_dupe.append(bid)
                continue

            raw_text = row['searchable_text']
            title    = books_meta.get(bid, {}).get('title', f'Book {bid}')

            # Manual override takes absolute precedence
            if lang_override.get(bid) == 'exclude':
                lang_excluded.append((bid, title, 'override', 1.0, 'override'))
                continue
            if lang_override.get(bid) == 'include':
                # Force-include: skip detection entirely
                books_data[bid] = {'text': preprocess_raw_text(raw_text), '_src': fname}
                n_new += 1
                continue

            # Auto-detect from text
            detected_lang, confidence = detect_book_language(raw_text)
            if detected_lang != 'en' and confidence >= _LANG_CONF_THRESHOLD:
                lang_excluded.append((bid, title, detected_lang, confidence, 'auto'))
                continue

            books_data[bid] = {'text': preprocess_raw_text(raw_text), '_src': fname}
            n_new += 1
    print(f"  {fname}  +{n_new} (total {len(books_data)})")

# ── Language filter report ────────────────────────────────────────────────────
if lang_excluded:
    print(f"\nLanguage filter: excluded {len(lang_excluded)} non-English books:")
    for bid, title, lang, conf, src in sorted(lang_excluded, key=lambda x: x[2]):
        print(f"  [{bid}] ({lang} {conf:.2f}, {src}) {title}")
else:
    print("\nLanguage filter: all books detected as English (or detection skipped)")

# ── Attach metadata and finalise ──────────────────────────────────────────────
for bid in books_data:
    meta = books_meta.get(bid, {})
    books_data[bid].update({'title': meta.get('title', f'Book {bid}'),
                            'author': meta.get('author', ''),
                            'pubdate': meta.get('pubdate', '')})
    del books_data[bid]['_src']

print(f"Dupes skipped: {len(skipped_dupe)}")
print(f"Final corpus: {len(books_data)} books")
with open(str(JSON_DIR / 'books_parsed.json'), 'w', encoding='utf-8') as f:
    json.dump(books_data, f, ensure_ascii=False)
print("Saved books_parsed.json")

# ── runlog.csv: append one row per dropped book for auditability ─────────────
_runlog_path = CSV_DIR / 'runlog.csv'
_run_ts  = datetime.datetime.now().isoformat(timespec='seconds')
_logrows = []
for bid, title, lang, conf, src in lang_excluded:
    _logrows.append({'run_timestamp': _run_ts, 'step': '01_parse_books',
                     'action': 'lang_excluded', 'book_id': bid,
                     'title': title, 'lang_code': lang,
                     'confidence': conf, 'source': src})
for bid in skipped_dupe:
    title = books_meta.get(bid, {}).get('title', '')
    _logrows.append({'run_timestamp': _run_ts, 'step': '01_parse_books',
                     'action': 'dupe_skipped', 'book_id': bid,
                     'title': title, 'lang_code': '', 'confidence': '', 'source': ''})
_log_fields = ['run_timestamp', 'step', 'action', 'book_id', 'title',
               'lang_code', 'confidence', 'source']
_write_header = not _runlog_path.exists()
with open(str(_runlog_path), 'a', encoding='utf-8', newline='') as _lf:
    _writer = csv.DictWriter(_lf, fieldnames=_log_fields)
    if _write_header:
        _writer.writeheader()
    _writer.writerows(_logrows)
print(f"runlog.csv: appended {len(_logrows)} row(s) ({_runlog_path})")
