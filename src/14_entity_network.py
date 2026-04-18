"""
14_entity_network.py
────────────────────────────────────────────────────────────────────────────
Builds person–concept and person–location relational networks from the
index vocabulary, using two complementary closeness measures:

  1. Book-level PMI × reliability
     PMI = log P(P,C) / (P(P)·P(C))   — how much more likely C is given P
     reliability = sqrt(min(overlap,20)/20)  — dampens small-sample noise
     → Overview: which concepts define each person's intellectual context

  2. Paragraph-window co-occurrence (±5 sentences)
     → Detail: which concepts appear in the same local textual context

Reads:
  json/index_analysis.json    (persons, concepts, locations from index)
  json/books_clean.json       (clean text for paragraph windows)
  json/nlp_results.json       (topic labels)

Writes:
  json/entity_network.json    (nodes + edges for both network types)
  data/outputs/book_nlp_entity_network.html

Usage:
  python3 src/14_entity_network.py
  python3 src/14_entity_network.py --min-books 5   # stricter entity threshold
  python3 src/14_entity_network.py --no-windows    # skip paragraph windows (faster)
"""

# ── METHODOLOGICAL NOTE — all outputs are provisional ────────────────────────
# This script generates HTML from automated analysis of a 542-book corpus.
# Results should be treated as provisional: known data quality issues have been
# characterised and mitigated; residual errors of uncharacterised distribution
# remain. Algorithm infection — residual input errors propagate into downstream
# computations (LDA, PMI, TF-IDF, etc.) with effects that cannot be quantified
# in advance. Individual associations should be verified against source material
# before being treated as established findings.
# Full argument: docs/methodology.md §"Implication for dissemination —
# all outputs are provisional"
# ─────────────────────────────────────────────────────────────────────────────

_PROV_NOTICE = (
    '<style>body{padding-top:54px!important}</style>'
    '<div style="position:fixed;top:0;left:0;right:0;z-index:9999;'
    'background:#fef3c7;border-bottom:3px solid #d97706;'
    'padding:0.55rem 1.25rem;font-size:.82rem;color:#78350f;'
    'line-height:1.5;box-shadow:0 2px 6px rgba(0,0,0,.12)">'
    '<strong>Provenance notice:</strong> Results are derived from '
    'automated analysis of the CyberneticsNLP corpus and should be '
    'treated as provisional. '
    'Known data quality issues have been characterised and mitigated; '
    'residual errors of uncharacterised distribution remain. '
    'Individual associations should be verified against source material '
    'before being treated as established findings. '
    'See <em>docs/methodology.md</em> &sect;&ldquo;Implication for '
    'dissemination &mdash; all outputs are provisional&rdquo;.'
    '</div>'
)
import json, re, math, sys, os
from collections import defaultdict

import pathlib as _pl
CSV_DIR  = _pl.Path('csv')
JSON_DIR = _pl.Path('json')
JSON_DIR.mkdir(exist_ok=True)

import os as _os
_here = _os.path.dirname(_os.path.abspath(__file__))
_root = _os.path.dirname(_here) if _os.path.basename(_here) == 'src' else _here
_os.chdir(_root)

# ── CLI flags ─────────────────────────────────────────────────────────────────
MIN_BOOKS  = 3    # minimum books for an entity to be included
NO_WINDOWS = '--no-windows' in sys.argv
if '--min-books' in sys.argv:
    try: MIN_BOOKS = int(sys.argv[sys.argv.index('--min-books') + 1])
    except (IndexError, ValueError): pass

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading data...")
with open(str(JSON_DIR / 'index_analysis.json')) as f: IA = json.load(f)
with open(str(JSON_DIR / 'books_clean.json'))    as f: BC = json.load(f)
with open(str(JSON_DIR / 'nlp_results.json'))    as f: R  = json.load(f)

# Load NER cache from 15_entity_classify.py (if available)
_cache_path = JSON_DIR / 'entity_types_cache.json'
ENTITY_CACHE = {}
if _cache_path.exists():
    ENTITY_CACHE = json.loads(_cache_path.read_text())
    print(f'  Entity cache: {len(ENTITY_CACHE):,} entries')
else:
    print('  Entity cache not found — run 15_entity_classify.py for better classification')

vocab      = IA['vocab']
book_terms = IA['book_terms']
N          = len(BC)
n_topics   = R['n_topics']

_LDA_BASE = [
    'Management Cybernetics',
    'Second-Order Cybernetics Applied to Social Systems',
    'Dynamical Systems, Homeostasis & Biological Regulation',
    'Psychological Cybernetics',
    'Non-Anglophone Engineering Cybernetics',
    'Mathematical Foundations of Cybernetics',
    'Cultural Cybernetics, Posthumanism & Digital Media',
    'Applied Cybernetics & Computers in Society',
    'Residual / Outlier Cluster',
]
_carried = R.get('topic_names') or _LDA_BASE
LDA_NAMES = (_carried + [f'Topic {i+1}' for i in range(len(_carried), n_topics)])[:n_topics]

# ── Entity classification ─────────────────────────────────────────────────────
# Canonical single-name historical persons (ancient, medieval, early modern)
KNOWN_SINGLE_PERSONS = {
    # Ancient world
    'aristotle', 'plato', 'socrates', 'pythagoras', 'heraclitus',
    'democritus', 'archimedes', 'epicurus', 'thales', 'anaximander',
    'anaximenes', 'empedocles', 'parmenides', 'zeno', 'hippocrates',
    'euclid', 'ptolemy', 'diogenes', 'plotinus',
    # Medieval / Renaissance
    'averroes', 'avicenna', 'aquinas', 'paracelsus', 'copernicus',
    'galileo', 'kepler',
    # Early modern philosophy and science
    'descartes', 'spinoza', 'leibniz', 'newton', 'locke', 'hume',
    'kant', 'hegel', 'schopenhauer', 'nietzsche', 'marx', 'engels',
    'freud', 'jung', 'darwin', 'lamarck', 'malthus',
    # 20th century (single-name usage canonical in scholarship)
    'einstein', 'bohr', 'heisenberg', 'schrodinger', 'wittgenstein',
    'husserl', 'heidegger', 'sartre', 'lacan', 'derrida',
}

PERSON_PAT = re.compile(
    r'^[A-Z][\w\-]+(?:\s+[A-Z][\w\-]+)*,\s'   # Surname(s), First
    r'|^(?:von|de|van|der|du|al)\s+[A-Z]',
    re.UNICODE)

