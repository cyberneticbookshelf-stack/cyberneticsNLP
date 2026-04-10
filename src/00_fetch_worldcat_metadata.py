"""
00_fetch_worldcat_metadata.py
─────────────────────────────────────────────────────────────────────────────
Fetch external metadata for each book using:
  1. Google Books API  (primary — 94% coverage via google_id)
     Returns: categories, authors/editors distinction, subtitle, description
  2. OCLC Classify API (secondary — 94% coverage via isbn)
     Returns: DDC class, LCC class, total library holdings
  3. Internet Archive  (tertiary — 23% coverage via archive_id)
     Returns: collection, subject, mediatype

All results are cached to json/external_metadata_cache.json so re-runs
only fetch books not yet in the cache. Rate-limited to be polite.

Input:  csv/books_metadata_full.csv
Output: json/external_metadata_cache.json  — raw API responses per book
        json/book_styles_enriched.json     — book_styles.json + API signals

Usage:
  python3 src/00_fetch_worldcat_metadata.py             # fetch all
  python3 src/00_fetch_worldcat_metadata.py --limit 20  # test with 20 books
  python3 src/00_fetch_worldcat_metadata.py --reclassify # update styles from cache
  python3 src/00_fetch_worldcat_metadata.py --stats      # cache coverage stats only

APIs used (all free, no key required for basic use):
  Google Books:  https://www.googleapis.com/books/v1/volumes?id=GOOGLE_ID
  OCLC Classify: http://classify.oclc.org/classify2/Classify?isbn=ISBN&summary=true
  Open Library:  https://openlibrary.org/api/books?bibkeys=ISBN:ISBN&jscmd=data&format=json
  Archive.org:   https://archive.org/metadata/ARCHIVE_ID

Rate limits:
  Google Books:  1,000 req/day without key (sufficient for 726 books in one run)
  OCLC Classify: no published limit — polite 0.3s delay used
  Open Library:  generous fair use — 0.2s delay
  Archive.org:   no published limit — 0.2s delay
"""

# ── Directory layout ──────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')
JSON_DIR = _pl.Path('json')
JSON_DIR.mkdir(exist_ok=True)

import csv, json, sys, re, time
import urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date

LIMIT      = None
RECLASSIFY = '--reclassify' in sys.argv
STATS_ONLY = '--stats'      in sys.argv

if '--limit' in sys.argv:
    try:
        LIMIT = int(sys.argv[sys.argv.index('--limit') + 1])
        print(f"  [--limit] fetching at most {LIMIT} books")
    except (IndexError, ValueError):
        print('  [--limit] usage: --limit N')

DELAY_GOOGLE  = 0.5   # seconds between Google Books requests
DELAY_OCLC    = 0.4
DELAY_ARCHIVE = 0.3

# ── DDC style mapping ─────────────────────────────────────────────────────────
# Maps Dewey Decimal class prefixes to epistemic style signals
DDC_STYLE_HINTS = {
    # Pure science / technical → likely monograph
    '003': ('monograph', 'Systems theory'),
    '004': ('monograph', 'Computer science'),
    '006': ('monograph', 'AI / cognitive science'),
    '150': ('monograph', 'Psychology'),
    '153': ('monograph', 'Cognitive psychology'),
    '500': ('monograph', 'Natural sciences'),
    '510': ('monograph', 'Mathematics'),
    '570': ('monograph', 'Biology'),
    '610': ('monograph', 'Medicine'),
    # Social sciences
    '300': ('monograph', 'Social sciences'),
    '330': ('monograph', 'Economics'),
    '658': ('monograph', 'Management'),
    # Reference / handbook territory
    '020': ('handbook',  'Library science'),
    '030': ('handbook',  'General encyclopedias'),
}

# ── LCC style mapping ─────────────────────────────────────────────────────────
LCC_ANTHOLOGY_RE = re.compile(
    r'\b(?:collected works|essays|addresses|lectures|congresses|symposia)\b',
    re.IGNORECASE)


# ── Fetch helpers ─────────────────────────────────────────────────────────────

