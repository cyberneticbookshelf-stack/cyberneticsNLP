"""
diagnose_topic_alignment.py
─────────────────────────────────────────────────────────────────────────────
One-off diagnostic. Tests whether the topic-word vs top-book mismatches in
data/outputs/topic_validation.md (and the corresponding section of the
runlog) are explained SOLELY by an unaligned topic-index permutation
between the canonical 5-seed reference (random_state=42) and the final fit
(random_state=99) written by src/03_nlp_pipeline.py.

Background
──────────
src/03_nlp_pipeline.py runs a 5-seed stability sweep on
[42, 7, 123, 256, 999] and aligns all seeds to seed 42 via Hungarian (line
937: `ref = all_top_words[0]`). canonical_words in topic_stability.json is
seed 42's top words. The script then runs a SEPARATE 6th LDA fit at
random_state=99 (lines 782/787) whose top_words and doc_topic are written
to nlp_results.json. The 6th fit is never aligned back to the seed-42
reference, so its topic indices are a permutation of the canonical
indices.

src/09c_validate_topics.py pairs canonical_words[t] (aligned to seed 42)
with doc_topic[:, t] (raw seed-99 indexing) — across two unrelated
coordinate systems. That permutation is the suspected sole cause of the
words↔books mismatch shown in topic_validation.md.

Tests A and B (run earlier from existing JSON artefacts) passed and
collectively rule out (a) any internal inconsistency inside
nlp_results.json and (b) any anomaly that would make seed 99 differ from
"just another seed" in the canonical sweep.

This script runs the two remaining tests that require new LDA fits.

  TEST C(i) — canonical-fit reproducibility
    Re-fit LDA at random_state=42 with the same parameters as the
    canonical sweep. Verify its per-topic top words equal
    topic_stability.json['canonical_words'] exactly. This is a sanity
    check on the reference-handling at src/03_nlp_pipeline.py:937.

  TEST C(ii) + D — round-trip equivalence under permutation
    Fit LDA at random_state=99. Hungarian-align seed-99 → seed-42 on top
    words. For each canonical (seed-42) topic, compare its top-N books
    against the top-N books from the seed-99 doc_topic column that the
    permutation maps to it. If they agree (modulo 1–2 stochastic swaps in
    loading order), permutation is the only thing the canonical-vs-final
    coordinate gap obscures.

PASS on all three tests ⇒ index permutation is the SOLE driver of the
09c mismatch; no other distortion source exists.

Important
─────────
This script DUPLICATES the preprocessing pipeline of src/03_nlp_pipeline.py
inline (publication-type filter, alpha-ratio filter, OCR exclusion,
full-text body extraction, lemmatisation, hyphen-joining, CountVectorizer
config). Each block carries an inline reference to the source-of-truth
line range. If the canonical preprocessing changes, this script must be
updated. A future refactor that extracts the preprocessing into a shared
module (per the "fix upstream" principle in CLAUDE.md) would make this
duplication unnecessary.

Parameters mirror the canonical run line in src/run_all.sh:
    --min-chars 10000 --lemmatize --topics 9 --seeds 5
    --full-text --max-features 15000 --max-iter 100

Usage
─────
    python3 src/diagnose_topic_alignment.py
    python3 src/diagnose_topic_alignment.py --top 10        # top N books per topic
    python3 src/diagnose_topic_alignment.py --cache         # cache X_count to disk
    python3 src/diagnose_topic_alignment.py --no-md         # skip markdown report

Outputs
───────
    json/topic_alignment_diagnostic.json         structured results
    data/outputs/topic_alignment_diagnostic.md   human-readable report
    json/topic_align_cache.npz                   cached X_count (with --cache)

Exit code: 0 if all tests pass, 1 otherwise.
"""

import sys
import re
import csv
import json
import pathlib as _pl
from datetime import date

import numpy as np
from scipy.sparse import csr_matrix
from scipy.optimize import linear_sum_assignment
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation


