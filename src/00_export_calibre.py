"""
00_export_calibre.py
────────────────────────────────────────────────────────────────────────────
Export books_metadata_full.csv from the Calibre metadata.db SQLite database.

This script is the canonical source for csv/books_metadata_full.csv — the
enriched metadata file used by all downstream pipeline scripts:
  - 00_classify_book_styles.py  → book style heuristics
  - 00_fetch_worldcat_metadata.py / 00_fetch_anu_primo.py → enrichment
  - train_monograph_classifier.py → supervised classifier features
  - 01_parse_books.py / parse_and_clean_stream.py → corpus ingestion

Output: csv/books_metadata_full.csv (tab-separated, UTF-8)

Columns (22):
  id                — Calibre book ID
  title             — book title
  author_sort       — author(s) in sort form (Last, First)
  pubdate           — publication year (YYYY extracted from Calibre pubdate)
  publisher         — publisher name
  series            — series name (empty if none)
  isbn              — ISBN-13 (preferred) or ISBN-10 from identifiers
  google_id         — Google Books ID from identifiers (type=google)
  amazon_id         — Amazon ASIN from identifiers (type=amazon or asin)
  source_url        — URL from custom column 1 (URL field)
  available_at      — provenance label from custom column 2 (Available at)
  theme             — curatorial theme from custom column 4 (Theme)
  pub_type          — manually assigned publication type from custom column 5
                      (Publication Type). Values are comma-separated and
                      non-disjoint: e.g. "monograph, textbook" is valid.
                      Canonical values: monograph, anthology, textbook,
                      proceedings, journal special issue, reference,
                      collected works, catalog, popular, history_bio.
                      Pipeline inclusion rule: include if 'monograph' OR
                      'collected works' appears in the label; exclude otherwise.
  description       — HTML description from comments table
  tags              — comma-separated tag names
  archive_id        — Internet Archive / URI identifier
  lang_code         — ISO 639-2 language code from Calibre (e.g. eng, fra, deu);
                      empty if not set in Calibre
  in_title          — yes/no: "cybernetic(s)" in title
  in_description    — yes/no: "cybernetic(s)" in description
  in_tags           — yes/no: "cybernetic(s)" in any tag
  in_publisher      — yes/no: "cybernetic(s)" in publisher name
  inclusion_stratum — corpus inclusion basis (see below)

Inclusion stratum logic:
  title_corroborated — cybernetic(s) in title AND ≥1 other field
  title_only         — cybernetic(s) in title only
  curated_keyword    — theme=Cybernetics; cybernetic(s) in description/tags
                       but NOT in title
  curated_pure       — theme=Cybernetics; no cybernetic(s) anywhere
  metadata_search    — not theme-tagged as Cybernetics

Usage:
  python3 src/00_export_calibre.py
  python3 src/00_export_calibre.py --db /path/to/metadata.db
  python3 src/00_export_calibre.py --db /path/to/metadata.db --out csv/books_metadata_full.csv

Calibre DB location (default): data/inputs/calibre/metadata.db
Re-run whenever books are added to or removed from the Calibre library,
or when custom column values (Available at, Theme) are updated.
"""

import argparse
import csv
import pathlib
import re
import shutil
import sqlite3
import sys
import tempfile

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT    = pathlib.Path('.')
CSV_DIR = ROOT / 'csv'
CSV_DIR.mkdir(exist_ok=True)

DEFAULT_DB  = ROOT / 'data' / 'inputs' / 'calibre' / 'metadata.db'
DEFAULT_OUT = CSV_DIR / 'books_metadata_full.csv'

# ── Args ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description='Export Calibre metadata to CSV')
parser.add_argument('--db',  default=str(DEFAULT_DB),
                    help='Path to Calibre metadata.db')
parser.add_argument('--out', default=str(DEFAULT_OUT),
                    help='Output CSV path (tab-separated)')
args = parser.parse_args()

db_path  = pathlib.Path(args.db)
out_path = pathlib.Path(args.out)