def is_person(tl, term):
    """Return True if the index term is a person."""
    if PERSON_PAT.match(term): return True
    if tl.strip().lower() in KNOWN_SINGLE_PERSONS: return True
    return False

# Organisations: institutions with a location but classified as orgs
ORG_PAT = re.compile(
    r'\b(University|College|Institute|Laboratory|Labs?|Foundation|'
    r'Corporation|School|Academy|Center|Centre|Association|Press|'
    r'Media Lab|RAND|Caltech|MIT|NSF|NASA|DARPA|BBC|CIA|FBI)\b',
    re.IGNORECASE)

# Pure geographic locations: countries, cities, regions
GEO_PAT = re.compile(
    r'\b(Soviet Union|Germany|France|Britain|England|Japan|China|India|'
    r'America|Europe|Russia|Australia|Canada|Italy|Spain|Brazil|Mexico|'
    r'Africa|Asia|Antarctica|London|New York|Cambridge|Chicago|Paris|'
    r'Berlin|Vienna|Tokyo|Moscow|Beijing|Amsterdam|Copenhagen|Brussels|'
    r'California|Massachusetts|Edinburgh|Toronto|Budapest|Silicon Valley|'
    r'Latin America|Middle East|South America|North America|Great Britain|'
    r'United States|United Kingdom|New Zealand|South Africa|Hong Kong)\b',
    re.IGNORECASE)

# Noise: overly long strings, comma-separated author affiliations, garbled
def is_noise_location(term):
    if len(term) > 60 and ',' in term: return True
    if term.count(',') >= 2: return True
    if term in {'Laboratory', 'Society', 'University)', 'Institute',
                'Conference', 'Congress', 'Association'}: return True
    return False

NOISE_TERMS = {
    'index', 'systems', 'science', 'time', 'and', 'university',
    'society', 'international', 'american', 'world', 'english',
    'general', 'human', 'social', 'cultural', 'mathematical',
    'political', 'theoretical', 'historical', 'natural', 'modern',
    'new', 'old', 'first', 'second', 'third', 'early', 'late',
    'good', 'best', 'great', 'higher', 'lower', 'basic', 'applied',
    # Structural document navigation terms (belt-and-suspenders: 09b filters
    # these upstream, but defence-in-depth catches any that slip through)
    'chapter', 'section', 'volume', 'introduction', 'conclusion',
    'appendix', 'bibliography', 'foreword', 'preface', 'series',
    'below', 'above', 'contents', 'glossary',
}

# Modern technology platforms: excluded from the entity network entirely
# because they generate spurious PMI associations with historical figures
# (e.g. Wiener–Google) via co-occurrence in modern books that discuss both
# cybernetics history and contemporary tech. Exclusion happens before PMI
# computation so no edge scores are corrupted. Added 17 April 2026 (KI-04).
KNOWN_TECH_PLATFORMS = {
    'google', 'amazon', 'facebook', 'meta', 'twitter', 'apple',
    'microsoft', 'ibm', 'openai', 'netflix', 'uber', 'airbnb',
    'tiktok', 'instagram', 'whatsapp', 'youtube', 'linkedin',
    'intel', 'nvidia', 'oracle', 'salesforce', 'adobe',
}

# Trailing-function-word fragments: "evolution of", "wiener and", "ai and",
# "free will and", etc.  _FUNC_FRAG in 09b catches terms *starting* with a
# function word; this catches terms *ending* with one, which slip through NER
# as apparent named entities.  Applied before cache lookup so it cannot be
# overridden by a stale cache entry.  Added 18 April 2026.
_TRAILING_FUNC = re.compile(
    r'\s(?:and|of|on|the|to|for|in|with|or|by|at|from|about|'
    r'its|their|our|a|an|is|are|was|were|has|have|had|be|been|being|'
    r'not|nor|yet|whether|though|although|'
    r'this|that|these|those|it|we|they|he|she)\s*[.,;]?\s*$',
    re.I
)

# Back-matter / CTA strings that NER misidentifies as named entities.
# Applied before cache lookup.  Added 18 April 2026.
# "about the authors" (plural) added 18 April 2026.
_CTA_BACK_MATTER = re.compile(
    r'^(?:sign\s+up|discover\s+your|all\s+rights\s+reserved|'
    r'about\s+the\s+authors?|first\s+edition|copyright\s+\d|'
    r'published\s+by|printed\s+in|table\s+of\s+contents|'
    r'terms\s+of\s+(?:use|service)|click\s+here|'
    r'download\s+now|get\s+started)',
    re.I
)

# EOLSS encyclopedia noise: volume-title strings, editor attribution lines, and
# encyclopedia section headers leaking from EOLSS volumes in the corpus.
# Patterns: contains "eolss"; contains em-dash + "volume"; starts with
# "editor:" or "editors:"; DESWARE encyclopedia header.
# Applied before cache lookup.  Added 18 April 2026.
_EOLSS_NOISE = re.compile(
    r'eolss'
    r'|–\s*volume\b'
    r'|^\s*editors?\s*:'
    r'|encyclopedia\s+of\s+desalination',
    re.I
)

# Trailing-colon fragments: index sub-entry headers where the colon leaked
# through NER as apparent named entities ("approach:", "cybernetics:", etc.).
# Applied before cache lookup.  Added 18 April 2026.
_TRAILING_COLON = re.compile(r':\s*$')

persons       = {}
organisations = {}
locations     = {}
concepts      = {}

for tl, v in vocab.items():
    t  = v['term']
    nb = v['n_books']
    if nb < MIN_BOOKS: continue
    if tl.lower() in NOISE_TERMS: continue
    if tl.lower() in KNOWN_TECH_PLATFORMS: continue  # KI-04: suppress before PMI
    if _TRAILING_FUNC.search(t): continue             # fragment: "evolution of", "wiener and"
    if _CTA_BACK_MATTER.match(t): continue            # back-matter: "sign up now", "about the authors?"
    if _EOLSS_NOISE.search(t): continue               # EOLSS vol titles, editor attributions
    if _TRAILING_COLON.search(t): continue            # index sub-entry headers: "approach:", etc.
    if len(t) < 3: continue
    # Skip clearly garbled OCR entries
    if re.search(r'\d{3,}|[^\w\s\-\',\.\(\)\/&]', t): continue

    # Check NER cache first (from 15_entity_classify.py)
    _cached = ENTITY_CACHE.get(tl)
    if _cached and _cached.get('confidence', 0) >= 0.75:
        _kind = _cached['kind']
        if _kind == 'suppress':       pass
        elif _kind == 'person':       persons[tl]       = v
        elif _kind == 'organisation': organisations[tl] = v
        elif _kind == 'location':     locations[tl]     = v
        else:                         concepts[tl]      = v
    else:
        # Fall back to heuristics if no cache entry
        if is_person(tl, t):          persons[tl]       = v
        elif is_noise_location(t):    pass
        elif ORG_PAT.search(t):       organisations[tl] = v
        elif GEO_PAT.search(t):       locations[tl]     = v
        else:                         concepts[tl]      = v

