import json, re, sys, math, numpy as np, pandas as pd
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity

# ── Stopwords (manual, since nltk unavailable) ──────────────────────────────

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_lang.csv, csv/books_text_*.csv
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
many much first second third new old p pp pp cited ibid et al chapter book
fig figure table see also note notes pp chapter chapters vol volume edition
ed eds press university oxford cambridge london new york
""".split())

# ── CLI flags ────────────────────────────────────────────────────────────────
WEIGHTED     = '--weighted'     in sys.argv
NAME_TOPICS  = '--name-topics'  in sys.argv

# --topics N: override the automatic k selection for LDA
_FIXED_TOPICS = None
if '--topics' in sys.argv:
    try:
        _FIXED_TOPICS = int(sys.argv[sys.argv.index('--topics') + 1])
        print(f'  [--topics] fixed at {_FIXED_TOPICS}')
    except (IndexError, ValueError):
        print('  [--topics] usage: --topics N  (integer)')

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
titles     = [books[b]['title'] for b in book_ids]
authors    = [books[b]['author'] for b in book_ids]

# Multi-point sampling: three 20k-char slices (early/middle/late) concatenated.
# Total sample = 60k chars, same as before, but now representative of the whole
# book rather than just the introduction.
# Slice positions: 10% (past front matter), 50% (argumentative core), 85% (conclusions).
# Minimum offset of 4000 chars avoids publisher pages / copyright blocks.
SLICE_LEN = 20000

def sample_book(text):
    n = len(text)
    offsets = [max(int(n * p), 4000) for p in (0.10, 0.50, 0.85)]
    slices = [text[o: o + SLICE_LEN] for o in offsets]
    return ' '.join(slices)

texts = [sample_book(books[b]['clean_text']) for b in book_ids]

print(f"Processing {len(texts)} books...")

# ── 1. TF-IDF Vectorisation ──────────────────────────────────────────────────
tfidf = TfidfVectorizer(max_features=3000, stop_words=list(STOPWORDS),
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
cv = CountVectorizer(max_features=3000, stop_words=list(STOPWORDS),
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

# Fit LDA for k = N_TOPICS_MIN..N_TOPICS_MAX, select by mean NPMI coherence
N_TOPICS_MIN = 2
N_TOPICS_MAX = min(12, max(3, len(book_ids) // 2))
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

if _FIXED_TOPICS is not None and _FIXED_TOPICS in perplexities:
    best_n = _FIXED_TOPICS
    best_lda = LatentDirichletAllocation(
        n_components=best_n, max_iter=20, learning_method='online',
        random_state=99, learning_offset=50., doc_topic_prior=0.1)
    best_lda.fit(X_count)
    best_coh = coherences.get(best_n, 0.0)
    print(f'\n[--topics] Using forced n_topics={best_n}')
else:
    print(f"\nBest n_topics={best_n} (highest coherence={best_coh:.4f}, "
          f"perplexity={perplexities[best_n]:.1f})")

# Get topic-word distributions for best model
def get_top_words(model, feature_names, n_top=12):
    topics = []
    for idx, topic in enumerate(model.components_):
        top_idx = topic.argsort()[:-n_top-1:-1]
        topics.append([feature_names[i] for i in top_idx])
    return topics

top_words      = get_top_words(best_lda, cv_vocab)
doc_topic      = best_lda.transform(X_count)
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

    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
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
            f"(675 books, 1954-2025).\n\n"
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
}

# Carry forward topic_names from a previous run if n_topics matches
# (so names survive --weighted re-runs without --name-topics)
try:
    with open(str(JSON_DIR / 'nlp_results.json')) as _f:
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

with open(str(JSON_DIR / 'nlp_results.json'), 'w') as f:
    json.dump(results, f)
print("\nNLP pipeline complete. Results saved to nlp_results.json")
if results.get('topic_names'):
    print('Topic names:')
    for i, name in enumerate(results['topic_names']):
        print(f'  T{i+1}: {name}')