if not db_path.exists():
    sys.exit(f"ERROR: metadata.db not found at {db_path}\n"
             f"  Set --db to the correct path or copy the file to {DEFAULT_DB}")

# ── Open DB (copy to temp to avoid locking issues with Calibre open) ──────────
print(f"[1] Opening database: {db_path}")
with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
    tmp_path = pathlib.Path(tmp.name)
shutil.copy(db_path, tmp_path)
conn = sqlite3.connect(tmp_path)
conn.row_factory = sqlite3.Row

# ── Keyword pattern ───────────────────────────────────────────────────────────
CYBER_RE = re.compile(r'cybernetic', re.IGNORECASE)


def has_cyber(text):
    """Return 'yes' if text contains 'cybernetic(s)', else 'no'."""
    if not text:
        return 'no'
    return 'yes' if CYBER_RE.search(text) else 'no'


# ── 1. Core book fields ───────────────────────────────────────────────────────
print("[2] Loading core book fields...")
books = {}
for row in conn.execute(
        "SELECT id, title, author_sort, pubdate FROM books ORDER BY id"):
    bid = str(row['id'])
    # Calibre stores pubdate as ISO string; extract 4-digit year
    pubdate_raw = row['pubdate'] or ''
    year = pubdate_raw[:4] if len(pubdate_raw) >= 4 else ''
    books[bid] = {
        'id':          bid,
        'title':       row['title'] or '',
        'author_sort': row['author_sort'] or '',
        'pubdate':     year,
    }
print(f"  {len(books)} books")

# ── 2. Publishers ─────────────────────────────────────────────────────────────
print("[3] Loading publishers...")
publisher_map = {}  # book_id → publisher name
for row in conn.execute("""
        SELECT bpl.book, p.name
        FROM publishers p
        JOIN books_publishers_link bpl ON p.id = bpl.publisher
"""):
    publisher_map[str(row['book'])] = row['name'] or ''

# ── 3. Series ─────────────────────────────────────────────────────────────────
print("[4] Loading series...")
series_map = {}  # book_id → series name
for row in conn.execute("""
        SELECT bsl.book, s.name
        FROM series s
        JOIN books_series_link bsl ON s.id = bsl.series
"""):
    series_map[str(row['book'])] = row['name'] or ''

# ── 4. Identifiers (isbn, google, amazon, archive, uri/url) ───────────────────
print("[5] Loading identifiers...")
isbn_map    = {}   # book_id → ISBN string
google_map  = {}   # book_id → Google Books ID
amazon_map  = {}   # book_id → Amazon ASIN
archive_map = {}   # book_id → archive/uri identifier

for row in conn.execute("SELECT book, type, val FROM identifiers"):
    bid  = str(row['book'])
    itype = (row['type'] or '').lower().strip()
    val   = row['val'] or ''

    if not val:
        continue

    # ISBN: prefer isbn13, accept isbn or bare 'isbn' variants
    if itype in ('isbn',) and bid not in isbn_map:
        isbn_map[bid] = val
    elif itype.startswith('isbn13') and bid not in isbn_map:
        isbn_map[bid] = val

    # Google Books ID
    if itype == 'google' and bid not in google_map:
        google_map[bid] = val

    # Amazon ASIN — 'amazon' or 'asin' or 'mobi-asin'
    if itype in ('amazon', 'asin') and bid not in amazon_map:
        amazon_map[bid] = val

    # Archive / URI — internet archive ID or generic URI
    if itype in ('uri', 'url') and bid not in archive_map:
        archive_map[bid] = val

# ── 5. Descriptions (comments table) ─────────────────────────────────────────
print("[6] Loading descriptions...")
desc_map = {}  # book_id → HTML description
for row in conn.execute("SELECT book, text FROM comments"):
    desc_map[str(row['book'])] = row['text'] or ''