# Deduplicate persons — e.g. "Wiener, N." and "Wiener, Norbert" are the same
# Keep the one with higher n_books
surname_map = defaultdict(list)
for tl, v in persons.items():
    surname = tl.split(',')[0].strip()
    surname_map[surname].append((v['n_books'], tl, v))

persons_dedup = {}
for surname, entries in surname_map.items():
    entries.sort(reverse=True)   # highest n_books first
    _, keep_tl, keep_v = entries[0]
    persons_dedup[keep_tl] = keep_v

persons = persons_dedup

print(f"  Persons:        {len(persons):,}  (after dedup)")
print(f"  Organisations:  {len(organisations):,}")
print(f"  Locations:      {len(locations):,}")
print(f"  Concepts:       {len(concepts):,}")

# ── Build book-set lookup ─────────────────────────────────────────────────────
print("Building book sets...")
book_lower = {bid: {t.lower().strip() for t in terms}
              for bid, terms in book_terms.items()}

def book_set(tl):
    return frozenset(bid for bid, s in book_lower.items() if tl in s)

person_booksets       = {tl: book_set(tl) for tl in persons}
organisation_booksets = {tl: book_set(tl) for tl in organisations}
location_booksets     = {tl: book_set(tl) for tl in locations}
concept_booksets      = {tl: book_set(tl) for tl in concepts}

# ── Book-level PMI × reliability ─────────────────────────────────────────────
def pmi_score(a_books, b_books, min_both=3):
    both = len(a_books & b_books)
    if both < min_both: return 0.0
    p_a  = len(a_books) / N
    p_b  = len(b_books) / N
    p_ab = both / N
    pmi  = math.log(p_ab / (p_a * p_b + 1e-10))
    reliability = math.sqrt(min(both, 20) / 20)
    return round(pmi * reliability, 4)

# ── Paragraph-window co-occurrence ───────────────────────────────────────────
WINDOW = 5  # sentences either side

def para_cooccur(text, entity_term, target_terms, sample_chars=80000):
    """
    Count how often each target term appears within ±WINDOW sentences
    of the entity term. Returns {term_lower: count}.
    """
    text = text[:sample_chars]
    sentences = re.split(r'(?<=[.!?])\s+', text)
    entity_lower = entity_term.lower()

    # Find entity sentence indices
    entity_idxs = [i for i, s in enumerate(sentences)
                   if entity_lower in s.lower()]
    if not entity_idxs:
        return {}

    # Build window text
    window_indices = set()
    for idx in entity_idxs:
        window_indices.update(range(max(0, idx - WINDOW),
                                     min(len(sentences), idx + WINDOW + 1)))
    window_text = ' '.join(sentences[i] for i in sorted(window_indices)).lower()

    counts = {}
    for tl in target_terms:
        tv = vocab.get(tl, {}).get('term', tl)
        if tv.lower() in window_text:
            # Count occurrences
            counts[tl] = window_text.count(tv.lower())
    return counts

# ── Compute edges ─────────────────────────────────────────────────────────────
print("Computing person–concept edges (book-level)...")

MIN_PMI   = 0.3   # minimum PMI score for an edge
MAX_EDGES_PER_NODE = 20  # keep top N per person

person_concept_edges = []
person_location_edges = []

for p_tl, p_v in persons.items():
    p_books = person_booksets[p_tl]
    if not p_books: continue
    p_name = p_v['term']

    # Person–concept
    scores = []
    for c_tl, c_books in concept_booksets.items():
        s = pmi_score(p_books, c_books)
        if s >= MIN_PMI:
            scores.append((s, c_tl))
    scores.sort(reverse=True)
    for s, c_tl in scores[:MAX_EDGES_PER_NODE]:
        person_concept_edges.append({
            'source': p_tl, 'target': c_tl,
            'weight': s,
            'overlap': len(p_books & concept_booksets[c_tl]),
            'type': 'person-concept', 'level': 'book',
        })

    # Person–organisation
    for o_tl, o_books in organisation_booksets.items():
        s = pmi_score(p_books, o_books, min_both=2)
        if s >= MIN_PMI:
            person_location_edges.append({
                'source': p_tl, 'target': o_tl,
                'weight': s,
                'overlap': len(p_books & o_books),
                'type': 'person-organisation', 'level': 'book',
            })

    # Person–location
    for l_tl, l_books in location_booksets.items():
        s = pmi_score(p_books, l_books, min_both=2)
        if s >= MIN_PMI:
            person_location_edges.append({
                'source': p_tl, 'target': l_tl,
                'weight': s,
                'overlap': len(p_books & l_books),
                'type': 'person-location', 'level': 'book',
            })

print(f"  Person–concept edges (book-level): {len(person_concept_edges):,}")
print(f"  Person–location edges (book-level): {len(person_location_edges):,}")

# ── Paragraph-window pass ─────────────────────────────────────────────────────
para_edges = []
if not NO_WINDOWS:
    print("Computing paragraph-window edges (this takes a few minutes)...")

    # Limit to top persons (by n_books) for performance
    TOP_PERSONS = 50
    top_persons = sorted(persons.items(), key=lambda x: -x[1]['n_books'])[:TOP_PERSONS]

    for p_idx, (p_tl, p_v) in enumerate(top_persons):
        p_name   = p_v['term']
        p_books  = person_booksets[p_tl]
        # Only scan books where person actually appears
        scan_bids = list(p_books)[:30]  # cap at 30 books

        window_counts = defaultdict(int)
        for bid in scan_bids:
            text = BC.get(bid, {}).get('clean_text', '')
            if not text: continue
            # Collect target terms present in this book
            book_tls = book_lower.get(bid, set())
            target_tls = [tl for tl in book_tls
                          if tl in concept_booksets or tl in location_booksets]
            counts = para_cooccur(text, p_v['term'].split(',')[0], target_tls)
            for tl, c in counts.items():
                window_counts[tl] += c

        # Build edges from window counts
        for tl, count in window_counts.items():
            if count < 2: continue
            edge_type = 'person-concept' if tl in concepts else 'person-location'
            para_edges.append({
                'source': p_tl, 'target': tl,
                'weight': round(math.log1p(count), 4),
                'overlap': count,
                'type': edge_type, 'level': 'paragraph',
            })

        if (p_idx + 1) % 10 == 0:
            print(f"  {p_idx+1}/{TOP_PERSONS} persons processed...")

    print(f"  Paragraph-window edges: {len(para_edges):,}")