def _get_json(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'CyberneticsNLP/0.4 (research)'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8', errors='replace'))
    except Exception as e:
        return {'_error': str(e)}


def _get_text(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'CyberneticsNLP/0.4 (research)'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        return ''


def fetch_google_books(google_id):
    """Fetch volume metadata from Google Books by volume ID."""
    if not google_id:
        return {}
    url = f'https://www.googleapis.com/books/v1/volumes/{google_id}'
    data = _get_json(url)
    if '_error' in data or 'volumeInfo' not in data:
        return {'_error': data.get('_error', 'no volumeInfo')}
    vi = data['volumeInfo']
    return {
        'title':          vi.get('title', ''),
        'subtitle':       vi.get('subtitle', ''),
        'authors':        vi.get('authors', []),
        'editors':        [a for a in vi.get('authors', [])
                           if any(x in a.lower() for x in ['(ed)', '(eds)', 'editor'])],
        'publisher':      vi.get('publisher', ''),
        'published_date': vi.get('publishedDate', ''),
        'categories':     vi.get('categories', []),
        'description':    vi.get('description', '')[:500],
        'page_count':     vi.get('pageCount', 0),
        'maturity':       vi.get('maturityRating', ''),
        'language':       vi.get('language', ''),
        'print_type':     vi.get('printType', ''),
    }


def fetch_oclc_classify(isbn):
    """Fetch DDC/LCC classification and holdings from OCLC Classify."""
    if not isbn:
        return {}
    # Clean ISBN
    isbn_clean = re.sub(r'[^0-9X]', '', isbn.upper())
    url = f'http://classify.oclc.org/classify2/Classify?isbn={isbn_clean}&summary=true'
    text = _get_text(url)
    if not text:
        return {'_error': 'no response'}
    try:
        root = ET.fromstring(text)
        ns = {'c': 'http://classify.oclc.org/classify2/ClassifyFeedback'}
        # Response code
        rc_el = root.find('.//c:response', ns)
        rc = rc_el.get('code', '') if rc_el is not None else ''
        if rc not in ('0', '2', '4'):
            return {'_error': f'classify response code {rc}'}
        # Work metadata
        work_el = root.find('.//c:work', ns)
        holdings = 0
        if work_el is not None:
            holdings = int(work_el.get('holdings', 0) or 0)
        # Recommendations
        ddc_el = root.find('.//c:ddc/c:mostPopular', ns)
        lcc_el = root.find('.//c:lcc/c:mostPopular', ns)
        ddc = ddc_el.get('nsfa', '') if ddc_el is not None else ''
        lcc = lcc_el.get('nsfa', '') if lcc_el is not None else ''
        return {
            'ddc':      ddc,
            'lcc':      lcc,
            'holdings': holdings,
            'rc':       rc,
        }
    except ET.ParseError as e:
        return {'_error': f'xml parse: {e}'}


def fetch_open_library(isbn):
    """Fetch subject headings and publisher from Open Library as fallback."""
    if not isbn:
        return {}
    isbn_clean = re.sub(r'[^0-9X]', '', isbn.upper())
    url = (f'https://openlibrary.org/api/books'
           f'?bibkeys=ISBN:{isbn_clean}&jscmd=data&format=json')
    data = _get_json(url)
    key = f'ISBN:{isbn_clean}'
    if key not in data:
        return {}
    book = data[key]
    subjects = [s.get('name', '') for s in book.get('subjects', [])]
    publishers = [p.get('name', '') for p in book.get('publishers', [])]
    return {
        'subjects':   subjects[:10],
        'publishers': publishers[:3],
        'lc_class':   book.get('classifications', {}).get('lc_classifications', []),
        'dewey':      book.get('classifications', {}).get('dewey_decimal_class', []),
        'num_pages':  book.get('number_of_pages', 0),
    }


def fetch_archive_org(archive_id):
    """Fetch metadata from Internet Archive."""
    if not archive_id:
        return {}
    url = f'https://archive.org/metadata/{archive_id}'
    data = _get_json(url)
    if '_error' in data or 'metadata' not in data:
        return {'_error': data.get('_error', 'no metadata')}
    meta = data['metadata']
    return {
        'mediatype':   meta.get('mediatype', ''),
        'collection':  meta.get('collection', []),
        'subject':     meta.get('subject', []),
        'date':        meta.get('date', ''),
        'language':    meta.get('language', ''),
        'creator':     meta.get('creator', ''),
        'description': str(meta.get('description', ''))[:300],
    }


# ── Style inference from API data ─────────────────────────────────────────────

def infer_style_from_api(google, oclc, openlibrary, archive):
    """
    Return (style_hint, confidence, signals) from API data.
    These supplement heuristic signals — they don't override manual verification.
    """
    signals = []
    votes = Counter()

    # ── Google Books ──────────────────────────────────────────────────────────
    if google and '_error' not in google:
        # Editor detection — most reliable anthology signal
        subtitle = (google.get('subtitle') or '').lower()
        desc     = (google.get('description') or '').lower()
        cats     = [c.lower() for c in google.get('categories', [])]

        if google.get('editors'):
            signals.append('google:has_editors')
            votes['anthology'] += 4

        if re.search(r'\bedited\s+by\b|\b\(ed\.\)|\b\(eds\.\)', subtitle + desc):
            signals.append('google:edited_by_in_text')
            votes['anthology'] += 3

        if re.search(r'\bessays\b|\bcollected\b|\bcontributions\b', subtitle):
            signals.append('google:anthology_subtitle')
            votes['anthology'] += 2

        if re.search(r'\bintroduction\s+to\b|\bfundamentals\b|\bprimer\b', subtitle):
            signals.append('google:textbook_subtitle')
            votes['textbook'] += 2

        # Category signals
        for cat in cats:
            if re.search(r'\bfiction\b|\bnovel\b|\bpoetry\b', cat):
                signals.append(f'google:cat_fiction')
                votes['popular'] += 1
            if re.search(r'\bself.help\b|\bpersonal\s+growth\b', cat):
                signals.append('google:cat_self_help')
                votes['popular'] += 3
            if re.search(r'\btextbook\b|\bcourse\b', cat):
                signals.append('google:cat_textbook')
                votes['textbook'] += 2
            if re.search(r'\bbiograd\b|\bbiograph\b|\bhistor\b', cat):
                signals.append('google:cat_biography')
                votes['history_bio'] += 2

        # Page count heuristic — very short → report/pamphlet
        pages = google.get('page_count', 0) or 0
        if 0 < pages < 80:
            signals.append(f'google:short_{pages}pp')
            votes['report'] += 1

    # ── OCLC Classify ─────────────────────────────────────────────────────────
    if oclc and '_error' not in oclc:
        ddc = oclc.get('ddc', '')
        lcc = oclc.get('lcc', '')
        holdings = oclc.get('holdings', 0)

        # DDC prefix hints
        for prefix, (style_hint, label) in DDC_STYLE_HINTS.items():
            if ddc.startswith(prefix):
                signals.append(f'oclc:ddc_{prefix}_{label}')
                votes[style_hint] += 1

        # LCC anthology markers
        if LCC_ANTHOLOGY_RE.search(lcc):
            signals.append('oclc:lcc_anthology_marker')
            votes['anthology'] += 2

        # Holdings: widely held → likely significant monograph or textbook
        if holdings > 500:
            signals.append(f'oclc:holdings_{holdings}')
            votes['monograph'] += 1
        elif holdings > 2000:
            votes['textbook'] += 1  # very widely held → likely textbook

    # ── Open Library ──────────────────────────────────────────────────────────
    if openlibrary and '_error' not in openlibrary:
        subjects = ' '.join(openlibrary.get('subjects', [])).lower()
        if re.search(r'\bcongresses\b|\bsymposia\b', subjects):
            signals.append('openlibrary:proceedings_subject')
            votes['proceedings'] += 3
        if re.search(r'\bcollected works\b|\bessays\b', subjects):
            signals.append('openlibrary:anthology_subject')
            votes['anthology'] += 2

    if not votes:
        return 'monograph', 'low', signals

    best, score = votes.most_common(1)[0]
    total = sum(votes.values())
    dom = score / total if total else 0
    conf = 'high' if score >= 4 and dom >= 0.7 else 'medium' if score >= 2 else 'low'
    return best, conf, signals


# ── Load inputs ───────────────────────────────────────────────────────────────

print("Loading inputs...")
meta_rows = {}
with open(str(CSV_DIR / 'books_metadata_full.csv'), encoding='utf-8') as f:
    for row in csv.DictReader(f, delimiter='\t'):
        meta_rows[str(row['id'])] = row
print(f"  {len(meta_rows)} books in books_metadata_full.csv")

book_styles = {}
try:
    book_styles = json.load(open(str(JSON_DIR / 'book_styles.json')))
    print(f"  {len(book_styles)} books in book_styles.json")
except FileNotFoundError:
    print("  book_styles.json not found — run 00_classify_book_styles.py first")
    sys.exit(1)

# Load or init cache
cache_path = str(JSON_DIR / 'external_metadata_cache.json')
try:
    cache = json.load(open(cache_path))
    print(f"  Cache: {len(cache)} books already fetched")
except (FileNotFoundError, json.JSONDecodeError):
    cache = {}
    print("  Cache: empty — fetching all")

if STATS_ONLY:
    print(f"\nCache coverage:")
    for source in ['google', 'oclc', 'openlibrary', 'archive']:
        n = sum(1 for v in cache.values() if v.get(source) and '_error' not in v.get(source, {}))
        print(f"  {source:15s}: {n}/{len(cache)}")
    sys.exit(0)

# ── Fetch loop ────────────────────────────────────────────────────────────────

to_fetch = [bid for bid in meta_rows if bid not in cache]
if LIMIT:
    to_fetch = to_fetch[:LIMIT]

print(f"\nFetching metadata for {len(to_fetch)} books "
      f"({len(cache)} already cached)...")

for i, bid in enumerate(to_fetch, 1):
    row        = meta_rows[bid]
    google_id  = row.get('google_id', '').strip()
    isbn       = row.get('isbn', '').strip()
    archive_id = row.get('archive_id', '').strip()
    title      = row.get('title', '')[:50]

    print(f"  [{i:3d}/{len(to_fetch)}] [{bid}] {title:50s}", end=' ', flush=True)

    entry = {}

    # Google Books (primary)
    if google_id:
        entry['google'] = fetch_google_books(google_id)
        time.sleep(DELAY_GOOGLE)
        ok = '_error' not in entry['google']
        print(f"G{'✓' if ok else '✗'}", end=' ', flush=True)
    else:
        entry['google'] = {}

    # OCLC Classify — currently returning 403; skipped in favour of Open Library
    entry['oclc'] = {}

    # Open Library (subjects, classifications, page count)
    if isbn:
        entry['openlibrary'] = fetch_open_library(isbn)
        time.sleep(DELAY_OCLC)
        ok = bool(entry['openlibrary'].get('subjects'))
        print(f"L{'✓' if ok else '✗'}", end=' ', flush=True)
    else:
        entry['openlibrary'] = {}

    # Internet Archive (tertiary)
    if archive_id:
        entry['archive'] = fetch_archive_org(archive_id)
        time.sleep(DELAY_ARCHIVE)
        ok = '_error' not in entry['archive']
        print(f"A{'✓' if ok else '✗'}", end=' ', flush=True)
    else:
        entry['archive'] = {}

    print()
    cache[bid] = entry

    # Save cache every 10 books
    if i % 10 == 0:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False)

# Final cache save
with open(cache_path, 'w', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False)
print(f"\nCache saved: {len(cache)} books → {cache_path}")

# ── Reclassify using API data ─────────────────────────────────────────────────

print("\nEnriching style classifications with API signals...")
enriched = {}
changed = 0

for bid, style_data in book_styles.items():
    entry = cache.get(bid, {})
    api_style, api_conf, api_signals = infer_style_from_api(
        entry.get('google', {}),
        entry.get('oclc', {}),
        entry.get('openlibrary', {}),
        entry.get('archive', {}),
    )

    orig_style = style_data['style']
    orig_conf  = style_data['confidence']

    # Merge: API signal overrides heuristic only when API confidence is higher
    # and the book hasn't been manually verified
    conf_rank = {'high': 3, 'medium': 2, 'low': 1}
    if (not style_data.get('verified')
            and api_style != 'monograph'
            and conf_rank[api_conf] > conf_rank[orig_conf]):
        final_style = api_style
        final_conf  = api_conf
        if final_style != orig_style:
            changed += 1
    else:
        final_style = orig_style
        final_conf  = orig_conf

    # Attach API metadata for review
    oclc  = entry.get('oclc', {})
    google = entry.get('google', {})
    enriched[bid] = {
        **style_data,
        'style':           final_style,
        'confidence':      final_conf,
        'api_style':       api_style,
        'api_confidence':  api_conf,
        'api_signals':     api_signals,
        'ddc':             oclc.get('ddc', ''),
        'lcc':             oclc.get('lcc', ''),
        'holdings':        oclc.get('holdings', 0),
        'google_cats':     google.get('categories', []),
        'google_subtitle': google.get('subtitle', ''),
        'has_editors':     bool(google.get('editors')),
        'page_count':      google.get('page_count', 0),
    }

# Save enriched
enriched_path = str(JSON_DIR / 'book_styles_enriched.json')
with open(enriched_path, 'w', encoding='utf-8') as f:
    json.dump(enriched, f, ensure_ascii=False, indent=2)

# Summary
style_counts = Counter(v['style'] for v in enriched.values())
print(f"\nEnriched classifications ({changed} changed from heuristic):")
for style, n in style_counts.most_common():
    pct = 100 * n / len(enriched)
    bar = '█' * int(pct / 2)
    print(f"  {style:15s} {n:4d}  ({pct:5.1f}%)  {bar}")

# Highlight changed classifications
if changed > 0:
    print(f"\nChanged classifications (heuristic → API):")
    for bid, v in enriched.items():
        orig = book_styles[bid]['style']
        if v['style'] != orig and not book_styles[bid].get('verified'):
            print(f"  [{bid}] {v['title'][:50]:50s}  {orig} → {v['style']}  "
                  f"({v['api_confidence']})  {v['api_signals'][:2]}")

# Holdings stats
holdings_data = [(v['holdings'], v['title']) for v in enriched.values() if v.get('holdings')]
if holdings_data:
    holdings_data.sort(reverse=True)
    print(f"\nTop 10 by library holdings (OCLC):")
    for h, t in holdings_data[:10]:
        print(f"  {h:6,}  {t[:60]}")

print(f"\nSaved {enriched_path}")
print(f"\nNext steps:")
print(f"  1. Review changed classifications above")
print(f"  2. Check high-holdings books for textbook/handbook reclassification")
print(f"  3. Set 'verified': true in book_styles_enriched.json for confirmed entries")
print(f"  4. Re-run 00_classify_book_styles.py --reclassify to apply")
