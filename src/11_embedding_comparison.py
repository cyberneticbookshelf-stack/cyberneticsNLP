"""


11_embedding_comparison.py
──────────────────────────────────────────────────────────────────────────────
Compares four embedding approaches for the 695-book corpus and produces an
interactive HTML report with side-by-side clustering and similarity metrics.

Methods compared
────────────────
A. TF-IDF + LSA (100-dim)       — current pipeline baseline
B. TF-IDF + LSA (384-dim)       — same vocabulary, higher-dimensional space
C. Sentence Transformers         — all-MiniLM-L6-v2 (384-dim dense)
   (requires: pip install sentence-transformers)
D. API Embeddings                — Anthropic's voyage-3 via the API
   (requires: ANTHROPIC_API_KEY, outbound HTTPS)

Methods A and B always run. C and D run automatically if dependencies are
available, otherwise they are skipped with a clear message.

Metrics reported (per method, per k=3..10)
──────────────────────────────────────────
• Silhouette score           (higher = better, max 1.0)
• Davies-Bouldin index       (lower = better)
• Calinski-Harabász score    (higher = better)
• Intra-cluster cosine sim   (higher = tighter clusters)
• Inter-cluster cosine sim   (lower = better separation)
• Top-3 nearest neighbours per book (qualitative check)

Output
──────
• embedding_results.json     — raw embeddings and metrics for all methods
• book_nlp_embedding_comparison.html — interactive Plotly comparison report

Usage
─────
    python3 src/11_embedding_comparison.py                       # run A, B, C, D
    python3 src/11_embedding_comparison.py --no-voyage           # skip Method D
    python3 src/11_embedding_comparison.py --no-st               # skip Method C
    python3 src/11_embedding_comparison.py --no-voyage --no-st   # run A and B only
    python3 src/11_embedding_comparison.py --k 7                 # fix cluster count at 7

    Use --no-voyage when Voyage AI rate limits or key availability is an issue.
    Use --no-st when PyTorch is not installed or CPU inference is too slow.

Input:  summaries.json, nlp_results.json
Output: embedding_results.json,  data/outputs/book_nlp_embedding_comparison.html
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
# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_metadata_full.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


import json, os, sys, time, argparse
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from sklearn.cluster import KMeans
from sklearn.metrics import (silhouette_score, davies_bouldin_score,
                              calinski_harabasz_score)
from sklearn.metrics.pairwise import cosine_similarity

os.makedirs('data/outputs', exist_ok=True)

# ── CLI ────────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(
    description='Compare embedding methods for the book corpus.')
parser.add_argument('--k', type=int, default=None,
                    help='Fix cluster count (default: sweep 3-10, pick best silhouette)')
parser.add_argument('--no-voyage', dest='no_voyage', action='store_true',
                    default=False,
                    help='Skip Method D (Voyage AI). Use when rate limits are an issue.')
parser.add_argument('--no-st', dest='no_st', action='store_true',
                    default=False,
                    help='Skip Method C (Sentence Transformers). Use without PyTorch.')
args = parser.parse_args()

# ── Load data ──────────────────────────────────────────────────────────────────
print("Loading data...")
with open(str(JSON_DIR / 'summaries.json'), encoding='utf-8') as f:
    S = json.load(f)
with open(str(JSON_DIR / 'nlp_results.json')) as f:
    R = json.load(f)

book_ids    = R['book_ids']
titles      = R['titles']
authors     = R['authors']
pub_years   = R.get('pub_years', [None]*len(book_ids))
lda_topics  = R['dominant_topics']

_LDA_BASE = [
    'Cybernetics of Political Economy',
    'Cybernetics and Circularity',
    'Biological Systems Cybernetics',
    'Applied Engineering Cybernetics',
    'Cultural Applications of Cybernetics',
    'Formal Foundations of Cybernetics',
    'History and Biography of Cybernetics',
    'Cybernetic Management Theory',
    'Residual / Outlier Cluster',
]
_ntop = R['n_topics']
_carried = R.get('topic_names') or _LDA_BASE
LDA_NAMES = (_carried + [f'Topic {i+1}' for i in range(len(_carried), _ntop)])[:_ntop]

# Build per-book text: descriptive + argumentative + all chapter summaries
texts = []
for bid in book_ids:
    d = S.get(bid, {})
    parts = [d.get('descriptive',''), d.get('argumentative','')]
    parts += [c.get('summary','') for c in d.get('chapters',[])
              if c.get('summary','').strip()]
    texts.append(' '.join(p for p in parts if p.strip()))

N = len(book_ids)
print(f"  {N} books, avg {np.mean([len(t.split()) for t in texts]):.0f} words/book")

# ── TF-IDF vectorisation (shared by methods A and B) ──────────────────────────
print("\nBuilding TF-IDF matrix...")
vec = TfidfVectorizer(
    max_features=3000, min_df=2, max_df=0.95,
    ngram_range=(1, 2), sublinear_tf=True,
    token_pattern=r'(?u)\b[a-zA-Z]{4,}\b',
)
X_tfidf = vec.fit_transform(texts)
print(f"  TF-IDF shape: {X_tfidf.shape}")

# ── Cluster sweep ──────────────────────────────────────────────────────────────
K_RANGE = range(3, 11)

def best_k_by_silhouette(X, k_range=K_RANGE, seed=99):
    best_k, best_sil = k_range[0], -1
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=seed, n_init=10)
        labs = km.fit_predict(X)
        sil = silhouette_score(X, labs, sample_size=min(N, 500), random_state=seed)
        if sil > best_sil:
            best_sil, best_k = sil, k
    return best_k

def cluster_metrics(X, k, seed=99):
    km = KMeans(n_clusters=k, random_state=seed, n_init=10)
    labels = km.fit_predict(X)
    sim = cosine_similarity(X)
    np.fill_diagonal(sim, 0)

    intra, inter = [], []
    for c in range(k):
        idx = np.where(labels == c)[0]
        if len(idx) < 2: continue
        pairs = sim[np.ix_(idx, idx)]
        intra.append(pairs[pairs > 0].mean())
        other = np.delete(np.arange(N), idx)
        inter.append(sim[np.ix_(idx, other)].mean())

    return {
        'labels':     labels.tolist(),
        'silhouette': float(silhouette_score(X, labels,
                            sample_size=min(N, 500), random_state=seed)),
        'davies_bouldin': float(davies_bouldin_score(X, labels)),
        'calinski_harabasz': float(calinski_harabasz_score(X, labels)),
        'intra_sim':  float(np.mean(intra)),
        'inter_sim':  float(np.mean(inter)),
    }

def top_neighbours(X, k=3):
    sim = cosine_similarity(X)
    np.fill_diagonal(sim, -1)
    nbrs = []
    for i in range(N):
        top = np.argsort(sim[i])[-k:][::-1]
        nbrs.append([{'idx': int(j), 'sim': float(sim[i,j])} for j in top])
    return nbrs

def embed_2d(X, seed=99):
    """2D projection via TruncatedSVD (LSA) — deterministic, no extra deps."""
    svd2 = TruncatedSVD(n_components=2, random_state=seed)
    return normalize(svd2.fit_transform(X)).tolist()

# ── Method A: TF-IDF + LSA 100d ───────────────────────────────────────────────
print("\n[A] TF-IDF + LSA 100d ...")
t0 = time.time()
svd_a = TruncatedSVD(n_components=100, random_state=99)
X_a   = normalize(svd_a.fit_transform(X_tfidf))
k_a   = args.k or best_k_by_silhouette(X_a)
m_a   = cluster_metrics(X_a, k_a)
n_a   = top_neighbours(X_a)
c2_a  = embed_2d(X_tfidf)
t_a   = time.time() - t0
m_a['time'] = round(t_a, 2)
m_a['dims'] = 100
m_a['best_k'] = k_a
m_a['variance_explained'] = float(svd_a.explained_variance_ratio_.sum())
print(f"  k={k_a}  sil={m_a['silhouette']:.4f}  db={m_a['davies_bouldin']:.4f}"
      f"  time={t_a:.1f}s")

# ── Method B: TF-IDF + LSA 384d ───────────────────────────────────────────────
print("\n[B] TF-IDF + LSA 384d ...")
t0 = time.time()
n_dims_b = min(384, X_tfidf.shape[1] - 1)
svd_b = TruncatedSVD(n_components=n_dims_b, random_state=99)
X_b   = normalize(svd_b.fit_transform(X_tfidf))
k_b   = args.k or best_k_by_silhouette(X_b)
m_b   = cluster_metrics(X_b, k_b)
n_b   = top_neighbours(X_b)
t_b   = time.time() - t0
m_b['time'] = round(t_b, 2)
m_b['dims'] = n_dims_b
m_b['best_k'] = k_b
m_b['variance_explained'] = float(svd_b.explained_variance_ratio_.sum())
print(f"  k={k_b}  sil={m_b['silhouette']:.4f}  db={m_b['davies_bouldin']:.4f}"
      f"  time={t_b:.1f}s")

# ── Method C: Sentence Transformers ───────────────────────────────────────────
X_c = None
m_c = {'available': False,
       'reason': 'sentence-transformers not installed. '
                 'Run: pip install sentence-transformers'}
n_c = None

if args.no_st:
    m_c['reason'] = 'Skipped via --no-st flag'
    print("\n[C] Sentence Transformers — SKIPPED (--no-st)")
else:
    try:
        try:
            import torch
            from packaging.version import Version
            if Version(torch.__version__.split('+')[0]) < Version('2.4'):
                raise RuntimeError(
                    f"PyTorch {torch.__version__} installed but sentence-transformers "
                    f"requires >= 2.4.\n"
                    f"Fix A: pip install torch --upgrade\n"
                    f"Fix B: pip install 'sentence-transformers==2.7.0' (supports 2.2)"
                )
        except ImportError:
            raise RuntimeError(
                "PyTorch is not installed.\n"
                "Fix: pip install torch sentence-transformers"
            )
        from sentence_transformers import SentenceTransformer
        print("\n[C] Sentence Transformers (all-MiniLM-L6-v2) ...")
        t0 = time.time()
        model = SentenceTransformer('all-MiniLM-L6-v2')
        X_c_raw = model.encode(texts, batch_size=32, show_progress_bar=True,
                               convert_to_numpy=True)
        X_c = normalize(X_c_raw)
        k_c = args.k or best_k_by_silhouette(X_c)
        m_c = cluster_metrics(X_c, k_c)
        n_c = top_neighbours(X_c)
        t_c = time.time() - t0
        m_c['available'] = True
        m_c['time']      = round(t_c, 2)
        m_c['dims']      = X_c.shape[1]
        m_c['best_k']    = k_c
        m_c['model']     = 'all-MiniLM-L6-v2'
        print(f"  k={k_c}  sil={m_c['silhouette']:.4f}  db={m_c['davies_bouldin']:.4f}"
              f"  time={t_c:.1f}s")
    except ImportError:
        print("\n[C] Sentence Transformers — SKIPPED (not installed)")
        print("    pip install sentence-transformers")
    except Exception as e:
        m_c['reason'] = str(e)
        print(f"\n[C] Sentence Transformers — ERROR: {e}")

# ── Method D: Anthropic API Embeddings ────────────────────────────────────────
X_d = None
m_d = {'available': False}
n_d = None

VOYAGE_KEY = os.environ.get('VOYAGE_API_KEY', '')
if args.no_voyage:
    m_d['reason'] = 'Skipped via --no-voyage flag'
    print("\n[D] Voyage AI Embeddings — SKIPPED (--no-voyage)")
elif not VOYAGE_KEY:
    m_d['reason'] = (
        'VOYAGE_API_KEY not set. Voyage AI is separate from Anthropic — '
        'get a key at https://dash.voyageai.com/ then: '
        'export VOYAGE_API_KEY=pa-...  '
        '(or use --no-voyage to skip)'
    )
    print("\n[D] Voyage AI Embeddings — SKIPPED (no VOYAGE_API_KEY)")
else:
    try:
        import urllib.request
        EMBED_MODEL = 'voyage-3'
        CACHE_PATH  = str(JSON_DIR / 'voyage_embeddings_cache.json')
        BATCH       = 1    # one text at a time — safest for free tier
        DELAY       = 22   # ~2.7 req/min, well within free-tier limit of 3 req/min

        # Load partial cache so we can resume if interrupted
        cache = {}
        if os.path.exists(CACHE_PATH):
            with open(CACHE_PATH) as cf:
                cache = json.load(cf)
            print(f"\n[D] Voyage AI Embeddings — resuming ({len(cache)}/{N} cached)")
        else:
            print("\n[D] Voyage AI Embeddings (voyage-3, one text at a time) ...")
            print(f"  Free tier: ~3 req/min. Estimated time: ~{N*DELAY//60} min.")
        t0 = time.time()

        for i, text in enumerate(texts):
            bid = book_ids[i]
            if bid in cache:
                continue   # already embedded

            payload = json.dumps({
                'model': EMBED_MODEL,
                'input': [text],
                'input_type': 'document',
            }).encode()
            req = urllib.request.Request(
                'https://api.voyageai.com/v1/embeddings',
                data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {VOYAGE_KEY}',
                },
                method='POST',
            )
            for attempt in range(8):
                try:
                    with urllib.request.urlopen(req, timeout=60) as r:
                        resp = json.loads(r.read())
                    cache[bid] = resp['data'][0]['embedding']
                    # Save after every book — crash-safe
                    with open(CACHE_PATH, 'w') as cf:
                        json.dump(cache, cf)
                    break
                except urllib.error.HTTPError as e:
                    if e.code == 429:
                        wait = min(DELAY * (2 ** attempt), 300)
                        print(f"  [{i+1}/{N}] rate limit — waiting {wait}s",
                              flush=True)
                        time.sleep(wait)
                    else:
                        raise
            else:
                raise RuntimeError(
                    f"Rate limit exceeded after 8 retries for book {bid}.\n"
                    f"Progress saved to {CACHE_PATH} — rerun to resume."
                )
            if i % 20 == 0 or i == N-1:
                elapsed = time.time()-t0
                remaining = (N - len(cache)) * DELAY
                print(f"  {len(cache)}/{N} embedded "
                      f"(~{remaining//60:.0f} min remaining)", flush=True)
            time.sleep(DELAY)

        # Assemble in book_ids order
        embeddings = [cache[bid] for bid in book_ids]

        X_d_raw = np.array(embeddings, dtype=np.float32)
        X_d   = normalize(X_d_raw)
        k_d   = args.k or best_k_by_silhouette(X_d)
        m_d   = cluster_metrics(X_d, k_d)
        n_d   = top_neighbours(X_d)
        t_d   = time.time() - t0
        m_d['available'] = True
        m_d['time']      = round(t_d, 2)
        m_d['dims']      = X_d.shape[1]
        m_d['best_k']    = k_d
        m_d['model']     = EMBED_MODEL
        m_d['provider'] = 'Voyage AI'
        print(f"  k={k_d}  sil={m_d['silhouette']:.4f}  db={m_d['davies_bouldin']:.4f}"
              f"  time={t_d:.1f}s")
    except Exception as e:
        m_d['reason'] = str(e)
        print(f"\n[D] Voyage AI Embeddings — ERROR: {e}")

# ── Save raw results ───────────────────────────────────────────────────────────
results = {
    'book_ids':  book_ids,
    'titles':    titles,
    'authors':   authors,
    'pub_years': pub_years,
    'lda_topics': lda_topics,
    'lda_names': LDA_NAMES,
    'coords_2d_lsa': c2_a,
    'methods': {
        'A': m_a,
        'B': m_b,
        'C': m_c,
        'D': m_d,
    },
    'neighbours': {
        'A': n_a,
        'B': n_b,
        'C': n_c,
        'D': n_d,
    },
    'cluster_labels': {
        'A': m_a['labels'],
        'B': m_b['labels'],
        'C': m_c.get('labels'),
        'D': m_d.get('labels'),
    },
}

with open(str(JSON_DIR / 'embedding_results.json'), 'w') as f:
    json.dump(results, f, ensure_ascii=False)
print("\nSaved: embedding_results.json")

# ── Build HTML report ──────────────────────────────────────────────────────────
PAL = ['#2563eb','#16a34a','#dc2626','#d97706','#7c3aed',
       '#0891b2','#be185d','#0f766e','#c2410c','#065f46']

METHOD_LABELS = {
    'A': 'A · TF-IDF + LSA 100d',
    'B': 'B · TF-IDF + LSA 384d',
    'C': 'C · Sentence Transformers',
    'D': 'D · API Embeddings',
}

def metric_row(key, methods):
    cells = ''
    vals = {m: methods[m].get(key) for m in 'ABCD'
            if methods[m].get('available', True) and methods[m].get(key) is not None}
    if not vals: return ''
    if key in ('silhouette', 'calinski_harabasz', 'intra_sim'):
        best = max(vals, key=vals.get)
    else:
        best = min(vals, key=vals.get)
    for m in 'ABCD':
        v = methods[m].get(key)
        if v is None:
            cells += '<td>—</td>'
        else:
            bold = ' style="font-weight:700;color:#2563eb"' if m == best else ''
            cells += f'<td{bold}>{v:.4f}</td>'
    return cells

methods = results['methods']
j_res   = json.dumps(results)

# Pre-computed to avoid backslash-in-f-string (Python < 3.12 compatibility)
if m_d.get('available'):
    method_d_card = ('<p style="font-size:.88rem"><strong>Model:</strong> '
                     + m_d.get('model', 'voyage-3')
                     + ' via Voyage AI. Batched at 8 texts per request. '
                     'Voyage embeddings are optimised for retrieval and '
                     'semantic similarity tasks.</p>')
else:
    method_d_card = ('<p class="unavail">Not available. Get a free API key at '
                     '<a href="https://dash.voyageai.com/">dash.voyageai.com</a> '
                     'then:<br><code>export VOYAGE_API_KEY=pa-...</code></p>')

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Embedding Method Comparison</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.27.0/plotly.min.js"></script>
<style>
:root{{--blue:#2563eb;--bg:#f8fafc;--card:#fff;--border:#e2e8f0}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:#1e293b;line-height:1.6}}
.header{{background:linear-gradient(135deg,#1e3a5f,#2563eb);color:#fff;padding:2.5rem 2rem;text-align:center}}
.header h1{{font-size:1.8rem;font-weight:700;margin-bottom:.4rem}}
.header p{{opacity:.85;font-size:.95rem}}
nav{{background:#fff;border-bottom:1px solid var(--border);padding:.6rem 1.5rem;position:sticky;top:0;z-index:99;display:flex;gap:1rem;flex-wrap:wrap}}
nav a{{text-decoration:none;color:#475569;font-size:.85rem;padding:.3rem .7rem;border-radius:4px}}
nav a:hover{{background:#eff6ff;color:var(--blue)}}
.container{{max-width:1400px;margin:0 auto;padding:1.5rem}}
section{{margin-bottom:3rem;scroll-margin-top:60px}}
h2{{font-size:1.35rem;font-weight:700;margin-bottom:.5rem;padding-bottom:.5rem;border-bottom:2px solid var(--blue)}}
.desc{{font-size:.9rem;color:#475569;margin-bottom:1rem}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:1.2rem;box-shadow:0 1px 3px rgba(0,0,0,.06);margin-bottom:1.5rem}}
table{{width:100%;border-collapse:collapse;font-size:.88rem}}
th{{background:#f1f5f9;padding:.5rem .9rem;text-align:left;font-weight:600;border-bottom:2px solid var(--border)}}
td{{padding:.45rem .9rem;border-bottom:1px solid #f1f5f9}}
tr:last-child td{{border-bottom:none}}
.method-badge{{display:inline-block;padding:.2rem .7rem;border-radius:4px;font-size:.8rem;font-weight:700;color:#fff}}
.unavail{{color:#94a3b8;font-style:italic}}
.ctrls{{display:flex;gap:.6rem;flex-wrap:wrap;margin-bottom:.8rem;align-items:center}}
.ctrls label{{font-size:.82rem;color:#475569;font-weight:500}}
.ctrls select{{padding:.3rem .6rem;border:1px solid var(--border);border-radius:5px;font-size:.82rem;background:#fff}}
.search-box{{padding:.45rem .8rem;border:1px solid var(--border);border-radius:5px;font-size:.88rem;width:280px}}
.nbr-result{{background:#f8fafc;border:1px solid var(--border);border-radius:6px;padding:.6rem 1rem;margin-bottom:.4rem;font-size:.85rem}}
.sim-score{{float:right;color:#2563eb;font-weight:600}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem}}
@media(max-width:800px){{.grid2{{grid-template-columns:1fr}}}}
.note{{background:#fffbeb;border:1px solid #fde68a;border-radius:6px;padding:.8rem 1rem;font-size:.85rem;color:#92400e;margin-bottom:1rem}}
</style>
</head>
<body>
<div class="header">
  <h1>📐 Embedding Method Comparison</h1>
  <p>TF-IDF + LSA vs Sentence Transformers vs API Embeddings · {N} books · Clustering quality metrics</p>
</div>
<nav>
  <a href="#metrics">📊 Metrics</a>
  <a href="#scatter">🗺 2D Scatter</a>
  <a href="#neighbours">🔗 Nearest Neighbours</a>
  <a href="#clusters">📦 Cluster Profiles</a>
  <a href="#methods">ℹ Methods</a>
</nav>
<div class="container">

<!-- 1. Metrics table -->
<section id="metrics">
  <h2>1 · Clustering Quality Metrics</h2>
  <p class="desc">All methods evaluated with K-Means at their optimal k (by silhouette score sweep k=3..10).
  <strong>Bold blue = best value</strong> per metric.</p>
  {'<div class="note">⚠ Methods C and/or D were not available — only A and B are shown. See the Methods section for install instructions.</div>' if not m_c.get('available') or not m_d.get('available') else ''}
  <div class="card">
    <table>
      <thead><tr>
        <th>Metric</th>
        <th><span class="method-badge" style="background:#2563eb">A</span> TF-IDF + LSA 100d</th>
        <th><span class="method-badge" style="background:#16a34a">B</span> TF-IDF + LSA 384d</th>
        <th><span class="method-badge" style="background:#dc2626">C</span> Sentence Transformers</th>
        <th><span class="method-badge" style="background:#d97706">D</span> API Embeddings</th>
      </tr></thead>
      <tbody>
        <tr><td>Best k</td>
          {''.join(f'<td>{methods[m].get("best_k","—")}</td>' for m in "ABCD")}</tr>
        <tr><td>Dimensions</td>
          {''.join(f'<td>{methods[m].get("dims","—")}</td>' for m in "ABCD")}</tr>
        <tr><td>Time (s)</td>
          {''.join(f'<td>{methods[m].get("time","—")}</td>' if methods[m].get("available",True) else "<td class=unavail>N/A</td>" for m in "ABCD")}</tr>
        <tr><td>Silhouette ↑</td>{metric_row("silhouette", methods)}</tr>
        <tr><td>Davies-Bouldin ↓</td>{metric_row("davies_bouldin", methods)}</tr>
        <tr><td>Calinski-Harabász ↑</td>{metric_row("calinski_harabasz", methods)}</tr>
        <tr><td>Intra-cluster sim ↑</td>{metric_row("intra_sim", methods)}</tr>
        <tr><td>Inter-cluster sim ↓</td>{metric_row("inter_sim", methods)}</tr>
      </tbody>
    </table>
  </div>
</section>

<!-- 2. 2D Scatter -->
<section id="scatter">
  <h2>2 · 2D Semantic Map</h2>
  <p class="desc">LSA 2D projection of the TF-IDF space. Colour by embedding cluster or LDA topic.
    The scatter geometry is the same for A and B (both derived from TF-IDF); if C or D are available
    their 2D projections are shown in separate tabs.</p>
  <div class="ctrls">
    <label>Colour by:</label>
    <select id="scatter_colour" onchange="drawScatter()">
      <option value="lda">LDA topic</option>
      <option value="A">Method A clusters</option>
      <option value="B">Method B clusters</option>
      {'<option value="C">Method C clusters</option>' if m_c.get('available') else ''}
      {'<option value="D">Method D clusters</option>' if m_d.get('available') else ''}
    </select>
  </div>
  <div class="card" id="scatter_chart"></div>
</section>

<!-- 3. Nearest neighbours explorer -->
<section id="neighbours">
  <h2>3 · Nearest Neighbours Explorer</h2>
  <p class="desc">For a given book, compare the top-3 nearest neighbours found by each method.
  Differences reveal where TF-IDF and semantic embeddings disagree.</p>
  <div class="ctrls">
    <input class="search-box" id="nbr_q" type="text" placeholder="Search book title…" oninput="filterNbrBooks()">
  </div>
  <div id="nbr_book_list" style="max-height:200px;overflow-y:auto;margin-bottom:.8rem"></div>
  <div id="nbr_results"></div>
</section>

<!-- 4. Cluster profiles -->
<section id="clusters">
  <h2>4 · Cluster Composition by Method</h2>
  <p class="desc">For each method, how do its clusters map onto the LDA topic labels? A diagonal-heavy
  heatmap means the clusters align with LDA topics. Off-diagonal cells reveal books that cluster
  differently under TF-IDF vs semantic embeddings.</p>
  <div class="ctrls">
    <label>Method:</label>
    <select id="cluster_method" onchange="drawClusterHeatmap()">
      <option value="A">A · TF-IDF + LSA 100d</option>
      <option value="B">B · TF-IDF + LSA 384d</option>
      {'<option value="C">C · Sentence Transformers</option>' if m_c.get('available') else ''}
      {'<option value="D">D · API Embeddings</option>' if m_d.get('available') else ''}
    </select>
  </div>
  <div class="card" id="cluster_heatmap"></div>
</section>

<!-- 5. Methods reference -->
<section id="methods">
  <h2>5 · Methods Reference</h2>
  <div class="grid2">
    <div class="card">
      <h3 style="margin-bottom:.5rem"><span class="method-badge" style="background:#2563eb">A</span>
        TF-IDF + LSA 100d</h3>
      <p style="font-size:.88rem">Current pipeline baseline. TF-IDF vectorisation (3,000 features,
      bigrams) followed by Truncated SVD to 100 dimensions. Fast and interpretable.
      Captures lexical co-occurrence patterns but not semantic similarity between different words.</p>
    </div>
    <div class="card">
      <h3 style="margin-bottom:.5rem"><span class="method-badge" style="background:#16a34a">B</span>
        TF-IDF + LSA 384d</h3>
      <p style="font-size:.88rem">Same TF-IDF vocabulary, expanded to 384 dimensions to match the
      output size of sentence-transformer models. Covers {results['methods']['B'].get('variance_explained', 0):.1%} of TF-IDF
      variance vs 41% for 100d. Useful for isolating the effect of dimensionality
      from the effect of the embedding model.</p>
    </div>
    <div class="card">
      <h3 style="margin-bottom:.5rem"><span class="method-badge" style="background:#dc2626">C</span>
        Sentence Transformers</h3>
      {'<p style="font-size:.88rem"><strong>Model:</strong> all-MiniLM-L6-v2 (22M params, 384-dim output). Trained on 1B sentence pairs via contrastive learning. Encodes semantic meaning — two sentences with different words but the same meaning will have similar embeddings. Strong at paraphrase detection and semantic clustering.</p><p style="font-size:.85rem;margin-top:.4rem;color:#475569">Install: <code>pip install sentence-transformers</code></p>' if m_c.get('available') else f'<p class="unavail">Not available. Install with:<br><code>pip install sentence-transformers</code><br>Then re-run this script.</p>'}
    </div>
    <div class="card">
      <h3 style="margin-bottom:.5rem"><span class="method-badge" style="background:#d97706">D</span>
        Anthropic API Embeddings</h3>
      {method_d_card}
    </div>
  </div>
</section>

</div>
<footer style="text-align:center;padding:1.5rem;color:#94a3b8;font-size:.8rem;border-top:1px solid var(--border);margin-top:2rem">
  Embedding Comparison · {N} books · Plotly.js
</footer>

<script>
const R = {j_res};
const PAL = {json.dumps(PAL)};
const LAYOUT = {{paper_bgcolor:'transparent',plot_bgcolor:'#f8fafc',
                 hoverlabel:{{bgcolor:'#1e293b',font:{{color:'white',size:12}}}}}};

// ── Scatter ──────────────────────────────────────────────────────────────────
function drawScatter() {{
  const colBy = document.getElementById('scatter_colour').value;
  const xy    = R.coords_2d_lsa;
  const groups = colBy === 'lda' ? R.lda_topics : (R.cluster_labels[colBy] || R.lda_topics);
  const names  = colBy === 'lda' ? R.lda_names  : [...new Set(groups)].sort((a,b)=>a-b).map(g=>'Cluster '+(g+1));
  const n_g    = colBy === 'lda' ? R.lda_names.length : Math.max(...groups)+1;

  const traces = [];
  for (let g=0; g<n_g; g++) {{
    const idx = groups.map((v,i)=>v===g?i:-1).filter(i=>i>=0);
    if (!idx.length) continue;
    traces.push({{
      x: idx.map(i=>xy[i][0]), y: idx.map(i=>xy[i][1]),
      mode:'markers', type:'scatter',
      name: colBy==='lda' ? (R.lda_names[g]||'T'+(g+1)) : 'Cluster '+(g+1),
      marker:{{color:PAL[g%PAL.length],size:8,opacity:.75,line:{{color:'white',width:0.5}}}},
      text: idx.map(i=>`<b>${{R.titles[i].substring(0,50)}}</b><br>${{R.authors[i]}}<br>${{R.pub_years[i]||''}}`),
      hovertemplate:'%{{text}}<extra></extra>',
    }});
  }}
  Plotly.react('scatter_chart', traces, {{
    ...LAYOUT, height:520,
    margin:{{t:10,b:60,l:60,r:20}},
    xaxis:{{title:'LSA Dim 1',zeroline:false}},
    yaxis:{{title:'LSA Dim 2',zeroline:false}},
    legend:{{orientation:'h',y:-0.2,font:{{size:9}}}},
  }});
}}
drawScatter();

// ── Nearest neighbours ────────────────────────────────────────────────────────
let nbr_selected = 0;

function filterNbrBooks() {{
  const q = document.getElementById('nbr_q').value.toLowerCase();
  const list = document.getElementById('nbr_book_list');
  list.innerHTML = '';
  R.titles.forEach((t,i) => {{
    if (!q || t.toLowerCase().includes(q)) {{
      const d = document.createElement('div');
      d.style.cssText = 'padding:.3rem .6rem;cursor:pointer;font-size:.85rem;border-bottom:1px solid #f1f5f9';
      d.textContent = t;
      d.onclick = () => {{ nbr_selected=i; showNeighbours(i); }};
      list.appendChild(d);
    }}
  }});
}}

function showNeighbours(idx) {{
  const methods = {{'A':'TF-IDF + LSA 100d','B':'TF-IDF + LSA 384d',
    'C':'Sentence Transformers','D':'API Embeddings'}};
  const colors  = {{'A':'#2563eb','B':'#16a34a','C':'#dc2626','D':'#d97706'}};
  let html = `<h4 style="margin-bottom:.6rem">${{R.titles[idx]}}</h4>`;
  for (const [m, label] of Object.entries(methods)) {{
    const nbrs = R.neighbours[m];
    if (!nbrs) {{
      html += `<div class="nbr-result"><span class="method-badge" style="background:${{colors[m]}}">${{m}}</span>
        <span class="unavail" style="margin-left:.5rem">Not available</span></div>`;
      continue;
    }}
    html += `<div class="nbr-result"><span class="method-badge" style="background:${{colors[m]}}">${{m}}</span>
      <strong style="margin-left:.5rem">${{label}}</strong><br>`;
    nbrs[idx].forEach((n,i) => {{
      html += `<div style="padding:.2rem 0 .2rem 1rem;font-size:.83rem">
        ${{i+1}}. ${{R.titles[n.idx].substring(0,60)}}
        <span class="sim-score">${{n.sim.toFixed(3)}}</span>
      </div>`;
    }});
    html += '</div>';
  }}
  document.getElementById('nbr_results').innerHTML = html;
}}
filterNbrBooks();
if (R.titles.length > 0) showNeighbours(0);

// ── Cluster heatmap ───────────────────────────────────────────────────────────
function drawClusterHeatmap() {{
  const m = document.getElementById('cluster_method').value;
  const cl = R.cluster_labels[m];
  if (!cl) {{ Plotly.purge('cluster_heatmap'); return; }}
  const n_lda = R.lda_names.length;
  const n_cl  = Math.max(...cl) + 1;

  // Build confusion matrix: rows=clusters, cols=LDA topics
  const mat = Array.from({{length:n_cl}},()=>Array(n_lda).fill(0));
  cl.forEach((c,i) => mat[c][R.lda_topics[i]]++);
  const mat_norm = mat.map(row=>{{
    const tot = row.reduce((a,b)=>a+b,0);
    return tot>0 ? row.map(v=>+(v/tot).toFixed(3)) : row;
  }});

  const ann = [];
  mat_norm.forEach((row,i) => row.forEach((v,j) => {{
    if (v>0) ann.push({{
      x:j, y:i, text:`${{(v*100).toFixed(0)}}%`,
      showarrow:false, font:{{size:9,color:v>0.4?'white':'#1e293b'}}
    }});
  }}));

  Plotly.react('cluster_heatmap',[{{
    z:mat_norm, x:R.lda_names, y:mat.map((_,i)=>'Cluster '+(i+1)),
    type:'heatmap',
    colorscale:[[0,'#f0f9ff'],[0.25,'#7dd3fc'],[0.5,'#2563eb'],[1,'#1e3a5f']],
    hovertemplate:'Cluster %{{y}}<br>LDA: %{{x}}<br>%{{z:.0%}}<extra></extra>',
  }}],{{
    ...LAYOUT, height: Math.max(300, n_cl*36+120),
    margin:{{t:10,b:120,l:90,r:20}},
    xaxis:{{tickangle:-35,tickfont:{{size:9}}}},
    yaxis:{{tickfont:{{size:10}}}},
    annotations: ann,
  }});
}}
drawClusterHeatmap();
</script>
</body></html>"""

html = html.replace('</body>', _PROV_NOTICE + '\n</body>', 1)
out_path = 'data/outputs/book_nlp_embedding_comparison.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Saved: {out_path}  ({len(html)//1024} KB)")