# ── Assemble nodes ────────────────────────────────────────────────────────────
all_edges   = person_concept_edges + person_location_edges + para_edges
active_tls  = {e['source'] for e in all_edges} | {e['target'] for e in all_edges}

def topic_label(v):
    td = v.get('topic_dist', {})
    if not td: return None
    best = max(td.items(), key=lambda x: x[1])
    t = int(best[0])
    return LDA_NAMES[t] if t < len(LDA_NAMES) else f'Topic {t+1}'

nodes = {}
for tl in active_tls:
    v = vocab.get(tl, {})
    if tl in persons:
        kind = 'person'
    elif tl in organisations:
        kind = 'organisation'
    elif tl in locations:
        kind = 'location'
    else:
        kind = 'concept'
    nodes[tl] = {
        'id':       tl,
        'label':    v.get('term', tl),
        'kind':     kind,
        'n_books':  v.get('n_books', 0),
        'topic':    topic_label(v),
    }

print(f"\nNetwork summary:")
print(f"  Nodes: {len(nodes):,}  "
      f"(persons={sum(1 for n in nodes.values() if n['kind']=='person')}, "
      f"orgs={sum(1 for n in nodes.values() if n['kind']=='organisation')}, "
      f"locations={sum(1 for n in nodes.values() if n['kind']=='location')}, "
      f"concepts={sum(1 for n in nodes.values() if n['kind']=='concept')})")
print(f"  Edges: {len(all_edges):,}  "
      f"(book={len(person_concept_edges)+len(person_location_edges)}, "
      f"para={len(para_edges)})")

# ── Network statistics ───────────────────────────────────────────────────────
print("Computing network statistics...")

import numpy as _np
from collections import defaultdict as _dd

_degree  = _dd(int)
_wdegree = _dd(float)
for _e in all_edges:
    _s = _e['source']; _t = _e['target']
    _degree[_s]  += 1;  _degree[_t]  += 1
    _wdegree[_s] += _e['weight']; _wdegree[_t] += _e['weight']

# Attach degree to each node
for n in nodes.values():
    n['degree']  = _degree.get(n['id'], 0)
    n['wdegree'] = round(_wdegree.get(n['id'], 0.0), 3)

_degs = _np.array(sorted(_degree.values(), reverse=True))
_deg_percentiles = {
    'p50': float(_np.percentile(_degs, 50)),
    'p75': float(_np.percentile(_degs, 75)),
    'p90': float(_np.percentile(_degs, 90)),
    'p95': float(_np.percentile(_degs, 95)),
    'max': int(_degs.max()),
    'mean': round(float(_degs.mean()), 2),
    'min': int(_degs.min()),
}

# Degree distribution histogram (log-binned)
_hist_bins = [0,1,2,3,5,8,13,21,34,55,89,144,233,400]
_hist = [0] * (len(_hist_bins)-1)
for _d in _degs:
    for _i in range(len(_hist_bins)-1):
        if _hist_bins[_i] <= _d < _hist_bins[_i+1]:
            _hist[_i] += 1; break

# Adjacency for graph metrics
_adj = _dd(set)
for _e in all_edges:
    _s = _e['source']; _t = _e['target']
    _adj[_s].add(_t); _adj[_t].add(_s)

# Connected components
_visited = set()
_components = []
for _nid in nodes:
    if _nid not in _visited:
        _comp = []
        _stack = [_nid]
        while _stack:
            _cur = _stack.pop()
            if _cur in _visited: continue
            _visited.add(_cur); _comp.append(_cur)
            _stack.extend(_adj[_cur] - _visited)
        _components.append(_comp)
_comp_sizes = sorted([len(c) for c in _components], reverse=True)
_lcc = max(_components, key=len) if _components else []

# Sampled average path length (BFS on LCC sample)
import random as _rnd
_rnd.seed(99)
_apl = None
_diameter = None
if len(_lcc) >= 10:
    _srcs = _rnd.sample(_lcc, min(80, len(_lcc)))
    _tgts = set(_rnd.sample(_lcc, min(40, len(_lcc))))
    _paths = []
    for _src in _srcs:
        _dist = {_src: 0}; _q = [_src]
        while _q:
            _cur = _q.pop(0)
            if _dist[_cur] >= 8: continue
            for _nb in _adj[_cur]:
                if _nb not in _dist:
                    _dist[_nb] = _dist[_cur] + 1
                    _q.append(_nb)
                    if _nb in _tgts:
                        _paths.append(_dist[_nb])
    if _paths:
        _apl      = round(sum(_paths)/len(_paths), 3)
        _diameter = max(_paths)

# Density
_n = len(nodes); _m = len(all_edges)
_density = round(2*_m / (_n*(_n-1)) if _n > 1 else 0, 6)

# Hub nodes (top 1% by degree)
_hub_thr = float(_np.percentile(_degs, 99)) if len(_degs) > 10 else _degs.max()
_hubs = sorted(
    [(nid, _degree[nid], nodes[nid].get('label',''), nodes[nid].get('kind',''))
     for nid in nodes if _degree.get(nid,0) >= _hub_thr],
    key=lambda x: -x[1])[:20]

_stats = {
    'n_nodes':          _n,
    'n_edges':          _m,
    'density':          _density,
    'n_components':     len(_components),
    'lcc_size':         len(_lcc),
    'lcc_fraction':     round(len(_lcc)/_n, 3) if _n else 0,
    'avg_degree':       _deg_percentiles['mean'],
    'max_degree':       _deg_percentiles['max'],
    'deg_percentiles':  _deg_percentiles,
    'avg_path_length':  _apl,
    'diameter':         _diameter,
    'component_sizes':  _comp_sizes[:10],
    'deg_hist_bins':    _hist_bins[:-1],
    'deg_hist':         _hist,
    'hubs':             [{'id':h[0],'degree':h[1],'label':h[2],'kind':h[3]}
                         for h in _hubs],
}