# ── Paths ────────────────────────────────────────────────────────────────────
CSV_DIR     = _pl.Path('csv')
JSON_DIR    = _pl.Path('json')
OUTPUTS_DIR = _pl.Path('data/outputs')
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


# ── Canonical run parameters (mirror src/run_all.sh:123 and lines 882-886) ──
N_TOPICS         = 9
MAX_FEATURES     = 15_000
MAX_ITER         = 100
MIN_CHARS        = 10_000
SEED_REF         = 42       # canonical reference seed in the 5-seed sweep
SEED_FINAL       = 99       # hardcoded final-fit seed in 03_nlp_pipeline.py
DOC_TOPIC_PRIOR  = 0.1
LEARNING_OFFSET  = 50.0
LEARNING_METHOD  = 'online'

TOP_N_BOOKS = 10
WRITE_MD    = '--no-md' not in sys.argv
USE_CACHE   = '--cache' in sys.argv
if '--top' in sys.argv:
    try:
        TOP_N_BOOKS = int(sys.argv[sys.argv.index('--top') + 1])
    except (IndexError, ValueError):
        print('  [--top] usage: --top N  (integer)')


# ── Stopwords (mirror src/03_nlp_pipeline.py:27-62) ──────────────────────────
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
aren couldn didn doesn hadn hasn haven mustn shan shouldn wasn weren wouldn
""".split())


# ── Preprocessing helpers (mirror src/03_nlp_pipeline.py:373-563) ───────────
MIN_ALPHA_RATIO       = 0.40
FRONT_SKIP_MIN_CHARS  = 3000
FRONT_SKIP_FRAC       = 0.05
BACK_MIN_FRAC         = 0.50

_BODY_START_RE = re.compile(
    r'^\s*(?:'
    r'chapter\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|'
    r'eleven|twelve|[1-9][0-9]?)\b'
    r'|part\s+(?:one|two|three|i{1,4}|v?i{0,3}|[1-9])\b'
    r'|introduction\b'
    r'|prologue\b'
    r'|[1-9][0-9]?\s*\n'
    r')',
    re.IGNORECASE | re.MULTILINE,
)

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
    re.IGNORECASE | re.MULTILINE,
)

OCR_EXCLUDED = {'2133'}  # mirrors src/03_nlp_pipeline.py:408-410


def _alpha_ratio(text, sample=5000, n_windows=3):
    n = len(text)
    if n < sample:
        return sum(c.isalpha() for c in text) / n if n else 0.0
    start = max(sample, n // 10)
    body  = text[start:]
    if len(body) < sample:
        return sum(c.isalpha() for c in body) / len(body)
    step = (len(body) - sample) // max(n_windows - 1, 1)
    ratios = []
    for i in range(n_windows):
        offset = i * step
        window = body[offset:offset + sample]
        ratios.append(sum(c.isalpha() for c in window) / len(window))
    return sum(ratios) / len(ratios)


def strip_front_matter(text):
    n = len(text)
    m = _BODY_START_RE.search(text, FRONT_SKIP_MIN_CHARS)
    if m and m.start() < n * 0.30:
        return text[m.start():]
    offset = max(FRONT_SKIP_MIN_CHARS, int(n * FRONT_SKIP_FRAC))
    return text[offset:]


def strip_back_matter(text):
    n = len(text)
    min_offset = int(n * BACK_MIN_FRAC)
    last_match = None
    for m in _BACK_START_RE.finditer(text):
        if m.start() >= min_offset:
            last_match = m
    return text[:last_match.start()] if last_match else text


def prepare_full_text(text):
    return strip_back_matter(strip_front_matter(text))


# ── Load corpus and apply canonical filters ──────────────────────────────────
print('Loading json/books_clean.json …')
with open(str(JSON_DIR / 'books_clean.json')) as f:
    books = json.load(f)
book_ids = list(books.keys())
print(f'  loaded {len(book_ids)} books')

# Pub-type filter (mirrors src/03_nlp_pipeline.py:310-348)
INCLUDE_TYPES = {'monograph', 'collected works'}
pubtype_map = {}
meta_path = CSV_DIR / 'books_metadata_full.csv'
if meta_path.exists():
    with open(str(meta_path), encoding='utf-8') as mf:
        for row in csv.DictReader(mf, delimiter='\t'):
            bid = row['id'].strip()
            pt  = row.get('pub_type', '').strip().lower()
            if pt:
                pubtype_map[bid] = pt
    if pubtype_map:
        before = len(book_ids)

        def _is_included(bid):
            pt = pubtype_map.get(bid, '')
            if not pt:
                return True   # no label → include (safe default; same as canonical)
            parts = [p.strip() for p in pt.replace(';', ',').split(',')]
            return any(p in INCLUDE_TYPES for p in parts)

        book_ids = [b for b in book_ids if _is_included(b)]
        print(f'  [pub-type]    {before} → {len(book_ids)}')
else:
    print('  [pub-type]    books_metadata_full.csv NOT FOUND — '
          'this script will diverge from the canonical run; aborting.')
    sys.exit(2)

# Min-chars filter
before = len(book_ids)
book_ids = [b for b in book_ids if len(books[b]['clean_text']) >= MIN_CHARS]
print(f'  [min-chars≥{MIN_CHARS}] {before} → {len(book_ids)}')

# Alpha-ratio filter
before = len(book_ids)
book_ids = [b for b in book_ids if _alpha_ratio(books[b]['clean_text']) >= MIN_ALPHA_RATIO]
print(f'  [alpha≥{MIN_ALPHA_RATIO}]   {before} → {len(book_ids)}')

# OCR exclusion
before = len(book_ids)
book_ids = [b for b in book_ids if b not in OCR_EXCLUDED]
print(f'  [ocr-excluded] {before} → {len(book_ids)}')

# Cross-check vs nlp_results.json (the canonical run we're testing against)
nlp = json.load(open(str(JSON_DIR / 'nlp_results.json')))
nlp_book_ids = nlp['book_ids']
if len(book_ids) != len(nlp_book_ids):
    print(f'  ABORT: book_id count mismatch — diagnostic={len(book_ids)} '
          f'vs nlp_results.json={len(nlp_book_ids)}. Preprocessing has '
          f'drifted from the canonical pipeline.')
    sys.exit(2)
if book_ids != nlp_book_ids:
    # Order matters because we'll pair doc_topic rows with book_ids by index.
    # Reorder to match the canonical run, but warn.
    print('  WARNING: book_id ORDER differs from nlp_results.json — reordering.')
    book_ids = list(nlp_book_ids)


# ── Build (or load) the count matrix ────────────────────────────────────────
CACHE_PATH = JSON_DIR / 'topic_align_cache.npz'
X_count = None
cv_vocab = None

if USE_CACHE and CACHE_PATH.exists():
    print(f'\n[--cache] loading X_count from {CACHE_PATH}')
    npz = np.load(str(CACHE_PATH), allow_pickle=True)
    cached_book_ids = list(npz['book_ids'])
    if cached_book_ids != book_ids:
        print('  cache book_ids differ — rebuilding')
    else:
        X_count = csr_matrix(
            (npz['data'], npz['indices'], npz['indptr']),
            shape=tuple(npz['shape']),
        )
        cv_vocab = list(npz['vocab'])
        print(f'  loaded X_count {X_count.shape}, vocab {len(cv_vocab)}')

if X_count is None:
    print('\nPreparing full-text bodies …')
    texts = [prepare_full_text(books[b]['clean_text']) for b in book_ids]

    print('Lemmatising with spaCy en_core_web_sm …')
    import spacy
    nlp_spacy = spacy.load('en_core_web_sm', disable=['parser', 'ner'])

    def _lemmatise_text(text, batch_size=50):
        chunks = [text[i:i + 10000] for i in range(0, len(text), 10000)]
        lemmas = []
        for doc in nlp_spacy.pipe(chunks, batch_size=batch_size):
            lemmas.extend(
                token.lemma_.lower()
                for token in doc
                if not token.is_punct and not token.is_space and len(token.lemma_) > 1
            )
        return ' '.join(lemmas)

    out_texts = []
    for i, t in enumerate(texts, 1):
        out_texts.append(_lemmatise_text(t))
        if i % 25 == 0 or i == len(texts):
            print(f'  {i}/{len(texts)}', end='\r')
    print()
    texts = out_texts  # lemmatiser already handles word boundaries

    print('Building CountVectorizer …')
    cv = CountVectorizer(
        max_features=MAX_FEATURES, stop_words=list(STOPWORDS),
        ngram_range=(1, 1), min_df=2, max_df=0.95,
        token_pattern=r'(?u)\b[a-zA-Z]{4,}\b',
    )
    X_count  = cv.fit_transform(texts)
    cv_vocab = list(cv.get_feature_names_out())
    print(f'  X_count {X_count.shape}, vocab {len(cv_vocab)}')

    if USE_CACHE:
        np.savez(
            str(CACHE_PATH),
            data=X_count.data, indices=X_count.indices,
            indptr=X_count.indptr, shape=np.array(X_count.shape),
            vocab=np.array(cv_vocab), book_ids=np.array(book_ids),
        )
        print(f'  cached to {CACHE_PATH}')


# ── Fit LDA at the two seeds ────────────────────────────────────────────────
def fit_lda(seed):
    print(f'  fitting LDA (random_state={seed}) …')
    lda = LatentDirichletAllocation(
        n_components=N_TOPICS, max_iter=MAX_ITER,
        learning_method=LEARNING_METHOD, random_state=seed,
        learning_offset=LEARNING_OFFSET, doc_topic_prior=DOC_TOPIC_PRIOR,
    )
    lda.fit(X_count)
    return lda


def top_words(lda, vocab, n_top=12):
    return [
        [vocab[i] for i in lda.components_[t].argsort()[::-1][:n_top]]
        for t in range(lda.n_components)
    ]


def top_books_for(dt, topic_idx, top_n):
    pairs = sorted(
        ((book_ids[i], float(dt[i, topic_idx])) for i in range(len(book_ids))),
        key=lambda x: -x[1],
    )[:top_n]
    return pairs


print('\n=== Fitting LDA at canonical reference (42) and final-fit (99) ===')
lda_42 = fit_lda(SEED_REF)
lda_99 = fit_lda(SEED_FINAL)
tw_42 = top_words(lda_42, cv_vocab)
tw_99 = top_words(lda_99, cv_vocab)
dt_42 = lda_42.transform(X_count)
dt_99 = lda_99.transform(X_count)


# ── TEST C(i): seed-42 top words equal canonical_words ──────────────────────
print('\n=== TEST C(i): seed-42 top_words vs topic_stability.json canonical_words ===')
stab = json.load(open(str(JSON_DIR / 'topic_stability.json')))
canonical = stab['canonical_words']

c1 = []
for t in range(N_TOPICS):
    s42 = tw_42[t][:10]
    can = canonical[t][:10]
    set_eq   = set(s42) == set(can)
    order_eq = s42 == can
    c1.append({'topic': t, 'seed42': s42, 'canonical': can,
               'set_eq': set_eq, 'order_eq': order_eq})
    print(f'  T{t+1}  set_eq={set_eq}  order_eq={order_eq}')

C1_PASS = all(r['set_eq'] for r in c1)
print(f'\n  TEST C(i): {"PASS" if C1_PASS else "FAIL"}')


# ── Hungarian alignment seed-99 → seed-42 ───────────────────────────────────
def jaccard_matrix(a, b, n_top=12):
    K = len(a)
    M = np.zeros((K, K))
    for i in range(K):
        sa = set(a[i][:n_top])
        for j in range(K):
            sb = set(b[j][:n_top])
            inter = len(sa & sb); union = len(sa | sb)
            M[i, j] = inter / union if union else 0
    return M


print('\n=== Hungarian alignment: seed-99 → seed-42 ===')
J = jaccard_matrix(tw_99, tw_42, n_top=12)
row_ind, col_ind = linear_sum_assignment(-J)
perm_99_to_42 = {int(r): int(c) for r, c in zip(row_ind, col_ind)}
for r, c in zip(row_ind, col_ind):
    print(f'  seed99 T{r+1} → seed42 T{c+1}   J={J[r,c]:.3f}')
print(f'\n  Mean Jaccard: {J[row_ind, col_ind].mean():.3f}')


# ── TEST C(ii) + D: top books equivalence under permutation ────────────────
print('\n=== TEST C(ii) + D: top books per canonical topic, seed-42 vs permuted seed-99 ===')

c2 = []
for c in range(N_TOPICS):
    src_99 = next(r for r, dst in perm_99_to_42.items() if dst == c)
    books_42 = top_books_for(dt_42, c,      TOP_N_BOOKS)
    books_99 = top_books_for(dt_99, src_99, TOP_N_BOOKS)
    ids_42 = [b for b, _ in books_42]
    ids_99 = [b for b, _ in books_99]
    overlap   = len(set(ids_42) & set(ids_99))
    rank_eq   = sum(1 for a, b in zip(ids_42, ids_99) if a == b)
    c2.append({
        'canonical_topic':   c,
        'seed99_topic':      src_99,
        'top_books_42':      books_42,
        'top_books_99_perm': books_99,
        'overlap':           overlap,
        'rank_match':        rank_eq,
    })
    print(f'  canon T{c+1}  ←  seed99 T{src_99+1}   '
          f'overlap={overlap}/{TOP_N_BOOKS}  exact-rank={rank_eq}/{TOP_N_BOOKS}')

# Pass criterion: top-N book sets overlap ≥(N-2) per topic.
# Allows 1-2 swaps from independent-fit stochastic loading variation; this
# tolerance is justified by Test B (cross-fit ≈ within-sweep, mean ~0.35)
# and a tighter bound would simply rediscover stochastic variance.
TOL = 2
C2_PASS = all(r['overlap'] >= TOP_N_BOOKS - TOL for r in c2)
print(f'\n  TEST C(ii)+D: {"PASS" if C2_PASS else "FAIL"}  '
      f'(criterion: overlap ≥ {TOP_N_BOOKS - TOL}/{TOP_N_BOOKS} per topic)')


# ── Verdict ──────────────────────────────────────────────────────────────────
ALL_PASS = C1_PASS and C2_PASS
print('\n' + '═' * 72)
print(f'OVERALL: {"PASS — index permutation is the SOLE driver of the 09c mismatch" if ALL_PASS else "INVESTIGATE — at least one test failed"}')
print('═' * 72)


# ── Persist ──────────────────────────────────────────────────────────────────
out = {
    'date':         str(date.today()),
    'corpus_size':  len(book_ids),
    'params': {
        'n_topics':         N_TOPICS,
        'max_features':     MAX_FEATURES,
        'max_iter':         MAX_ITER,
        'min_chars':        MIN_CHARS,
        'doc_topic_prior':  DOC_TOPIC_PRIOR,
        'learning_offset':  LEARNING_OFFSET,
        'learning_method':  LEARNING_METHOD,
        'seed_ref':         SEED_REF,
        'seed_final':       SEED_FINAL,
    },
    'mean_jaccard_99_to_42':  float(J[row_ind, col_ind].mean()),
    'permutation_99_to_42':   perm_99_to_42,
    'test_C1':                {'pass': bool(C1_PASS), 'per_topic': c1},
    'test_C2_D':              {'pass': bool(C2_PASS),
                               'tolerance': TOL,
                               'top_n_books': TOP_N_BOOKS,
                               'per_topic': c2},
    'overall_pass':           bool(ALL_PASS),
}
out_path = str(JSON_DIR / 'topic_alignment_diagnostic.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f'\nSaved {out_path}')


# ── Markdown report ─────────────────────────────────────────────────────────
if WRITE_MD:
    md = [
        '# Topic Alignment Diagnostic',
        '',
        f'**Date:** {date.today()}  ',
        f'**Corpus:** {len(book_ids)} books  ',
        f'**LDA params:** k={N_TOPICS}, max_features={MAX_FEATURES}, '
        f'max_iter={MAX_ITER}, learning=online, doc_topic_prior={DOC_TOPIC_PRIOR}  ',
        f'**Seeds compared:** ref={SEED_REF} (canonical sweep reference), '
        f'final={SEED_FINAL} (final-fit in nlp_results.json)  ',
        '',
        '## Hypothesis under test',
        '',
        'Mismatches in `data/outputs/topic_validation.md` between top words and',
        'top books per topic are explained SOLELY by an unaligned topic-index',
        'permutation between the canonical 5-seed reference (seed 42) and the',
        'final fit (seed 99) written by `src/03_nlp_pipeline.py`.',
        '',
        '## Verdict',
        '',
        f'**{"PASS — permutation is the sole driver" if ALL_PASS else "INVESTIGATE — at least one test failed"}**',
        '',
        '## Test C(i) — seed-42 top words equal `canonical_words`',
        '',
        f'**Result: {"PASS" if C1_PASS else "FAIL"}**',
        '',
        '| Topic | set equal | order equal | seed-42 top 6 |',
        '|---|---|---|---|',
    ]
    for r in c1:
        md.append(
            f'| T{r["topic"]+1} | {r["set_eq"]} | {r["order_eq"]} | '
            f'{", ".join(r["seed42"][:6])} |'
        )

    md += [
        '',
        '## Hungarian alignment (seed-99 → seed-42)',
        '',
        f'Mean Jaccard on top-12 words: **{J[row_ind, col_ind].mean():.3f}**',
        '',
        '| seed-99 | → seed-42 | Jaccard |',
        '|---|---|---|',
    ]
    for r, c in zip(row_ind, col_ind):
        md.append(f'| T{r+1} | T{c+1} | {J[r,c]:.3f} |')

    md += [
        '',
        '## Test C(ii) + D — top books per canonical topic',
        '',
        f'**Result: {"PASS" if C2_PASS else "FAIL"}**  '
        f'(criterion: top-{TOP_N_BOOKS} sets overlap ≥{TOP_N_BOOKS - TOL}/{TOP_N_BOOKS} per topic)',
        '',
        '| Canon | Seed-99 src | Set overlap | Exact-rank match |',
        '|---|---|---|---|',
    ]
    for r in c2:
        md.append(
            f'| T{r["canonical_topic"]+1} | T{r["seed99_topic"]+1} | '
            f'{r["overlap"]}/{TOP_N_BOOKS} | {r["rank_match"]}/{TOP_N_BOOKS} |'
        )

    md += ['', '## Detail — per-topic top books', '']
    for r in c2:
        c = r['canonical_topic']
        ids_42 = ', '.join(b for b, _ in r['top_books_42'])
        ids_99 = ', '.join(b for b, _ in r['top_books_99_perm'])
        md.append(f'### canon T{c+1}  ←  seed-99 T{r["seed99_topic"]+1}')
        md.append('')
        md.append(f'**seed-42 top {TOP_N_BOOKS}:** {ids_42}  ')
        md.append(f'**seed-99 (permuted) top {TOP_N_BOOKS}:** {ids_99}  ')
        md.append('')

    md_path = str(OUTPUTS_DIR / 'topic_alignment_diagnostic.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(f'Saved {md_path}')

sys.exit(0 if ALL_PASS else 1)
