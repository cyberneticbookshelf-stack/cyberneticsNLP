"""
00_classify_book_styles.py
─────────────────────────────────────────────────────────────────────────────
Classify books in the corpus by epistemic style:
  monograph       — single-author sustained argument
  anthology       — edited collection of independent chapters
  textbook        — pedagogical survey of established knowledge
  handbook        — comprehensive reference work, often multi-contributor
  reader          — curated reprints of canonical texts
  popular         — trade/popular science, non-specialist register
  history_bio     — biography or intellectual history
  proceedings     — conference proceedings bound as a book
  report          — technical report, working paper, or grey literature
  unknown         — insufficient signal to classify

Classification uses heuristic signals from title keywords, author/editor
fields, publisher, description, and tags — all available in the enriched
csv/books_metadata_full.csv (exported from Calibre metadata.db).

Input:  csv/books_metadata_full.csv  (tab-separated, from 00_export_calibre.py)
        json/books_clean.json        (for books not in metadata CSV)
Output: json/book_styles.json            — machine-readable classification per book
        docs/reference/book_styles.md    — human-readable review table

Usage:
  python3 src/00_classify_book_styles.py
  python3 src/00_classify_book_styles.py --stats      # summary statistics only
  python3 src/00_classify_book_styles.py --uncertain  # show low-confidence only

Methodology note:
  Book style is an epistemic subtype, not just a format. Each style has
  distinct affordances for NLP analysis:
    - Monographs: coherent vocabulary signal, valid body-text sampling
    - Anthologies: mixed vocabulary, editor introduction is key signal
    - Textbooks: retrospective/consensus signal, temporal lag
    - Handbooks: community concept map, aggregated index
    - Popular: distinct register, thin or absent index
    - History/bio: proper-noun heavy, narrative rather than argumentative
  See docs/memos/memo_media_aware_nlp_epistemic_affordances.md §10 for full discussion.

  The inclusion_stratum field from books_metadata_full.csv is carried through
  directly — it encodes the precision-recall trade-off in corpus construction:
    title_corroborated — cybernetic(s) in title + other fields (highest precision)
    title_only         — cybernetic(s) in title only
    curated_keyword    — theme-tagged + cybernetic(s) in description/tags
    curated_pure       — theme-tagged, no cybernetic(s) anywhere (expert judgement)
    metadata_search    — found via search, not theme-tagged
  See docs/memos/corpus_construction.md §3.3 for full discussion.
"""

# ── Directory layout ──────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')
JSON_DIR = _pl.Path('json')
DOCS_REF_DIR = _pl.Path('docs/reference')
JSON_DIR.mkdir(exist_ok=True)
DOCS_REF_DIR.mkdir(parents=True, exist_ok=True)

import json, re, csv, sys
from collections import Counter
from datetime import date

STATS_ONLY = '--stats' in sys.argv
UNCERTAIN  = '--uncertain' in sys.argv

# ── Classification rules ──────────────────────────────────────────────────────
# Each rule is (pattern, style, confidence, signal_label)
# Applied to lowercased title. First matching rule wins for primary style;
# all matching rules are recorded as signals.

