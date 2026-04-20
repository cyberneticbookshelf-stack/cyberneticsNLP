# Methodology

## 1. Text Parsing and Cleaning

### Parsing (`01_parse_books.py` / `parse_and_clean_stream.py`)

The Calibre text export is provided as a set of CSV files named
`books_text_01.csv` … `books_text_25.csv`, each with two columns:
`id` (Calibre book identifier) and `searchable_text` (full OCR-extracted
book text). Metadata (title, author, publication year, publisher, inclusion stratum,
and keyword flags) is sourced from `books_metadata_full.csv` (tab-separated,
20 columns, exported from Calibre via `00_export_calibre.py`).

For small corpora (<~300 books), `01_parse_books.py` globs all matching CSV
files, merges them into a single `books_parsed.json`, and feeds step 02.
For large corpora, `parse_and_clean_stream.py` processes one CSV file at a
time, writing directly to `books_clean.json` and bypassing steps 01 and 02
entirely to avoid loading a 500+ MB JSON into memory.

Duplicate book IDs across files are resolved by keeping the first occurrence
(alphabetical file order).

### Boilerplate Removal and Dictionary Filtering (`02_clean_text.py`)

Two-stage cleaning:

**Stage 1: Section removal (state machine)**

A state machine scans the text and removes structural sections by detecting
their headers, consuming up to 500 lines per section. Sections removed:
table of contents, list of figures/tables, preface/foreword/prologue,
series editor preface, editorial note, acknowledgements, dedication,
about the author, contributors list, index (subject/name/author/analytical),
bibliography, references, works cited, further reading.

Inline patterns removed: copyright blocks, ISBN/ISSN, Library of Congress
cataloguing data, blank-page markers, URLs, DOIs.

**Stage 2: Dictionary filtering**

Tokens are accepted or rejected against an English dictionary supplemented
with a 281-term academic/cybernetics domain whitelist. Dictionary discovery
uses a portable, OS-agnostic mechanism with no hardcoded file paths —
`_find_dic_via_system()` tries five methods in order: (1) `DICPATH`
environment variable (hunspell's own standard, set this to override
everything else), (2) `hunspell -D` binary query, (3) recursive glob of
`CONDA_PREFIX` (works for any conda package regardless of subdirectory
name), (4) `find` on `/usr`, `/opt`, `/usr/local`, (5) `pkg-config`.
Falls back to (6) `pyspellchecker` if installed, then (7) no filtering
with a warning. The Hunspell dictionary contains ~76,226 base words.
See `README.md` for install instructions and the `DICPATH` override. See
installation instructions on each platform.

Acceptance criteria:
- Dictionary hit or whitelist hit
- Title-case word (potential proper noun)
- Suffix-stripped stem hits dictionary (handles inflections)
- Hyphenated compound whose constituent words both hit dictionary

Rejection criteria:
- Non-ASCII characters
- Less than 60% alphabetic
- OCR garbage: >85% consonants, or <12% vowels for tokens longer than 4 characters

Typical removal rate: 7–16% of tokens per book.

The script is **resumable**: it writes after every book and skips books already
present in `books_clean.json`, so it is safe to interrupt and restart.

**Note**: For large corpora the Hunspell step is slow (~2–5 s per book).
`parse_and_clean_stream.py` uses regex-only cleaning (~0.1 s per book); the
TF-IDF `min_df=2` cutoff in step 03 handles residual OCR artefacts adequately.
All texts are capped at **300,000 characters** before cleaning — sufficient
for 20+ chapters of content.

**JSONL output format (v2)**: `parse_and_clean_stream.py` now writes to
`books_clean.jsonl` (JSON Lines) rather than `books_clean.json`. Each line
is a single JSON object for one book. This is a pure append operation — the
script never reads back the growing output file, so memory usage stays flat
regardless of how many files have already been processed. The ID-skip check
reads only the `"id"` field from each existing line using a fast regex, not
the full clean text. A conversion helper at the bottom of the script converts
`books_clean.jsonl` → `books_clean.json` for downstream scripts that expect
the dict format.

**De-hyphenation (v2)**: OCR line-break hyphens (`feed-\nback` → `feedback`)
are now rejoined before tokenisation using:
```python
re.sub(r'([a-zA-Z])-\n([a-zA-Z])', r'\1\2', text)
```
This runs before all other cleaning steps. See decisions.md for discussion.

---

## 2. Book-Level Topic Modelling (LDA, `03_nlp_pipeline.py`)

### Vectorisation

`TfidfVectorizer` with:
- `max_features = 3000`
- `token_pattern = r'(?u)\b[a-zA-Z]{4,}\b'` (alphabetic, ≥4 chars)
- `min_df = 2`, `max_df = 0.95`
- `sublinear_tf = True`
- Custom stopword list (~220 terms including academic boilerplate)

Three 20,000-character slices are extracted and concatenated to form a
60,000-character sample per book. Slice positions are at 10%, 50%, and 85%
of the clean text length, with a minimum offset of 4,000 characters to skip
publisher pages and copyright blocks. This multi-point approach gives the
vectoriser a representative view of the full book — introduction, argumentative
core, and conclusions — rather than over-weighting the opening chapters.

The same three-slice strategy is used in `generate_summaries_api.py` (at 15%,
50%, 80%) for consistency. Full texts range from 52K to 693K characters;
concatenating three 20K slices keeps the input to the TF-IDF vectoriser
bounded and memory-efficient regardless of book length.

### Latent Dirichlet Allocation

`sklearn.decomposition.LatentDirichletAllocation` with:
- `learning_method = 'online'`, `max_iter = 20`, `learning_offset = 50`
- `doc_topic_prior = 0.1` (sparse document-topic distributions)
- `random_state = 99`

Fitted for k = N_TOPICS_MIN (5) … N_TOPICS_MAX (12). Model selected by
**mean NPMI coherence** across all topics (see below).

### Topic Coherence — NPMI Implementation

Rather than perplexity, the pipeline selects k using **Normalised Pointwise
Mutual Information (NPMI) coherence**, implemented directly with numpy and
sklearn without requiring gensim. For each candidate k, the top 10 unigrams
per topic are extracted and NPMI is computed for every pair:

```python
pmi  = log( P(w_i, w_j) / (P(w_i) * P(w_j)) )
npmi = pmi / -log( P(w_i, w_j) )
```

where probabilities are estimated from binary document co-occurrence counts
(a word is "present" in a document if it appears at least once). The topic
coherence score is the mean NPMI across all word pairs. The k with the
highest mean coherence across all topics is selected.

NPMI ranges from -1 (never co-occur) through 0 (independent) to +1 (always
co-occur together). Scores in the range 0.03–0.06 are typical for academic
corpora of this vocabulary breadth. Both perplexity and coherence are saved
to `nlp_results.json` for comparison and audit.

**Why NPMI rather than C_V**: C_V coherence (the metric most strongly
correlated with human judgement) requires gensim's `CoherenceModel`, which
was not available in the offline execution environment. NPMI is the
underlying computational primitive that C_V builds on — C_V additionally
applies a cosine-similarity aggregation over NPMI vectors. The simpler
mean-NPMI approach used here is equivalent to the UMass coherence family
and gives a reliable signal for model selection on this corpus.

---

## 3. Chapter-Level Topic Modelling (NMF, `03_nlp_pipeline_chapters.py`)

### Why Not LDA at Chapter Level?

LDA was first applied to the chapter corpus and produced degenerate results:
near-identical topic distributions, dominated by OCR noise terms (`lemma`,
`dans`, `ibid`, `approximation`). Contributing factors:

- **Short documents**: chapters average ~2,000 words, below LDA's optimal range
- **OCR noise**: mathematical notation, French terms from Wiener's papers,
  footnote artefacts
- **High between-subject variance**: semantically distinct subject areas

### Input: Abstractive Summaries

Instead of raw OCR text, the NMF model is trained on the **API-generated
abstractive chapter summaries** from `summaries.json`. These are clean
prose descriptions (target: 2 sentences / ~40–60 words) of what each chapter
covers. Chapters with fewer than 20 summary words are augmented with the
book's descriptive summary for context.

Raw OCR text is still used for keyphrase extraction (see below).

### Non-Negative Matrix Factorisation

`sklearn.decomposition.NMF` with:
- `init = 'nndsvda'` (deterministic SVD-based initialisation — produces a
  well-conditioned starting point that converges to interpretable topics
  without requiring warm-starts or multiple random initialisations)
- `alpha_W = 0.0`, `alpha_H = 0.0` (no regularisation — see rationale below)
- `max_iter = 500`
- `random_state = 99`

Fitted for k = N_MIN … N_MAX. Model selected by **elbow on reconstruction
error**: the k at the largest second difference of the error curve.

**Why no L1/L2 regularisation**: L1 sparsity encourages each topic to be
represented by fewer, more distinctive words — sound in principle. However,
empirical testing across `alpha` values of 0.01–1.0 showed that any
`alpha > 0` causes complete topic degeneration on this corpus: all six topics
collapse to identical word lists. The root cause is document length — chapter
summaries average ~50 words, producing TF-IDF vectors that are already
extremely sparse. Any L1 pressure immediately overcorrects, driving all H
matrix weights to zero. The `nndsvda` initialisation provides the effective
structure for this corpus; vocabulary-level sparsity is managed via TF-IDF
hyperparameters (`max_features=1500`, `min_df=2`, `max_df=0.90`).

**Note on a previous code error**: an earlier version included `l1_ratio=0.1`
without a corresponding `alpha_W` or `alpha_H` value. In sklearn's NMF,
`l1_ratio` only takes effect when `alpha_W > 0` or `alpha_H > 0`; without
these, `l1_ratio` is a no-op regardless of its value. The code has been
corrected to explicit `alpha_W=0.0, alpha_H=0.0` to make the intent clear.

### Resulting 6 Topics (k=6, full 675-book corpus)

| Topic | Name | Characteristic Keywords |
|-------|------|------------------------|
| T1 | Human & Social Experience | human, people, world, life, mind, social |
| T2 | Mathematical & Formal Systems | function, state, input, output, number, value |
| T3 | General Systems Theory | systems theory, social, self, organisation, complexity |
| T4 | History & Philosophy of Cybernetics | cybernetics, wiener, science, computer, technology |
| T5 | Management & Organisational Cybernetics | management, decision, economic, production, process |
| T6 | Control Theory & Engineering | control, feedback, loop, signal, error, behaviour |

Topic names are human-assigned after inspecting top keywords. The `_BASE_NAMES`
list in the report scripts should be updated whenever topic names change.

---

## 4. Abstractive Summarisation (`generate_summaries_api.py`)

### Approach

Summaries are generated by the Anthropic Messages API
(`claude-sonnet-4-20250514`). This replaced earlier approaches: (a) hand-written
summaries, and (b) a first-generation API script that produced overly long,
partially extractive output. The current script (v2) applies six quality controls
described below.

For each book, three whole-book summaries are provided:

| Style | Focus |
|-------|-------|
| **Descriptive** | Scope, key concepts, structure (2 sentences) |
| **Argumentative** | Central thesis and supporting argument (2 sentences) |
| **Critical** | Key contribution and notable limitation or debate (2 sentences) |

For each chapter, a 2-sentence summary (~40–60 words) describes what the chapter
covers. Chapter summaries double as the NMF input for chapter-level topic modelling.

### Quality Controls (v2)

**1. Strict length enforcement**

`max_tokens=250` for book summaries (previously 1,200) and `max_tokens=130` for
chapter summaries (previously 200). The prompt specifies "EXACTLY 2 sentences."
This prevents the model from producing 300–400 word extracted passages.

