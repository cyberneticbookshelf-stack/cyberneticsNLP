import json, re, sys, math, numpy as np, pandas as pd
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity

# ── Stopwords (manual, since nltk unavailable) ──────────────────────────────
# Data-quality fixes (v0.4.1):
#   - Stopword list expanded with academic boilerplate terms (author, paper,
#     journal, review, result, study, approach, proposed, based, show, etc.)
#     that were inflating TF-IDF scores for generic academic prose.
#   - tokenize() now joins hyphenated compounds before stripping punctuation
#     ('self-organising' → 'selforganising') so they survive as single features
#     rather than being split into short fragments that are then discarded.
#   - sampled texts passed through _join_hyphens() before TF-IDF and LDA
#     vectorisation to keep the pre-processing consistent with tokenize().

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_metadata_full.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


STOPWORDS = set("""
a about above after again against all also am an and any are aren't as at
be because been before being below between both but by can't cannot could
couldn't did didn't do does doesn't doing don't down during each few for
from further get go had hadn't has hasn't have haven't having he he'd he'll
he's her here here's hers herself him himself his how how's i i'd i'll i'm
i've if in into is isn't it it's its itself let's me more most mustn't my
myself no nor not of off on once only or other ought our ours ourselves out
over own same shan't she she'd she'll she's should shouldn't so some such
than that that's the their theirs them themselves then there there's these
they they'd they'll they're they've this those through to too under until up
very was wasn't we we'd we'll we're we've were weren't what what's when
when's where where's which while who who's whom why why's will with won't
would wouldn't you you'd you'll you're you've your yours yourself yourselves
also may thus hence therefore however moreover furthermore indeed whereas
whether although though since upon within without toward towards one two
three four five six seven eight nine ten use used using well just like even
many much first second third new old p pp cited ibid et al chapter book
fig figure table see also note notes chapter chapters vol volume edition
ed eds press university oxford cambridge london new york
author authors paper papers journal journals review reviews
research study studies approach proposed based show shown
result results finding findings suggest suggests suggested
present presented discuss discussed discuss analysis analyse
across following given thus within despite recent
give gives given take takes taken make makes made come comes
came seem seems seemed need needs needed know knows knew
think thinks thought want wants wanted call called become
becomes became keep keeps kept show shows showed turn turns
turned leave leaves left move moves moved back still around
must past example something great thing things page pages
good best better true large small possible general certain
google digitize digitized digitised original california
university california digitized google original
""".split())

# ── CLI flags ────────────────────────────────────────────────────────────────
WEIGHTED     = '--weighted'     in sys.argv
NAME_TOPICS  = '--name-topics'  in sys.argv

# --full-text: use the full book body (front/back-matter stripped) as LDA input
# instead of the default 3-point 60k-char sample. Intended for server-class
# machines (Cybersonic) with ample RAM. Increases vocabulary coverage and LDA
# signal quality at the cost of longer vectorisation and fitting time.
# Combine with --max-features to expand the vocabulary beyond the default 3000.
# Example: python3 src/03_nlp_pipeline.py --full-text --max-features 15000 \
#                                          --topics 9 --seeds 5
FULL_TEXT = '--full-text' in sys.argv
if FULL_TEXT:
    print('  [--full-text] Full body text mode — front/back-matter will be stripped')

# --max-features N: vocabulary size for TF-IDF and CountVectorizer.
# Default: 3000 (preserves backward compatibility for laptop runs).
# Recommended for --full-text runs: 10000–20000 (more signal, more RAM needed).
# With 695 books and 15000 features the count matrix is still sparse and
# comfortably within 16 GB RAM.
_MAX_FEATURES = 3000
if '--max-features' in sys.argv:
    try:
        _MAX_FEATURES = int(sys.argv[sys.argv.index('--max-features') + 1])
        print(f'  [--max-features] vocabulary size set to {_MAX_FEATURES:,}')
    except (IndexError, ValueError):
        print('  [--max-features] usage: --max-features N  (integer)')

# --gpu: use RAPIDS cuML for LDA fitting (CUDA required).
# Accelerates the final model fit and --seeds stability runs. The coherence
# sweep (k-selection) still runs on sklearn/CPU because cuML LDA does not
# expose a perplexity() method. Falls back to sklearn automatically if cuML
# or CuPy is not installed.
# Install: conda install -c rapidsai cuml cudatoolkit=12.x
# Example: python3 src/03_nlp_pipeline.py --full-text --gpu --topics 9 --seeds 5
GPU = '--gpu' in sys.argv
_cuLDA = None
if GPU:
    try:
        import cupy as _cp
        import cupyx.scipy.sparse as _cpsp
        from cuml.decomposition import LatentDirichletAllocation as _cuLDA
        print('  [--gpu] cuML + CuPy loaded — LDA fitting will use GPU')
    except ImportError as _e:
        print(f'  [--gpu] WARNING: cuML/CuPy not available ({_e}) — '
              f'falling back to sklearn (CPU)')
        GPU = False
        _cuLDA = None

# --topics N: override the automatic k selection for LDA
_FIXED_TOPICS = None
if '--topics' in sys.argv:
    try:
        _FIXED_TOPICS = int(sys.argv[sys.argv.index('--topics') + 1])
        print(f'  [--topics] fixed at {_FIXED_TOPICS}')
    except (IndexError, ValueError):
        print('  [--topics] usage: --topics N  (integer)')

# --min-chars N: exclude books with fewer than N chars of clean text.
# Useful for filtering source-extraction failures (empty or near-empty books)
# without permanently removing them from books_clean.json.
# Default: 0 (no filtering). Recommended: 10000 when known bad books exist.
# Example: python3 src/03_nlp_pipeline.py --min-chars 10000
_MIN_CHARS = 0
if '--min-chars' in sys.argv:
    try:
        _MIN_CHARS = int(sys.argv[sys.argv.index('--min-chars') + 1])
        print(f'  [--min-chars] excluding books with < {_MIN_CHARS:,} chars clean text')
    except (IndexError, ValueError):
        print('  [--min-chars] usage: --min-chars N  (integer)')