TITLE_RULES = [

    # ── Handbook / reference ──────────────────────────────────────────────────
    (r'\bhandbook\b',                    'handbook',   'high',   'title:handbook'),
    (r'\bencyclop(?:a|e)dia\b',          'handbook',   'high',   'title:encyclopedia'),
    (r'\bcompendium\b',                  'handbook',   'high',   'title:compendium'),
    (r'\bdictionary\s+of\b',             'handbook',   'high',   'title:dictionary_of'),
    (r'\breference\s+(?:guide|manual)\b','handbook',   'medium', 'title:reference'),

    # ── Anthology / edited volume ─────────────────────────────────────────────
    (r'\bessays\s+(?:on|in|about)\b',    'anthology',  'high',   'title:essays_on'),
    (r'\bcollected\s+(?:works|papers|essays|writings)\b',
                                         'anthology',  'high',   'title:collected'),
    (r'\breader\b',                      'reader',     'high',   'title:reader'),
    (r'\breadings\s+in\b',               'reader',     'high',   'title:readings_in'),
    (r'\bselected\s+(?:papers|writings|readings)\b',
                                         'reader',     'high',   'title:selected'),
    (r'\banthology\b',                   'anthology',  'high',   'title:anthology'),
    (r'\bvolume\s+\d+\b',               'anthology',  'medium', 'title:volume_N'),
    (r'\bvol\.\s*\d+\b',                'anthology',  'medium', 'title:vol_N'),
    (r'\bpart\s+[ivx]+\b',              'anthology',  'low',    'title:part_roman'),

    # ── Textbook ──────────────────────────────────────────────────────────────
    # NOTE: 'introduction to' and 'principles of' are deliberately kept at
    # lower confidence — cybernetics has many canonical monographs with these
    # phrases (Ashby's Introduction to Cybernetics, Varela's Principles of
    # Biological Autonomy, Forrester's Principles of Systems). These signals
    # only classify as textbook when combined with other corroborating signals.
    (r'\bintroduction\s+to\b',           'textbook',   'medium', 'title:introduction_to'),
    (r'\bintroductory\b',                'textbook',   'high',   'title:introductory'),
    (r'\bfundamentals\s+of\b',           'textbook',   'high',   'title:fundamentals_of'),
    (r'\bprinciples\s+of\b',             'textbook',   'low',    'title:principles_of'),
    (r'\bprimer\s+(?:on|in|of)\b',       'textbook',   'high',   'title:primer'),
    (r'\btextbook\b',                    'textbook',   'high',   'title:textbook'),
    (r'\bcourse\b',                      'textbook',   'low',    'title:course'),
    (r'\bfor\s+(?:students|beginners|dummies)\b',
                                         'textbook',   'high',   'title:for_students'),
    (r'\bworkbook\b',                    'textbook',   'high',   'title:workbook'),
    (r'\blecture\s+notes\b',             'textbook',   'high',   'title:lecture_notes'),

    # ── Proceedings ───────────────────────────────────────────────────────────
    (r'\bproceedings\b',                 'proceedings','high',   'title:proceedings'),
    (r'\bconference\s+on\b',             'proceedings','high',   'title:conference_on'),
    (r'\bsymposium\s+on\b',              'proceedings','high',   'title:symposium_on'),
    (r'\bworkshop\s+on\b',               'proceedings','medium', 'title:workshop_on'),
    (r'\bannual\s+(?:meeting|conference)\b',
                                         'proceedings','high',   'title:annual_meeting'),

    # ── Popular / trade ───────────────────────────────────────────────────────
    (r'\bfor\s+(?:everyone|the\s+rest\s+of\s+us|the\s+layman)\b',
                                         'popular',    'high',   'title:for_everyone'),
    (r'\byou\s+(?:can|need|should)\b',   'popular',    'medium', 'title:you_can'),
    (r'\bhow\s+to\b',                    'popular',    'medium', 'title:how_to'),
    (r'\bself[- ]help\b',                'popular',    'high',   'title:self_help'),
    (r'\bpsycho-cybernetics\b',          'popular',    'high',   'title:psycho_cyber'),
    (r'\bsuccess\b',                     'popular',    'low',    'title:success'),
    (r'\brich\s+(?:new\s+)?life\b',      'popular',    'high',   'title:rich_life'),

    # ── Biography / history ───────────────────────────────────────────────────
    (r'\bbiograph(?:y|ies)\b',           'history_bio','high',   'title:biography'),
    (r'\bmemoir\b',                      'history_bio','high',   'title:memoir'),
    (r'\bhistory\s+of\b',                'history_bio','high',   'title:history_of'),
    (r'\blife\s+of\b',                   'history_bio','high',   'title:life_of'),
    (r'\bintellectual\s+(?:history|biography|life)\b',
                                         'history_bio','high',   'title:intellectual_hist'),
    (r'\bportrait\s+of\b',               'history_bio','medium', 'title:portrait_of'),
    (r'\blegacy\s+of\b',                 'history_bio','medium', 'title:legacy_of'),

    # ── Report / grey literature ──────────────────────────────────────────────
    (r'\btech(?:nical)?\s+report\b',     'report',     'high',   'title:tech_report'),
    (r'\bworking\s+paper\b',             'report',     'high',   'title:working_paper'),
    (r'\bbibliograph(?:y|ies)\b',        'report',     'high',   'title:bibliography'),
    (r'\bannotated\s+list\b',            'report',     'high',   'title:annotated_list'),
]

# Author field signals — 'ed.' or 'eds.' strongly suggests edited volume
EDITOR_RE = re.compile(
    r'\b(?:ed\.|eds\.|edited\s+by|editor|editors)\b', re.IGNORECASE)

SERIES_RE = re.compile(
    r'volume\s+\d+|vol\.\s*\d+|\bpart\s+(?:i{1,3}v?|vi*|\d+)\b',
    re.IGNORECASE)