**2. Multi-point text sampling**

Three 2,000-character slices are taken at the 15th, 50th, and 80th percentile
positions of the clean text, rather than one 10,000-character block from the
start. This avoids front-matter traps (editorial boards, tables of contents,
publisher pages) that caused the v1 script to summarise journal infrastructure
rather than intellectual content.

**3. Document type detection**

Books whose titles contain keywords such as `journal`, `festschrift`,
`handbook`, `encyclopedia`, `proceedings`, `anthology`, `reader`, or
`collection` are identified as edited volumes and receive a different prompt.
The edited-volume prompt asks for coverage overview and unifying themes rather
than a single thesis and argument, which is inappropriate for collections.
Approximately 32 of the 675 corpus books fall into this category.

**4. Anti-extraction instruction**

The prompt explicitly prohibits copying: *"Do NOT copy or paraphrase any
sentence from the excerpts — write entirely in your own words."* On retry,
this escalates to: *"DO NOT quote or paraphrase the excerpts at all, use only
your prior knowledge."*

**5. Verbatim similarity check with retry**

After generation, the summary is tested for 8-gram overlap with the source
text. If overlap exceeds 35%, the model is retried with the stricter prompt.
For chapter summaries, the retry prompt discards the source excerpt entirely
and asks the model to summarise based on the chapter title and book context
alone. If both attempts exceed the threshold, the better of the two is kept.

**6. Chapter title cleaning**

Chapter titles that are OCR sentence fragments (starting with a lowercase
letter, a digit followed by lowercase, or under 2 words) are replaced with
the generic label `"Chapter N"`. This prevents the model from attempting to
interpret a title like `"3. This is especially true where the negative mess…"`
as a real chapter heading.

### Resumability

The script saves `summaries.json` after every book. It is safe to interrupt
and restart — already-processed books are skipped. This is important given
the ~2–3 hour runtime for 675 books at 0.4 s/call average.

### Running

```bash
# From project root (where books_clean.json and nlp_results.json live):
python3 src/generate_summaries_api.py              # 4 concurrent workers (default)
python3 src/generate_summaries_api.py --workers 8  # faster; watch rate limits
python3 src/generate_summaries_api.py --workers 1  # sequential (original behaviour)
```

Requires outbound HTTPS to `api.anthropic.com` and the `ANTHROPIC_API_KEY`
environment variable set to a valid key.

### Concurrency (v3)

The script uses `ThreadPoolExecutor` to process multiple books concurrently.
Threads are appropriate (not processes) because the bottleneck is network I/O
— each API call spends ~10 seconds waiting for a response, during which a
thread releases the GIL and another thread can make the next request.

A shared `RateLimiter` (token bucket) coordinates all threads so the aggregate
request rate stays within Anthropic's API limits. The limiter uses exponential
backoff (2ˢ × 5s) on 429 rate-limit responses. A `SafeWriter` serialises all
JSONL appends through a `threading.Lock`, ensuring no two threads corrupt the
output file simultaneously.

**Intermediate format**: completed books are appended to `summaries.jsonl`
(one JSON object per line) as they finish — append-only, crash-safe, no read-
back. On completion the script converts `summaries.jsonl` → `summaries.json`
for downstream compatibility. Resuming after a crash skips books whose `"id"`
field already appears in `summaries.jsonl`.

**Choosing worker count**: with Anthropic's standard tier (~50 req/min),
4 workers is safe and cuts runtime from ~112 min to ~28 min. 8 workers
halves it again to ~14 min but may trigger rate limits — watch for 429
responses and reduce workers if they become frequent.

---

## 5. Keyphrase Extraction

Keyphrases are extracted from **raw chapter text** (book-level: from the book
text sample; chapter-level: from the individual chapter text).

Method: `TfidfVectorizer` with `ngram_range=(1, 3)`, fitted per document.
Top-k terms by TF-IDF score are returned as keyphrases. Using per-document
TF-IDF rather than corpus-wide TF-IDF ensures that terms distinctive to
each document are surfaced rather than corpus-wide frequent terms.

---

## 6. Document Clustering (K-Means)

`sklearn.cluster.KMeans` with:
- `n_init = 10`, `max_iter = 300`, `random_state = 99`
- k searched over KM_MIN … KM_MAX

**Model selection**: elbow method on inertia (largest second difference).
Silhouette scores are computed and plotted for validation but not used for
selection (at chapter scale they favour high k).

Clustering is performed on the L2-normalised TF-IDF matrix, not on the NMF
topic distributions. This captures lexical differences within topics and produces
richer cluster structure than topic-aligned grouping.

---

## 7. Dimensionality Reduction and Visualisation

**2-D projection**: `TruncatedSVD` (LSA) with `n_components=2` on the TF-IDF
matrix. Deterministic and fast; preserves latent semantic structure better
than PCA on sparse matrices.

**Interactive charts** (Plotly.js, loaded from CDN):

| Chart | Description |
|-------|-------------|
| 2D scatter | Hover for title/author/topic/cluster; filter by topic or cluster |
| Cosine similarity heatmap | Hover for book pair and similarity score; toggle to top-50 pairs |
| Book × Topic heatmap | Hover for chapter count and proportion |
| Keyphrases table | Live search and filter by topic and cluster |
| Topic distribution bar | Stacked bar with hover proportions |
| Publication year analysis | Six time-series charts (publications/yr, topic mix over time, cluster evolution, cumulative totals) |

Static PNG figures (matplotlib, 150 DPI) are also generated for the NMF error
curve, K-Means elbow, and scatter plots, and embedded as base64 data URIs in
the HTML reports for offline fallback.

---

## 8. Chapter Splitting

The chapter splitter uses a regex matching these heading patterns:

```python
# Word-form: CHAPTER ONE … CHAPTER FIFTEEN
r'CHAPTER\s+(?:ONE|TWO|...|FIFTEEN)(?:\s+[A-Z][A-Za-z\s,:\-]{0,80})?'

# Numeric: CHAPTER 1 … CHAPTER 15
r'CHAPTER\s+(?:1[0-5]|\d)(?:\s+[A-Z][A-Za-z\s,:\-]{0,80})?'

# Title-case: Chapter 1 … Chapter 15
r'Chapter\s+(?:1[0-5]|\d)(?:\s+[A-Z][A-Za-z\s,:\-]{0,60})?'

# Part markers: Part I … Part VIII, Part 1 … Part 8
r'Part\s+(?:[IVX]{1,4}|\d)(?:\s+[A-Z][A-Za-z\s,:\-]{0,60})?'

# Numbered sections with ≥4 words in title
r'\b(?:1[0-5]|\d)\.\s+[A-Z][a-zA-Z]{3,}(?:\s+[A-Za-z]{2,}){3,}'
```

Chapters below `MIN_CH_WORDS = 400` words are merged into an
"Other / Minor Sections" aggregate. If no chapter markers are found,
text is split into 5 equal sections. Chapters are capped at `MAX_CHAPTERS = 20`
per book (keeping the largest chapters when the limit is exceeded).

OCR-fragment chapter titles (starting lowercase, digit + lowercase, or under
2 words) are replaced with the generic label `"Chapter N"` before summarisation.

---

## 9. Publication Year Analysis (`08_build_timeseries.py`)

Publication years are extracted from the `pubdate` field of `books_metadata_full.csv`
(format: `YYYY-MM-DD HH:MM:SS+TZ`). Only years in the range 1900–2025 are
retained; one book with a placeholder date of `0101` is excluded.

Six interactive Plotly.js charts are produced:

1. **Publications per year** — bar chart with 5-year rolling average; hover
   reveals individual book titles
2. **LDA topic mix over time** — average topic proportion per year (stacked
   area / line / bar toggle)
3. **NMF chapter topic mix over time** — chapter topic proportions grouped by
   book publication year (same toggles)
4. **Cluster composition by decade** — stacked, grouped, or 100% normalised bar
5. **Year vs semantic position** — scatter of publication year vs LSA dimension,
   coloured by topic or cluster
6. **Cumulative publications by topic** — running total per dominant LDA topic

---

## Reproducibility

All random seeds: `random_state=99` (changed from the pilot value of 42;
sensitivity analysis across seeds confirmed stable topic and cluster solutions).
Intermediate JSON files allow any step to be re-run without repeating expensive
earlier steps. The Hunspell dictionary provides deterministic word filtering.

---

## 10. Controlled Vocabulary — Index Term Extraction (`09_extract_index.py`)

### Motivation

Back-of-book indexes provide a human-curated controlled vocabulary that
complements the statistical NMF/LDA topic representations. Index terms are:
- Already normalised by editors/authors (e.g. "feedback loops" rather than
  raw token variants)
- Concept-level rather than word-level (handles synonymy better than TF-IDF)
- Cross-book comparable — the same term appearing in 40 books carries
  clear intellectual significance

### Index Detection

The back-of-book index is identified by matching the last occurrence of a
set of heading patterns against the raw OCR text:

```
"Index", "Subject Index", "Name Index", "Author Index",
"Analytical Index", "General Index", "Index of Terms", etc.
```

The **last** occurrence is used (not the first) to avoid matching index
references in tables of contents.

### Extraction Pipeline

**Step 1 — Quality check**

The first 50 lines of the candidate index section are sampled. If fewer than
15% of lines start with a letter and have >60% alphabetic content, the section
is classified as `garbled` (severe OCR failure) and discarded.

**Step 2 — Line classification**

Each line is classified as one of:
- **Main entry** — starts with a capital letter, 3–80 chars, passes
  alphabetic ratio test (>45%), no trailing pure-number
- **Sub-entry** — starts with em-dash (—, \x97) or en-dash; stripped and
  appended as `"parent — sub"`
- **See/See also** — cross-reference; target term extracted and added
- **Section divider** — single capital letter (A, B, C...); discarded
- **Page number only** — discarded
- **Long prose line** (>120 chars) — discarded (leaked book text)
- **Garbage** — alphabetic ratio <45%; discarded

**Step 3 — Page number stripping**

Trailing page references are stripped with:
```python
re.sub(r'[,\s]+\d[\d,\s;n\.–\-ff]*$', '', term)
```
This handles formats like `"feedback, 12, 34–56, 78n, 90ff"` → `"feedback"`.

**Step 4 — Deduplication**

Terms are deduplicated case-insensitively within each book.

### Extraction Results (675-book corpus)

| Status | Books | Notes |
|--------|-------|-------|
| Clean index extracted | 270 (40%) | Full or near-full index |
| Truncated | 216 (32%) | Index cut by 300k char cap |
| No index detected | 194 (29%) | No matching heading found |
| Garbled OCR | 13 (2%) | Discarded |

**Note on truncation**: The 300k character cap applied during cleaning (step 2)
cuts off the index for longer books. This affects ~32% of books. The index
could be recovered for these books by re-extracting directly from the raw
`books_text_*.csv` files (uncapped) rather than from `books_clean.json`.

### Controlled Vocabulary Statistics

After filtering to terms appearing in 2+ corpus books and removing common
stopwords and structural noise (`"index"`, `"system"`, single uppercase words):

- **9,807 unique terms** across the corpus
- **524 terms** appearing in 10+ books
- **1,800 terms** appearing in 5+ books

Top terms by book frequency: Wiener, Norbert (126), cybernetics (100),
feedback (51), von Neumann, John (53), communication (47), thermodynamics (37),
homeostasis (36), Bateson, Gregory (33), Shannon, Claude (32), autopoiesis (26).

### Analyses Produced (`09_build_index_report.py`)

