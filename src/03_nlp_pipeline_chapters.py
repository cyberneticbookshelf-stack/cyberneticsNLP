"""


03_nlp_pipeline_chapters.py
─────────────────────────────────────────────────────────────────────────────
Chapter-level NLP pipeline.

Document source for topic modelling and clustering:
  → Chapter summaries (clean prose written per chapter)
  → Short chapters (<20 words) are augmented with the book-level
    descriptive summary for context.

Keyphrase extraction uses the raw chapter text from books_clean.json.

Steps:
  1. Build chapter corpus from summaries.json
  2. TF-IDF vectorisation
  3. NMF topic modelling  (k = N_MIN..N_MAX, choose by reconstruction error elbow;
  #     no L1/L2 regularisation — short 50-word documents collapse under any alpha>0)
  4. K-Means clustering   (k = KM_MIN..KM_MAX, elbow + silhouette)
  5. Keyphrase extraction from raw chapter text
  6. Cosine similarity (chapter × chapter)
  7. 2-D LSA projection

Input:  summaries.json, books_clean.json, nlp_results.json (for book order)
Output: nlp_results_chapters.json
"""

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_lang.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


import re, json, warnings
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF, TruncatedSVD
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity

warnings.filterwarnings('ignore')

# ── Config ────────────────────────────────────────────────────────────────────
MAX_FEATURES   = 1500
N_MIN, N_MAX   = 5, 12
KM_MIN, KM_MAX = 5, 20
TOP_WORDS      = 12
TOP_KP         = 8
SAMPLE_LEN     = 20000   # chars for keyphrase extraction

STOPWORDS = set("""
a about above after again against all also am an and any are as at be because
been before being below between both but by can cannot could did do does doing
down during each few for from further get had has have having he her here hers
herself him himself his how if in into is it its itself let me more most my
myself no nor not of off on once only or other our ours ourselves out over own
same she should so some such than that the their theirs them themselves then
there these they this those through to too under until up very was we were what
when where which while who whom why will with would you your yours yourself
yourselves may thus hence therefore however moreover furthermore indeed whereas
whether although though since upon within without toward towards
also one two three four five six seven eight nine ten eleven twelve
first second third fourth fifth finally thus hence
book chapter section appendix notes references bibliography
ibid dans pour avec les des une par que qui sur aussi
lemma theorem proof corollary proposition hence suppose therefore qed
figure table page item listed provides discussion
said used made well known given shows shown
isbn issn isbn published press university
""".split())


# ── Chapter splitter (for raw-text keyphrase extraction) ─────────────────────
CHPAT = [
    r'CHAPTER\s+(?:ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|'
    r'ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN)(?:\s+[A-Z][A-Za-z\s,:\-]{0,80})?',
    r'CHAPTER\s+(?:1[0-5]|\d)(?:\s+[A-Z][A-Za-z\s,:\-]{0,80})?',
    r'Chapter\s+(?:1[0-5]|\d)(?:\s+[A-Z][A-Za-z\s,:\-]{0,60})?',
    r'Part\s+(?:[IVX]{1,4}|\d)(?:\s+[A-Z][A-Za-z\s,:\-]{0,60})?',
    r'\b(?:1[0-5]|\d)\.\s+[A-Z][a-zA-Z]{3,}(?:\s+[A-Za-z]{2,}){3,}',
]
SPLIT_RE = re.compile(r'(?<!\w)(?:' + '|'.join(CHPAT) + r')(?!\w)', re.UNICODE)