# --lemmatize: apply spaCy lemmatisation to texts before vectorisation.
# Collapses inflected forms to base forms ('systems' → 'system',
# 'organising' → 'organise') while preserving readability — unlike stemming
# which produces uninterpretable truncations ('cybernetics' → 'cybernet').
# Requires spaCy en_core_web_sm: python -m spacy download en_core_web_sm
# Timing: ~2-5 min for 695 books at 60k chars/book (default sample).
#         ~20-50 min for 695 books at full body text (~500k chars/book).
#         Use --lemmatize with --full-text only on Cybersonic or equivalent.
LEMMATIZE = '--lemmatize' in sys.argv
if LEMMATIZE:
    try:
        import spacy as _spacy
        _nlp = _spacy.load('en_core_web_sm', disable=['parser', 'ner'])
        print('  [--lemmatize] spaCy en_core_web_sm loaded — lemmatising texts')
    except OSError:
        print('  [--lemmatize] ERROR: en_core_web_sm not found.')
        print('  Run: python -m spacy download en_core_web_sm')
        import sys as _sys; _sys.exit(1)
    except ImportError:
        print('  [--lemmatize] ERROR: spaCy not installed.')
        print('  Run: pip install spacy && python -m spacy download en_core_web_sm')
        import sys as _sys; _sys.exit(1)

# --seeds N: run LDA N times with different random seeds and compute topic
# stability scores (mean Jaccard similarity of top-10 words across runs,
# aligned via the Hungarian algorithm). Writes topic_stability.json.
# Only meaningful when used with --topics to fix k.
# Example: python3 src/03_nlp_pipeline.py --topics 20 --seeds 5 --lemmatize
_N_SEEDS = 1
if '--seeds' in sys.argv:
    try:
        _N_SEEDS = max(2, int(sys.argv[sys.argv.index('--seeds') + 1]))
        print(f'  [--seeds] running {_N_SEEDS} LDA seeds for stability analysis')
        if _FIXED_TOPICS is None:
            print('  [--seeds] WARNING: --seeds is most useful with --topics N '
                  'to fix k; auto-selection may choose different k per seed')
    except (IndexError, ValueError):
        print('  [--seeds] usage: --seeds N  (integer ≥ 2)')

# --run-id ID: suffix appended to all output filenames, enabling concurrent runs
# without clobbering each other's results.
#   nlp_results.json       → nlp_results_<ID>.json
#   topic_stability.json   → topic_stability_<ID>.json
# Use a short descriptive tag, e.g. --run-id k8 or --run-id sweep or --run-id ft_k12
# Example (three concurrent terminals):
#   python3 src/03_nlp_pipeline.py --full-text --topics  8 --seeds 5 --run-id k8   &
#   python3 src/03_nlp_pipeline.py --full-text --topics 12 --seeds 5 --run-id k12  &
#   python3 src/03_nlp_pipeline.py --full-text            --seeds 5 --run-id sweep &
_RUN_ID = ''
if '--run-id' in sys.argv:
    try:
        _RUN_ID = sys.argv[sys.argv.index('--run-id') + 1].strip()
        print(f'  [--run-id] output suffix: _{_RUN_ID}')
    except (IndexError, ValueError):
        print('  [--run-id] usage: --run-id ID  (short string, no spaces)')

def _out(stem: str) -> str:
    """Return JSON_DIR / stem[_RUN_ID].json, e.g. 'nlp_results_k8.json'."""
    suffix = f'_{_RUN_ID}' if _RUN_ID else ''
    return str(JSON_DIR / f'{stem}{suffix}.json')

# ── Index-term weight builder ─────────────────────────────────────────────────
def build_index_weights(feature_names, index_analysis_path=str(JSON_DIR / 'index_analysis.json'),
                        topic_grounding_path=str(JSON_DIR / 'topic_index_grounding.json')):
    """
    Assign a relevance multiplier to each TF-IDF feature using index-term
    lift scores (how strongly each term characterises a specific topic).

    Formula: w = 1.0 + (sigmoid_lift - 1.0) * reliability
      sigmoid_lift  = 1 + 2*(1 - 1/(1+(lift-1)^1.5))  [maps lift → 1..3]
      reliability   = sqrt(min(n_books, 20) / 20)     [dampens small-n terms]

    Result:
      Anchor terms  (uniform across topics, high n): w ≈ 1.0–1.7x
      Signal terms  (topic-specific, moderate n):    w ≈ 1.7–2.8x
      Frontier terms(topic-specific, small n):       w ≈ 1.2–2.0x
      Generic noise (low lift, any n):               w = 1.0x
    """
    try:
        with open(index_analysis_path) as f:
            IA = json.load(f)
    except FileNotFoundError:
        print(f'  [--weighted] {index_analysis_path} not found — running unweighted')
        return np.ones(len(feature_names))

    vocab      = IA['vocab']
    dom_topics = None
    # Load dominant_topics for global fraction computation
    try:
        with open(str(JSON_DIR / 'nlp_results.json')) as f:
            prev = json.load(f)
        dom_topics = prev['dominant_topics']
    except Exception:
        pass

    if dom_topics is None:
        print('  [--weighted] no nlp_results.json yet; using flat weights first run')
        # First run: use n_books-based Gaussian (no lift available)
        weights = np.ones(len(feature_names))
        for i, f in enumerate(feature_names):
            v = vocab.get(f)
            if v and v['n_books'] >= 2:
                n = v['n_books']
                # Gaussian peak at n=5 (Signal midpoint)
                weights[i] = 1.0 + 2.0 * math.exp(-((n - 5) / 2.0) ** 2)
        return weights

    N = len(dom_topics)
    global_frac = defaultdict(float)
    for t in dom_topics:
        global_frac[t] += 1.0 / N

    def max_lift(v):
        td    = v['topic_dist']
        total = sum(td.values())
        if total < 3: return 0.0
        return max((c / total) / max(global_frac[int(t)], 0.001)
                   for t, c in td.items())

    def sigmoid_lift(lift):
        if lift <= 1.0: return 1.0
        return min(1.0 + 2.0 * (1 - 1.0 / (1 + (lift - 1) ** 1.5)), 3.0)

    weights = np.ones(len(feature_names))
    for i, f in enumerate(feature_names):
        v = vocab.get(f)
        if v and v['n_books'] >= 2:
            n           = v['n_books']
            lift        = max_lift(v)
            reliability = math.sqrt(min(n, 20) / 20.0)
            w_lift      = sigmoid_lift(lift)
            weights[i]  = 1.0 + (w_lift - 1.0) * reliability
    return weights

