"""


09b_build_index_analysis.py
────────────────────────────────────────────────────────────────────────────
Builds the aggregated index analysis files needed by 10_build_index_report.py,
12_index_grounding.py, and 08_build_timeseries.py (Chart 7).

Must run AFTER 09_extract_index.py and 03_nlp_pipeline.py.

Reads:
  index_terms.json     — per-book term lists       (written by 09)
  index_vocab.json     — raw term vocabulary        (written by 09)
  nlp_results.json     — pub_years, dom_topics, titles (written by 03)
  books_clean.json     — clean text for snippets    (written by 02/stream)

Writes:
  index_analysis.json  — aggregated vocab with topic/year distributions
  index_snippets.json  — per-term context sentences for the term explorer
"""

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_metadata_full.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


import json, re, math
from collections import defaultdict


# ── Verify working directory has required data files ────────────────────────
import os as _os
if not _os.path.exists(str(JSON_DIR / 'books_clean.json')):
    print('ERROR: books_clean.json not found in current directory.')
    print(f'Run this script from your project root, not from {_os.getcwd()}')
    print('Example: cd /path/to/project && python3 src/generate_summaries_api.py')
    import sys as _sys; _sys.exit(1)

# ── Vocab canonicalisation helpers ───────────────────────────────────────────
import unicodedata as _ud
from collections import defaultdict as _dd2

def _accent_key(s):
    return ''.join(c for c in _ud.normalize('NFD', s) if _ud.category(c) != 'Mn')

def _is_clean_name(term):
    if ',' not in term: return False
    first = term.split(',', 1)[1].strip()
    if re.search(r'\d', first): return False
    if re.search(r'[;:]', first): return False
    if len(first) > 30: return False
    return True

def _firstname_fullwords(term):
    first = term.split(',', 1)[1].strip() if ',' in term else ''
    return sum(1 for w in first.split()
               if len(w) > 2 and not w.endswith('.') and w.isalpha())

def _is_initial_of(vfirst, cfirst):
    vw, cw = vfirst.split(), cfirst.split()
    if len(vw) > len(cw): return False
    return all(v == c or (len(v.rstrip('.')) == 1 and v.rstrip('.') == c[0])
               for v, c in zip(vw, cw))

def build_person_merge_rules(IV):
    """Return {variant_lower: canonical_lower} for initialised person names."""
    PERSON_PAT = re.compile(r'^[A-Z][\w\-]+(?:\s+[A-Z][\w\-]+)*,\s', re.UNICODE)
    groups = _dd2(list)
    for tl, v in IV.items():
        nb = v.get('n_books', v.get('count', 0))
        if nb < 2: continue
        if PERSON_PAT.match(v['term']):
            groups[tl.split(',')[0].strip()].append((tl, v['term'], nb))
    merge = {}
    for surname, entries in groups.items():
        clean = [(tl, t, nb) for tl, t, nb in entries if _is_clean_name(t)]
        if len(clean) <= 1: continue
        max_nb = max(nb for _, _, nb in clean)
        def _score(e):
            _, t, nb = e
            fw = _firstname_fullwords(t)
            return (fw if (nb / max_nb) >= 0.08 else max(fw-1, 0), nb)
        clean.sort(key=lambda x: (-_score(x)[0], -_score(x)[1]))
        ctl, cterm, _ = clean[0]
        cfirst = cterm.split(',', 1)[1].strip()
        for tl, term, nb in clean[1:]:
            if tl == ctl: continue
            if _is_initial_of(term.split(',', 1)[1].strip(), cfirst):
                merge[tl] = ctl
    return merge

_FUNC_FRAG  = re.compile(r'^(of|and|in|on|at|to|for|with|by|from|the|a|an)\b', re.I)
_CAPS_NOISE = re.compile(r'^[A-Z][A-Z\s\-&/]{4,}$')
_PREAMBLE   = re.compile(r'page numbers|printed version|e-reader|scroll forward', re.I)

# Structural document navigation terms that leak into back-of-book indexes
# via cross-references ("see Chapter 3"), section markers, or front matter.
# Two forms caught: (a) standalone structural words; (b) terms that embed
# structural markers mid-string ("includes bibliographical references and index.").
# Added 17 April 2026; extended same session.
_STRUCT_NAV = re.compile(
    r'^(?:chapter|section|volume|index|introduction|conclusion|appendix|'
    r'bibliography|references|foreword|preface|afterword|glossary|contents|'
    r'part|series|below|above|see also|see|ibid|passim|cf\.|et al\.?)'
    r'[\s\.\d\-:]*$', re.I
)
_STRUCT_EMBED = re.compile(
    r'(?:bibliographical\s+references\s+and\s+index|'
    r'\bvolume\s+\d+\b)', re.I
)