# ── 6. Tags ───────────────────────────────────────────────────────────────────
print("[7] Loading tags...")
tags_map = {}  # book_id → list of tag names
for row in conn.execute("""
        SELECT btl.book, t.name
        FROM tags t
        JOIN books_tags_link btl ON t.id = btl.tag
        ORDER BY btl.book, t.name
"""):
    bid = str(row['book'])
    tags_map.setdefault(bid, []).append(row['name'] or '')

# ── 7. Custom column 1 — URL (source_url) ─────────────────────────────────────
print("[8] Loading source URLs (custom column 1)...")
url_map = {}  # book_id → URL string
# custom_column_1 is a text lookup table; books link via books_custom_column_1_link
try:
    url_lookup = {
        str(row['id']): row['value']
        for row in conn.execute("SELECT id, value FROM custom_column_1")
    }
    for row in conn.execute(
            "SELECT book, value FROM books_custom_column_1_link"):
        bid    = str(row['book'])
        val_id = str(row['value'])
        if val_id in url_lookup:
            url_map[bid] = url_lookup[val_id]
except Exception as e:
    print(f"  WARNING: could not load custom_column_1 (URL): {e}")

# ── 8. Custom column 2 — Available at ────────────────────────────────────────
print("[9] Loading availability (custom column 2)...")
avail_map = {}  # book_id → availability string
try:
    avail_lookup = {
        str(row['id']): row['value']
        for row in conn.execute("SELECT id, value FROM custom_column_2")
    }
    for row in conn.execute(
            "SELECT book, value FROM books_custom_column_2_link"):
        bid    = str(row['book'])
        val_id = str(row['value'])
        if val_id in avail_lookup:
            avail_map[bid] = avail_lookup[val_id]
except Exception as e:
    print(f"  WARNING: could not load custom_column_2 (Available at): {e}")

# ── 9. Custom column 4 — Theme ────────────────────────────────────────────────
print("[10] Loading themes (custom column 4)...")
theme_map = {}  # book_id → theme string
try:
    for row in conn.execute("SELECT book, value FROM custom_column_4"):
        theme_map[str(row['book'])] = row['value'] or ''
except Exception as e:
    print(f"  WARNING: could not load custom_column_4 (Theme): {e}")

# ── 9b. Custom column 5 — Publication Type ────────────────────────────────────
print("[10b] Loading publication types (custom column 5)...")
pubtype_map = {}  # book_id → publication type string (may be multi-valued)
try:
    for row in conn.execute("SELECT book, value FROM custom_column_5"):
        pubtype_map[str(row['book'])] = (row['value'] or '').strip()
    print(f"  {len(pubtype_map)} books with Publication Type")
except Exception as e:
    print(f"  WARNING: could not load custom_column_5 (Publication Type): {e}")

# ── 10. Languages ──────────────────────────────────────────────────────────────
print("[11] Loading languages...")
lang_map = {}  # book_id → ISO 639-2 lang_code (e.g. 'eng', 'fra', 'deu')
# Calibre schema: books_languages_link.lang_code is a FK to languages.id;
# the actual code string lives in languages.lang_code.
# item_order=0 is the primary language; we keep only the first per book.
try:
    for row in conn.execute("""
            SELECT bll.book, l.lang_code
            FROM   languages l
            JOIN   books_languages_link bll ON l.id = bll.lang_code
            ORDER  BY bll.book, bll.item_order
    """):
        bid = str(row['book'])
        if bid not in lang_map:          # first row = primary language
            lang_map[bid] = (row['lang_code'] or '').strip().lower()
    print(f"  {len(lang_map)} books with language metadata")
except Exception as e:
    print(f"  WARNING: could not load languages table: {e}")

conn.close()
tmp_path.unlink(missing_ok=True)

# ── 10. Assemble rows and compute derived fields ───────────────────────────────
print("[11] Assembling output rows...")
output_rows = []

