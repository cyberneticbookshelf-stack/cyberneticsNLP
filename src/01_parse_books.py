"""


01_parse_books.py
─────────────────────────────────────────────────────────────────────────────
Step 1 of the Book NLP Pipeline.

Auto-detects every books_text_*.csv in the current directory, merges them
into a single collection, and joins with metadata from books_lang.csv.
Duplicate book IDs resolved by keeping the FIRST occurrence (alphabetical order).

NOTE FOR LARGE CORPORA (>~300 books):
  This script produces books_parsed.json which can exceed 500 MB.
  Step 02 must then load that entire file, which can time out in constrained
  environments. For large corpora, use parse_and_clean_stream.py instead —
  it processes one CSV at a time and writes directly to books_clean.json,
  bypassing steps 01 and 02 entirely:

      for f in books_text_*.csv; do
          python3 src/parse_and_clean_stream.py "$f"
      done

Input:  books_lang.csv (tab-sep), books_text_*.csv (CSV, auto-detected)
Output: books_parsed.json
"""

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_lang.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


import csv, glob, json, os
csv.field_size_limit(10_000_000)

valid_book_ids = set()
books_meta = {}
with open(str(CSV_DIR / 'books_lang.csv'), encoding='utf-8') as f:
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
            books_data[bid] = {'text': row['searchable_text'], '_src': fname}
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