Five interactive Plotly.js charts are produced in
`data/outputs/book_nlp_index_analysis.html`:

| Chart | Description |
|-------|-------------|
| Term frequency ranking | Horizontal bar, top 30/50/80 terms by book count |
| Term density over time | Line chart by decade; select up to 8 terms to compare |
| Co-occurrence network | Terms connected by shared books; strongest pairs include Wiener+von Neumann (42 books), cybernetics+feedback (30) |
| Term × NMF topic matrix | Stacked bar showing topic distribution per term; distinguishes topic-specific vs cross-cutting terms |
| Term explorer | Free-text search returning all books containing matching index terms, filterable by NMF topic |

### Noise Characterisation

Line-level noise analysis across all index sections:

| Line type | Proportion |
|-----------|-----------|
| Entry-like (letter start, page ref) | 47% |
| Other (sub-entries, cross-refs, fragments) | 41% |
| Garbage OCR | 9% |
| Page numbers only | 3% |

The 41% "other" category contains legitimate content (sub-entries, wrapped
lines, cross-references) as well as OCR artefacts (split words, mid-sentence
fragments from adjacent text). The extraction rules handle the most common
patterns; residual noise at the term level is filtered by the ≥2 book
frequency threshold applied at the vocabulary stage.

---

## 11. Topic Coherence Scoring

### What Is Topic Coherence?

Perplexity (used in the current pipeline for LDA model selection) measures how
well a probability model predicts a held-out sample. It correlates poorly with
human judgement of topic quality — lower perplexity does not reliably mean more
interpretable topics.

**Coherence metrics** measure semantic similarity between the top words of a
topic, based on co-occurrence statistics in the corpus or a reference corpus.
They correlate significantly better with human assessments of topic quality.

### Common Coherence Metrics

**UMass coherence** is an intrinsic metric computed on the training corpus:

```
C_UMass(t) = Σ log( P(w_i, w_j) / P(w_j) )
```

For each pair of top words (w_i, w_j) in the topic, it measures how often w_i
appears in documents that also contain w_j, normalised by the marginal frequency
of w_j. Higher (less negative) scores indicate more coherent topics. Fast to
compute but can overfit to corpus-specific co-occurrences.

**C_V coherence** is an extrinsic metric based on a sliding window over a
reference corpus (typically Wikipedia or the training corpus):

```
C_V(t) = mean cosine_similarity(NPMI vectors for top word pairs)
```

Where NPMI is Normalised Pointwise Mutual Information. C_V is the metric most
strongly correlated with human coherence judgements (Röder et al., 2015) and
is the recommended default for model selection.

**C_UCI** uses PMI computed on an external corpus (Wikipedia), making it
independent of the training data. Useful for detecting topics that are
coherent in the training corpus but nonsensical in general usage.

### Why the Current Pipeline Uses Perplexity

The pipeline uses sklearn's `LatentDirichletAllocation` which only exposes
`perplexity_score()`. Computing C_V or UMass coherence requires `gensim`'s
`CoherenceModel`, which was not available in the original offline execution
environment.

**Consequence**: the LDA model selection (k=7) is based on perplexity, which
may not align with the most humanly interpretable solution. The NMF model
selection (k=6) uses reconstruction error elbow, which has similar limitations.

### Recommended Improvement

Replace perplexity-based model selection with C_V coherence using `gensim`:

```python
from gensim.models.ldamodel import LdaModel
from gensim.models.coherencemodel import CoherenceModel
from gensim.corpora import Dictionary

# Build gensim corpus from tokenised texts
texts = [text.split() for text in clean_texts]
dictionary = Dictionary(texts)
corpus = [dictionary.doc2bow(t) for t in texts]

scores = {}
for k in range(k_min, k_max + 1):
    lda = LdaModel(corpus=corpus, num_topics=k, id2word=dictionary,
                   random_state=99, passes=10)
    cm = CoherenceModel(model=lda, texts=texts, dictionary=dictionary,
                        coherence='c_v')
    scores[k] = cm.get_coherence()
    print(f'  k={k}  C_V={scores[k]:.4f}')

best_k = max(scores, key=scores.get)
```

C_V scores above ~0.55 indicate good coherence; above ~0.65 is considered
excellent for most corpora. The elbow of the C_V curve (where adding more
topics produces diminishing coherence gains) is a more reliable stopping
criterion than perplexity minimisation.

### Interpreting Coherence in This Corpus

The cybernetics corpus presents specific challenges for coherence scoring:

- **Vocabulary heterogeneity**: the corpus spans pure mathematics, biology,
  management, philosophy, and fiction. Topics spanning multiple domains will
  naturally score lower on coherence than domain-specific topics.
- **OCR noise**: residual OCR artefacts reduce co-occurrence counts for
  legitimate terms, artificially depressing coherence scores.
- **Short documents (NMF)**: chapter summaries of ~50 words produce sparse
  co-occurrence matrices that reduce the reliability of window-based coherence
  metrics. For NMF on short documents, human inspection of top words remains
  the most reliable quality criterion.

---

## 12. Embedding Method Comparison (`11_embedding_comparison.py`)

### Motivation

TF-IDF + LSA represents each document as a weighted bag of words projected
into a lower-dimensional latent space. This captures lexical co-occurrence
patterns well but misses semantic equivalence — two sentences with different
words but the same meaning receive dissimilar representations. Sentence
transformers and API embeddings encode meaning directly, potentially
producing better-organised clusters and more meaningful nearest-neighbour
relationships.

This optional script (`11_embedding_comparison.py`) runs four embedding
approaches side-by-side and reports standardised clustering quality metrics,
nearest-neighbour comparisons, and a cluster-vs-LDA alignment heatmap.

### Methods

**A — TF-IDF + LSA 100d** (current pipeline baseline)

TF-IDF vectorisation (3,000 features, bigrams, `min_df=2`, `max_df=0.95`)
followed by `TruncatedSVD` to 100 dimensions. Covers 41% of TF-IDF variance.
Fast (~3s for 675 books), no additional dependencies. The same approach used
in `03_nlp_pipeline.py`.

**B — TF-IDF + LSA 384d**

Same TF-IDF vocabulary expanded to 384 dimensions, matching the output size
of `all-MiniLM-L6-v2`. Covers 82.5% of TF-IDF variance. Allows isolating the
effect of dimensionality from the effect of the embedding model.

**C — Sentence Transformers** (`all-MiniLM-L6-v2`)

22M-parameter transformer trained on 1 billion sentence pairs via contrastive
learning. Produces 384-dimensional dense embeddings that encode semantic
meaning. Two sentences with different words but the same meaning receive
similar embeddings. Requires `pip install sentence-transformers`. Runs
locally on CPU (~5–15 min for 675 books depending on hardware; much faster
with a GPU).

**D — Anthropic API Embeddings** (`voyage-3`)

Voyage embeddings via the Anthropic API. Optimised for retrieval and semantic
similarity. Batched at 8 texts per request. Requires `ANTHROPIC_API_KEY` and
outbound HTTPS. Typical cost: ~$0.01 per 675 books.

### Input text

Each book is represented by the concatenation of its descriptive summary,
argumentative summary, and all chapter summaries from `summaries.json` —
averaging ~812 words per book. This is the same text used for NMF topic
modelling in `03_nlp_pipeline_chapters.py`.

### Metrics

All methods are evaluated with K-Means clustering (sweep k=3..10, select by
maximum silhouette score) after L2 normalisation:

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Silhouette** | mean((b-a)/max(a,b)) | Compactness vs separation. Range -1..1; higher = better |
| **Davies-Bouldin** | mean(max(σᵢ+σⱼ)/d(cᵢ,cⱼ)) | Cluster scatter vs centroid distance; lower = better |
| **Calinski-Harabász** | (B/k-1) / (W/n-k) | Between-cluster vs within-cluster variance; higher = better |
| **Intra-cluster cosine** | mean pairwise sim within clusters | Tightness; higher = better |
| **Inter-cluster cosine** | mean pairwise sim across clusters | Separation; lower = better |

### Results (methods A, B and C)

| | A · LSA 100d | B · LSA 384d | C · Sentence Transformers |
|-|-------------|-------------|--------------------------|
| Best k | 5 | 7 | 8 |
| Silhouette ↑ | **0.039 ★** | 0.012 | 0.031 |
| Davies-Bouldin ↓ | 4.22 | 6.35 | **3.68 ★** |
| Calinski-Harabász ↑ | **18.79 ★** | 6.74 | 14.11 |
| Intra-cluster sim ↑ | **0.445 ★** | 0.264 | 0.415 |
| Inter-cluster sim ↓ | 0.365 | 0.213 | **0.211 ★** |
| Time | **1.2s ★** | 2.6s | 29–36s |
| Cluster purity vs LDA | **0.600 ★** | 0.575 | 0.459 |

**Interpretation:**

The low silhouette scores across all methods (0.01–0.04, vs typical 0.3–0.7
for well-separated corpora) reflect the genuine intellectual structure of the
cybernetics corpus — books span pure mathematics, ecology, management science,
philosophy, and fiction with no hard conceptual boundaries.

**LSA 100d wins on within-cluster tightness** (silhouette, intra-sim,
Calinski-Harabász). Its clusters are internally consistent — books in the
same cluster reliably share vocabulary.

**Sentence transformers wins on between-cluster separation** (Davies-Bouldin,
inter-sim). Its clusters are more distinct from each other — it finds groupings
that don't bleed into neighbouring topic regions as much.

**LSA 384d is strictly worse than 100d** on every metric — more dimensions
from the same TF-IDF vocabulary introduce noise rather than signal.

**Nearest-neighbour comparison (A vs C, 628 disagreements out of 669 books):**
- LSA gives a same-LDA-topic neighbour 58% of the time
- Sentence transformers gives a same-LDA-topic neighbour 40% of the time
- Pairwise Adjusted Rand Index A vs C: 0.146 (low — they measure genuinely different things)

**The methods find different kinds of similarity:**
- LSA finds *lexically* similar books (shared vocabulary)
- Sentence transformers finds *semantically* similar books (shared meaning across different words)

Example: *Understanding Understanding* (von Foerster) — LSA links it to
*Observing Systems* (same author, same words); sentence transformers links it
to *Organism-Oriented Ontology* (different vocabulary, same second-order
cybernetics concepts).

**Recommendation:** LSA 100d remains the pipeline default for speed and cluster
tightness. Sentence transformers is the better choice for the nearest-neighbours
explorer, where crossing vocabulary boundaries to find conceptual relatives is
more intellectually valuable than finding books that happen to share vocabulary.

### Running

```bash
# Methods A and B only (fastest, no extra dependencies)
python3 src/11_embedding_comparison.py --no-voyage --no-st

# Add Sentence Transformers (Method C) — requires PyTorch
# Check version: python3 -c "import torch; print(torch.__version__)"
pip install torch --upgrade          # upgrade to >= 2.4
pip install sentence-transformers
# Or if PyTorch upgrade is not possible:
pip install 'sentence-transformers==2.7.0'   # supports PyTorch 2.2
python3 src/11_embedding_comparison.py --no-voyage

# Add Voyage AI (Method D) — free key at https://dash.voyageai.com/
# Note: free tier is ~3 req/min; 675 books takes ~4 hours
export VOYAGE_API_KEY=pa-...
python3 src/11_embedding_comparison.py --no-st

# Run all methods
python3 src/11_embedding_comparison.py

# Fix cluster count instead of sweeping k=3..10
python3 src/11_embedding_comparison.py --k 7 --no-voyage
```

**Flag reference:**

