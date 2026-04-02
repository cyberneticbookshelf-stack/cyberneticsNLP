"""
00_fetch_anu_primo.py
─────────────────────────────────────────────────────────────────────────────
Fetch bibliographic records from the ANU Library Primo catalogue for each
book in the corpus using ISBN lookup. Extracts MARC-derived fields including:
  - Resource type (book, edited_book, reference_entry, proceedings, etc.)
  - Format / physical description
  - Subject headings (LCSH)
  - Publisher / edition information
  - Language

The Primo search API is publicly accessible without authentication for
read-only catalogue queries. ANU's Primo VE instance is at:
  https://anu.primo.exlibrisgroup.com

API endpoint pattern:
  https://anu.primo.exlibrisgroup.com/primaws/rest/pub/pnxs?
    blendFacetsSeparately=false
    &disableCache=false
    &getMore=0
    &inst=61ANU_INST
    &lang=en
    &limit=1
    &newspapersActive=false
    &newspapersSearch=false
    &offset=0
    &pcAvailability=false
    &q=isbn,exact,ISBN_HERE
    &qExclude=
    &qInclude=
    &rtaLinks=true
    &scope=MyInst_and_CI
    &searchInFulltextUserSelection=false
    &skipDelivery=Y
    &tab=Everything
    &vid=61ANU_INST:ANU

The response is JSON with a `docs` array. Each doc has:
  pnx.display.type       — resource type (book, edited_book, etc.)
  pnx.display.subject    — subject headings
  pnx.display.format     — physical description
  pnx.display.publisher  — publisher
  pnx.facets.resourcetype — facet resource type
  pnx.addata.format      — format code

Run this script on a machine with access to ANU Library systems
(on-campus or via VPN). Results are cached to avoid re-fetching.

Usage:
  python3 src/00_fetch_anu_primo.py                  # fetch all
  python3 src/00_fetch_anu_primo.py --limit 20       # test with 20 books
  python3 src/00_fetch_anu_primo.py --stats           # cache stats only
  python3 src/00_fetch_anu_primo.py --reclassify      # re-run inference only

Output:
  json/anu_primo_cache.json          — raw Primo API responses per book
  json/book_styles_primo.json        — styles enriched with Primo signals
  docs/book_styles_primo_review.md   — review table with Primo resource types
"""

# ── Directory layout ──────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')
JSON_DIR = _pl.Path('json')
DOCS_DIR = _pl.Path('docs')
JSON_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)

import csv, json, sys, re, time
import urllib.request, urllib.parse
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

# ANU Primo configuration
PRIMO_BASE = 'https://anu.primo.exlibrisgroup.com/primaws/rest/pub/pnxs'
PRIMO_INST = '61ANU_INST'
PRIMO_VID  = '61ANU_INST:ANU'
PRIMO_TAB  = 'Everything'
PRIMO_SCOPE= 'MyInst_and_CI'
DELAY      = 0.5   # seconds between requests — be polite to the catalogue

# ── Resource type mapping ─────────────────────────────────────────────────────
# Maps Primo resource types to epistemic style votes.
# NOTE: 'book' and 'text' are deliberately mapped to None (neutral) because
# Primo uses them as catch-alls that include both monographs AND edited volumes.
# Only 'edited_book' is authoritative for anthology detection. For plain 'book'
# records we rely on contributor/creator/subject signals to distinguish style.
PRIMO_TYPE_TO_STYLE = {
    'edited_book':      'anthology',    # authoritative — MARC-derived
    'reference_entry':  'handbook',     # authoritative
    'conference_paper': 'proceedings',  # authoritative
    'proceedings':      'proceedings',  # authoritative
    'dissertation':     'report',
    'report':           'report',
    # Generic/ambiguous — neutral, let contributor/subject signals decide
    'book':             None,
    'books':            None,
    'text':             None,
    'map':              None,
    'audio':            None,
    'video':            None,
}

# Subject heading patterns indicating style
LCSH_ANTHOLOGY_RE = re.compile(
    r'\b(?:congresses|conference|symposium|proceedings|collected works|'
    r'essays|addresses|lectures|contributions)\b', re.IGNORECASE)
LCSH_TEXTBOOK_RE = re.compile(
    r'\b(?:textbooks|study and teaching|examinations|problems, exercises)\b',
    re.IGNORECASE)
LCSH_HANDBOOK_RE = re.compile(
    r'\b(?:handbooks, manuals|encyclopedias|dictionaries|bibliography)\b',
    re.IGNORECASE)