# Platform/digitisation attribution strings that survive upstream cleaning
# and appear as index terms in OCR-derived text.
# Added 17 April 2026; "eolss" added same session.
_PLATFORM   = re.compile(
    r'(?:digitized\s+by|internet\s+archive|kahle|austin\s+foundation|'
    r'kindle\s+edition|amazon\s+digital|google\s+play|google\s+books|'
    r'this\s+page\s+intentionally|\beolss\b)', re.I
)

# Author-affiliation strings: "Surname, University of X, Country"
# Original pattern used \bUniversit\b which misses "Universite"/"Universiteit".
# Fixed: use \bUniversit\w* to match any inflection. Country list extended.
_AUTHAFFIL  = re.compile(
    r'\b(University|Instituto|Universit\w+)\b.{0,80}'
    r'\b(USA|UK|Germany|France|Australia|Brazil|China|India|Spain|Italy|'
    r'Japan|Mexico|Egypt|Canada|Switzerland|Sweden|Norway|Denmark|Austria|'
    r'Belgium|Poland|Greece|Portugal|Israel|South Africa|New Zealand|'
    r'Slovenia|Croatia|Hungary|Czech|Slovakia|Romania|Bulgaria|Serbia|'
    r'Finland|Netherlands|Ireland|Scotland|Wales|Singapore|Argentina|'
    r'Chile|Colombia|Russia|Ukraine|Turkey|Iran|Korea|Taiwan)\b', re.I)

# Single-name historical figures not caught by the "Surname, Firstname" pattern
# (fallback only — used when entity_types_cache.json is not available)
_ANCIENT_PERSONS = {
    'aristotle', 'plato', 'socrates', 'pythagoras', 'archimedes', 'euclid',
    'heraclitus', 'democritus', 'epicurus', 'cicero', 'virgil', 'homer',
    'confucius', 'buddha', 'newton', 'galileo', 'copernicus', 'leibniz',
    'kant', 'hegel', 'spinoza', 'locke', 'hume', 'nietzsche', 'marx',
    'freud', 'jung', 'descartes',
}

# Load the NER cache produced by 15_entity_classify.py (if available)
_ENTITY_CACHE = {}
_entity_cache_path = JSON_DIR / 'entity_types_cache.json'
if _entity_cache_path.exists():
    try:
        with open(str(_entity_cache_path)) as _f:
            _ENTITY_CACHE = json.load(_f)
        print(f"  Loaded entity cache: {len(_ENTITY_CACHE):,} entries")
    except Exception:
        pass

def is_person_term(tl, term):
    """Return True if this index term is a person name rather than a concept.
    Prefers the NER cache from 15_entity_classify.py; falls back to heuristics."""
    # Check NER cache first (most accurate)
    cached = _ENTITY_CACHE.get(tl.strip().lower())
    if cached:
        return cached['kind'] == 'person'
    # Fallback: comma-inverted index form "Wiener, Norbert" or "mcluhan, marshall"
    if _is_clean_name(term): return True
    # Fallback: single-name ancients
    if tl.strip().lower() in _ANCIENT_PERSONS: return True
    return False

def is_noise_term(tl, term):
    t = term.strip()
    if len(t) < 3: return True
    # Short OCR fragments: suffix stubs like "tion", "ing" with no vowel context
    if len(t) <= 4 and not any(c in 'aeiouAEIOU' for c in t): return True
    if _FUNC_FRAG.match(term) and len(term.split()) <= 6: return True
    if _CAPS_NOISE.match(term): return True
    if _PREAMBLE.search(term): return True
    if _AUTHAFFIL.search(term): return True          # author affiliations
    if _STRUCT_NAV.match(term): return True          # standalone structural words
    if _STRUCT_EMBED.search(term): return True       # structural words mid-string
    if _PLATFORM.search(term): return True           # digitisation / platform strings
    if len(term) > 80 and term.count(',') >= 2: return True
    return False