for bid, b in sorted(books.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
    title       = b['title']
    publisher   = publisher_map.get(bid, '')
    description = desc_map.get(bid, '')
    tags_list   = tags_map.get(bid, [])
    tags_str    = ','.join(tags_list)
    theme       = theme_map.get(bid, '')

    # Keyword flags — search for "cybernetic" (covers cybernetics, cybernetic)
    in_title       = has_cyber(title)
    in_description = has_cyber(description)
    in_tags        = has_cyber(tags_str)
    in_publisher   = has_cyber(publisher)

    # Inclusion stratum
    any_other = (in_description == 'yes' or
                 in_tags        == 'yes' or
                 in_publisher   == 'yes')

    if in_title == 'yes':
        stratum = 'title_corroborated' if any_other else 'title_only'
    elif theme.strip().lower() == 'cybernetics':
        stratum = ('curated_keyword'
                   if (in_description == 'yes' or in_tags == 'yes')
                   else 'curated_pure')
    else:
        stratum = 'metadata_search'

    output_rows.append({
        'id':               bid,
        'title':            title,
        'author_sort':      b['author_sort'],
        'pubdate':          b['pubdate'],
        'publisher':        publisher,
        'series':           series_map.get(bid, ''),
        'isbn':             isbn_map.get(bid, ''),
        'google_id':        google_map.get(bid, ''),
        'amazon_id':        amazon_map.get(bid, ''),
        'source_url':       url_map.get(bid, ''),
        'available_at':     avail_map.get(bid, ''),
        'theme':            theme,
        'pub_type':         pubtype_map.get(bid, ''),
        'description':      description,
        'tags':             tags_str,
        'archive_id':       archive_map.get(bid, ''),
        'lang_code':        lang_map.get(bid, ''),
        'in_title':         in_title,
        'in_description':   in_description,
        'in_tags':          in_tags,
        'in_publisher':     in_publisher,
        'inclusion_stratum': stratum,
    })

# ── 11. Write CSV ─────────────────────────────────────────────────────────────
COLUMNS = [
    'id', 'title', 'author_sort', 'pubdate', 'publisher', 'series',
    'isbn', 'google_id', 'amazon_id', 'source_url', 'available_at',
    'theme', 'pub_type', 'description', 'tags', 'archive_id', 'lang_code',
    'in_title', 'in_description', 'in_tags', 'in_publisher',
    'inclusion_stratum',
]

print(f"[12] Writing {out_path}...")
with open(out_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter='\t',
                            quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    writer.writerows(output_rows)

# ── 12. Summary ───────────────────────────────────────────────────────────────
from collections import Counter
strata = Counter(r['inclusion_stratum'] for r in output_rows)
themes = Counter(r['theme'] for r in output_rows if r['theme'])
langs  = Counter(r['lang_code'] for r in output_rows if r['lang_code'])

print(f"\n{'='*55}")
print(f"EXPORT COMPLETE: {out_path}")
print(f"{'='*55}")
print(f"  Total books:       {len(output_rows)}")
print(f"\n  Languages (set in Calibre):")
for lang, n in langs.most_common():
    print(f"    {lang:<10} {n:4d}")
no_lang = sum(1 for r in output_rows if not r['lang_code'])
print(f"    {'(not set)':<10} {no_lang:4d}")
print(f"\n  Inclusion strata:")
for s, n in strata.most_common():
    print(f"    {s:<25} {n:4d}")
print(f"\n  Top themes:")
for t, n in themes.most_common(10):
    print(f"    {t:<25} {n:4d}")
print(f"\n  Keyword flags:")
print(f"    in_title=yes:       {sum(1 for r in output_rows if r['in_title']=='yes'):4d}")
print(f"    in_description=yes: {sum(1 for r in output_rows if r['in_description']=='yes'):4d}")
print(f"    in_tags=yes:        {sum(1 for r in output_rows if r['in_tags']=='yes'):4d}")
print(f"    in_publisher=yes:   {sum(1 for r in output_rows if r['in_publisher']=='yes'):4d}")
print(f"\nRun next: python3 src/00_classify_book_styles.py")