def _isbn13_to_10(isbn13):
    """Convert ISBN-13 to ISBN-10 if it starts with 978."""
    digits = re.sub(r'[^0-9]', '', isbn13)
    if len(digits) != 13 or not digits.startswith('978'):
        return None
    core = digits[3:12]
    total = sum((10 - i) * int(d) for i, d in enumerate(core))
    check = (11 - (total % 11)) % 11
    return core + ('X' if check == 10 else str(check))


def _primo_query(isbn_clean, scope):
    """Run a single Primo ISBN query and return parsed result or None."""
    params = {
        'blendFacetsSeparately': 'false',
        'disableCache': 'false',
        'getMore': '0',
        'inst': PRIMO_INST,
        'lang': 'en',
        'limit': '1',
        'newspapersActive': 'false',
        'newspapersSearch': 'false',
        'offset': '0',
        'pcAvailability': 'false',
        'q': f'isbn,exact,{isbn_clean}',
        'qExclude': '',
        'qInclude': '',
        'rtaLinks': 'true',
        'scope': scope,
        'searchInFulltextUserSelection': 'false',
        'skipDelivery': 'Y',
        'tab': PRIMO_TAB,
        'vid': PRIMO_VID,
    }
    url = PRIMO_BASE + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        'User-Agent': 'CyberneticsNLP/0.4 (research; paul.wong@anu.edu.au)',
        'Accept': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode('utf-8', errors='replace'))
    docs = data.get('docs', [])
    if not docs:
        return None
    doc = docs[0]
    pnx     = doc.get('pnx', {})
    display = pnx.get('display', {})
    facets  = pnx.get('facets', {})
    addata  = pnx.get('addata', {})
    return {
        'primo_id':      doc.get('pnxId', ''),
        'resource_type': display.get('type', []),
        'facet_type':    facets.get('resourcetype', []),
        'subject':       display.get('subject', [])[:10],
        'format':        display.get('format', []),
        'publisher':     display.get('publisher', []),
        'language':      display.get('language', []),
        'edition':       display.get('edition', []),
        'description':   display.get('description', [])[:3],
        'contributor':   display.get('contributor', [])[:5],
        'creator':       display.get('creator', [])[:3],
        'addata_format': addata.get('format', []),
    }


def fetch_primo_by_isbn(isbn):
    """
    Fetch Primo record for a book by ISBN.
    Tries in order:
      1. ISBN-13 in MyInst_and_CI scope (ANU + CDI)
      2. ISBN-10 equivalent in MyInst_and_CI scope
      3. ISBN-13 in CDI-only scope (catches ILL-only items)
    Returns the first matching PNX document dict, or not_found status.
    """
    isbn_clean = re.sub(r'[^0-9X]', '', isbn.upper())
    if not isbn_clean:
        return {}

    # Build list of ISBNs to try
    isbns_to_try = [isbn_clean]
    if len(isbn_clean) == 13:
        isbn10 = _isbn13_to_10(isbn_clean)
        if isbn10:
            isbns_to_try.append(isbn10)
    elif len(isbn_clean) == 10:
        # Convert to ISBN-13
        core = '978' + isbn_clean[:9]
        total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(core))
        check = (10 - (total % 10)) % 10
        isbns_to_try.append(core + str(check))

    # Try each ISBN in primary scope, then CDI-only fallback
    scopes = [PRIMO_SCOPE, 'CDI']
    try:
        for scope in scopes:
            for isbn_try in isbns_to_try:
                result = _primo_query(isbn_try, scope)
                if result:
                    result['_status'] = 'found'
                    result['_scope']  = scope
                    result['_isbn_used'] = isbn_try
                    return result
                time.sleep(0.2)  # small delay between variant attempts
        return {'_status': 'not_found'}
    except urllib.error.HTTPError as e:
        return {'_status': 'error', '_error': f'HTTP {e.code}'}
    except Exception as e:
        return {'_status': 'error', '_error': str(e)}