print(f"  Density: {_density:.6f}  Components: {len(_components)}")
print(f"  LCC: {len(_lcc)}/{_n} nodes ({_stats['lcc_fraction']:.0%})")
if _apl: print(f"  Avg path length: {_apl}  Diameter: {_diameter}")
print(f"  Degree: mean={_deg_percentiles['mean']}  "
      f"p50={_deg_percentiles['p50']:.0f}  "
      f"p90={_deg_percentiles['p90']:.0f}  "
      f"p95={_deg_percentiles['p95']:.0f}  "
      f"max={_deg_percentiles['max']}")

# ── Save JSON ─────────────────────────────────────────────────────────────────
network = {
    'nodes':       list(nodes.values()),
    'edges':       all_edges,
    'stats':       _stats,
    'n_persons':       len(persons),
    'n_organisations': len(organisations),
    'n_locations':     len(locations),
    'n_concepts':      len(concepts),
    'lda_names':   LDA_NAMES,
    'min_books':   MIN_BOOKS,
    'min_pmi':     MIN_PMI,
}
with open(str(JSON_DIR / 'entity_network.json'), 'w') as f:
    json.dump(network, f, ensure_ascii=False)
print(f"\nSaved: json/entity_network.json")

# ── Build HTML report ─────────────────────────────────────────────────────────
print("Building HTML report...")

PAL_KIND = {'person': '#2563eb', 'concept': '#16a34a',
            'organisation': '#7c3aed', 'location': '#d97706'}
PAL_TOPIC = ['#2563eb','#16a34a','#dc2626','#d97706','#7c3aed',
             '#0891b2','#be185d','#0f766e','#c2410c','#065f46']