def tokenize(text):
    text = text.lower()
    # FIX: join hyphenated compounds before stripping punctuation so that
    # 'self-organising' → 'selforganising' rather than 'self' + 'organising'
    # (both fragments are too short or too generic to be useful features).
    # The joined form is then treated as a single token by TF-IDF.
    text = re.sub(r'([a-z])-([a-z])', r'\1\2', text)
    text = re.sub(r'[^a-z\s]', ' ', text)
    tokens = [w for w in text.split() if len(w) > 3 and w not in STOPWORDS]
    return tokens

# ── Load data ────────────────────────────────────────────────────────────────

# ── Verify working directory has required data files ────────────────────────
import os as _os
if not _os.path.exists(str(JSON_DIR / 'books_clean.json')):
    print('ERROR: books_clean.json not found in current directory.')
    print(f'Run this script from your project root, not from {_os.getcwd()}')
    print('Example: cd /path/to/project && python3 src/generate_summaries_api.py')
    import sys as _sys; _sys.exit(1)

with open(str(JSON_DIR / 'books_clean.json')) as f:
    books = json.load(f)

book_ids   = list(books.keys())

# ── Publication type filter ───────────────────────────────────────────────────
# Inclusion rule: include if pub_type contains 'monograph' OR 'collected works'.
# Publication types are non-disjoint — a book may carry multiple labels
# (e.g. "monograph, textbook"). The presence of either anchor type is sufficient
# for inclusion, regardless of other labels on the same book.
# Source: manually assigned Calibre custom column 5 (Publication Type),
# exported into books_metadata_full.csv by 00_export_calibre.py.
_INCLUDE_TYPES = {'monograph', 'collected works'}
_pubtype_map = {}  # bid → raw pub_type string
_meta_path = CSV_DIR / 'books_metadata_full.csv'
if _meta_path.exists():
    import csv as _csv
    with open(str(_meta_path), encoding='utf-8') as _mf:
        for _row in _csv.DictReader(_mf, delimiter='\t'):
            _bid = _row['id'].strip()
            _pt  = _row.get('pub_type', '').strip().lower()
            if _pt:
                _pubtype_map[_bid] = _pt
    if _pubtype_map:
        _before = len(book_ids)
        def _is_included(bid):
            pt = _pubtype_map.get(bid, '')
            if not pt:
                return True   # no label → include (safe default)
            parts = [p.strip() for p in pt.replace(';', ',').split(',')]
            return any(p in _INCLUDE_TYPES for p in parts)
        _pubtype_excluded = [b for b in book_ids if not _is_included(b)]
        book_ids = [b for b in book_ids if _is_included(b)]
        print(f"  [pub-type] excluded {len(_pubtype_excluded)} books "
              f"(no 'monograph' or 'collected works' label)  "
              f"({_before} → {len(book_ids)})")
        for bid in _pubtype_excluded:
            print(f"    excluded: [{bid}] ({_pubtype_map.get(bid,'?')}) "
                  f"{books[bid]['title'][:55]}")
    else:
        print("  [pub-type] pub_type column not found in books_metadata_full.csv "
              "— run 00_export_calibre.py to include it")
else:
    print("  [pub-type] books_metadata_full.csv not found — pub-type filter skipped")

# Apply --min-chars filter if set
if _MIN_CHARS > 0:
    before = len(book_ids)
    book_ids = [b for b in book_ids if len(books[b]['clean_text']) >= _MIN_CHARS]
    excluded = before - len(book_ids)
    print(f"  [--min-chars] excluded {excluded} books < {_MIN_CHARS:,} chars "
          f"({before} → {len(book_ids)})")
    if excluded > 0:
        excl_ids = [b for b in books if len(books[b]['clean_text']) < _MIN_CHARS]
        for bid in excl_ids:
            print(f"    excluded: [{bid}] {books[bid]['title'][:60]}")