def fetch_primo_by_title_author(title, author):
    """
    Fallback: fetch by title + author when ISBN lookup fails.
    Less precise but catches books without ISBNs.
    """
    if not title:
        return {}
    # Use first 5 words of title for a targeted search
    title_short = ' '.join(title.split()[:5])
    query = f'title,contains,{title_short}'
    if author:
        # First surname only
        surname = author.split(',')[0].strip().split()[-1] if ',' in author else author.split()[-1]
        query += f',AND&q=creator,contains,{surname}'

    params = {
        'blendFacetsSeparately': 'false',
        'disableCache': 'false',
        'getMore': '0',
        'inst': PRIMO_INST,
        'lang': 'en',
        'limit': '1',
        'newspapersActive': 'false',
        'newspapersSearch': 'false',
        'offset': '0',
        'pcAvailability': 'false',
        'q': query,
        'qExclude': '',
        'qInclude': '',
        'rtaLinks': 'true',
        'scope': PRIMO_SCOPE,
        'searchInFulltextUserSelection': 'false',
        'skipDelivery': 'Y',
        'tab': PRIMO_TAB,
        'vid': PRIMO_VID,
    }
    url = PRIMO_BASE + '?' + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'CyberneticsNLP/0.4 (research; paul.wong@anu.edu.au)',
            'Accept': 'application/json',
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode('utf-8', errors='replace'))
        docs = data.get('docs', [])
        if not docs:
            return {'_status': 'not_found_title'}
        doc = docs[0]
        pnx = doc.get('pnx', {})
        display = pnx.get('display', {})
        facets  = pnx.get('facets', {})
        return {
            '_status':       'found_by_title',
            'primo_id':      doc.get('pnxId', ''),
            'resource_type': display.get('type', []),
            'facet_type':    facets.get('resourcetype', []),
            'subject':       display.get('subject', [])[:10],
            'format':        display.get('format', []),
            'publisher':     display.get('publisher', []),
            'contributor':   display.get('contributor', [])[:5],
            'creator':       display.get('creator', [])[:3],
        }
    except Exception as e:
        return {'_status': 'error', '_error': str(e)}


def infer_style_from_primo(primo):
    """
    Infer epistemic style from Primo record fields.
    Returns (style, confidence, signals).
    """
    if not primo or primo.get('_status') not in ('found', 'found_by_title'):
        return 'monograph', 'low', ['primo:no_record']

    signals = []
    votes   = Counter()

    # Database/platform names that appear as contributors in ebook records —
    # these are delivery mechanism artefacts, not real contributors
    PLATFORM_CONTRIBUTORS = {
        'proquest', 'ebsco', 'ebrary', 'dawson', 'overdrive',
        'safari', "o'reilly", 'ieee', 'acm', 'springer',
        'elsevier', 'taylor', 'wiley', 'jstor',
    }

    def _is_platform(name):
        n = name.lower()
        return any(p in n for p in PLATFORM_CONTRIBUTORS)

    # ── Resource type — most authoritative signal ─────────────────────────────
    # Suppress 'other' and 'web_resource' — these reflect delivery format
    # not bibliographic type. Use subject/contributor signals instead.
    SUPPRESS_TYPES = {'other', 'web_resource', 'online_resource'}
    for rt_field in ['resource_type', 'facet_type', 'addata_format']:
        for rt in primo.get(rt_field, []):
            rt_lower = rt.lower().strip()
            if rt_lower in SUPPRESS_TYPES:
                signals.append(f'primo:type_{rt_lower}_suppressed')
                continue
            mapped = PRIMO_TYPE_TO_STYLE.get(rt_lower)
            if mapped:
                signals.append(f'primo:type_{rt_lower}→{mapped}')
                votes[mapped] += 4   # high weight — authoritative MARC-derived
            elif rt_lower:
                signals.append(f'primo:type_{rt_lower}')

    # ── Contributors vs creators ──────────────────────────────────────────────
    # Primo puts editors in 'contributor' field, authors in 'creator'.
    # Filter out platform/database names before reasoning about authorship.
    contributors = [c for c in primo.get('contributor', [])
                    if not _is_platform(c)]
    creators     = primo.get('creator', [])

    if contributors and not creators:
        # Has real contributors but no primary creator → likely anthology
        signals.append('primo:contributors_no_creator')
        votes['anthology'] += 3
    elif contributors and creators:
        # Both present — check if contributors are editors
        if any(re.search(r'\bed\.|\beditor\b|\beds\b', c, re.IGNORECASE)
               for c in contributors):
            signals.append('primo:editor_in_contributor')
            votes['anthology'] += 3

    # ── Subject headings ─────────────────────────────────────────────────────
    all_subjects = ' '.join(primo.get('subject', []))
    if LCSH_ANTHOLOGY_RE.search(all_subjects):
        signals.append('primo:lcsh_anthology')
        votes['anthology'] += 2
    if LCSH_TEXTBOOK_RE.search(all_subjects):
        signals.append('primo:lcsh_textbook')
        votes['textbook'] += 2
    if LCSH_HANDBOOK_RE.search(all_subjects):
        signals.append('primo:lcsh_handbook')
        votes['handbook'] += 2

    # ── Format field ─────────────────────────────────────────────────────────
    format_str = ' '.join(primo.get('format', []))
    if re.search(r'\bvolumes?\b', format_str, re.IGNORECASE):
        signals.append('primo:multi_volume')
        votes['anthology'] += 1

    if not votes:
        return 'monograph', 'low', signals

    best, score = votes.most_common(1)[0]
    total = sum(votes.values())
    dom   = score / total if total else 0
    conf  = 'high' if score >= 4 and dom >= 0.6 else 'medium' if score >= 2 else 'low'
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
    # Prefer enriched styles if available
    enriched_path = str(JSON_DIR / 'book_styles_enriched.json')
    book_styles = json.load(open(enriched_path))
    print(f"  {len(book_styles)} books in book_styles_enriched.json")