print("Loading data...")
with open(str(JSON_DIR / 'index_terms.json')) as f:  IT = json.load(f)
with open(str(JSON_DIR / 'index_vocab.json')) as f:  IV = json.load(f)
with open(str(JSON_DIR / 'nlp_results.json')) as f:  R  = json.load(f)
with open(str(JSON_DIR / 'books_clean.json')) as f:  BC = json.load(f)

# ── Book-level exclusion from book_styles.json ───────────────────────────────
# Skip index terms from books classified as reference/proceedings/handbook.
# This handles encyclopedias (e.g. EOLSS) whose "index" is a contributor list,
# without requiring term-by-term pattern matching.
# Added 17 April 2026.
_EXCLUDED_STYLES = {'reference', 'proceedings', 'handbook'}
_excluded_book_ids = set()
_bs_path = CSV_DIR.parent / 'json' / 'book_styles.json'
if not _bs_path.exists():
    _bs_path = _pl.Path('json') / 'book_styles.json'
if _bs_path.exists():
    try:
        with open(str(_bs_path)) as _f:
            _bs = json.load(_f)
        _excluded_book_ids = {
            bid for bid, v in _bs.items()
            if v.get('style', '') in _EXCLUDED_STYLES and v.get('verified', False)
        }
        print(f"  Book-level exclusions (verified reference/proceedings/handbook): "
              f"{len(_excluded_book_ids)} books")
    except Exception as _e:
        print(f"  WARNING: could not load book_styles.json: {_e}")

book_ids   = R['book_ids']
titles     = dict(zip(book_ids, R['titles']))
dom_topics = dict(zip(book_ids, R['dominant_topics']))
pub_years  = dict(zip(book_ids, R.get('pub_years', [None]*len(book_ids))))
n_topics   = R['n_topics']

_LDA_BASE = [
    'History and Historiography of Cybernetics',
    'Techno-political Complexes',
    'Engineering Control',
    'Social and Organisational Cybernetics',
    'Formal Foundations of Cybernetics',
    'Reinventing Selves and Others, Past and Future',
    'Psychological and Behavioural Regulation and Control',
    'Biological and Neural Cybernetics',
    'Extensions of Cybernetics',
]
_carried = R.get('topic_names') or _LDA_BASE
TOPIC_NAMES = (_carried + [f'Topic {i+1}' for i in range(len(_carried), n_topics)])[:n_topics]

# ── Build aggregated vocab ─────────────────────────────────────────────────
# IV has: {term_lower: {term, books: [bid,...], count}}
# Enrich with year_dist, topic_dist, n_books

print("Building person name merge rules...")
person_merge = build_person_merge_rules(IV)
print(f"  Person name merges: {len(person_merge)}")

# Accent normalisation: René/Rene, Schrödinger/Schrodinger
accent_merge = {}
for tl, v in IV.items():
    norm = _accent_key(tl)
    if norm != tl and norm in IV:
        nb_tl = v.get("n_books", 0)
        nb_norm = IV[norm].get("n_books", 0)
        if nb_tl >= nb_norm:
            accent_merge[norm] = tl
        else:
            accent_merge[tl] = norm
print(f"  Accent merges: {len(accent_merge)}")

_all_merges = {**person_merge, **accent_merge}