# Alpha-ratio filter: exclude books whose clean text is predominantly non-alphabetic.
# Catches OCR-failure books that cleared the min-chars threshold with garbage content
# (e.g. Luhmann's Ecological Communication [1262] — 27k chars of pure OCR noise).
#
# Sampling strategy: skip the first 10% of the text (front matter — copyright
# pages, series information, publisher metadata, Cyrillic OCR fragments from
# translated works) and draw three evenly-spaced 5,000-char windows from the
# remaining body. Average alpha across windows for a robust estimate.
# This fixes false exclusions for [205], [265], [413], [597], [1261], [1918]
# whose front matter dragged the first-5000-char sample below threshold despite
# good body text (alpha 0.75+ over full text).
MIN_ALPHA_RATIO = 0.40
before = len(book_ids)
def _alpha_ratio(text, sample=5000, n_windows=3):
    n = len(text)
    if n < sample: return sum(c.isalpha() for c in text) / n if n else 0.0
    # Skip first 10% — front matter is unreliable
    start = max(sample, n // 10)
    body  = text[start:]
    if len(body) < sample:
        s = body
        return sum(c.isalpha() for c in s) / len(s)
    # Draw n evenly-spaced windows across the body
    step = (len(body) - sample) // max(n_windows - 1, 1)
    ratios = []
    for i in range(n_windows):
        offset = i * step
        window = body[offset:offset + sample]
        ratios.append(sum(c.isalpha() for c in window) / len(window))
    return sum(ratios) / len(ratios)

low_alpha = [b for b in book_ids if _alpha_ratio(books[b]['clean_text']) < MIN_ALPHA_RATIO]
if low_alpha:
    book_ids = [b for b in book_ids if b not in set(low_alpha)]
    print(f"  [alpha-ratio] excluded {len(low_alpha)} books with <{MIN_ALPHA_RATIO:.0%} "
          f"alphabetic content ({before} → {len(book_ids)})")
    for bid in low_alpha:
        ratio = _alpha_ratio(books[bid]['clean_text'])
        print(f"    excluded: [{bid}] {books[bid]['title'][:60]}  (alpha={ratio:.2f})")

# ── Explicit OCR exclusion list ───────────────────────────────────────────────
# Books that pass heuristic filters (min-chars, alpha-ratio) but have
# confirmed OCR quality issues that make them unsuitable for analysis.
# Add book IDs here as strings when a book is known-bad and cannot be fixed.
# See also: generate_summaries_api.py — books excluded here should also be
# absent from summaries.json (they will not be summarised).
OCR_EXCLUDED = {
    '2133',  # Cybernation and Social Change (Donald N. Michael) — confirmed OCR failure
}
_ocr_before = len(book_ids)
book_ids = [b for b in book_ids if b not in OCR_EXCLUDED]
if _ocr_before > len(book_ids):
    n = _ocr_before - len(book_ids)
    print(f"  [ocr-excluded] excluded {n} book(s) from explicit exclusion list "
          f"({_ocr_before} → {len(book_ids)})")
    for bid in OCR_EXCLUDED:
        if bid in books:
            print(f"    excluded: [{bid}] {books[bid]['title'][:60]}")

titles     = [books[b]['title'] for b in book_ids]
authors    = [books[b]['author'] for b in book_ids]

# ── Text preparation: sample mode (default) ──────────────────────────────────
# Multi-point sampling: three 20k-char slices (early/middle/late) concatenated.
# Total sample = 60k chars (~12,000 words); representative of whole book
# without front-matter traps.
# Slice positions: 10% (past front matter), 50% (argumentative core), 85%
# (conclusions). Minimum offset of 4000 chars avoids publisher/copyright pages.
# Use this mode on laptop/desktop. For server runs use --full-text instead.
SLICE_LEN = 20000

def sample_book(text):
    n = len(text)
    offsets = [max(int(n * p), 4000) for p in (0.10, 0.50, 0.85)]
    slices = [text[o: o + SLICE_LEN] for o in offsets]
    return ' '.join(slices)

# ── Text preparation: full-text mode (--full-text) ───────────────────────────
# Strip front matter (copyright pages, TOC, dedication, preface) and back
# matter (references/bibliography, index) to produce a clean body text.
# Designed for server-class machines (Cybersonic) with ample RAM.
#
# Front-matter strategy:
#   After a minimum safe offset (FRONT_SKIP_MIN_CHARS), scan for the first
#   strong body-text marker (chapter heading, "Introduction", etc.).
#   If no marker is found within the first 30% of the text, fall back to
#   skipping FRONT_SKIP_FRAC of the text length.
#
# Back-matter strategy:
#   Find the LAST occurrence of a section heading that indicates back matter
#   (References, Bibliography, Index, etc.) at least BACK_MIN_FRAC into the
#   text (to avoid false positives early in the body). Truncate there.
#
# Both functions return (stripped_text, chars_removed) for logging.

FRONT_SKIP_MIN_CHARS = 3000    # Never start before this offset
FRONT_SKIP_FRAC      = 0.05    # Fallback: skip first 5% if no body marker found
BACK_MIN_FRAC        = 0.50    # Only truncate if back-matter marker ≥ 50% in

# Body-text start markers — first occurrence past FRONT_SKIP_MIN_CHARS
# Matches "Chapter One", "Chapter 1", "Part I", "Introduction", "Prologue",
# or a bare chapter-number line (e.g. "1\n" or "I\n").
_BODY_START_RE = re.compile(
    r'^\s*(?:'
    r'chapter\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|'
    r'eleven|twelve|[1-9][0-9]?)\b'
    r'|part\s+(?:one|two|three|i{1,4}|v?i{0,3}|[1-9])\b'
    r'|introduction\b'
    r'|prologue\b'
    r'|[1-9][0-9]?\s*\n'     # bare chapter number on its own line
    r')',
    re.IGNORECASE | re.MULTILINE
)

# Back-matter section headings — we find the LAST occurrence past BACK_MIN_FRAC.
# Matches headings that are essentially alone on their line (end-of-line anchored)
# to avoid matching mid-paragraph phrases like "see references above".
_BACK_START_RE = re.compile(
    r'^\s*(?:'
    r'references?\s*$'
    r'|bibliography\s*$'
    r'|works\s+cited\s*$'
    r'|further\s+reading\s*$'
    r'|notes?\s+and\s+references?\s*$'
    r'|selected\s+bibliography\s*$'
    r'|bibliographical\s+notes?\s*$'
    r'|index\s*$'
    r'|general\s+index\s*$'
    r'|subject\s+index\s*$'
    r'|author\s+index\s*$'
    r'|name\s+index\s*$'
    r')',
    re.IGNORECASE | re.MULTILINE
)


def strip_front_matter(text: str):
    """
    Remove front matter from cleaned book text.

    Returns (body_text, chars_skipped).

    Strategy:
      1. Scan for the first body-text marker (chapter heading, Introduction,
         etc.) after FRONT_SKIP_MIN_CHARS. If found within the first 30% of
         text, start there.
      2. Otherwise fall back to skipping max(FRONT_SKIP_MIN_CHARS,
         FRONT_SKIP_FRAC * len(text)).
    """
    n = len(text)
    m = _BODY_START_RE.search(text, FRONT_SKIP_MIN_CHARS)
    if m and m.start() < n * 0.30:
        return text[m.start():], m.start()
    offset = max(FRONT_SKIP_MIN_CHARS, int(n * FRONT_SKIP_FRAC))
    return text[offset:], offset


def strip_back_matter(text: str):
    """
    Remove back matter (bibliography, references, index) from cleaned book text.

    Returns (body_text, chars_removed).

    Strategy:
      Find the LAST occurrence of a back-matter heading that appears at least
      BACK_MIN_FRAC into the text. Truncate there. If none found, return text
      unchanged.
    """
    n = len(text)
    min_offset = int(n * BACK_MIN_FRAC)
    last_match = None
    for m in _BACK_START_RE.finditer(text):
        if m.start() >= min_offset:
            last_match = m
    if last_match:
        return text[:last_match.start()], n - last_match.start()
    return text, 0


def prepare_full_text(text: str):
    """
    Apply front- and back-matter stripping to produce a clean body text.

    Returns (body_text, stats_dict).
    stats keys: original_chars, front_stripped, back_stripped,
                body_chars, body_pct.
    """
    original_chars = len(text)
    stripped_front, front_chars = strip_front_matter(text)
    stripped_body,  back_chars  = strip_back_matter(stripped_front)
    body_chars = len(stripped_body)
    stats = {
        'original_chars': original_chars,
        'front_stripped':  front_chars,
        'back_stripped':   back_chars,
        'body_chars':      body_chars,
        'body_pct':        round(100 * body_chars / original_chars, 1)
                           if original_chars else 0,
    }
    return stripped_body, stats


# ── Apply text preparation ────────────────────────────────────────────────────
if FULL_TEXT:
    print(f"\n  [--full-text] Preparing body texts for {len(book_ids)} books...")
    texts = []
    ft_stats_list = []
    for i, b in enumerate(book_ids, 1):
        body, stats = prepare_full_text(books[b]['clean_text'])
        texts.append(body)
        ft_stats_list.append(stats)
        if i <= 5 or i % 100 == 0:          # print first 5 then every 100
            print(f"    [{b}] {books[b]['title'][:45]:45s}  "
                  f"orig={stats['original_chars']//1000:4d}k  "
                  f"body={stats['body_chars']//1000:4d}k  "
                  f"({stats['body_pct']}%)  "
                  f"-front={stats['front_stripped']//1000}k  "
                  f"-back={stats['back_stripped']//1000}k")
    mean_body = int(np.mean([s['body_chars'] for s in ft_stats_list]))
    mean_orig = int(np.mean([s['original_chars'] for s in ft_stats_list]))
    mean_pct  = round(np.mean([s['body_pct'] for s in ft_stats_list]), 1)
    print(f"  [--full-text] Mean body: {mean_body//1000}k chars  "
          f"(mean original: {mean_orig//1000}k chars, {mean_pct}% retained)")
else:
    texts = [sample_book(books[b]['clean_text']) for b in book_ids]

# ── Lemmatisation (--lemmatize) ───────────────────────────────────────────────
def _lemmatise_text(text, nlp, batch_size=50):
    """
    Lemmatise a text string using spaCy.
    Processes in 10k-char chunks to avoid spaCy's max_length limit.
    Returns a string of space-joined lemmas, filtering punctuation and
    whitespace tokens. Preserves the token stream for TF-IDF input.
    """
    chunks = [text[i:i+10000] for i in range(0, len(text), 10000)]
    lemmas = []
    for doc in nlp.pipe(chunks, batch_size=batch_size):
        lemmas.extend(
            token.lemma_.lower()
            for token in doc
            if not token.is_punct and not token.is_space and len(token.lemma_) > 1
        )
    return ' '.join(lemmas)

if LEMMATIZE:
    print(f"  Lemmatising {len(texts)} texts (this may take a while)...")
    texts = [_lemmatise_text(t, _nlp) for i, t in enumerate(texts, 1)
             if not print(f"    {i}/{len(texts)}", end='\r') or True]
    print()

print(f"Processing {len(texts)} books...")

# ── 1. TF-IDF Vectorisation ──────────────────────────────────────────────────
# FIX: token_pattern updated from [a-zA-Z]{4,} to [a-zA-Z]{4,} — hyphens are
# now pre-joined in sample_book text via a pre-processing step so the pattern
# does not need to handle them; but we apply the same hyphen-join to the sampled
# texts before vectorisation to ensure TF-IDF and tokenize() are consistent.
def _join_hyphens(text):
    """Join hyphenated compounds: 'self-organising' → 'selforganising'."""
    return re.sub(r'([a-zA-Z])-([a-zA-Z])', r'\1\2', text)

texts = [_join_hyphens(t) if not LEMMATIZE else t for t in texts]

tfidf = TfidfVectorizer(max_features=_MAX_FEATURES, stop_words=list(STOPWORDS),
                        ngram_range=(1,2), min_df=2, max_df=0.95,
                        token_pattern=r'(?u)\b[a-zA-Z]{4,}\b')
X_tfidf = tfidf.fit_transform(texts)
feature_names = tfidf.get_feature_names_out()
print(f"TF-IDF matrix: {X_tfidf.shape}")

# Apply index-term weighting if --weighted flag is set
if WEIGHTED:
    print("\n[--weighted] Building index-term weight vector...")
    iw = build_index_weights(feature_names)
    X_tfidf = X_tfidf.multiply(iw)
    n_boosted = (iw > 1.05).sum()
    print(f"  Boosted {n_boosted}/{len(feature_names)} features  "
          f"(mean boost on boosted: {iw[iw>1.05].mean():.2f}x  "
          f"max: {iw.max():.2f}x)")

# ── 2. LDA Topic Modelling ───────────────────────────────────────────────────
# Build a unigram count matrix for coherence scoring (NPMI over co-occurrences)
# and a separate TF-IDF count matrix for LDA fitting.
cv = CountVectorizer(max_features=_MAX_FEATURES, stop_words=list(STOPWORDS),
                     ngram_range=(1,1), min_df=2, max_df=0.95,
                     token_pattern=r'(?u)\b[a-zA-Z]{4,}\b')
X_count   = cv.fit_transform(texts)
cv_vocab  = cv.get_feature_names_out()
vocab_idx = {w: i for i, w in enumerate(cv_vocab)}

# Binary document-term matrix and document frequencies for NPMI
X_bin = (X_count > 0).astype(float)
N_docs = X_bin.shape[0]
df    = np.asarray(X_bin.sum(axis=0)).flatten()

from itertools import combinations

def npmi_coherence(top_words, X_bin, df, vocab_idx, N, eps=1.0):
    """Mean NPMI for all pairs of top words (higher = more coherent)."""
    indices = [vocab_idx[w] for w in top_words if w in vocab_idx]
    if len(indices) < 2:
        return 0.0
    scores = []
    for i, j in combinations(indices, 2):
        df_i  = df[i] + eps
        df_j  = df[j] + eps
        df_ij = float(X_bin[:, i].toarray().flatten() @
                      X_bin[:, j].toarray().flatten()) + eps
        pmi   = np.log(df_ij * N / (df_i * df_j))
        denom = -np.log(df_ij / N)
        scores.append(pmi / denom if denom != 0 else 0.0)
    return float(np.mean(scores))

# ── k-selection sweep (always CPU / sklearn) ─────────────────────────────────
# The coherence sweep runs on sklearn regardless of --gpu because cuML LDA
# does not expose a perplexity() or coherence method. The GPU is used only
# for the final model fit and the --seeds stability runs.
# FIX: if --topics N is set and N > N_TOPICS_MAX, extend the sweep to include N
# so perplexity/coherence are recorded for it and the override fires correctly.
N_TOPICS_MIN = 2
N_TOPICS_MAX = min(12, max(3, len(book_ids) // 2))
if _FIXED_TOPICS is not None and _FIXED_TOPICS > N_TOPICS_MAX:
    N_TOPICS_MAX = _FIXED_TOPICS
    print(f"  [--topics] extending sweep to k={N_TOPICS_MAX} to include forced value")

best_n, best_coh, best_lda = None, -np.inf, None
perplexities, coherences = {}, {}

print(f"\n{'k':<5} {'perplexity':<14} {'coherence'}")
for n_topics in range(N_TOPICS_MIN, N_TOPICS_MAX + 1):
    lda = LatentDirichletAllocation(n_components=n_topics, max_iter=20,
                                    learning_method='online', random_state=99,
                                    learning_offset=50., doc_topic_prior=0.1)
    lda.fit(X_count)
    perp = lda.perplexity(X_count)
    perplexities[n_topics] = round(perp, 1)
    # Top 10 unigrams per topic for coherence scoring
    top_words_coh = []
    for t in range(n_topics):
        top_idx = lda.components_[t].argsort()[-10:][::-1]
        words   = [cv_vocab[i] for i in top_idx if ' ' not in cv_vocab[i]][:10]
        top_words_coh.append(words)
    coh = float(np.mean([npmi_coherence(tw, X_bin, df, vocab_idx, N_docs)
                         for tw in top_words_coh]))
    coherences[n_topics] = round(coh, 4)
    print(f"  k={n_topics:<3} perplexity={perp:<10.1f} coherence={coh:.4f}")
    if coh > best_coh:
        best_coh, best_n, best_lda = coh, n_topics, lda

# FIX: override condition no longer requires _FIXED_TOPICS in perplexities —
# the sweep above now always includes it when --topics N is set.
if _FIXED_TOPICS is not None:
    best_n = _FIXED_TOPICS
    best_coh = coherences.get(best_n, 0.0)
    print(f'\n[--topics] Fitting final model at forced n_topics={best_n} '
          f'(coherence={best_coh:.4f}, perplexity={perplexities.get(best_n, 0):.1f})')
else:
    print(f"\nBest n_topics={best_n} (highest coherence={best_coh:.4f}, "
          f"perplexity={perplexities[best_n]:.1f})")

# ── Final model fit (GPU if --gpu, else sklearn) ──────────────────────────────
# If --gpu is set and cuML loaded successfully, fit the final model on GPU.
# The count matrix is converted to a CuPy sparse array for cuML. cuML LDA
# uses the same online learning approach as sklearn but dispatches to CUDA
# for the E-step and M-step matrix operations.
#
# cuML LDA note: max_iter here corresponds to n_components in cuML ≥ 24.06.
# If you see an API error, check your cuML version:
#   python -c "import cuml; print(cuml.__version__)"
# Confirmed working: cuML 24.06+  (RAPIDS 24.06).
def _fit_lda_gpu(n_topics, X_count_sparse, random_state=99):
    """Fit LDA on GPU via cuML. Returns a fitted cuML LDA object."""
    import cupy as cp
    import cupyx.scipy.sparse as cpsp
    X_gpu = cpsp.csr_matrix(X_count_sparse.astype(np.float32))
    lda_gpu = _cuLDA(
        n_components=n_topics,
        max_iter=20,
        learning_method='online',
        random_state=random_state,
        learning_offset=50.,
        doc_topic_prior=0.1,
    )
    lda_gpu.fit(X_gpu)
    return lda_gpu, X_gpu


def _transform_lda_gpu(lda_gpu, X_gpu):
    """Return doc-topic matrix from a fitted cuML LDA (as numpy array)."""
    import cupy as cp
    return cp.asnumpy(lda_gpu.transform(X_gpu))


if GPU and _cuLDA is not None:
    print(f'\n[--gpu] Fitting final LDA (k={best_n}) on GPU...')
    try:
        best_lda_gpu, X_count_gpu = _fit_lda_gpu(best_n, X_count)
        # Extract components as numpy for downstream use
        import cupy as _cp_main
        best_components = _cp_main.asnumpy(best_lda_gpu.components_)
        doc_topic_gpu   = _transform_lda_gpu(best_lda_gpu, X_count_gpu)
        print(f'  [--gpu] GPU fit complete.')
        # Wrap in a lightweight namespace so downstream code can call
        # best_lda.components_ and best_lda.transform() uniformly.
        class _GPULDAWrapper:
            def __init__(self, components, doc_topic_arr):
                self.components_ = components
                self._doc_topic  = doc_topic_arr
            def transform(self, X):
                return self._doc_topic
            def perplexity(self, X):
                return float('nan')  # not available for GPU model
        best_lda = _GPULDAWrapper(best_components, doc_topic_gpu)
    except Exception as _gpu_err:
        print(f'  [--gpu] GPU fit failed ({_gpu_err}) — falling back to sklearn')
        GPU = False
        best_lda = LatentDirichletAllocation(
            n_components=best_n, max_iter=20, learning_method='online',
            random_state=99, learning_offset=50., doc_topic_prior=0.1)
        best_lda.fit(X_count)
else:
    best_lda = LatentDirichletAllocation(
        n_components=best_n, max_iter=20, learning_method='online',
        random_state=99, learning_offset=50., doc_topic_prior=0.1)
    best_lda.fit(X_count)

# ── Topic stability analysis (--seeds) ───────────────────────────────────────
def _jaccard(set_a, set_b):
    """Jaccard similarity between two sets of words."""
    a, b = set(set_a), set(set_b)
    return len(a & b) / len(a | b) if (a | b) else 0.0

def _align_topics(words_a, words_b):
    """
    Align topics from two runs using the Hungarian algorithm to maximise
    total Jaccard similarity. Returns (row_ind, col_ind, similarity_matrix).
    """
    from scipy.optimize import linear_sum_assignment
    n = len(words_a)
    sim = np.array([[_jaccard(words_a[i], words_b[j]) for j in range(n)]
                    for i in range(n)])
    row_ind, col_ind = linear_sum_assignment(-sim)  # maximise
    return row_ind, col_ind, sim

def run_stability_analysis(n_topics, X_count, cv_vocab, n_seeds, n_top=10):
    """
    Run LDA n_seeds times, align topics across all pairs of runs using the
    Hungarian algorithm, and compute per-topic mean Jaccard stability scores.

    Uses GPU (cuML) for each seed run if --gpu is active.

    Returns:
        seed_top_words  : list of n_seeds × n_topics × n_top word lists
        stability_scores: list of n_topics floats (mean Jaccard across pairs)
        canonical_words : top words from seed 0 (reference run), reordered
                          to match the canonical topic ordering
    """
    SEEDS = [42, 7, 123, 256, 999, 17, 88, 314, 501, 777][:n_seeds]
    backend = 'GPU (cuML)' if GPU and _cuLDA is not None else 'CPU (sklearn)'
    print(f"\n[--seeds] Fitting {n_seeds} LDA runs at k={n_topics} ({backend})...")

    all_top_words = []
    for i, seed in enumerate(SEEDS):
        if GPU and _cuLDA is not None:
            try:
                lda_s, X_gpu_s = _fit_lda_gpu(n_topics, X_count,
                                               random_state=seed)
                import cupy as _cp_s
                comps = _cp_s.asnumpy(lda_s.components_)
            except Exception as _se:
                print(f'  seed {seed}: GPU failed ({_se}), using sklearn')
                lda_s = LatentDirichletAllocation(
                    n_components=n_topics, max_iter=20,
                    learning_method='online', random_state=seed,
                    learning_offset=50., doc_topic_prior=0.1)
                lda_s.fit(X_count)
                comps = lda_s.components_
        else:
            lda_s = LatentDirichletAllocation(
                n_components=n_topics, max_iter=20, learning_method='online',
                random_state=seed, learning_offset=50., doc_topic_prior=0.1)
            lda_s.fit(X_count)
            comps = lda_s.components_

        tw = []
        for t in range(n_topics):
            top_idx = comps[t].argsort()[-n_top:][::-1]
            tw.append([cv_vocab[idx] for idx in top_idx
                       if ' ' not in cv_vocab[idx]][:n_top])
        all_top_words.append(tw)
        print(f"  seed {seed} done ({i+1}/{n_seeds})")

    # Align all runs to run 0 as reference
    from itertools import combinations as _comb
    n_pairs   = 0
    pair_sims = [[] for _ in range(n_topics)]  # per canonical topic

    ref = all_top_words[0]
    for i, j in _comb(range(n_seeds), 2):
        wa, wb = all_top_words[i], all_top_words[j]
        row_ind, col_ind, sim = _align_topics(wa, wb)
        # Align j's topics to i's ordering, then align i to ref
        _, ref_col, ref_sim = _align_topics(ref, wa)
        for r_idx, a_idx in enumerate(ref_col):
            # Find where a_idx maps in the i→j alignment
            if a_idx in row_ind:
                pos = list(row_ind).index(a_idx)
                b_idx = col_ind[pos]
                pair_sims[r_idx].append(sim[a_idx, b_idx])
        n_pairs += 1

    stability_scores = [float(np.mean(s)) if s else 0.0 for s in pair_sims]

    # Canonical word lists: from reference run (seed 0), in ref topic order
    canonical_words = ref

    return all_top_words, stability_scores, canonical_words

stability_results = None
if _N_SEEDS >= 2:
    all_seed_words, stability_scores, canonical_words = run_stability_analysis(
        best_n, X_count, cv_vocab, _N_SEEDS)

    print(f"\n[--seeds] Topic stability (mean Jaccard, {_N_SEEDS} seeds):")
    print(f"  {'Topic':<8} {'Stability':>10}  {'Top words'}")
    for t, (score, words) in enumerate(zip(stability_scores, canonical_words)):
        bar = '█' * int(score * 20)
        print(f"  T{t+1:<6} {score:>10.3f}  {bar}  {', '.join(words[:6])}")

    mean_stab = float(np.mean(stability_scores))
    print(f"\n  Mean stability: {mean_stab:.3f}  "
          f"({'good' if mean_stab > 0.3 else 'moderate' if mean_stab > 0.15 else 'low'})")
    print(f"  Stable topics (≥0.3):  "
          f"{sum(1 for s in stability_scores if s >= 0.3)}/{best_n}")
    print(f"  Unstable topics (<0.15): "
          f"{sum(1 for s in stability_scores if s < 0.15)}/{best_n}")

    stability_results = {
        'n_topics':        best_n,
        'n_seeds':         _N_SEEDS,
        'seeds_used':      [42, 7, 123, 256, 999, 17, 88, 314, 501, 777][:_N_SEEDS],
        'stability_scores': stability_scores,
        'mean_stability':  mean_stab,
        'canonical_words': canonical_words,
        'all_seed_words':  all_seed_words,
        'thresholds': {
            'stable':   [t for t, s in enumerate(stability_scores) if s >= 0.3],
            'moderate': [t for t, s in enumerate(stability_scores)
                         if 0.15 <= s < 0.3],
            'unstable': [t for t, s in enumerate(stability_scores) if s < 0.15],
        }
    }
    with open(_out('topic_stability'), 'w') as f:
        json.dump(stability_results, f, indent=2)
    print(f"  Saved {_out('topic_stability')}")

# Get topic-word distributions for best model
def get_top_words(model, feature_names, n_top=12):
    topics = []
    for idx, topic in enumerate(model.components_):
        top_idx = topic.argsort()[:-n_top-1:-1]
        topics.append([feature_names[i] for i in top_idx])
    return topics

top_words      = get_top_words(best_lda, cv_vocab)
doc_topic      = best_lda.transform(X_count)
if not isinstance(doc_topic, np.ndarray):
    doc_topic = np.array(doc_topic)
dominant_topics = doc_topic.argmax(axis=1)

# ── 3. Key Phrase Extraction (TF-IDF per document) ───────────────────────────
def extract_keyphrases(text, top_n=8):
    vec = TfidfVectorizer(max_features=500, stop_words=list(STOPWORDS),
                          ngram_range=(1,3), token_pattern=r'(?u)\b[a-zA-Z]{4,}\b')
    try:
        mat = vec.fit_transform([text])
        scores = mat.toarray()[0]
        idx = scores.argsort()[::-1][:top_n]
        return [vec.get_feature_names_out()[i] for i in idx if scores[i] > 0]
    except:
        return []

keyphrases = {}
for bid, text in zip(book_ids, texts):
    keyphrases[bid] = extract_keyphrases(text)
    print(f"  [{bid}] {books[bid]['title'][:40]:40s} → {keyphrases[bid][:5]}")

# ── 4. Clustering ─────────────────────────────────────────────────────────────
# Cosine similarity matrix
cos_sim = cosine_similarity(X_tfidf)

# K-Means with elbow method
inertias, silhouettes = {}, {}
for k in range(2, min(10, len(book_ids))):
    km = KMeans(n_clusters=k, random_state=99, n_init=10)
    labels = km.fit_predict(X_tfidf.toarray())
    inertias[k] = km.inertia_
    if k < len(set(labels)) + 1:
        silhouettes[k] = silhouette_score(X_tfidf, labels)

# Find elbow (largest drop in inertia)
ks = sorted(inertias.keys())
drops = {ks[i]: inertias[ks[i-1]] - inertias[ks[i]] for i in range(1, len(ks))}
best_k = max(drops, key=drops.get)
print(f"\nElbow method suggests k={best_k} clusters")
print(f"Silhouettes: {silhouettes}")

km_final = KMeans(n_clusters=best_k, random_state=99, n_init=10)
cluster_labels = km_final.fit_predict(X_tfidf.toarray())

# ── Publication years ────────────────────────────────────────────────────────
import re as _re
pub_years = []
for b in book_ids:
    raw = books[b].get('pub_year') or books[b].get('pubdate', '')
    m = _re.search(r'\b(19|20)\d{2}\b', str(raw)) if raw else None
    pub_years.append(int(m.group()) if m else None)

# ── 2D LSA projection for scatter plots ──────────────────────────────────────
from sklearn.decomposition import TruncatedSVD as _SVD2
from sklearn.preprocessing import normalize as _norm2
_svd2 = _SVD2(n_components=2, random_state=99)
coords_2d = _norm2(_svd2.fit_transform(X_tfidf)).tolist()

# ── Topic naming via Anthropic API (--name-topics) ───────────────────────────
def name_topics_via_api(top_words, n_topics,
                        grounding_path=str(JSON_DIR / 'topic_index_grounding.json')):
    """
    Call the Anthropic API once per topic to generate a concise 2-5 word label.
    Uses top LDA words + highest-lift index terms as input.
    Returns a list of n_topics label strings; falls back to 'Topic N' on error.
    """
    import anthropic as _anth
    import json as _json

    api_key = _os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        print("  [--name-topics] ANTHROPIC_API_KEY not set — skipping naming")
        return [f'Topic {t+1}' for t in range(n_topics)]

    grounding = {}
    try:
        with open(grounding_path) as f:
            _TG = _json.load(f)
        for t_str, entries in _TG['lda_top_terms'].items():
            grounding[int(t_str)] = [e['term'] for e in entries[:8]]
    except Exception:
        pass

    client = _anth.Anthropic(api_key=api_key)
    names  = []
    print(f"  [--name-topics] Naming {n_topics} topics via API...")

    for t in range(n_topics):
        words  = top_words[t][:12]
        ground = grounding.get(t, [])
        prompt = (
            f"You are labelling topic clusters from a cybernetics book corpus "
            f"(695 books, 1954-2025).\n\n"
            f"Topic {t+1} of {n_topics}:\n"
            f"  Top LDA words: {', '.join(words)}\n"
            f"  Highest-lift index terms: "
            f"{', '.join(ground) if ground else '(none)'}\n\n"
            f"Give a concise label for this intellectual cluster. Rules:\n"
            f"1. 2-5 words maximum.\n"
            f"2. Name the intellectual orientation, not just a subject area.\n"
            f"3. Use scholarly terminology where appropriate.\n"
            f"4. If a specific tradition, figure, or concept dominates, name it.\n"
            f"5. Reply with ONLY the label — no explanation, no punctuation at end."
        )
        try:
            resp = client.messages.create(
                model='claude-sonnet-4-20250514',
                max_tokens=30,
                messages=[{'role': 'user', 'content': prompt}]
            )
            label = resp.content[0].text.strip().strip('.,;:')
            names.append(label)
            print(f"    T{t+1}: {label}")
        except Exception as e:
            fallback = f'Topic {t+1}'
            print(f"    T{t+1}: [error: {e}] → {fallback}")
            names.append(fallback)

    return names

# Save all results
results = {
    'book_ids': book_ids,
    'titles': titles,
    'authors': authors,
    'n_topics': best_n,
    'perplexities': perplexities,
    'coherences': coherences,
    'top_words': top_words,
    'doc_topic': doc_topic.tolist(),
    'dominant_topics': dominant_topics.tolist(),
    'keyphrases': keyphrases,
    'cos_sim': cos_sim.tolist(),
    'inertias': {str(k): v for k, v in inertias.items()},
    'silhouettes': {str(k): v for k, v in silhouettes.items()},
    'best_k': best_k,
    'cluster_labels': cluster_labels.tolist(),
    'tfidf_matrix': X_tfidf.toarray().tolist(),
    'feature_names': feature_names.tolist()[:100],  # top 100 for viz
    'pub_years': pub_years,
    'coords_2d': coords_2d,
    'topic_names': None,  # populated by --name-topics or carried from prev run
    'stability': stability_results,  # None unless --seeds was used
    'pipeline_mode': 'full_text' if FULL_TEXT else 'sampled',
    'max_features': _MAX_FEATURES,
    'gpu_used': GPU,
}

# Carry forward topic_names from a previous run if n_topics matches
# (so names survive --weighted re-runs without --name-topics)
try:
    with open(_out('nlp_results')) as _f:
        _prev = json.load(_f)
    if (_prev.get('n_topics') == results['n_topics']
            and _prev.get('topic_names')
            and not NAME_TOPICS):
        results['topic_names'] = _prev['topic_names']
        print(f"  [topic_names] carried forward: {results['topic_names']}")
except Exception:
    pass

if NAME_TOPICS:
    results['topic_names'] = name_topics_via_api(top_words, best_n)

with open(_out('nlp_results'), 'w') as f:
    json.dump(results, f)
print(f"\nNLP pipeline complete. Results saved to {_out('nlp_results')}")
if results.get('topic_names'):
    print('Topic names:')
    for i, name in enumerate(results['topic_names']):
        print(f'  T{i+1}: {name}')