| Flag | Effect |
|------|--------|
| `--no-voyage` | Skip Method D (Voyage AI). Use when rate limits or key unavailable. |
| `--no-st` | Skip Method C (Sentence Transformers). Use without PyTorch. |
| `--k N` | Fix cluster count at N instead of sweeping 3–10. |
| (none) | Run all available methods automatically. |

---

## 09b. Index Analysis Builder (`09b_build_index_analysis.py`)

Bridges `09_extract_index.py` and `10_build_index_report.py` by aggregating
the raw per-book term lists into the enriched analysis format that downstream
scripts expect.

**Reads:** `index_terms.json`, `index_vocab.json` (from 09), `nlp_results.json`
(for pub_years, dom_topics, titles), `books_clean.json` (for context snippets)

**Writes:**
- `index_analysis.json` — aggregated vocabulary with per-term year and topic
  distributions, top-200 list, co-occurrence pairs, and per-book term lists
- `index_snippets.json` — one context sentence per term per book, used by
  the term explorer in `book_nlp_index_analysis.html`

This step was previously run interactively and not captured in the pipeline.
It is now a formal script and runs as step 9b in `run_all.sh`.

---

## 13. Index Grounding Analysis (`12_index_grounding.py`)

### Overview

Three analyses that use back-of-book index terms to enrich and validate the
topic models:

1. **Index-term topic labelling** — which established expert-curated terms
   ground each LDA/NMF topic
2. **Concept Density** — terminological richness per book
3. **Concept Velocity** — how index terms migrate between topic clusters
   across publication decades

### 13.1 Index-Term Topic Labelling

For each LDA (book-level) and NMF (chapter-level) topic, the index terms most
over-represented in that topic's books are identified using a **lift score**:

```
lift(term, topic) = P(topic | term) / P(topic)
```

A lift of 3× means a term appears in that topic's books 3× more often than
would be expected by chance. Terms are filtered to those appearing in ≥5 books,
with OCR noise patterns and structural noise removed.

This produces a "Rosetta Stone" linking bag-of-words topic keywords to
human-expert index terminology — e.g. LDA T5 (2nd-Order Cybernetics) is
grounded by "schismogenesis", "Watzlawick, Paul", "Observation", "psychotherapy".

### 13.2 Concept Density

Concept Density is defined as:

```
density = (unique index terms) / word_count × 1000
```

This measures terminological richness per 1,000 words — a proxy for how
encyclopaedic or technically dense a book is. High density books include
bibliographies, handbooks, and technical monographs; low density books include
narrative histories, philosophical essays, and popular science.

Density is used as **bubble size** in the 2D semantic scatter plot
(`book_nlp_index_grounding.html`, chart 3), so that terminologically dense
books appear visually larger on the map.

### 13.3 Concept Velocity

For each index term appearing in ≥10 books, the **dominant LDA topic** of
books containing it is tracked by publication decade. Terms whose dominant
topic changes across decades reveal intellectual migration patterns.

Example: "information" moved from Control Theory (1960s) → History &
Philosophy (1980s) → Human & Social Experience (2010s), tracing the
transition of information theory from an engineering discipline to a
humanistic one.

55 of the 60 most frequent terms show at least one topic migration across
their publication history.

---

## 14. Recursive Summarisation (`generate_summaries_api.py --recursive`)

### Motivation

The standard `generate_summaries_api.py` samples three 2,000-character slices
(at 15%, 50%, 80% through the text) for book-level summaries. This captures
representative vocabulary but may miss the argumentative arc — the logical
progression from chapter to chapter that defines a book's intellectual
contribution.

### Map-Reduce Approach

With `--recursive`, the script implements a two-stage summarisation:

**Stage 1 (Map)**: Summarise each chapter individually (unchanged from
standard mode — 2 sentences per chapter).

