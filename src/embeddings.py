"""


embeddings.py — Improvement 5: Embedding provider abstraction
─────────────────────────────────────────────────────────────
Provides a unified interface for producing document embeddings.
03_nlp_pipeline.py and 11_embedding_comparison.py import from here.

Usage in 03_nlp_pipeline.py:
    from embeddings import get_embedder
    embedder = get_embedder('lsa')          # fast, no deps
    embedder = get_embedder('sentence')     # requires sentence-transformers
    embedder = get_embedder('voyage')       # requires VOYAGE_API_KEY
    X = embedder.embed(texts)              # returns (n, d) normalised array
"""

# ── Directory layout ─────────────────────────────────────────────────────────
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')    # input CSVs:  csv/books_metadata_full.csv, csv/books_text_*.csv
JSON_DIR = _pl.Path('json')   # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)


import os, json, time
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize


# ── Base class ────────────────────────────────────────────────────────────────
class Embedder:
    name = 'base'
    dims = None

    def embed(self, texts: list[str]) -> np.ndarray:
        raise NotImplementedError

    def __repr__(self):
        return f"<Embedder: {self.name} ({self.dims}d)>"


# ── A: TF-IDF + LSA ──────────────────────────────────────────────────────────
class LSAEmbedder(Embedder):
    def __init__(self, n_components=100, tfidf_vectorizer=None, random_state=99):
        self.n_components = n_components
        self.random_state = random_state
        self.vec = tfidf_vectorizer   # can inject pre-fitted vectoriser
        self.svd = None
        self.name = f'lsa_{n_components}d'
        self.dims = n_components

    def embed(self, texts):
        from sklearn.feature_extraction.text import TfidfVectorizer
        if self.vec is None:
            self.vec = TfidfVectorizer(
                max_features=3000, min_df=2, max_df=0.95,
                ngram_range=(1, 2), sublinear_tf=True,
                token_pattern=r'(?u)\b[a-zA-Z]{4,}\b',
            )
            X_tfidf = self.vec.fit_transform(texts)
        else:
            X_tfidf = self.vec.transform(texts)

        n_comp = min(self.n_components, X_tfidf.shape[1] - 1)
        self.svd = TruncatedSVD(n_components=n_comp, random_state=self.random_state)
        X = normalize(self.svd.fit_transform(X_tfidf))
        self.dims = n_comp
        self.variance_explained = float(self.svd.explained_variance_ratio_.sum())
        return X

    def transform_2d(self, texts):
        """Return 2D LSA projection for visualisation."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        if self.vec is None:
            raise RuntimeError("Call embed() before transform_2d()")
        X_tfidf = self.vec.transform(texts)
        svd2 = TruncatedSVD(n_components=2, random_state=self.random_state)
        return normalize(svd2.fit_transform(X_tfidf))


# ── C: Sentence Transformers ─────────────────────────────────────────────────
class SentenceEmbedder(Embedder):
    def __init__(self, model_name='all-MiniLM-L6-v2', batch_size=32):
        self.model_name = model_name
        self.batch_size = batch_size
        self.name = f'sentence:{model_name}'
        self.dims = None
        self._check_deps()

    def _check_deps(self):
        try:
            import torch
            from packaging.version import Version
            if Version(torch.__version__.split('+')[0]) < Version('2.4'):
                raise RuntimeError(
                    f"PyTorch {torch.__version__} found; sentence-transformers "
                    f"requires >= 2.4. Fix: pip install torch --upgrade  "
                    f"or: pip install 'sentence-transformers==2.7.0'"
                )
        except ImportError:
            raise RuntimeError(
                "PyTorch not installed. Fix: pip install torch sentence-transformers"
            )

    def embed(self, texts):
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(self.model_name)
        X = model.encode(texts, batch_size=self.batch_size,
                         show_progress_bar=True, convert_to_numpy=True)
        self.dims = X.shape[1]
        return normalize(X)


# ── D: Voyage AI ─────────────────────────────────────────────────────────────
class VoyageEmbedder(Embedder):
    def __init__(self, model='voyage-3', cache_path=str(JSON_DIR / 'voyage_embeddings_cache.json'),
                 delay=22):
        self.model      = model
        self.cache_path = cache_path
        self.delay      = delay          # seconds between requests (free tier ~3/min)
        self.name       = f'voyage:{model}'
        self.dims       = None
        self.key        = os.environ.get('VOYAGE_API_KEY', '')
        if not self.key:
            raise RuntimeError(
                "VOYAGE_API_KEY not set. Get a free key at https://dash.voyageai.com/ "
                "then: export VOYAGE_API_KEY=pa-..."
            )

    def embed(self, texts, book_ids=None):
        """
        Embed texts via Voyage AI API.
        book_ids: optional list of IDs for cache keying (uses index if None).
        """
        import urllib.request
        keys = book_ids if book_ids else [str(i) for i in range(len(texts))]
        cache = {}
        if os.path.exists(self.cache_path):
            with open(self.cache_path) as f:
                cache = json.load(f)
            print(f"  Voyage cache: {len(cache)}/{len(texts)} already done")

        for i, (text, key) in enumerate(zip(texts, keys)):
            if key in cache:
                continue
            payload = json.dumps({
                'model': self.model,
                'input': [text],
                'input_type': 'document',
            }).encode()
            req = urllib.request.Request(
                'https://api.voyageai.com/v1/embeddings',
                data=payload,
                headers={'Content-Type': 'application/json',
                         'Authorization': f'Bearer {self.key}'},
                method='POST',
            )
            for attempt in range(8):
                try:
                    with urllib.request.urlopen(req, timeout=60) as r:
                        resp = json.loads(r.read())
                    cache[key] = resp['data'][0]['embedding']
                    with open(self.cache_path, 'w') as f:
                        json.dump(cache, f)
                    break
                except urllib.error.HTTPError as e:
                    if e.code == 429:
                        wait = min(self.delay * (2 ** attempt), 300)
                        print(f"  [{i+1}/{len(texts)}] rate limit — waiting {wait}s")
                        time.sleep(wait)
                    else:
                        raise
            else:
                raise RuntimeError(
                    f"Rate limit exceeded after 8 retries for key {key}. "
                    f"Progress saved to {self.cache_path} — rerun to resume."
                )
            if i % 20 == 0 or i == len(texts) - 1:
                remaining = (len(texts) - len(cache)) * self.delay
                print(f"  {len(cache)}/{len(texts)} embedded "
                      f"(~{remaining//60:.0f} min remaining)")
            time.sleep(self.delay)

        X = np.array([cache[k] for k in keys], dtype=np.float32)
        self.dims = X.shape[1]
        return normalize(X)


# ── Factory ───────────────────────────────────────────────────────────────────
def get_embedder(mode: str, **kwargs) -> Embedder:
    """
    Factory function — returns the right embedder for the requested mode.

    Modes:
        'lsa'      — TF-IDF + LSA 100d (default, no deps)
        'lsa384'   — TF-IDF + LSA 384d
        'sentence' — Sentence Transformers all-MiniLM-L6-v2
        'voyage'   — Voyage AI API (requires VOYAGE_API_KEY)

    Extra kwargs are passed to the embedder constructor.

    Example:
        embedder = get_embedder('lsa', n_components=200)
        embedder = get_embedder('sentence', model_name='all-mpnet-base-v2')
    """
    mode = mode.lower().strip()
    if mode == 'lsa':
        return LSAEmbedder(n_components=kwargs.get('n_components', 100),
                           random_state=kwargs.get('random_state', 99))
    elif mode == 'lsa384':
        return LSAEmbedder(n_components=384,
                           random_state=kwargs.get('random_state', 99))
    elif mode in ('sentence', 'st', 'sbert'):
        return SentenceEmbedder(
            model_name=kwargs.get('model_name', 'all-MiniLM-L6-v2'),
            batch_size=kwargs.get('batch_size', 32))
    elif mode in ('voyage', 'voyageai'):
        return VoyageEmbedder(
            model=kwargs.get('model', 'voyage-3'),
            cache_path=kwargs.get('cache_path', str(JSON_DIR / 'voyage_embeddings_cache.json')),
            delay=kwargs.get('delay', 22))
    else:
        raise ValueError(
            f"Unknown embedding mode: '{mode}'. "
            f"Choose from: lsa, lsa384, sentence, voyage"
        )


# ── CLI convenience ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("Available embedding modes:")
    for mode, cls in [('lsa', LSAEmbedder), ('lsa384', LSAEmbedder),
                      ('sentence', SentenceEmbedder), ('voyage', VoyageEmbedder)]:
        print(f"  {mode:12s} — {cls.__doc__ or cls.__name__}")