print("Building aggregated vocabulary...")
vocab = {}
for tl, v in IV.items():
    term = v['term']
    if is_noise_term(tl, term): continue          # suppress noise
    if tl in _all_merges: continue               # skip variants

    # Aggregate books from canonical + all variants pointing here,
    # excluding any books from verified reference/proceedings/handbook titles.
    variant_tls = {tl} | {vt for vt, ct in _all_merges.items() if ct == tl}
    books_with_term = list({b for vtl in variant_tls
                             for b in IV.get(vtl, {}).get('books', [])
                             if b not in _excluded_book_ids})
    if not books_with_term: continue             # term only existed in excluded books
    year_dist   = defaultdict(int)
    topic_dist  = defaultdict(int)
    for bid in books_with_term:
        y = pub_years.get(bid)
        t = dom_topics.get(bid)
        if y: year_dist[str((y // 10) * 10)] += 1
        if t is not None: topic_dist[str(t)] += 1
    vocab[tl] = {
        'term':       v['term'],
        'count':      len(books_with_term),
        'n_books':    len(books_with_term),
        'year_dist':  dict(year_dist),
        'topic_dist': dict(topic_dist),
        'is_person':  is_person_term(tl, v['term']),
    }

print(f"  Vocab terms: {len(vocab):,}")

# ── Top 200 terms by book count ────────────────────────────────────────────
top200_raw = sorted(vocab.items(), key=lambda x: x[1]['n_books'], reverse=True)[:200]
top200 = []
for tl, v in top200_raw:
    top200.append({
        'term':       v['term'],
        'count':      v['n_books'],
        'year_dist':  v['year_dist'],
        'topic_dist': v['topic_dist'],
        'is_person':  v['is_person'],
    })

n_persons  = sum(1 for v in top200 if v['is_person'])
n_concepts = len(top200) - n_persons
print(f"  Top 200 breakdown: {n_concepts} concepts, {n_persons} persons")

# ── Top co-occurrence pairs (top 50 terms) ─────────────────────────────────
print("Computing co-occurrence pairs...")
top50_keys = {tl for tl, _ in top200_raw[:50]}

# Build book → terms lookup for top50
book_top50 = defaultdict(set)
for bid, d in IT.items():
    for t in d['terms']:
        tl = t.lower()
        if tl in top50_keys:
            book_top50[bid].add(tl)

# Count co-occurrences
cooc_counts = defaultdict(int)
for bid, terms in book_top50.items():
    terms_list = sorted(terms)
    for i in range(len(terms_list)):
        for j in range(i+1, len(terms_list)):
            pair = (terms_list[i], terms_list[j])
            cooc_counts[pair] += 1

cooc_top50 = sorted(
    [{'a': vocab[a]['term'], 'b': vocab[b]['term'], 'count': c}
     for (a,b), c in cooc_counts.items() if c >= 3],
    key=lambda x: x['count'], reverse=True
)[:50]

# ── Book terms (display terms per book) ───────────────────────────────────
# Resolve each book's terms to canonical vocab keys
book_terms = {}
for bid, d in IT.items():
    raw_terms = d.get('terms', [])
    # Map each raw term to its canonical key
    canonical_set = set()
    for t in raw_terms:
        tl = t.lower().strip()
        resolved = _all_merges.get(tl, tl)
        if resolved in vocab:
            canonical_set.add(resolved)
        elif tl in vocab:
            canonical_set.add(tl)
    book_terms[bid] = sorted(canonical_set)

# ── Assemble index_analysis.json ──────────────────────────────────────────
index_analysis = {
    'vocab':      vocab,
    'top200':     top200,
    'cooc_top50': cooc_top50,
    'book_terms': book_terms,
    'topic_names': TOPIC_NAMES,
    'pub_years':  {bid: pub_years.get(bid) for bid in book_ids},
    'dom_topics': {bid: dom_topics.get(bid) for bid in book_ids},
    'titles':     {bid: titles.get(bid, '') for bid in book_ids},
    'n_topics':   n_topics,
}

with open(str(JSON_DIR / 'index_analysis.json'), 'w', encoding='utf-8') as f:
    json.dump(index_analysis, f, ensure_ascii=False)
print("Saved: index_analysis.json")

# ── Build index_snippets.json ──────────────────────────────────────────────
# For top 200 terms: find one context sentence per book that contains the term
print("Building snippets for top 200 terms...")

def find_snippet(text, term, max_len=180):
    """Return first sentence containing term (case-insensitive), truncated."""
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    sentences = re.split(r'(?<=[.!?])\s+', text[:50000])
    for sent in sentences:
        if pattern.search(sent):
            s = sent.strip()
            return s[:max_len] + ('…' if len(s) > max_len else '')
    return ''

snippets = {}  # term_lower -> {bid: snippet_text}
for tl, v in top200_raw[:200]:
    books_with_term = IV[tl].get('books', [])
    term_display    = v['term']
    snip_map        = {}
    for bid in books_with_term[:30]:   # cap at 30 books per term
        text = BC.get(bid, {}).get('clean_text', '')
        if not text:
            continue
        snippet = find_snippet(text, term_display)
        if snippet:
            snip_map[bid] = snippet
    if snip_map:
        snippets[tl] = snip_map

with open(str(JSON_DIR / 'index_snippets.json'), 'w', encoding='utf-8') as f:
    json.dump(snippets, f, ensure_ascii=False)
print(f"Saved: index_snippets.json  ({len(snippets)} terms with snippets)")
print("\nDone.")