**Stage 2 (Reduce)**: Use the chapter excerpts (first 400 characters of each
chapter's text, up to 12 chapters) as input to the book-level summary prompt,
rather than raw text slices. The model effectively reads a "chapter-by-chapter
digest" of the full book.

This ensures the book-level descriptive, argumentative, and critical summaries
reflect the complete narrative arc without hitting API token limits.

```bash
python3 src/generate_summaries_api.py --recursive            # 4 workers
python3 src/generate_summaries_api.py --recursive --workers 8
```

The output format is identical to standard mode — `summaries.json` is fully
compatible with all downstream pipeline steps.

---

## 15. Embedding Abstraction (`embeddings.py`)

### Overview

`embeddings.py` provides a unified `Embedder` interface for all embedding
methods, allowing `03_nlp_pipeline.py` and `11_embedding_comparison.py` to
swap between methods via a single configuration parameter.

### Classes

| Class | Mode string | Description |
|-------|------------|-------------|
| `LSAEmbedder` | `'lsa'` | TF-IDF + TruncatedSVD (current pipeline default) |
| `LSAEmbedder` | `'lsa384'` | Same as above, 384 dimensions |
| `SentenceEmbedder` | `'sentence'` | all-MiniLM-L6-v2 via sentence-transformers |
| `VoyageEmbedder` | `'voyage'` | Voyage AI API (requires `VOYAGE_API_KEY`) |

### Usage

```python
from embeddings import get_embedder

# In 03_nlp_pipeline.py — switch from LSA to semantic embeddings:
embedder = get_embedder('lsa')          # fast, no deps (default)
embedder = get_embedder('sentence')     # semantic, needs PyTorch
embedder = get_embedder('voyage')       # API, needs VOYAGE_API_KEY

X = embedder.embed(texts)              # returns (n, d) normalised array
print(embedder.dims)                   # embedding dimensionality
```

The `VoyageEmbedder` includes the crash-safe cache (`voyage_embeddings_cache.json`)
and exponential backoff logic from `11_embedding_comparison.py`, making it
safe to interrupt and resume.

---

## 16. Sliding-Scale Index-Term Weighting (`03_nlp_pipeline.py --weighted`)

### Motivation

Standard TF-IDF assigns weights based purely on term frequency and document
frequency. It treats "system" (appearing in every cybernetics book) identically
to "schismogenesis" (appearing in six, almost all in the 2nd-Order Cybernetics
cluster). From a topical discrimination standpoint, schismogenesis is far more
valuable — it tells you *which* cluster a book belongs to. TF-IDF cannot know
this because it has no external knowledge of conceptual relevance.

The `--weighted` flag augments TF-IDF with knowledge from the back-of-book
index vocabulary: terms that are strongly associated with specific LDA topics
(high lift score) are boosted, while structurally pervasive terms (low lift,
uniform distribution) are left at their natural TF-IDF weight.

### Weight Formula

```
w(term) = 1.0 + (sigmoid_lift − 1.0) × reliability

sigmoid_lift(lift) = 1 + 2 × (1 − 1 / (1 + (lift − 1)^1.5))
reliability(n)     = sqrt(min(n_books, 20) / 20)
```

`sigmoid_lift` maps a term's maximum topic lift score onto [1.0, 3.0]:
- lift = 1.0 (uniform across topics) → sigmoid_lift = 1.0 (no boost)
- lift = 3.0 → sigmoid_lift ≈ 2.5×
- lift = 8.0 → sigmoid_lift ≈ 3.0× (ceiling)

`reliability` dampens weights for terms with few supporting books:
- n = 2  → reliability = 0.32 (significant dampening)
- n = 5  → reliability = 0.50
- n = 20 → reliability = 1.00 (full weight)

This naturally implements the Anchor / Signal / Frontier bands:

| Band | n_books | Typical lift | Typical weight |
|------|---------|-------------|----------------|
| Anchor (top 5%) | ≥9 | ~1.4–2.0 | 1.4–2.1× |
| Signal (5–40%) | 3–8 | ~2–8 | 1.7–2.9× |
| Frontier (40–100%) | 2 | variable | 1.0–1.8× |
| Unweighted | any | ~1.0 | 1.0× |

### Results

Running `python3 src/03_nlp_pipeline.py --weighted` on the 675-book corpus:

- 1,146 of 3,000 TF-IDF features boosted (mean 1.74×, max 2.57×)
- Silhouette: 0.0519 → 0.0526 (+1.3%)
- Variance explained: 44.8% → 49.5%
- Cluster size distribution improves (less dominant by single large cluster)

Notable weights: `autopoiesis` (n=26) 2.10×, `schismogenesis` (n=6) 2.04×,
`viable system model` (n=16) 2.57×, `varela` (n=27) 2.63×, `feedback` (n=51)
1.65× (Anchor — present everywhere, mild boost only).

### Usage

```bash
# Standard unweighted run (default — always run this first on a clean start)
python3 src/03_nlp_pipeline.py

# Index-term weighted second pass (run ONLY after the full pipeline has
# completed once — requires nlp_results.json and index_analysis.json)
python3 src/03_nlp_pipeline.py --weighted

# Weighted with fixed topic count
python3 src/03_nlp_pipeline.py --weighted --topics 7
```

### Dependency on prior pipeline runs

`--weighted` has a **bootstrap dependency**: it reads `index_analysis.json`
(written by `09b_build_index_analysis.py`) and `nlp_results.json` (written
by the first unweighted run of this script) to compute per-term lift scores.
Neither file exists on a clean start.

The dependency chain is:

```
03_nlp_pipeline.py          → nlp_results.json
09_extract_index.py         → index_terms.json
09b_build_index_analysis.py → index_analysis.json
                                      ↓
03_nlp_pipeline.py --weighted  (can now run safely)
```

If either dependency is missing the script falls back automatically:
- No `index_analysis.json` → runs unweighted (prints a warning)
- No `nlp_results.json` → uses a simple Gaussian curve on n_books instead
  of lift scores (still better than unweighted, but suboptimal)

The optional second-pass block in `run_all.sh` is pre-written and commented
out — uncomment it to run the weighted pass after the first full pipeline run.

### Implementation

The `build_index_weights()` function in `03_nlp_pipeline.py` reads
`index_analysis.json` and the previous `nlp_results.json` (for dominant topic
fractions). On a first run with no `nlp_results.json`, it falls back to a
simpler Gaussian curve centred on n_books=5. The weight vector is applied as
a sparse column multiply: `X_weighted = X_tfidf.multiply(weight_vector)`.

---

## 17. Band Prevalence & Concept Velocity Time Series (Chart 7, `08_build_timeseries.py`)

Chart 7 in `book_nlp_timeseries.html` adds two panels:

**Left — Band Prevalence by Decade**: Mean number of Anchor, Signal, and
Frontier index terms per book per decade. This tracks whether the field's
conceptual vocabulary is stable, expanding (Signal terms proliferating), or
fragmenting (Frontier terms growing). A rise in Frontier terms indicates
a field diversifying into specialist niches; a rise in Anchor terms suggests
convergence on shared vocabulary.

**Right — Concept Velocity**: Select any high-frequency index term to see its
dominant LDA topic distribution shift across publication decades. Terms with
high velocity (topic migration across multiple decades) reveal the intellectual
journeys of key concepts — e.g. "information" moving from Control Theory
(1960s) through General Systems Theory (1990s) to Human & Social (2010s).

The chart reads `index_analysis.json` and `concept_velocity.json` (produced by
`12_index_grounding.py`) and gracefully skips if those files are not present.

---

## Directory Layout

All scripts are run from the **project root** directory. Two sub-directories
organise all data files:

```
project_root/
├── csv/                   ← place all Calibre CSV exports here before running
│   ├── books_metadata_full.csv  ← enriched metadata: 20 cols (from 00_export_calibre.py)
│   └── books_text_*.csv         ← full text: id, searchable_text
├── json/                  ← all JSON/JSONL pipeline outputs (auto-created)
│   ├── books_clean.json   ← cleaned text corpus (written by 02/stream)
│   ├── nlp_results.json   ← LDA/cluster results (written by 03)
│   └── ...                ← all other intermediate and output JSON files
├── src/                   ← pipeline scripts
├── data/outputs/          ← HTML and Excel reports
└── figures/               ← matplotlib figures
```

Every script contains these three lines after its imports:

```python
import pathlib as _pl
CSV_DIR  = _pl.Path('csv')   # all input CSVs
JSON_DIR = _pl.Path('json')  # all JSON/JSONL files
JSON_DIR.mkdir(exist_ok=True)
```

`JSON_DIR.mkdir(exist_ok=True)` ensures `json/` is created automatically
on first run — you only need to create `csv/` and place your files there.

**Before first run:**
```bash
mkdir -p csv
python3 src/00_export_calibre.py            # exports csv/books_metadata_full.csv
cp /path/to/calibre_export/books_text_*.csv csv/
python3 src/run_all.sh --stream
```

---

## Pipeline Execution Order & Dependencies

The pipeline has a strict dependency graph. Running steps out of order causes
`KeyError` or `FileNotFoundError` at runtime.

```
books_metadata_full.csv + books_text_*.csv
        │
        ├── STREAMING: parse_and_clean_stream.py  (× 25 CSV files)
        └── STANDARD:  01_parse_books.py → 02_clean_text.py
        │
        ▼
03_nlp_pipeline.py              → nlp_results.json
04_summarize.py                 → summaries.json
05_visualize.py
06_build_report.py
07_build_excel.py
        │
        ▼
03_nlp_pipeline_chapters.py     → nlp_results_chapters.json  (uses summaries.json)
05_visualize_chapters.py
06_build_report_chapters.py
07_build_excel_chapters.py
        │
        ▼
09_extract_index.py             → index_terms.json, index_vocab.json
09b_build_index_analysis.py     → index_analysis.json, index_snippets.json
10_build_index_report.py        → book_nlp_index_analysis.html
        │
        ▼
12_index_grounding.py           → concept_velocity.json       (needs index_analysis.json)
                                   concept_density.json
                                   topic_index_grounding.json
        │
        ▼
08_build_timeseries.py          → book_nlp_timeseries.html    (Chart 7 needs concept_velocity.json)
```

**Key dependency rules:**

| Script | Requires these files to exist first |
|--------|-------------------------------------|
| `03_nlp_pipeline_chapters.py` | `summaries.json` (from 04) |
| `09_extract_index.py` | `books_clean.json` (from 02/stream) |
| `09b_build_index_analysis.py` | `index_terms.json`, `index_vocab.json` (from 09), `nlp_results.json`, `books_clean.json` |
| `10_build_index_report.py` | `index_analysis.json`, `index_snippets.json` (from 09b) |
| `12_index_grounding.py` | `index_analysis.json` (from 09b), `nlp_results.json` (from 03) |
| `08_build_timeseries.py` | `nlp_results.json`, `nlp_results_chapters.json`, `concept_velocity.json` (from 12) |
| `11_embedding_comparison.py` | `summaries.json`, `nlp_results.json` |

`08_build_timeseries.py` will run without `concept_velocity.json` but Chart 7
will be silently skipped (the other 6 charts still render). The file size
difference is 142 KB (without Chart 7) vs 170 KB (with Chart 7).

---

## 18. Summary Quality — Epistemic Precision in Prompting (Prompt v4)

### Problem diagnosis

Auditing 675 book summaries revealed two systematic failure modes:

**Report-style description (237 summaries):** Summaries began with "This book
examines...", "This work explores...", "The author discusses..." — narrating what
the excerpt window contained rather than the work's intellectual substance. These
are descriptions of content, not analyses of argument.

**Excerpt-grounded abstraction:** Summaries described what happened to appear in
the 2,000-character sample slice rather than drawing on the model's knowledge of
the whole work. A sampling accident (all three slices landing in introductory
material) could produce a summary about scope rather than thesis.

**Root cause:** The original prompts asked "read these excerpts and write
summaries" — framing the task as excerpt comprehension. The model then described
the excerpt. The fix is to reframe the task as intellectual analysis using the
model's knowledge, with the excerpts serving only for orientation.

### Prompt v4 changes

**Core reframing — epistemic stance:**
The most important change is recognising that academic works do not all make the
same kind of intellectual move. Verbs like "argues", "demonstrates", "proves",
"contends" presuppose a thesis-first structure — the author had a conclusion and
marshalled evidence for it. But much of the most important work in cybernetics
proceeds differently: tracing what follows if a concept is taken seriously,
proposing a vocabulary and seeing what it illuminates, questioning whether a
received distinction holds up, connecting phenomena previously thought unrelated.

Choosing "demonstrates" for Ashby's *Design for a Brain* smuggles in an
interpretation — it implies he proved a pre-formed conclusion, when he was
actually working out what conditions are logically necessary for adaptation
and following the consequences. The verb encodes an epistemological assumption
about how knowledge is produced.

The prompts now instruct the model to:
1. Identify which kind of intellectual move the work is making before writing
2. Choose verbs that match that orientation: "develops", "traces", "proposes",
   "works through", "questions", "opens up", "reframes", "connects",
   "complicates" — not "argues" or "demonstrates" unless genuinely apt
3. Use hedged language when uncertain about intent: "can be read as",
   "what emerges from the analysis is", "one effect of this work is"
4. Frame the argumentative summary around the *kind* of move, not just its
   content: is it proving, exploring, proposing, questioning, or tracing?

This matters for readers and students because it models a broader range of
possible intellectual orientations — not all intellectual work is argument
in the sense of thesis-plus-evidence.

**Format fields reframed:**
All three fields (descriptive, argumentative, critical) are now phrased as
questions about intellectual work rather than content:

- *Descriptive:* "What intellectual problem or question does this work engage,
  and what kind of answer, framework, or reorientation does it propose or
  arrive at?" — not "what is the book about"
- *Argumentative:* "What is the work's core intellectual move — is it proving,
  exploring, proposing, questioning, or tracing? What gives the move its force?"
  — not "what is the thesis and evidence"
- *Critical:* "What has this work made possible or changed? What remains open,
  contested, or limited?" — not "what is the contribution and limitation"

**Chapter prompt restructured:**
Now asks: Sentence 1 — what intellectual move does this chapter make? Sentence 2
— what grounds that move, and how does it relate to the book's larger project?
Verb guidance included inline. Banned opener: "This chapter...".

**`REPORT_RE` filter:** Summaries matching `^(This (book|chapter|work) examines...`
or similar at the start are caught by `is_clean()` and trigger a retry.

### Regenerating existing summaries

The new prompts will improve quality on the next full run of
`generate_summaries_api.py`. To regenerate specific problematic entries without
paying for the full corpus:

```python
import json, re
with open('summaries.json') as f: S = json.load(f)

REPORT = re.compile(
    r'^(this (book|work|chapter|collection|volume) (examines|explores|discusses|'
    r'presents|covers|offers)|in this (book|chapter|work)|the author (examines|'
    r'explores|discusses|presents))', re.IGNORECASE)

bad_bids = [bid for bid, d in S.items()
            if REPORT.match(d.get('descriptive', '').strip())]
print(f"Report-style descriptives: {len(bad_bids)}")

# Delete and rerun generate_summaries_api.py to regenerate
for bid in bad_bids:
    del S[bid]
with open('summaries.json', 'w') as f:
    json.dump(S, f, ensure_ascii=False)
```

At ~$0.04 per book this costs roughly $9 to regenerate all 237 affected summaries.

---

## 19. Weighted vs Unweighted Comparison (`13_weighted_comparison.py`)

Reads `nlp_results_unweighted.json` and `nlp_results_weighted.json` and produces
an interactive HTML report showing exactly what changes when index-term lift
weighting is applied.

**To generate both files:**
```bash
python3 src/03_nlp_pipeline.py                   # standard run
cp nlp_results.json nlp_results_unweighted.json
python3 src/03_nlp_pipeline.py --weighted         # weighted second pass
cp nlp_results.json nlp_results_weighted.json
python3 src/13_weighted_comparison.py
```

**Report sections:**
1. **Overview stats** — books that changed topic, cluster ARI, purity delta
2. **Topic membership table** — each topic's book count before and after, with ± delta
3. **Topic shift heatmap** — which topics books moved FROM vs TO
4. **Scatter comparison** — side-by-side 2D LSA maps coloured by dominant topic
5. **Weight inspector** — top 40 index terms by relevance multiplier, showing
   lift score and book count
6. **Switched books table** — searchable list of all books that changed dominant topic

The ARI between unweighted and weighted cluster assignments measures overall
stability — a high ARI (>0.8) means weighting refined rather than restructured
the topic landscape.

---

## 20. Dynamic Topic Naming (`--name-topics` flag)

### Problem

Topic names like "2nd-Order Cybernetics & Bateson" were assigned by hand after
inspecting one run with seed=99. They were then hardcoded into every downstream
script. Two failure modes:

1. **n_topics overflow** — if the LDA coherence sweep selects k=9 instead of 7,
   the 7-name list crashes with IndexError. Fixed by padding with "Topic N".
2. **Semantic mismatch** — if the seed changes, the corpus grows, or the optimal
   k shifts, the hardcoded name may point at a completely different cluster
   with no error message — just silent misinformation.

### Solution: topic_names as a first-class field in nlp_results.json

`nlp_results.json` now stores a `topic_names` list alongside `n_topics`.
All downstream scripts read from it:

```python
LDA_NAMES = (R.get('topic_names') or
             (_LDA_BASE + [f'Topic {i+1}' for i in range(len(_LDA_BASE), n_topics)])
            )[:n_topics]
```

Priority order:
1. `R['topic_names']` if present and non-null — the API-generated or user-assigned names
2. `_LDA_BASE` padded with generic labels — the fallback for runs without naming

### --name-topics flag

```bash
python3 src/03_nlp_pipeline.py --name-topics
```

After fitting LDA, calls the Anthropic API once per topic (7 calls ≈ $0.01)
with the topic's top 12 TF-IDF words and top 8 highest-lift index terms as input.
The prompt asks for a 2-5 word label that captures intellectual orientation,
not a generic category — "Viable System & Stafford Beer" rather than "Management".

### Persistence across re-runs

If `nlp_results.json` already contains `topic_names` from a previous naming run,
and the new run produces the same n_topics, the names are **carried forward
automatically** — even for `--weighted` re-runs. If n_topics changes, the names
reset to the fallback (different k = different clusters = old names are wrong).

To rename: run `--name-topics` again.
To manually override: edit `topic_names` in `nlp_results.json` directly before
running downstream scripts.

### Which scripts were updated

All 10 downstream scripts now read `topic_names` dynamically:
`06_build_report.py`, `06_build_report_chapters.py`, `07_build_excel_chapters.py`,
`08_build_timeseries.py`, `09b_build_index_analysis.py`, `10_build_index_report.py`,
`11_embedding_comparison.py`, `12_index_grounding.py`, `13_weighted_comparison.py`,
and `build_embed_report.py`.

---

## 21. Entity–Concept Relational Network (`14_entity_network.py`)

### Overview

Builds a person–concept and person–location relational network from the
index vocabulary, visualised as an interactive force-directed graph using D3.js.

### Entity classification

The index vocabulary is classified into three node types:

- **Persons** — entries matching the pattern `Surname, Firstname` or
  `von/de/van Surname` (1,004 persons at n_books≥3 before deduplication).
  Duplicate entries like "Wiener, N." and "Wiener, Norbert" are merged,
  retaining the entry with the higher book count.
- **Locations** — entries matching institutional or geographic keywords
  (University, Institute, Laboratory, specific city/country names): 96 nodes.
- **Concepts** — all other index terms (3,438 nodes at n_books≥3).

### Closeness measures

**Book-level PMI × reliability** (overview):

```
PMI(P, C) = log[ P(P ∩ C) / (P(P) × P(C)) ]
reliability = sqrt( min(overlap, 20) / 20 )
edge_weight = PMI × reliability
```

PMI captures how much more often a concept appears in books that also
feature a given person, relative to its base rate. Reliability dampens
edges supported by very few books (same formula as index-term weighting
in `03_nlp_pipeline.py --weighted`).

**Paragraph-window co-occurrence** (detail):

For the top 50 persons by book count, the script scans up to 30 books per
person, extracting ±5-sentence windows around each mention of the person's
surname. Co-occurring index terms within those windows are counted; edge
weight = log(1 + count). This captures local textual proximity — concepts
that appear in the same paragraph as the person, not just the same book.

Paragraph edges are shown in purple in the visualisation; book-level edges
in grey.

### Graph layout algorithms

The report offers four layout algorithms selectable from a dropdown. All
are implemented using D3.js v7, which is already loaded for the force
simulation — no additional dependencies required.

| Layout | Algorithm | Best for |
|--------|-----------|----------|
| **Force-directed** (default) | Fruchterman-Reingold via `d3.forceSimulation` with `forceManyBody` (charge repulsion), `forceLink` (spring attraction), `forceCollide` (overlap prevention), and `forceCenter` | Revealing organic clusters; exploring the full graph |
| **Radial** | `d3.forceRadial` pins each node to a target radius determined by its kind: persons innermost (r≈13% W), organisations and locations middle (r≈22% W), concepts outermost (r≈37% W). Spring forces are weakened so radial placement dominates | Showing separation between entity kinds; comparing node density per ring |
| **Bipartite** | Fixed x-coordinates (persons left at 18% W, all others right at 82% W), y-coordinates spaced evenly by degree rank. Limited to top 100 nodes per side for readability. Spring forces set to zero | Tracing which specific persons connect to which concepts/orgs/locations |
| **Circular** | Nodes placed on a circle (r≈39% min(W,H)) divided into arc segments by kind: persons 0°–180°, concepts 180°–270°, organisations 270°–300°, locations 300°–360°. Ordered by degree within each arc | Overview of hub connectivity patterns; seeing which kinds have the densest cross-connections |

**Implementation note:** Bipartite and circular layouts use fixed positions
(`node.fx`, `node.fy`) — the simulation runs with minimal spring and charge
forces just to animate the transition. Force-directed layout clears all
fixed positions before running. Switching layouts calls `switchLayout()`,
which releases fixed coordinates and calls `filterGraph()` to rebuild.

**Bipartite note:** this graph is mathematically bipartite — persons only
connect to concepts, organisations, and locations, never to other persons.
The clustering coefficient is therefore always 0 and is not reported. The
bipartite layout makes this structure explicit.

### Visualisation controls

Interactive D3.js report. Controls:
- **Search** — filter to a person or concept and their immediate neighbours
- **Show checkboxes** — toggle Persons, Concepts, Organisations, Locations independently
- **Edges** — filter by edge type (person–concept, person–organisation, person–location)
- **Level** — book-level PMI edges, paragraph-window edges, or both
- **Min weight** — slider to hide weak associations
- **Min degree** — filter to top 25%/10%/5%/1% nodes by degree
- **Layout** — switch between the four layout algorithms
- **Charge** — adjust force-directed repulsion (only affects force layout)
- **📊 Network stats** — toggle the statistics panel
- **Click any node** — side panel shows top 25 associations with weights and level

### Usage

```bash
python3 src/14_entity_network.py                  # full (book + paragraph)
python3 src/14_entity_network.py --no-windows     # book-level only (fast)
python3 src/14_entity_network.py --min-books 5    # stricter entity threshold
```

The paragraph-window pass processes the top 50 persons against up to 30 books
each, scanning 80,000 characters per book. On a 675-book corpus this takes
approximately 3–5 minutes.

---

## 22. Entity Classification Pipeline (`15_entity_classify.py`)

### Motivation

The index vocabulary contains a wide range of term types — genuine intellectual
concepts, person names, institutions, geographic locations, book titles, and
noise (encyclopedia headings, garbled author affiliations). A single heuristic
classifier cannot handle all of these reliably. `15_entity_classify.py` runs
once, produces a persistent cache, and enables `14_entity_network.py` to make
accurate node-kind assignments without re-running expensive NER on every
network build.

### Three-stage pipeline

**Stage 1 — Heuristics (instant, no dependencies)**

Applied in order; first match wins:

1. **Noise suppression:** ALL_CAPS headings, entries < 3 characters,
   garbled author-affiliation strings (length > 60 with ≥2 commas),
   standalone stopwords (`and`, `or`, `the`, `of`, `etc`)
2. **Index sub-entry fragments:** terms ≤ 6 words starting with a preposition
   or conjunction (`of a`, `and control`, `in cybernetics`) — these are
   artifacts of flat index extraction, not genuine concepts
3. **Work/book titles:** entries matching `Word(s) (Surname)` pattern, a
   curated `BARE_BOOK_TITLES` set, and article-led phrases ≥ 4 words
   (`The Mathematical Theory of...`) — suppressed entirely
4. **Persons:** `Surname, Firstname` pattern + `von/de/van/der` prefixes +
   37 curated single-name historical persons (Aristotle, Plato, etc.)
5. **Organisations:** `ORG_PAT` keyword match (University, Foundation, Lab)
   + curated `KNOWN_TECH_ORGS` (Google, Facebook, IBM, NASA, etc.)
6. **Locations:** `GEO_PAT` country/city/region match

**Stage 2 — spaCy `en_core_web_sm` (local, offline, ~500 terms/sec)**

Remaining terms are classified by spaCy NER. Label mapping:
`PERSON→person`, `ORG→organisation`, `GPE/LOC→location`,
`WORK_OF_ART→suppress`, `NORP/EVENT/LAW/LANGUAGE→concept`.
Terms where spaCy confidence is below 0.75, or spaCy returns an unmapped
label, are sent to Stage 3.

Install: `pip install spacy && python3 -m spacy download en_core_web_sm`

**Stage 3 — Wikidata REST API (for uncertain terms, ~2 req/sec)**

Queries `wikidata.org/w/api.php` for each uncertain term:
1. `wbsearchentities` — finds the best-matching Wikidata entity
2. `wbgetentities` — retrieves P31 (instance of) claims
3. P31 Q-codes are mapped to our four kinds via `WIKIDATA_KIND_MAP`

No API key required. Rate-limited to 2 terms/sec (each term = 2 API calls).
At ~25% of 3,000 uncertain terms → ~375 Wikidata queries → ~3 minutes.

### Cache

Results are stored in `json/entity_types_cache.json` as:
```json
{"term_lower": {"kind": "concept", "source": "spacy", "label": "Original Term",
                "confidence": 0.9, "spacy_label": "NORP"}}
```

`14_entity_network.py` reads this cache and uses any entry with
`confidence ≥ 0.75` to override its own heuristic classification. Entries
below the threshold fall back to heuristics. The cache is permanent — re-run
with `--refresh` to reclassify everything, or `--no-wikidata` for offline use.

### Usage

```bash
# Full pipeline (requires spaCy model + network for Wikidata)
python3 src/15_entity_classify.py

# Offline / air-gapped (heuristics + spaCy only)
python3 src/15_entity_classify.py --no-wikidata

# Discard cache and reclassify everything
python3 src/15_entity_classify.py --refresh

# Then rebuild the network
python3 src/14_entity_network.py --no-windows
```

---

## 23. Index Extraction and Vocab Canonicalisation

### Extraction improvements (`09_extract_index.py`)

Several noise categories were identified in the raw index extraction and
filters added:

| Pattern | Fix | Examples caught |
|---------|-----|----------------|
| Multi-letter alphabetical headers | Extended `ALPHA_HEADER` to match `A B C D...` sequences | `X Y Z`, `A B C D E F` |
| Ebook preamble text | `PREAMBLE_RE` filter | `"page numbers refer to printed version"` |
| Author affiliation strings | `AUTHOR_AFFIL_RE` filter on `Editor: Name, University, Country` | 44 entries suppressed |
| Sub-entry function fragments | `FUNC_FRAGMENT_RE` filter in sub-entry and main entry loops | `"of cybernetics"`, `"and control"` |
| Pure page-number strings (incl. roman numerals) | Extended `PAGENUM_ONLY` to match roman numerals | `xxi–xxii`, `iii` |
| Very long lines | Lowered threshold from 120 → 100 chars | Run-on prose that leaked in |

### Vocab canonicalisation (`09b_build_index_analysis.py`)

Three canonicalisation passes are now applied when building `index_analysis.json`:

**1. Noise suppression**

Terms matching any of these patterns are excluded from the canonical vocab:
- Function-word fragments ≤ 6 words starting with `of`, `and`, `in`, etc.
- ALL-CAPS headings (5+ characters)
- Ebook preamble text
- Author affiliation strings (`University` + country name)
- Strings longer than 80 characters with ≥ 2 commas

**2. Person name merging** (`build_person_merge_rules`)

172 person-name surname groups had multiple variants (initialised vs full
firstname). The algorithm:

1. Groups entries by surname
2. Filters to clean entries (`_is_clean_name`: no digits, no semicolons, firstname ≤ 30 chars)
3. Selects canonical = clean form with most full firstname words, provided it has ≥ 8% the coverage of the most-cited variant (prevents rare full-form from overriding well-cited short form)
4. Merges initialised forms into canonical using `_is_initial_of`: checks that each word in the variant is either identical to or an initial of the corresponding canonical word

Examples: `Wiener, N.` → `Wiener, Norbert`; `Foucault, M.` → `Foucault, Michel`; `Shannon, C.` → `Shannon, Claude`. Produces 262 merge rules affecting ~1,214 book-term citations.

**3. Accent normalisation**

3 person-name pairs normalised: `Descartes, René/Rene`, `Schrödinger/Schrodinger`, `Durkheim, Émile/Emile`. The accented form is preferred when it has equal or greater coverage.

**Effect on vocab size**

| Stage | Entries at n_books ≥ 3 |
|-------|------------------------|
| Before canonicalisation | 4,720 |
| After noise suppression | ~4,540 (−180) |
| After person merging | ~4,280 (−260) |
| Final canonical vocab | ~4,280 |

The reduction is modest because most noise was already below the n_books ≥ 3
threshold. The person merges matter more for signal quality than vocab size:
they concentrate 1,214 scattered book-term citations into their correct
canonical entries, increasing PMI scores for those persons.

---

## Alpha-ratio computation — updated method (front-matter sampling)

*Updated 3 April 2026 — replaces original first-5000-char method*

### Purpose

The alpha-ratio filter excludes books whose clean text is predominantly
non-alphabetic — catching OCR-failure books that cleared the minimum character
threshold with garbage content (e.g. [1262] *Ecological Communication* at
alpha≈0.04 before OCR reindex, acting as an LDA probability sink).

### Original method (deprecated)

The first 5,000 characters of `clean_text` were sampled. Alpha ratio was
computed as the proportion of alphabetic characters. Threshold: 0.40.

**Problem:** Front matter (publisher metadata, series information, copyright
notices, Cyrillic OCR fragments in translated works) appears in the first
5,000 characters and is not representative of a book's intellectual content.
Six books with good body text (alpha 0.71–0.78 over full text) were
incorrectly excluded because front matter dragged the sample below threshold.

### Updated method

```python
def _alpha_ratio(text, sample=5000, n_windows=3):
    n = len(text)
    if n < sample:
        return sum(c.isalpha() for c in text) / n if n else 0.0
    # Skip first 10% — front matter is unreliable
    start = max(sample, n // 10)
    body  = text[start:]
    if len(body) < sample:
        return sum(c.isalpha() for c in body) / len(body)
    # Draw n_windows evenly-spaced windows across the body
    step = (len(body) - sample) // max(n_windows - 1, 1)
    ratios = []
    for i in range(n_windows):
        window = body[i * step : i * step + sample]
        ratios.append(sum(c.isalpha() for c in window) / len(window))
    return sum(ratios) / len(ratios)
```

**Key changes:**
- Skip first 10% of text (or at least the first `sample` characters) to
  avoid front-matter contamination
- Sample 3 evenly-spaced windows from the body rather than one window from
  the start
- Average across windows for a robust estimate

**Threshold:** 0.40 (unchanged). The fix raises the sampling start point,
not the threshold. Books with genuinely garbled OCR throughout still fail.

**Books recovered:** [205] *The Phenomenon of Science*, [265] *Organizational
Systems (VSM)*, [413] *Neocybernetics in Biological Systems*, [597] *Between
an Animal and a Machine*, [1261] *Social Systems*, [1918] *A More Developed
Sign* — all had clean body text (alpha 0.71–0.78) but contaminated front matter.

---

## LDA topic count selection — canonical k=9 (695-book corpus)

*Added 3 April 2026*

### Stopping criterion hierarchy

Three criteria applied in dependency order:

**1. Coherence sweep** identifies the region of feasible k. NPMI coherence
over top-10 words per topic, k=2–12. Provides a rough indication of meaningful
structure; not a sufficient criterion alone — coherence can increase with k
due to topic fragmentation without interpretive gain.

**2. Dead-topic count** bounds the ceiling of k. A dead topic has a
near-uniform word distribution, arising structurally when k exceeds the
corpus's data capacity. Dead-topic count is less sensitive to random seed
than stability scores, giving it higher epistemic standing as a stopping
criterion.

**3. Stability scores** characterise consistency within the fixed seed set.
Mean Jaccard overlap of top-N word sets across all pairs of the 5-seed run,
aligned by Hungarian algorithm. Stability scores are seed-set-relative (see
below).

### k=9 selection

Post-overhaul sweep (695 books, seeds 42/7/123/256/999):

| k | Coherence | Dead topics | Stable (≥0.3) | Mean stability |
|---|---|---|---|---|
| 9 | 0.0668 | 0 | 7/9 (78%) | 0.382 |
| 10 | 0.0721 | 0 | 6/10 (60%) | 0.383 |

k=9 selected: zero dead topics; 78% stable topics (vs k=10's 60%); two
unstable topics interpretable rather than noise (T3 vocabulary overlaps
multiple traditions; T9 is documented residual). k=10 redistributed
instability across more topics without resolving T9.

### Epistemic status of stability scores

Stability scores are **seed-set-relative**. "T1 is stable across seeds
42, 7, 123, 256, 999 at k=9" is the valid claim; "T1 is a stable topic for
this corpus" overclaims. A different seed set might produce different rankings.
Multiple distinct stable solutions may coexist at a given k — fixed seeds
provide one sample from a potentially multi-modal solution space.

The dead-topic criterion has higher epistemic standing: degenerate distributions
arise structurally from over-specification regardless of initialisation.

### Canonical solution and restoration

`topic_stability.json` always reflects the most recently run k. After any
comparison run at a different k, restore with:

```bash
python3 src/03_nlp_pipeline.py --min-chars 10000 --lemmatize --topics 9 --seeds 5
python3 src/09c_validate_topics.py --top 10 --md
python3 patch_topic_names.py   # re-apply agreed topic taxonomy
```

`run_all.sh` calls `03_nlp_pipeline.py --topics 9 --seeds 5` explicitly to
enforce the canonical solution.

---

## Publication type exclusion policy

*Added 3 April 2026*

### The implicit monograph assumption

Every analytical step in the pipeline embodies an implicit model of what a
book is: a single-author, thematically coherent text with end-of-book
references and a unified back-of-book index. This was never stated explicitly.
It is approximately correct for monographs (65.4% of the classified corpus)
and systematically wrong for other types in predictable, consequential ways.

### Violations by publication type

**Conference proceedings — excluded**

| Assumption | Violation |
|---|---|
| Thematic coherence | Proceedings deliberately aggregate diverse contributions; low LDA coherence is an epistemic practice, not a model failure |
| Reference location (end of book) | References at end of each paper; end-of-book extraction captures only the last paper's citations |
| Unified back-of-book index | No unified index typically present |
| Document unit = book | A proceedings volume is a container for N independent papers; treating it as one LDA document is a category error |

**Handbooks — excluded**

| Assumption | Violation |
|---|---|
| Thematic coherence | Chapters by different authors on different subtopics; positional sampling may capture entirely unrelated content |
| Reference location | Often at chapter ends, not volume end |
| Index authority | Aggregates community vocabulary, not one author's concept architecture |

**Readers — excluded**

| Assumption | Violation |
|---|---|
| Original authorial voice | Curates existing texts; no single author whose intellectual signal the pipeline extracts |
| Unified concept map | Index covers reprinted texts whose vocabulary the editor did not produce |

**Anthologies — retained with caveats**

Structurally more similar to monographs; editorial framing may provide
coherent intellectual argument. Retained but expected low coherence tolerated
and documented. Vocabulary dilution from multiple authors is a known bias.

### Corpus impact

After 4 manual reclassifications (verified=True in book_styles.json):
- [267] proceedings → history_bio (memoir of conference, not proceedings)
- [1195], [1774] reader → monograph (Powers' own collected papers)
- [1271] handbook → popular (popular science, misclassified)

Final: 22 books excluded (3.0%), 704 retained (97.0%). Excluded books are
disproportionately `curated_pure` stratum (68% of exclusions vs 45.5% of
corpus) — the exclusion policy and precision-recall stratification identify
overlapping populations of methodologically marginal inclusions.

### Temporal dimension

The exclusion decision is type × era, not type-only. Pre-digital (pre-1990)
proceedings and handbooks may be typeset as quasi-monographs — inspect
individually. Post-1990: exclude without individual inspection.

| | Pre-digital (~pre-1990) | Early digital (~1990–2010) | Born-digital (~2010+) |
|---|---|---|---|
| Proceedings | ⚠ Inspect individually | ✗ Exclude | ✗ Exclude |
| Handbook | ⚠ Inspect individually | ✗ Exclude | ✗ Exclude |
| Reader | ✗ Exclude | ✗ Exclude | ✗ Exclude |

### Implementation status

`book_styles.json` records classifications and reclassifications. Exclusion
filter in `03_nlp_pipeline.py` NOT yet implemented — pending signal inventory
audit and document unit decision (moratorium in effect).

---

## Signal inventory framework

*Added 3 April 2026*

### Motivation

The book style classification effort initially aimed to assign categorical
labels and validate against ground truth. Two observations disrupted this:

1. **Book types are not disjoint.** Ashby's *Introduction to Cybernetics* is
   simultaneously a monograph and a textbook. Categorical ground truth
   presupposes a structure the phenomenon does not have.

2. **The relevant question changes.** The pipeline cares not about what *type*
   a book is but which *pipeline assumptions* it violates. This question is
   answerable without categorical commitment and directly relevant to pipeline
   behaviour.

### Signal dimensions

For each book, record observable structural signals that directly determine
pipeline behaviour:

| Signal | Type | Observable from | Pipeline implication |
|---|---|---|---|
| `index_present` | binary | index_terms.json status | Include/exclude from index-term analysis |
| `reference_location` | 3-way: end/chapter/none | Text inspection (planned) | Reference extraction strategy |
| `author_count` | count | Calibre authors field | Vocabulary dilution flag for TF-IDF |
| `has_editor` | binary | Calibre/text first 400 chars | Anthology inference; vocabulary mixing |
| `publication_era` | 3-way: pre/early/born-digital | pubdate field | Index quality covariate |
| `chapter_count` | count | Text structure (planned) | Document unit decision |

### Schema

Each signal in `book_styles.json` has three fields: value, confidence
(0.0–1.0), and source (provenance). Source priority:
`manual` > `calibre:google` > `calibre:amazon` > `text_extraction` > `classifier`

```json
{
  "BOOK_ID": {
    "schema_version": 1,
    "index_present": true,
    "index_present_confidence": 0.95,
    "index_present_source": "text_extraction",
    "has_editor": false,
    "has_editor_confidence": 0.85,
    "has_editor_source": "calibre:google",
    "publication_era": "early_digital",
    "publication_era_confidence": 1.0,
    "publication_era_source": "calibre:pubdate"
  }
}
```

**Three-state model:** true / false / null (unknown). Null propagates
gracefully — unknown signals use default assumption and are flagged in output.

### Validation approach

Signal observations replace categorical ground truth for pipeline validation:
- "Do books the classifier labels as monographs tend to have `index_present=true`?"
- "Do books with `has_editor=true` tend to have lower LDA topic coherence?"

These questions are directly relevant to pipeline behaviour and do not require
categorical commitment. They replace "is the classifier correct?" which is
incoherent given non-disjoint types.

### Relation to Calibre labels

159 books already labeled in Calibre (`custom_column_5`) with multi-label
combinations — consistent with binary relevance and confirming non-disjoint
structure in practice. Signal inventory complements categorical labels: labels
serve interpretive and communication purposes; signals drive pipeline behaviour.

### Implementation status

Planned. Schema agreed. Moratorium on NLP pipeline code applies. Document unit
decision must be formally recorded before implementation begins.

---

## Publication type classification — expert labels, not ground truth

*Added 7 April 2026*

### Terminological principle

Publication type labels in this pipeline are **expert judgements**, not
ground truth. The distinction matters because:

- Publication types are not disjoint (§13, epistemic affordances memo):
  a book can simultaneously be a monograph and a textbook
- Reasonable experts may disagree on borderline cases — this disagreement
  is genuine ambiguity in the phenomenon, not labelling error
- "Ground truth" implies a single correct answer that exists independently
  of the observer; expert judgements do not have this property

The classifier is therefore described as learning to **replicate expert
judgement** on this corpus, not as detecting objective publication types.
Agreement with expert labels is the evaluation criterion, not accuracy
against a true label.

### Label source

Expert labels are stored in Calibre `custom_column_5` (159 books as of
7 April 2026). Labels use a controlled vocabulary:
`monograph`, `anthology`, `textbook`, `collected works`, `proceedings`,
`reference`, `journal special issue`.

Multi-label combinations are stored as comma-separated strings, sorted
alphabetically for consistency (e.g. `monograph, textbook` not
`textbook, monograph`).

**Critical rule:** machine-inferred labels from `00_classify_book_styles.py`
must never be injected into the expert-labelled set. The expert labels
are the reference set for evaluating the classifier; using machine output
as reference would be circular. The 4 manual reclassifications
(verified=True in `book_styles.json`) may be included as they represent
Paul's expert judgement, not machine inference.

### Classifier design

**Phase 1 — binary classifier (current):**
Monograph vs. not-monograph. Positive class includes all books with
`monograph` in their expert label set (including combinations).
Trained on 197 expert-labelled books using logistic regression with
`class_weight='balanced'` to compensate for 4:1 class imbalance.
Decision threshold set at 0.4 (not default 0.5) to recover monographs
with Springer/Routledge publishers that were false negatives at 0.5.

**Features:**
23 metadata features + 10 heuristic text features = 33 total.
Heuristic features are structural text signals extracted from
`books_clean.json` clean text (see `src/heuristic_features.py`).

**Validation:**
Random sampling from predicted classes followed by expert review.
The agreement rate (proportion of sampled predictions that match
expert review) estimates classifier reliability on unlabelled books.
Reviewed samples are added to the expert label set for subsequent
retraining — active learning without circularity.

**Phase 2 — expanded classifiers (deferred):**
Binary relevance classifiers for anthology, textbook, and collected
works, once sufficient expert labels exist (minimum ~20 positive
examples per class). Journal special issue and reference are too
sparse for supervised classification; rule-based classification
is appropriate for these rare types.

### Implication for AI-human teaming

This methodology embeds a general lesson: AI systems generate
classifications fluently and at scale, creating pressure to treat
machine output as authoritative. Maintaining the distinction between
expert judgement and machine inference — and enforcing it structurally
by keeping the two data sources separate — is a methodological
discipline that must be explicitly designed into the workflow.
It will not emerge spontaneously from the AI's elaboration.

---

## Corpus-scale epistemic access: what the pipeline reveals and what it cannot
*Added 15 April 2026 (Cowork session)*

### The scale problem in knowledge access

695 books spanning 70 years represents approximately 60,000–120,000 pages of text. No
individual reader can hold the full structure of such a collection in working memory
simultaneously. But the epistemic challenge is not only practical — it is structural. What
it means to "understand" a corpus rather than its individual texts is a different question
from what it means to understand any one of those texts.

### Two distinct epistemic modes

Individual reading and corpus-scale NLP produce different kinds of knowledge and answer
different questions.

**What individual reading affords:** comprehension of specific arguments and their logical
structure; sensitivity to rhetorical register, qualification, and provisionality; awareness
of intertextual relationships (specific debates, responses, objections); tacit context
required to interpret explicit claims.

**What corpus-scale NLP affords:** topic structure — which intellectual clusters exist
across the collection; temporal evolution — how thematic emphases have shifted over 70
years; concept velocity — which terms are stable anchors and which are migrating across
traditions; network centrality — which persons and concepts are most connected across
the field.

These are not two ways of answering the same questions at different speeds. They are
qualitatively different epistemic modes. The research questions in this project
(topic structure, temporal evolution, network centrality, concept velocity) are only
askable at corpus scale. They cannot be answered by reading individual books, no matter
how carefully or extensively.

### Additional caveat: index compilation changed across the 70-year span

The index-as-controlled-vocabulary signal is not uniform across the corpus. Books published
before approximately the 1990s typically have hand-compiled indexes: selective, semantically
rich, reflecting expert judgement about what is conceptually significant. Books published
after the widespread adoption of desktop publishing and automated index generation tend to
have denser, more mechanically produced indexes that are less discriminating.

This temporal shift in index compilation practice is a confound in the concept velocity
analysis: apparent changes in concept frequency over time may partially reflect changes in
indexing practice rather than changes in intellectual emphasis. This should be acknowledged
as a limitation in the paper's treatment of temporal trends, alongside the existing
index quality stratification framework (§4 of the epistemic affordances memo).

### What the pipeline preserves and what it loses

Each compression operation in the pipeline is not neutral with respect to epistemic
content:

**Preserved:** statistical vocabulary patterns across the corpus; most frequent and
distinctive index concepts; entity co-occurrence within paragraph windows; temporal
trends in concept frequency.

**Lost:** argument structure and logical relationships between claims; rhetorical register
(irony, qualification, provisionality); the reader-text relationship; intertextual
specificity (which author was responding to whom); tacit disciplinary knowledge.

The pipeline is better at characterising what the cybernetics tradition *discussed* than
what it *argued*. It maps the concept space more reliably than the claim space. This is a
systematic bias that should be stated explicitly in the paper rather than implied by
silence.

### Reference
Full theoretical development — including the self-referential connection to Ashby's Law of
Requisite Variety and the proposed theoretical contribution statement — is in §15 of
`docs/memo_media_aware_nlp_epistemic_affordances.md`.

---

## Residual error propagation and the limits of upstream cleaning

*Added 17 April 2026 — revised same session after corpus inspection*

### The methodological point

Data cleaning in a corpus NLP pipeline reduces *known* error classes. It does not
eliminate errors of unknown type and magnitude. The distribution of residual errors —
what remains after cleaning — is itself unknown. This is not a failure of the cleaning
procedure; it is a structural feature of working at scale with heterogeneous, OCR-derived
text from sources with variable production standards across seven decades.

The consequence is that any downstream algorithm which makes simplifying assumptions about
its input is susceptible to corruption by residual errors in ways that cannot be fully
anticipated or measured. The severity of corruption depends on the algorithm's specific
assumptions and on the statistical properties of the residual errors — neither of which
is known in advance.

### Observed instance: Wiener–Google association in the entity network

The entity network (`14_entity_network.py`) uses book-level PMI to score person–concept
associations: how much more often do two index terms co-occur across books than chance
would predict? Norbert Wiener appeared with a PMI score of 1.0 against Google, based on
9-book overlap — the 4th strongest association in his edge list, ranking above Cold War.

Corpus inspection revealed two distinct sources for this artefact, which require different
fixes:

**Source 1 — Temporal co-occurrence (structural):** Google and Amazon are mentioned
legitimately in 95 and 60 books respectively — modern books on algorithms, AI, and digital
culture that discuss Wiener as a historical founding figure *and* contemporary platforms as
examples. This is not a data quality error. It is a structural consequence of the corpus
spanning 70 years: book-level PMI does not distinguish between historical and contemporary
entities, so genuine co-occurrence across the temporal range produces associations that are
statistically real but intellectually meaningless (Wiener died in 1964; Google was founded
in 1998).

**Fix:** Exclude known modern technology platforms from the entity network *before* PMI
is computed. For book-level PMI, each edge is computed independently, so pre-computation
exclusion is equivalent to post-computation exclusion — no other entity's scores are
affected by a platform's presence. `14_entity_network.py` now maintains a
`KNOWN_TECH_PLATFORMS` set (Google, Amazon, Facebook, Meta, Twitter, Apple, Microsoft,
OpenAI, etc.) checked at entity classification, before book sets or PMI scores are
built. Added 17 April 2026.

**Source 2 — Index vocabulary noise (data quality):** Structural document navigation
terms — "Chapter" (12 books), "Index" (15 books), "Introduction" (15 books), "Volume"
(14 books), "Series" (11 books), "Section" (7 books), "Below." (5 books) — were
appearing as index vocabulary items in `index_analysis.json`. These enter the index from
cross-references in back-of-book indexes ("see Chapter 3"), section markers, and
front-matter fragments that survived the extraction step. Additionally, Internet Archive
digitisation notices ("Digitized by the Internet Archive in 2022 with funding from
Kahle/Austin Foundation") appeared in 67 books and contributed "Internet Archive" and
related strings to the entity vocabulary.

**Fix:** Extended `is_noise_term` in `09b_build_index_analysis.py` with two new
patterns: `_STRUCT_NAV` (structural navigation terms matched as whole tokens) and
`_PLATFORM` (digitisation attribution strings). Extended `INLINE_PATTERNS` in
`02_clean_text.py` to strip Internet Archive notices from body text before
`books_clean.json` is written. Added 17 April 2026.

### When output exclusion is and is not sufficient

The two sources above require different reasoning about where to intervene:

For **book-level PMI** (the mechanism in this case): each person–entity edge is computed
independently from two book sets. Excluding an entity before book sets are built means
it contributes no edges. It does not affect any other entity's book set or PMI score.
Output exclusion and input exclusion are equivalent. Either works.

For **paragraph-window co-occurrence** (the second mechanism in `14_entity_network.py`):
if a contaminating string is dense enough to appear in many windows alongside many other
entities, its presence could inflate co-occurrence counts for those other entities even
if the contaminating entity itself is later excluded. In this corpus the paragraph-window
signal is less dominant than book-level PMI, and the contaminating strings are not dense
enough to cause measurable inflation. But in principle, a very high-frequency
contaminating term (appearing in every book, in every window) could corrupt other
entities' co-occurrence scores — in which case input text stripping is the correct fix,
not entity exclusion.

The general rule: output exclusion is sufficient when edges are computed independently
and contamination does not inflate other entities' statistics. Input stripping is required
when contamination is dense enough to act as a global co-occurrence booster.

### General implication

This instance illustrates that domain expertise is a necessary check on algorithmic
outputs. The Wiener–Google association is immediately interpretable as wrong on historical
grounds. An association between two legitimately co-occurring entities with a slightly
inflated PMI due to residual noise would not be detectable by inspection. The pipeline
should be treated as producing findings that are reliable in aggregate and indicative at
the level of individual associations, but subject to residual error of unknown distribution
that is not self-diagnosing.

This does not invalidate the pipeline's findings. It does establish that:

1. Domain expertise is required to detect the class of artefacts that are implausible
   on substantive grounds — the algorithm cannot flag them.
2. Upstream cleaning must target the specific input of each algorithm, not only the
   global text preprocessing step. Different algorithms have different sensitivities.
3. The paper should state that entity network results are conditional on index vocabulary
   quality and that temporal co-occurrence across a 70-year corpus is a known limitation
   of book-level PMI without temporal stratification.

### Implication for dissemination — all outputs are provisional

*Added 18 April 2026*

The argument above about residual error applies not only to the entity network but to all
pipeline outputs. Because the distribution of residual errors is unknown, and because each
algorithm in the pipeline makes different simplifying assumptions, the degree to which any
specific result is corrupted by residual error cannot be determined in advance. Domain
knowledge can flag individual artefacts (as with Wiener–Google), but cannot certify the
absence of subtler, undetectable artefacts elsewhere.

This has a direct consequence for dissemination: **all pipeline outputs should be treated
as provisional results subject to validation, not as findings.** This applies equally to:

- **Interactive HTML reports shared with collaborators or the public** — viewers may
  identify misclassifications or implausible associations, and this is to be expected and
  welcomed. A mechanism for viewers to submit corrections is planned (see ROADMAP #15);
  in the meantime, any flagged issue should be checked against the source data before
  being dismissed or accepted.

- **Peer review** — reviewers should be told explicitly that (a) the pipeline operates
  at a scale that precludes manual verification of every output; (b) known error classes
  have been characterised and mitigated (OCR quality bands, platform contamination,
  fragment nodes, entity misclassification); (c) unknown residual errors remain and their
  distribution is uncharacterised; (d) results should therefore be interpreted as
  large-scale patterns that are robust in aggregate and indicative at the level of
  individual associations, rather than as individually certified facts.

The practical formulation for paper and report framing:

> *Results are derived from automated analysis of a 542-book corpus and should be treated
> as provisional. Known data quality issues have been characterised and mitigated; residual
> errors of uncharacterised distribution remain. Individual associations should be verified
> against source material before being treated as established findings.*

This is not a weakness to be minimised in the write-up. It is an honest account of what
corpus-scale computational analysis can and cannot claim — and it is consistent with the
broader argument in §15 of `docs/memo_media_aware_nlp_epistemic_affordances.md` that the
pipeline produces a form of *corpus-scale epistemic access* rather than ground truth.
