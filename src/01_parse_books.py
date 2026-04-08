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
"""

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_metadata_full.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


import csv, glob, json, os, re
csv.field_size_limit(10_000_000)

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

text_files = sorted(glob.glob(str(CSV_DIR / 'books_text_*.csv')))
books_data, skipped_dupe = {}, []
for fpath in text_files:
    fname = os.path.basename(fpath)
    n_new = 0
    with open(fpath, encoding='utf-8', errors='replace') as f:
        for row in csv.DictReader(f):
            bid = row['id'].strip()
            if bid not in valid_book_ids: continue
            if bid in books_data: skipped_dupe.append(bid); continue
            books_data[bid] = {'text': preprocess_raw_text(row['searchable_text']), '_src': fname}
            n_new += 1
    print(f"  {fname}  +{n_new} (total {len(books_data)})")

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