# Publisher signals — mapped to style with confidence
PUBLISHER_RULES = [
    # Textbook publishers — restricted to publishers that almost exclusively
    # publish textbooks. Wiley removed — too broad, publishes many monographs
    # in cybernetics/systems tradition (Beer, Watzlawick, Miller etc.)
    (r'\b(?:pearson|cengage|mcgraw.hill|norton|brooks.cole)\b',
     'textbook', 'medium', 'publisher:textbook_house'),
    # Popular / trade
    (r'\b(?:penguin|random\s+house|harper|simon\s+&\s+schuster|basic\s+books|'
     r'picador|vintage|anchor|bantam|crown|doubleday)\b',
     'popular', 'medium', 'publisher:trade_house'),
    # Academic proceedings / handbooks (Springer series)
    (r'\bspringer\b', 'monograph', 'low', 'publisher:springer'),
    (r'\blecture\s+notes\b', 'textbook', 'high', 'publisher:lecture_notes_series'),
]

# Description signals — short phrases that strongly indicate style
DESCRIPTION_RULES = [
    (r'\bedited\s+(?:by|volume)\b',      'anthology',  'high',   'desc:edited_by'),
    (r'\bcontribut(?:or|ed|ing)\b',      'anthology',  'medium', 'desc:contributors'),
    (r'\bintroductory\s+(?:text|course)\b', 'textbook','high',   'desc:intro_text'),
    (r'\bself.help\b',                   'popular',    'high',   'desc:self_help'),
    (r'\bbiograph(?:y|ical)\b',          'history_bio','high',   'desc:biography'),
    (r'\bmemoir\b',                      'history_bio','high',   'desc:memoir'),
    (r'\bproceedings\b',                 'proceedings','high',   'desc:proceedings'),
]


def classify_book(bid, title, author, pubdate, publisher='', description='', tags=''):
    """
    Return (style, confidence, signals) for a book.
    Now uses title, author, publisher, description, and tags.
    """
    t    = title.lower()
    pub  = publisher.lower()
    desc = (description or '').lower()
    signals = []
    style_votes = Counter()

    # ── Title rules ───────────────────────────────────────────────────────────
    for pattern, style, conf, label in TITLE_RULES:
        if re.search(pattern, t):
            signals.append(label)
            weight = {'high': 3, 'medium': 2, 'low': 1}[conf]
            style_votes[style] += weight

    # ── Author/editor field ───────────────────────────────────────────────────
    if EDITOR_RE.search(author):
        signals.append('author:editor_marker')
        style_votes['anthology'] += 3

    # ── Series / volume indicator ─────────────────────────────────────────────
    if SERIES_RE.search(title):
        signals.append('title:series_volume')
        style_votes['anthology'] += 1

    # ── Publisher rules ───────────────────────────────────────────────────────
    for pattern, style, conf, label in PUBLISHER_RULES:
        if re.search(pattern, pub):
            signals.append(label)
            weight = {'high': 3, 'medium': 2, 'low': 1}[conf]
            style_votes[style] += weight

    # ── Description rules ─────────────────────────────────────────────────────
    for pattern, style, conf, label in DESCRIPTION_RULES:
        if re.search(pattern, desc):
            signals.append(label)
            weight = {'high': 3, 'medium': 2, 'low': 1}[conf]
            style_votes[style] += weight

    # ── Tags: 'Edited' or 'Proceedings' tags ─────────────────────────────────
    tags_lower = (tags or '').lower()
    if re.search(r'\bproceedings\b', tags_lower):
        signals.append('tags:proceedings')
        style_votes['proceedings'] += 3
    if re.search(r'\bedited\b', tags_lower):
        signals.append('tags:edited')
        style_votes['anthology'] += 2

    # ── Determine style and confidence ────────────────────────────────────────
    if not style_votes:
        return 'monograph', 'low', ['default:no_signals']

    best_style, best_score = style_votes.most_common(1)[0]
    total_score = sum(style_votes.values())
    dominance = best_score / total_score if total_score > 0 else 0

    if best_score >= 3 and dominance >= 0.7:
        confidence = 'high'
    elif best_score >= 2 or dominance >= 0.5:
        confidence = 'medium'
    else:
        confidence = 'low'

    return best_style, confidence, signals


# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading metadata...")