def raw_split(text, min_words=400, max_chs=20):
    splits = [(m.start(), m.group()) for m in SPLIT_RE.finditer(text)]
    if not splits:
        chunk = max(len(text)//5, 10000)
        return [text[i*chunk:(i+1)*chunk] for i in range(5)
                if len(text[i*chunk:(i+1)*chunk].split()) >= min_words]
    raw = []
    if splits[0][0] > 200:
        raw.append(text[:splits[0][0]])
    for i, (pos, t) in enumerate(splits):
        end = splits[i+1][0] if i+1 < len(splits) else len(text)
        raw.append(text[pos+len(t):end].strip())
    good  = [t for t in raw if len(t.split()) >= min_words]
    minor = ' '.join(t for t in raw if len(t.split()) < min_words)
    if len(minor.split()) >= min_words:
        good.append(minor)
    if len(good) > max_chs:
        good.sort(key=lambda t: len(t.split()), reverse=True)
        good = good[:max_chs]
    return good


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    with open(str(JSON_DIR / 'summaries.json'), encoding='utf-8') as f:
        S = json.load(f)
    with open(str(JSON_DIR / 'books_clean.json'), encoding='utf-8') as f:
        books = json.load(f)
    with open(str(JSON_DIR / 'nlp_results.json')) as f:
        prev = json.load(f)

    book_ids = prev['book_ids']

    # ── 1. Build chapter corpus ───────────────────────────────────────────────
    all_chapters = []
    for bid in book_ids:
        book_data  = books[bid]
        book_desc  = S[bid].get('descriptive', '')
        raw_texts  = raw_split(book_data['clean_text'])

        for ch in S[bid]['chapters']:
            idx   = ch['index']
            summ  = ch.get('summary', '').strip()
            title = ch.get('title', f'Chapter {idx}')

            # Build NMF/cluster input: title + summary; short → augment with book desc
            if len(summ.split()) < 20:
                nlp_text = f"{title}. {book_desc}"
            else:
                nlp_text = f"{title}. {summ}"

            # Raw text for keyphrases: match by index if available
            raw_text = raw_texts[idx-1] if idx-1 < len(raw_texts) else book_data['clean_text']

            all_chapters.append({
                'chapter_id':  f"{bid}_ch{idx:03d}",
                'book_id':     bid,
                'book_title':  book_data['title'],
                'book_author': book_data['author'],
                'ch_index':    idx,
                'ch_title':    title,
                'word_count':  ch.get('word_count', 0),
                'summary':     summ,
                'nlp_text':    nlp_text,
                'raw_text':    raw_text[:SAMPLE_LEN],
            })

    N = len(all_chapters)
    print(f"Total chapters: {N}")

    nlp_texts  = [ch['nlp_text'] for ch in all_chapters]
    raw_texts_ = [ch['raw_text'] for ch in all_chapters]

    # ── 2. TF-IDF on summaries ────────────────────────────────────────────────
    print("TF-IDF on chapter summaries …")
    vec = TfidfVectorizer(
        max_features=MAX_FEATURES,
        stop_words=list(STOPWORDS),
        token_pattern=r'(?u)\b[a-zA-Z]{4,}\b',
        min_df=2,
        max_df=0.90,
        ngram_range=(1, 2),
        sublinear_tf=True,
    )
    tfidf = vec.fit_transform(nlp_texts)
    vocab = vec.get_feature_names_out()
    print(f"  Shape: {tfidf.shape}")

    # ── 3. NMF topic modelling ────────────────────────────────────────────────
    print(f"NMF (k={N_MIN}..{N_MAX}) …")
    errors = {}
    best_nmf, best_k_nmf, best_err = None, N_MIN, float('inf')
    for k in range(N_MIN, N_MAX + 1):
        nmf = NMF(n_components=k, random_state=99, max_iter=500,
                  init='nndsvda', alpha_W=0.0, alpha_H=0.0)
        W = nmf.fit_transform(tfidf)
        err = nmf.reconstruction_err_
        errors[k] = round(err, 2)
        print(f"  k={k}  reconstruction_err={err:.2f}")
        if err < best_err:
            best_err, best_k_nmf, best_nmf = err, k, nmf
            best_W = W

    # Elbow on reconstruction errors: biggest second difference
    ks_  = list(range(N_MIN, N_MAX + 1))
    vals = [errors[k] for k in ks_]
    if len(vals) >= 3:
        d2 = np.diff(np.diff(vals))
        elbow_k = ks_[int(np.argmax(np.abs(d2))) + 1]
    else:
        elbow_k = best_k_nmf

    print(f"Chosen k (elbow on recon error): {elbow_k}")
    best_k_nmf = elbow_k
    nmf_final  = NMF(n_components=best_k_nmf, random_state=99, max_iter=500,
                     init='nndsvda', alpha_W=0.0, alpha_H=0.0)
    W_final = nmf_final.fit_transform(tfidf)

    # Topic assignments
    dominant_topic = W_final.argmax(axis=1).tolist()
    doc_topic      = (W_final / (W_final.sum(axis=1, keepdims=True) + 1e-10)).tolist()

    # Top words per topic
    top_words = []
    for comp in nmf_final.components_:
        idx = comp.argsort()[::-1][:TOP_WORDS]
        top_words.append([vocab[i] for i in idx])

    print(f"\nNMF topics at k={best_k_nmf}:")
    for t, words in enumerate(top_words):
        print(f"  T{t+1}: {', '.join(words)}")

    # ── 4. K-Means clustering ─────────────────────────────────────────────────
    print("\nK-Means …")
    tfidf_dense  = tfidf.toarray()
    inertias, silhouettes = {}, {}
    for k in range(KM_MIN, KM_MAX + 1):
        km   = KMeans(n_clusters=k, random_state=99, n_init=10, max_iter=300)
        labs = km.fit_predict(tfidf_dense)
        inertias[k]    = km.inertia_
        silhouettes[k] = round(silhouette_score(tfidf_dense, labs,
                                                 sample_size=min(200, N)), 4)

    ks   = sorted(inertias)
    vals = [inertias[k] for k in ks]
    d2   = np.diff(np.diff(vals))
    best_k_km = ks[int(np.argmax(d2)) + 1]
    best_sil  = max(silhouettes, key=silhouettes.get)
    print(f"Elbow k={best_k_km}  Silhouette k={best_sil}")

    final_km      = KMeans(n_clusters=best_k_km, random_state=99,
                           n_init=10, max_iter=500)
    cluster_labels = final_km.fit_predict(tfidf_dense).tolist()

    # ── 5. Keyphrases from raw text ───────────────────────────────────────────
    print("Keyphrases …")
    kp_vec = TfidfVectorizer(
        max_features=8000,
        stop_words=list(STOPWORDS),
        token_pattern=r'(?u)\b[a-zA-Z]{4,}\b',
        ngram_range=(1, 3),
        min_df=1,
        sublinear_tf=True,
    )
    kp_mat   = kp_vec.fit_transform(raw_texts_)
    kp_vocab = kp_vec.get_feature_names_out()

    keyphrases = {}
    for i, ch in enumerate(all_chapters):
        row   = kp_mat[i].toarray().flatten()
        top_i = row.argsort()[::-1][:TOP_KP]
        kps   = [kp_vocab[j] for j in top_i if row[j] > 0]
        keyphrases[ch['chapter_id']] = kps

    # ── 6. Cosine similarity ──────────────────────────────────────────────────
    print("Cosine similarity …")
    normed = normalize(tfidf, norm='l2')
    cosine = cosine_similarity(normed)

    # ── 7. 2-D LSA projection ─────────────────────────────────────────────────
    print("LSA 2-D …")
    svd    = TruncatedSVD(n_components=2, random_state=99)
    coords = svd.fit_transform(tfidf)

    # ── 8. Book-level topic summary ───────────────────────────────────────────
    book_topic_counts = {}
    for i, ch in enumerate(all_chapters):
        bid = ch['book_id']
        t   = dominant_topic[i]
        if bid not in book_topic_counts:
            book_topic_counts[bid] = [0] * best_k_nmf
        book_topic_counts[bid][t] += 1

    # ── 9. Save ───────────────────────────────────────────────────────────────
    result = {
        'chapters':        [{k: v for k, v in ch.items()
                             if k not in ('nlp_text', 'raw_text', 'summary')}
                            for ch in all_chapters],
        'chapter_ids':     [ch['chapter_id'] for ch in all_chapters],
        'book_ids':        book_ids,
        'book_id_per_ch':  [ch['book_id'] for ch in all_chapters],
        'titles_list':     [f"{ch['book_title'][:30]}|{ch['ch_title'][:30]}"
                            for ch in all_chapters],
        # NMF
        'n_topics':        best_k_nmf,
        'recon_errors':    {str(k): v for k, v in errors.items()},
        'doc_topic':       doc_topic,
        'dominant_topics': dominant_topic,
        'top_words':       top_words,
        # Clustering
        'best_k':          best_k_km,
        'cluster_labels':  cluster_labels,
        'inertias':        {str(k): v for k, v in inertias.items()},
        'silhouettes':     {str(k): v for k, v in silhouettes.items()},
        # Keyphrases
        'keyphrases':      keyphrases,
        # Similarity / projection
        'cosine_sim':      cosine.tolist(),
        'coords_2d':       coords.tolist(),
        # Book-level aggregate
        'book_topic_counts': book_topic_counts,
    }

    with open(str(JSON_DIR / 'nlp_results_chapters.json'), 'w') as f:
        json.dump(result, f)

    print(f"\n✓ Saved nlp_results_chapters.json")
    print(f"  {N} chapters  |  {best_k_nmf} NMF topics  |  {best_k_km} clusters")

if __name__ == '__main__':
    main()