except FileNotFoundError:
    try:
        book_styles = json.load(open(str(JSON_DIR / 'book_styles.json')))
        print(f"  {len(book_styles)} books in book_styles.json")
    except FileNotFoundError:
        print("  ERROR: book_styles.json not found — run 00_classify_book_styles.py first")
        sys.exit(1)

# Load or init Primo cache
cache_path = str(JSON_DIR / 'anu_primo_cache.json')
try:
    cache = json.load(open(cache_path))
    print(f"  Primo cache: {len(cache)} books already fetched")
except (FileNotFoundError, json.JSONDecodeError):
    cache = {}
    print("  Primo cache: empty — fetching all")

if STATS_ONLY:
    found     = sum(1 for v in cache.values() if v.get('_status') == 'found')
    not_found = sum(1 for v in cache.values() if v.get('_status') == 'not_found')
    errors    = sum(1 for v in cache.values() if v.get('_status') == 'error')
    fallback  = sum(1 for v in cache.values() if v.get('_status') == 'found_by_title')
    print(f"\nPrimo cache stats ({len(cache)} books):")
    print(f"  Found by ISBN:   {found}")
    print(f"  Found by title:  {fallback}")
    print(f"  Not found:       {not_found}")
    print(f"  Errors:          {errors}")
    # Resource type distribution
    all_types = []
    for v in cache.values():
        all_types.extend(v.get('resource_type', []))
    print(f"\nResource type distribution:")
    for rt, n in Counter(all_types).most_common(15):
        print(f"  {n:4d}  {rt}")
    sys.exit(0)

if RECLASSIFY:
    print("\nReclassifying from existing Primo cache (no API calls)...")
else:
    # ── Fetch loop ────────────────────────────────────────────────────────────
    to_fetch = [bid for bid in meta_rows if bid not in cache]
    if LIMIT:
        to_fetch = to_fetch[:LIMIT]

    print(f"\nFetching Primo records for {len(to_fetch)} books "
          f"({len(cache)} already cached)...")

    for i, bid in enumerate(to_fetch, 1):
        row    = meta_rows[bid]
        isbn   = row.get('isbn', '').strip()
        title  = row.get('title', '')
        author = row.get('author_sort', '')

        print(f"  [{i:3d}/{len(to_fetch)}] [{bid}] {title[:50]:50s}", end=' ', flush=True)

        if isbn:
            result = fetch_primo_by_isbn(isbn)
            time.sleep(DELAY)
        else:
            result = {'_status': 'no_isbn'}

        # Fallback to title search if ISBN not found
        if result.get('_status') in ('not_found', 'no_isbn', 'error'):
            result2 = fetch_primo_by_title_author(title, author)
            time.sleep(DELAY)
            if result2.get('_status') == 'found_by_title':
                result = result2
                print(f"T✓", end=' ', flush=True)
            else:
                print(f"✗ ({result.get('_status', '?')})", end=' ', flush=True)
        else:
            status_char = '✓' if result.get('_status') == 'found' else '?'
            print(f"{status_char} {result.get('resource_type', ['?'])[0][:20] if result.get('resource_type') else ''}", end=' ', flush=True)

        print()
        cache[bid] = result

        # Save every 20 books
        if i % 20 == 0:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False)

    # Final save
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)
    print(f"\nPrimo cache saved: {len(cache)} books → {cache_path}")