j_nodes = json.dumps(list(nodes.values()))
j_edges = json.dumps(all_edges)
j_stats = json.dumps(_stats)
j_pal   = json.dumps(PAL_TOPIC)
j_lda   = json.dumps(LDA_NAMES)
j_pkind = json.dumps(PAL_KIND)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Entity–Concept Network</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<style>
:root{{--blue:#2563eb;--green:#16a34a;--amber:#d97706;--bg:#f8fafc;--card:#fff;--border:#e2e8f0}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:#1e293b;overflow:hidden;height:100vh;display:flex;flex-direction:column}}
.header{{background:linear-gradient(135deg,#1e3a5f,#2563eb);color:#fff;padding:.8rem 1.5rem;display:flex;align-items:center;gap:1.5rem;flex-shrink:0}}
.header h1{{font-size:1.15rem;font-weight:700}}
.header p{{font-size:.82rem;opacity:.8}}
.controls{{background:#fff;border-bottom:1px solid var(--border);padding:.5rem 1.2rem;display:flex;gap:1rem;align-items:center;flex-wrap:wrap;flex-shrink:0}}
.controls label{{font-size:.82rem;color:#475569;font-weight:500}}
.controls select,.controls input[type=range]{{padding:.25rem .5rem;border:1px solid var(--border);border-radius:5px;font-size:.82rem;background:#fff}}
.controls input[type=text]{{padding:.25rem .6rem;border:1px solid var(--border);border-radius:5px;font-size:.82rem;width:180px}}
.legend{{display:flex;gap:1rem;align-items:center;font-size:.78rem}}
.dot{{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:4px}}
#canvas{{flex:1;overflow:hidden}}
svg{{width:100%;height:100%}}
.node circle{{stroke:#fff;stroke-width:1.5px;cursor:pointer;transition:r .15s}}
.node circle:hover{{stroke:#1e293b;stroke-width:2.5px}}
.node text{{font-size:9px;fill:#1e293b;pointer-events:none;text-anchor:middle}}
.link{{stroke-opacity:0.35;pointer-events:none}}
.link.highlighted{{stroke-opacity:0.9}}
.tooltip{{position:fixed;background:#1e293b;color:#fff;padding:.5rem .8rem;border-radius:6px;font-size:.8rem;pointer-events:none;display:none;max-width:280px;line-height:1.5;z-index:100}}
.panel{{position:fixed;right:0;top:0;bottom:0;width:300px;background:#fff;border-left:1px solid var(--border);padding:1rem;overflow-y:auto;display:none;z-index:50;font-size:.82rem}}
.panel h3{{font-size:.95rem;font-weight:700;margin-bottom:.5rem;padding-bottom:.4rem;border-bottom:2px solid var(--blue)}}
.panel .close{{float:right;cursor:pointer;color:#94a3b8;font-size:1rem}}
.edge-item{{padding:.25rem 0;border-bottom:1px solid #f1f5f9;display:flex;justify-content:space-between}}
.edge-item:last-child{{border-bottom:none}}
.badge{{font-size:.7rem;padding:.1rem .4rem;border-radius:3px;color:#fff;font-weight:600}}
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>🕸 Entity–Concept Relational Network</h1>
    <p>{len(nodes):,} nodes · {len(all_edges):,} edges · PMI closeness + paragraph-window</p>
  </div>
  <div class="legend">
    <span><span class="dot" style="background:#2563eb"></span>Person</span>
    <span><span class="dot" style="background:#16a34a"></span>Concept</span>
    <span><span class="dot" style="background:#7c3aed"></span>Organisation</span>
    <span><span class="dot" style="background:#d97706"></span>Location</span>
  </div>
</div>
<div class="controls">
  <label>Filter: <input type="text" id="search" placeholder="Search person/concept…" oninput="filterGraph()"></label>
  <label style="display:flex;align-items:center;gap:.4rem">Show:
    <label style="font-weight:400"><input type="checkbox" id="show_person" checked onchange="filterGraph()"> Persons</label>
    <label style="font-weight:400"><input type="checkbox" id="show_concept" checked onchange="filterGraph()"> Concepts</label>
    <label style="font-weight:400"><input type="checkbox" id="show_org" checked onchange="filterGraph()"> Orgs</label>
    <label style="font-weight:400"><input type="checkbox" id="show_loc" checked onchange="filterGraph()"> Locations</label>
  </label>
  <label>Edges: <select id="edge_type" onchange="filterGraph()">
    <option value="all">All types</option>
    <option value="person-concept">Person–Concept</option>
    <option value="person-organisation">Person–Organisation</option>
    <option value="person-location">Person–Location</option>
  </select></label>
  <label>Level: <select id="edge_level" onchange="filterGraph()">
    <option value="all">Book + Paragraph</option>
    <option value="book">Book-level only</option>
    <option value="paragraph">Paragraph-window only</option>
  </select></label>
  <label>Min weight: <input type="range" id="min_weight" min="0" max="20" value="3"
    step="1" oninput="document.getElementById('wval').textContent=this.value/10;filterGraph()">
    <span id="wval">0.3</span></label>
  <label>Charge: <input type="range" id="charge" min="-500" max="-50" value="-150"
    step="10" oninput="updateForce()"></label>
  <label>Min degree: <select id="min_deg" onchange="filterGraph()">
    <option value="0">All nodes</option>
    <option value="p75">≥ p75 (top 25%)</option>
    <option value="p90">≥ p90 (top 10%)</option>
    <option value="p95">≥ p95 (top 5%)</option>
    <option value="p99">≥ p99 (top 1%)</option>
  </select></label>
  <button onclick="toggleStats()" style="padding:.3rem .7rem;border:1px solid var(--border);border-radius:5px;font-size:.82rem;cursor:pointer;background:#eff6ff;color:#2563eb">📊 Network stats</button>
  <label>Layout: <select id="layout_algo" onchange="switchLayout()">
    <option value="force">Force-directed (Fruchterman-Reingold)</option>
    <option value="radial">Radial (concentric rings by kind)</option>
    <option value="bipartite">Bipartite (persons ↔ entities, top 100)</option>
    <option value="circular">Circular (arc-grouped by kind)</option>
  </select></label>
  <button onclick="resetZoom()" style="padding:.3rem .7rem;border:1px solid var(--border);border-radius:5px;font-size:.82rem;cursor:pointer;background:#fff">Reset view</button>
</div>
<div id="canvas"></div>
<div class="tooltip" id="tooltip"></div>
<div class="panel" id="panel">
  <span class="close" onclick="closePanel()">✕</span>
  <h3 id="panel_title"></h3>
  <div id="panel_body"></div>
</div>
<div class="panel" id="stats_panel" style="width:340px;right:0">
  <span class="close" onclick="toggleStats()">✕</span>
  <h3>📊 Network Statistics</h3>
  <div id="stats_body"></div>
</div>
<div class="panel" id="stats_panel" style="width:340px">
  <span class="close" onclick="toggleStats()">✕</span>
  <h3>📊 Network Statistics</h3>
  <div id="stats_body"></div>
</div>

<script>
const NODES   = {j_nodes};
const EDGES   = {j_edges};
const STATS   = {j_stats};
const PAL_K   = {j_pkind};
const PAL_T   = {j_pal};
const LDA     = {j_lda};

// ── State ────────────────────────────────────────────────────────────────────
let activeNodes = new Set(NODES.map(n => n.id));
let activeEdges = EDGES;
let simulation, svg, link, node, zoom;

// ── Init D3 force simulation ──────────────────────────────────────────────────
const W = window.innerWidth, H = window.innerHeight - 90;
const canvas = document.getElementById('canvas');

svg = d3.select('#canvas').append('svg')
  .attr('width','100%').attr('height','100%');

const g = svg.append('g');

zoom = d3.zoom().scaleExtent([0.05, 8])
  .on('zoom', e => g.attr('transform', e.transform));
svg.call(zoom);

function initSim(nodes, edges) {{
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id(d => d.id)
           .distance(d => 120 / (d.weight + 0.5))
           .strength(d => Math.min(d.weight * 0.4, 0.8)))
    .force('charge', d3.forceManyBody()
           .strength(+document.getElementById('charge').value))
    .force('center', d3.forceCenter(W/2, H/2))
    .force('collision', d3.forceCollide().radius(d => nodeR(d) + 4));
}}

function nodeR(d) {{
  return Math.max(5, Math.min(18, Math.sqrt(d.n_books || 1) * 1.8));
}}

function nodeColor(d) {{
  return PAL_K[d.kind] || '#94a3b8';
}}

function drawGraph() {{
  g.selectAll('*').remove();

  const nodeMap = Object.fromEntries(activeNodes.values()
    ? NODES.filter(n => activeNodes.has(n.id)).map(n => [n.id, {{...n}}])
    : NODES.map(n => [n.id, {{...n}}]));

  const visibleNodes = Object.values(nodeMap);
  const visibleEdges = activeEdges
    .filter(e => nodeMap[e.source] && nodeMap[e.target])
    .map(e => ({{
      ...e,
      source: nodeMap[typeof e.source === 'object' ? e.source.id : e.source],
      target: nodeMap[typeof e.target === 'object' ? e.target.id : e.target],
    }}));

  // Links
  link = g.append('g').selectAll('line')
    .data(visibleEdges).join('line')
    .attr('class', 'link')
    .attr('stroke', d => d.level === 'paragraph' ? '#8b5cf6' : '#94a3b8')
    .attr('stroke-width', d => Math.max(0.8, d.weight * 0.8));

  // Nodes
  node = g.append('g').selectAll('g')
    .data(visibleNodes).join('g')
    .attr('class', 'node')
    .call(d3.drag()
      .on('start', (e, d) => {{ if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; }})
      .on('drag',  (e, d) => {{ d.fx=e.x; d.fy=e.y; }})
      .on('end',   (e, d) => {{ if (!e.active) simulation.alphaTarget(0); d.fx=null; d.fy=null; }}))
    .on('click', (e, d) => showPanel(d, visibleEdges))
    .on('mouseover', (e, d) => showTooltip(e, d))
    .on('mouseout', hideTooltip);

  node.append('circle')
    .attr('r', nodeR)
    .attr('fill', nodeColor)
    .attr('opacity', 0.85);

  // Labels for high-degree nodes
  const degree = {{}};
  visibleEdges.forEach(e => {{
    const sid = typeof e.source === 'object' ? e.source.id : e.source;
    const tid = typeof e.target === 'object' ? e.target.id : e.target;
    degree[sid] = (degree[sid]||0) + 1;
    degree[tid] = (degree[tid]||0) + 1;
  }});

  node.filter(d => (degree[d.id]||0) >= 3 || d.kind === 'person')
    .append('text')
    .attr('dy', d => nodeR(d) + 10)
    .text(d => d.label.split(',')[0].substring(0, 20));

  applyLayout(visibleNodes, visibleEdges);
  simulation.on('tick', () => {{
    link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
    node.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
  }});
}}

// ── Filtering ────────────────────────────────────────────────────────────────
function filterGraph() {{
  const q          = document.getElementById('search').value.toLowerCase();
  const edgeType   = document.getElementById('edge_type').value;
  const edgeLevel  = document.getElementById('edge_level').value;
  const minW       = +document.getElementById('min_weight').value / 10;
  const minDegSel  = document.getElementById('min_deg').value;
  const degThresh  = minDegSel === '0' ? 0
                   : (STATS.deg_percentiles?.[minDegSel] || 0);
  const showKinds  = new Set([
    document.getElementById('show_person').checked  ? 'person'       : null,
    document.getElementById('show_concept').checked ? 'concept'      : null,
    document.getElementById('show_org').checked     ? 'organisation' : null,
    document.getElementById('show_loc').checked     ? 'location'     : null,
  ].filter(Boolean));

  // Build allowed node set (degree + kind filters)
  const allowedNodes = new Set(
    NODES.filter(n =>
      showKinds.has(n.kind) &&
      (degThresh === 0 || (n.degree||0) >= degThresh)
    ).map(n => n.id)
  );

  activeEdges = EDGES.filter(e => {{
    if (edgeType  !== 'all' && e.type  !== edgeType)  return false;
    if (edgeLevel !== 'all' && e.level !== edgeLevel) return false;
    if (e.weight < minW) return false;
    const sid = typeof e.source==='object'?e.source.id:e.source;
    const tid = typeof e.target==='object'?e.target.id:e.target;
    if (!allowedNodes.has(sid)||!allowedNodes.has(tid)) return false;
    return true;
  }});

  if (q) {{
    const matchedIds = new Set(NODES
      .filter(n => n.label.toLowerCase().includes(q))
      .map(n => n.id));
    // Also include neighbors
    activeEdges.forEach(e => {{
      const sid = typeof e.source === 'object' ? e.source.id : e.source;
      const tid = typeof e.target === 'object' ? e.target.id : e.target;
      if (matchedIds.has(sid)) matchedIds.add(tid);
      if (matchedIds.has(tid)) matchedIds.add(sid);
    }});
    activeNodes = matchedIds;
    activeEdges = activeEdges.filter(e => {{
      const sid = typeof e.source === 'object' ? e.source.id : e.source;
      const tid = typeof e.target === 'object' ? e.target.id : e.target;
      return matchedIds.has(sid) && matchedIds.has(tid);
    }});
  }} else {{
    activeNodes = new Set(NODES.map(n => n.id));
  }}

  drawGraph();
}}

function updateForce() {{
  if (simulation) {{
    simulation.force('charge').strength(+document.getElementById('charge').value);
    simulation.alpha(0.3).restart();
  }}
}}

function resetZoom() {{
  svg.transition().duration(600).call(zoom.transform, d3.zoomIdentity);
}}

// ── Tooltip ───────────────────────────────────────────────────────────────────
const tip = document.getElementById('tooltip');
function showTooltip(e, d) {{
  tip.style.display = 'block';
  tip.style.left = (e.clientX + 12) + 'px';
  tip.style.top  = (e.clientY - 20) + 'px';
  tip.innerHTML = `<strong>${{d.label}}</strong><br>`
    + `Type: ${{d.kind}} · ${{d.n_books}} books`
    + (d.topic ? `<br>Topic: ${{d.topic}}` : '');
}}
function hideTooltip() {{ tip.style.display = 'none'; }}

// ── Side panel ────────────────────────────────────────────────────────────────
function showPanel(d, edges) {{
  const panel = document.getElementById('panel');
  document.getElementById('panel_title').textContent = d.label;

  const connected = edges.filter(e => {{
    const sid = typeof e.source === 'object' ? e.source.id : e.source;
    const tid = typeof e.target === 'object' ? e.target.id : e.target;
    return sid === d.id || tid === d.id;
  }}).map(e => {{
    const sid = typeof e.source === 'object' ? e.source.id : e.source;
    const tid = typeof e.target === 'object' ? e.target.id : e.target;
    const otherId = sid === d.id ? tid : sid;
    const other = NODES.find(n => n.id === otherId);
    return {{ weight: e.weight, overlap: e.overlap, level: e.level,
              type: e.type, other: other || {{label: otherId, kind:'?'}} }};
  }}).sort((a,b) => b.weight - a.weight).slice(0, 25);

  const kindColor = k => PAL_K[k] || '#94a3b8';

  document.getElementById('panel_body').innerHTML =
    `<p style="color:#64748b;font-size:.78rem;margin-bottom:.6rem">`
    + `${{d.kind}} · ${{d.n_books}} books`
    + (d.topic ? ` · ${{d.topic}}` : '') + `</p>`
    + `<p style="font-weight:600;margin-bottom:.4rem">Strongest associations (${{connected.length}})</p>`
    + connected.map(c => `
      <div class="edge-item">
        <span><span class="badge" style="background:${{kindColor(c.other.kind)}}">${{c.other.kind[0].toUpperCase()}}</span>
        ${{c.other.label.substring(0,30)}}</span>
        <span style="color:#64748b;font-size:.75rem">
          ${{c.weight.toFixed(2)}} · ${{c.overlap}} books · ${{c.level[0]}}
        </span>
      </div>`).join('');

  panel.style.display = 'block';
}}

function closePanel() {{
  document.getElementById('panel').style.display = 'none';
}}

// ── Network stats panel ──────────────────────────────────────────────────────
function buildStatsHTML() {{
  const S = STATS;
  const fmt = x => x == null ? 'N/A'
    : typeof x === 'number' ? x.toLocaleString(undefined,{{maximumFractionDigits:3}}) : x;
  const rows = [
    ['Nodes', fmt(S.n_nodes)],
    ['Edges', fmt(S.n_edges)],
    ['Persons', fmt(S.n_persons || {len(persons)})],
    ['Organisations', fmt(S.n_organisations || {len(organisations)})],
    ['Locations', fmt(S.n_locations || {len(locations)})],
    ['Concepts', fmt(S.n_concepts || {len(concepts)})],
    ['Density', S.density?.toExponential(2) ?? 'N/A'],
    ['Components', fmt(S.n_components)],
    ['Largest component', fmt(S.lcc_size) + ' nodes ('
      + ((S.lcc_fraction||0)*100).toFixed(0) + '%)'],
    ['Avg path length (sampled)', fmt(S.avg_path_length)],
    ['Diameter (sampled)', fmt(S.diameter)],
    ['Mean degree', fmt(S.avg_degree)],
    ['Max degree', fmt(S.max_degree)],
    ['Median degree (p50)', fmt(S.deg_percentiles?.p50)],
    ['p75', fmt(S.deg_percentiles?.p75)],
    ['p90', fmt(S.deg_percentiles?.p90)],
    ['p95', fmt(S.deg_percentiles?.p95)],
  ];
  const table = rows.map(([k,v]) =>
    `<div class='edge-item'><span style='color:#64748b'>${{k}}</span><strong>${{v}}</strong></div>`).join('');

  // Degree distribution bars
  const hist = S.deg_hist || [], bins = S.deg_hist_bins || [];
  const hmax = Math.max(...hist, 1);
  const bars = hist.map((c,i) =>
    `<div style='display:flex;align-items:center;gap:4px;font-size:.72rem;margin:.1rem 0'>
      <span style='width:36px;text-align:right;color:#94a3b8'>${{bins[i]}}</span>
      <div style='background:#2563eb;height:10px;border-radius:2px;min-width:2px;
        width:${{Math.round(c/hmax*130)}}px'></div>
      <span style='color:#475569'>${{c}}</span></div>`).join('');

  // Hub nodes
  const hubs = (S.hubs||[]).slice(0,12).map(h =>
    `<div class='edge-item'>
      <span><span class='badge' style='background:${{PAL_K[h.kind]||"#94a3b8"}}'>
        ${{h.kind[0].toUpperCase()}}</span> ${{h.label.substring(0,28)}}</span>
      <strong>${{h.degree}}</strong></div>`).join('');

  return `<p style='font-size:.75rem;color:#64748b;margin-bottom:.5rem'>
    Note: bipartite graph (persons ↔ concepts/locations only) —
    clustering coefficient is always 0 and not shown.</p>`
    + table
    + `<p style='font-weight:600;margin:.8rem 0 .3rem'>Degree distribution</p>`
    + bars
    + `<p style='font-weight:600;margin:.8rem 0 .3rem'>Top hubs by degree</p>`
    + hubs;
}}

function toggleStats() {{
  const p = document.getElementById('stats_panel');
  if (p.style.display === 'block') {{ p.style.display = 'none'; }}
  else {{
    document.getElementById('stats_body').innerHTML = buildStatsHTML();
    p.style.display = 'block';
  }}
}}


// ── Layout algorithms ────────────────────────────────────────────────────────
let currentLayout = 'force';

function switchLayout() {{
  // Clear pinned positions from previous layout
  if (node) node.each(d => {{ d.fx = null; d.fy = null; }});
  currentLayout = document.getElementById('layout_algo').value;
  filterGraph();
}}

function applyLayout(visibleNodes, visibleEdges) {{
  const W = canvas.offsetWidth || 1200;
  const H = canvas.offsetHeight || 700;
  const cx = W/2, cy = H/2;

  if (currentLayout === 'force') {{
    initSim(visibleNodes, visibleEdges);
    return;
  }}

  if (currentLayout === 'radial') {{
    // Concentric rings by kind — persons innermost
    const kindR = {{ person:W*0.13, organisation:W*0.22, location:W*0.22, concept:W*0.37 }};
    initSim(visibleNodes, visibleEdges);
    simulation
      .force('charge',   d3.forceManyBody().strength(-40))
      .force('link',     d3.forceLink(visibleEdges).id(d=>d.id).distance(35).strength(0.03))
      .force('radial',   d3.forceRadial(d => kindR[d.kind]||W*0.3, cx, cy).strength(0.85))
      .force('collide',  d3.forceCollide().radius(d => nodeR(d)+3))
      .alpha(1).restart();
    return;
  }}

  if (currentLayout === 'bipartite') {{
    // Two-column: persons left, concepts/orgs/locations right
    // Ranks by degree; auto-limits to top 100 per side for readability
    const TOP = 100;
    const leftNodes  = visibleNodes.filter(n=>n.kind==='person')
                         .sort((a,b)=>b.degree-a.degree).slice(0,TOP);
    const rightNodes = visibleNodes.filter(n=>n.kind!=='person')
                         .sort((a,b)=>b.degree-a.degree).slice(0,TOP);
    const xL=W*0.18, xR=W*0.82, pad=50;
    leftNodes.forEach((n,i) => {{
      n.fx=xL; n.fy=pad + i*(H-pad*2)/Math.max(leftNodes.length-1,1); }});
    rightNodes.forEach((n,i) => {{
      n.fx=xR; n.fy=pad + i*(H-pad*2)/Math.max(rightNodes.length-1,1); }});
    // Park remaining nodes off-canvas
    const shown = new Set([...leftNodes,...rightNodes].map(n=>n.id));
    visibleNodes.filter(n=>!shown.has(n.id)).forEach(n=>{{ n.fx=cx; n.fy=H*3; }});
    initSim(visibleNodes, visibleEdges);
    simulation
      .force('charge', d3.forceManyBody().strength(-5))
      .force('link',   d3.forceLink(visibleEdges).id(d=>d.id).distance(xR-xL).strength(0))
      .alpha(0.05).restart();
    return;
  }}

  if (currentLayout === 'circular') {{
    // Arc segments grouped by kind; nodes ordered by degree within arc
    // Persons: left semicircle  Concepts: right-bottom quadrant
    // Orgs: top-right arc       Locations: bottom-right arc
    const R = Math.min(W,H)*0.39;
    const arcMap = {{
      person:       [0,           Math.PI],
      concept:      [Math.PI,     1.5*Math.PI],
      organisation: [1.5*Math.PI, 1.83*Math.PI],
      location:     [1.83*Math.PI,2*Math.PI],
    }};
    const byKind={{}};
    visibleNodes.forEach(n=>{{ if(!byKind[n.kind])byKind[n.kind]=[]; byKind[n.kind].push(n); }});
    Object.entries(byKind).forEach(([kind,knodes])=>{{
      const [a0,a1]=arcMap[kind]||[0,2*Math.PI];
      knodes.sort((a,b)=>b.degree-a.degree);
      knodes.forEach((n,i)=>{{
        const frac = knodes.length===1?0.5:i/(knodes.length-1);
        n.fx = cx + R*Math.cos(a0+frac*(a1-a0));
        n.fy = cy + R*Math.sin(a0+frac*(a1-a0));
      }});
    }});
    initSim(visibleNodes, visibleEdges);
    simulation
      .force('charge', d3.forceManyBody().strength(-3))
      .force('link',   d3.forceLink(visibleEdges).id(d=>d.id).distance(10).strength(0.01))
      .force('center', null)
      .alpha(0.03).restart();
    return;
  }}
}}

// ── Initial render ──────────────────────────────────────────────────────────
filterGraph();
</script>
</body>
</html>"""

html = html.replace('</body>', _PROV_NOTICE + '\n</body>', 1)
os.makedirs('data/outputs', exist_ok=True)
out = 'data/outputs/book_nlp_entity_network.html'
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Saved: {out}  ({len(html)//1024} KB)")