# Primary source: books_metadata_full.csv (enriched Calibre export)
meta = {}
meta_path = str(CSV_DIR / 'books_metadata_full.csv')
try:
    with open(meta_path, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            bid = str(row['id']).strip()
            meta[bid] = row
    print(f"  books_metadata_full.csv: {len(meta)} books")
except FileNotFoundError:
    print(f"  WARNING: books_metadata_full.csv not found in csv/")
    print(f"  Run: python3 src/00_export_calibre.py")
    print(f"  Falling back to books_clean.json only (reduced metadata)")

# Fallback: books_clean.json for any books not in metadata CSV
books_clean = {}
try:
    books_clean = json.load(open(str(JSON_DIR / 'books_clean.json')))
    print(f"  books_clean.json: {len(books_clean)} books (fallback)")
except FileNotFoundError:
    pass

# Primo-enriched styles — most authoritative source if available.
# Carries through verified flags, Primo resource types, and LCSH signals.
# Preference order: book_styles_primo.json > book_styles_enriched.json > heuristic
primo_styles = {}
for fname in ['book_styles_primo.json', 'book_styles_enriched.json']:
    try:
        primo_styles = json.load(open(str(JSON_DIR / fname)))
        print(f"  {fname}: {len(primo_styles)} books loaded as override source")
        break
    except FileNotFoundError:
        pass
if not primo_styles:
    print("  No enriched styles found — using heuristic classification only")

# Merge: metadata CSV is authoritative; books_clean fills gaps
all_ids = set(meta.keys()) | set(books_clean.keys())
print(f"  Total unique book IDs: {len(all_ids)}")

# ── Classify ──────────────────────────────────────────────────────────────────
print("\nClassifying books...")
results = {}

for bid in sorted(all_ids, key=lambda x: int(x) if x.isdigit() else 0):
    # Prefer metadata CSV fields
    if bid in meta:
        row = meta[bid]
        title       = row.get('title', '')
        author      = row.get('author_sort', '')
        pubdate     = row.get('pubdate', '')
        publisher   = row.get('publisher', '')
        description = row.get('description', '')
        tags        = row.get('tags', '')
        inclusion_stratum = row.get('inclusion_stratum', '')
        available_at      = row.get('available_at', '')
        archive_id        = row.get('archive_id', '')
        google_id         = row.get('google_id', '')
        isbn              = row.get('isbn', '')
    else:
        # Fallback to books_clean.json
        data = books_clean.get(bid, {})
        title       = data.get('title', '')
        author      = data.get('author', '')
        pubdate     = data.get('pubdate', '')
        publisher   = ''
        description = ''
        tags        = ''
        inclusion_stratum = ''
        available_at = ''
        archive_id   = ''
        google_id    = ''
        isbn         = ''

    style, confidence, signals = classify_book(
        bid, title, author, pubdate, publisher, description, tags)

    # ── Primo/API override ────────────────────────────────────────────────────
    # If enriched styles are available, carry through their classification,
    # API signals, and verified status. Heuristic signals are preserved for
    # audit trail but the enriched style takes precedence unless manually
    # verified to a different value.
    primo_data = primo_styles.get(bid, {})
    if primo_data:
        # Use enriched style unless heuristic is manually verified differently
        if primo_data.get('verified'):
            style      = primo_data['style']
            confidence = primo_data['confidence']
            signals    = signals + ['override:verified_manual']
        elif primo_data.get('style') and primo_data.get('confidence') in ('high', 'medium'):
            # API-enriched with reasonable confidence — prefer over heuristic
            conf_rank = {'high': 3, 'medium': 2, 'low': 1}
            if conf_rank.get(primo_data['confidence'], 0) >= conf_rank.get(confidence, 0):
                style      = primo_data['style']
                confidence = primo_data['confidence']
                signals    = signals + primo_data.get('primo_signals', []) + \
                             primo_data.get('api_signals', [])

    results[bid] = {
        'book_id':           bid,
        'title':             title,
        'author':            author,
        'pubdate':           pubdate,
        'publisher':         publisher,
        'style':             style,
        'confidence':        confidence,
        'signals':           signals,
        'inclusion_stratum': inclusion_stratum,
        'available_at':      available_at,
        'archive_id':        archive_id,
        'google_id':         google_id,
        'isbn':              isbn,
        'notes':             primo_data.get('notes', ''),
        'verified':          primo_data.get('verified', False),
        # Carry through Primo/API metadata for downstream use
        'primo_type':        primo_data.get('primo_type', []),
        'primo_status':      primo_data.get('primo_status', ''),
        'ddc':               primo_data.get('ddc', ''),
        'lcc':               primo_data.get('lcc', ''),
        'holdings':          primo_data.get('holdings', 0),
    }

# ── Statistics ────────────────────────────────────────────────────────────────
style_counts = Counter(v['style'] for v in results.values())
conf_counts  = Counter(v['confidence'] for v in results.values())

print(f"\n{'─'*60}")
print(f"CLASSIFICATION SUMMARY  n={len(results)}  date={date.today()}")
print(f"{'─'*60}")
print(f"\nBy style:")
for style, count in style_counts.most_common():
    pct = 100 * count / len(results)
    bar = '█' * int(pct / 2)
    print(f"  {style:15s} {count:4d}  ({pct:5.1f}%)  {bar}")

print(f"\nBy confidence:")
for conf in ['high', 'medium', 'low']:
    count = conf_counts[conf]
    pct = 100 * count / len(results)
    print(f"  {conf:8s} {count:4d}  ({pct:5.1f}%)")

# Uncertain = low confidence non-monograph, or any unknown
uncertain = [v for v in results.values()
             if v['confidence'] == 'low' and v['style'] != 'monograph'
             or v['style'] == 'unknown']
print(f"\nUncertain classifications: {len(uncertain)}")

if STATS_ONLY:
    sys.exit(0)

# ── Show uncertain if requested ───────────────────────────────────────────────
if UNCERTAIN:
    print(f"\n{'─'*60}")
    print(f"LOW-CONFIDENCE CLASSIFICATIONS ({len(uncertain)} books)")
    print(f"{'─'*60}")
    for v in sorted(uncertain, key=lambda x: x['title']):
        print(f"  [{v['book_id']}] {v['title'][:55]:55s} {v['pubdate']}")
        print(f"         → {v['style']} ({v['confidence']})  signals: {v['signals']}")

# ── Save JSON ─────────────────────────────────────────────────────────────────
out_path = str(JSON_DIR / 'book_styles.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\nSaved {out_path}")

# ── Save Markdown review table ────────────────────────────────────────────────
md_path = str(DOCS_REF_DIR / 'book_styles.md')
lines = [
    f"# Book Style Classification",
    f"",
    f"**Date:** {date.today()}  ",
    f"**Corpus:** {len(results)} books  ",
    f"**Input:** csv/books_metadata_full.csv  ",
    f"**Method:** Heuristic signal matching — title, author, publisher, description, tags  ",
    f"",
    f"## Summary",
    f"",
    f"| Style | Count | % |",
    f"|---|---|---|",
]
for style, count in style_counts.most_common():
    lines.append(f"| {style} | {count} | {100*count/len(results):.1f}% |")

# Inclusion stratum summary
strat_counts = Counter(v['inclusion_stratum'] for v in results.values() if v['inclusion_stratum'])
if strat_counts:
    lines += [f"", f"## Inclusion Strata", f"", f"| Stratum | Count | % |", f"|---|---|---|"]
    for s, n in strat_counts.most_common():
        lines.append(f"| {s} | {n} | {100*n/len(results):.1f}% |")

lines += [
    f"",
    f"## Epistemic Affordances by Style",
    f"",
    f"| Style | Sampling validity | Index type | LDA signal | Temporal bias |",
    f"|---|---|---|---|---|",
    f"| Monograph | High | Author's concept map | Clean | None |",
    f"| Anthology | Low | Union of contributors | Mixed | Variable |",
    f"| Textbook | Medium | Comprehensive, conservative | Smoothed | Retrospective |",
    f"| Handbook | Low | Community concept map | Mixed | Retrospective |",
    f"| Reader | Low–Medium | Curated canon | Historically weighted | Retrospective |",
    f"| Popular | High | Thin or absent | Distinct register | None |",
    f"| History/Bio | High | Proper-noun heavy | Historiographic | None |",
    f"| Proceedings | Very low | Often absent | Highly mixed | None |",
    f"| Report | High | Variable | Variable | None |",
    f"",
    f"## Classification Review Table",
    f"",
    f"Review and correct the `style` column. Set `verified=true` in book_styles.json after checking.",
    f"",
    f"| ID | Title | Year | Publisher | Style | Conf | Stratum | Signals |",
    f"|---|---|---|---|---|---|---|---|",
]

for style, _ in style_counts.most_common():
    style_books = [v for v in results.values() if v['style'] == style]
    style_books.sort(key=lambda x: x['pubdate'])
    for v in style_books:
        sigs = ', '.join(v['signals'][:3])
        pub  = v.get('publisher', '')[:20]
        strat = v.get('inclusion_stratum', '')
        lines.append(
            f"| {v['book_id']} | {v['title'][:45]} | {v['pubdate']} "
            f"| {pub} | **{v['style']}** | {v['confidence']} | {strat} | {sigs} |"
        )

with open(md_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print(f"Saved {md_path}")

print(f"\nNext steps:")
print(f"  1. Review docs/reference/book_styles.md and correct misclassifications")
print(f"  2. Update 'style' and set 'verified': true in json/book_styles.json")
print(f"  3. Use style as a covariate in 03_nlp_pipeline.py (--style-aware flag, TBD)")
print(f"  4. Run 09c_validate_topics.py to see style distribution per topic")