# ── Enrich styles with Primo signals ─────────────────────────────────────────
print("\nEnriching style classifications with Primo signals...")
enriched = {}
changed  = 0
conf_rank = {'high': 3, 'medium': 2, 'low': 1}

for bid, style_data in book_styles.items():
    primo = cache.get(bid, {})
    primo_style, primo_conf, primo_signals = infer_style_from_primo(primo)

    orig_style = style_data.get('style', 'monograph')
    orig_conf  = style_data.get('confidence', 'low')

    # Primo resource type overrides heuristic when confidence is higher
    # and book hasn't been manually verified
    if (not style_data.get('verified')
            and primo_style != 'monograph'
            and conf_rank[primo_conf] >= conf_rank[orig_conf]):
        final_style = primo_style
        final_conf  = primo_conf
        if final_style != orig_style:
            changed += 1
    else:
        final_style = orig_style
        final_conf  = orig_conf

    enriched[bid] = {
        **style_data,
        'style':           final_style,
        'confidence':      final_conf,
        'primo_style':     primo_style,
        'primo_confidence':primo_conf,
        'primo_signals':   primo_signals,
        'primo_type':      primo.get('resource_type', []),
        'primo_subjects':  primo.get('subject', [])[:5],
        'primo_status':    primo.get('_status', 'not_fetched'),
    }

# Save
out_path = str(JSON_DIR / 'book_styles_primo.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(enriched, f, ensure_ascii=False, indent=2)

# Summary
style_counts = Counter(v['style'] for v in enriched.values())
print(f"\nEnriched classifications ({changed} changed with Primo data):")
for style, n in style_counts.most_common():
    pct = 100 * n / len(enriched)
    bar = '█' * int(pct / 2)
    print(f"  {style:15s} {n:4d}  ({pct:5.1f}%)  {bar}")

if changed > 0:
    print(f"\nChanged classifications (previous → Primo-enriched):")
    for bid, v in enriched.items():
        prev = book_styles[bid].get('style', 'monograph')
        if v['style'] != prev and not book_styles[bid].get('verified'):
            rt = v.get('primo_type', ['?'])[0] if v.get('primo_type') else '?'
            print(f"  [{bid}] {v['title'][:50]:50s}  {prev} → {v['style']}"
                  f"  [Primo:{rt}]  {v['primo_signals'][:2]}")

# Markdown review table
md_path = str(DOCS_DIR / 'book_styles_primo_review.md')
lines = [
    f"# Book Style Classification — Primo Enriched",
    f"",
    f"**Date:** {date.today()}  ",
    f"**Corpus:** {len(enriched)} books  ",
    f"**Primo instance:** {PRIMO_VID}  ",
    f"",
    f"## Summary",
    f"",
    f"| Style | Count | % |",
    f"|---|---|---|",
]
for style, n in style_counts.most_common():
    lines.append(f"| {style} | {n} | {100*n/len(enriched):.1f}% |")

lines += [
    f"",
    f"## Changed classifications",
    f"",
    f"| ID | Title | Previous | Primo | Primo Type | Signals |",
    f"|---|---|---|---|---|---|",
]
for bid, v in enriched.items():
    prev = book_styles.get(bid, {}).get('style', 'monograph')
    if v['style'] != prev:
        rt = v.get('primo_type', [''])[0] if v.get('primo_type') else ''
        lines.append(
            f"| {bid} | {v['title'][:45]} | {prev} | **{v['style']}** "
            f"| {rt} | {', '.join(v['primo_signals'][:2])} |"
        )

lines += [
    f"",
    f"## Full classification table",
    f"",
    f"| ID | Title | Year | Style | Conf | Primo Type | Primo Status |",
    f"|---|---|---|---|---|---|---|",
]
for bid, v in sorted(enriched.items(), key=lambda x: x[1].get('pubdate', '')):
    rt = v.get('primo_type', [''])[0] if v.get('primo_type') else ''
    lines.append(
        f"| {bid} | {v['title'][:45]} | {v.get('pubdate','')} "
        f"| **{v['style']}** | {v['confidence']} | {rt} | {v['primo_status']} |"
    )

with open(md_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f"\nSaved {out_path}")
print(f"Saved {md_path}")
print(f"\nNext steps:")
print(f"  1. Review docs/book_styles_primo_review.md")
print(f"  2. Verify changed classifications and set 'verified': true")
print(f"  3. Run --stats to check resource type distribution from Primo")
