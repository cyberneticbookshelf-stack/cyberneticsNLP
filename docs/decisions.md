# Design Decisions & Rationale

## Why two pipeline tracks (book-level and chapter-level)?

Book-level analysis gives a high-level view of how books cluster thematically.
Chapter-level analysis reveals the internal intellectual structure of each book
and enables cross-book comparison at finer granularity — showing, for example,
that chapters on mathematical control theory may cluster together whether their
dominant topic is "Mathematical & Formal Systems", "Control Theory & Engineering",
or "History & Philosophy of Cybernetics."

Both tracks are worth keeping. The book-level report is cleaner and easier to
navigate; the chapter-level report is richer analytically.

---

## Why NMF instead of LDA for chapter-level topics?

LDA was the first method tried. It failed on this corpus for three reasons:

**1. Document length**: LDA's variational inference works better with longer
documents. At ~2,000 words per chapter, the Dirichlet prior assumptions produce
near-uniform topic distributions.

**2. Corpus noise**: Raw OCR chapter text contains mathematical notation fragments,
French loanwords from Wiener's papers (`dans`, `pour`, `avec`), footnote number
patterns, and other artefacts.

**3. Vocabulary diversity**: The corpus spans distinct subject areas
(cybernetics, ecology, architecture, feminist theory, mathematics, etc.) with
almost no lexical overlap between areas. LDA expects documents to mix topics;
here many chapters are dominated by a single subject area, which suits NMF's
parts-based decomposition better.

The fix: NMF on clean abstractive summary text. NMF is more appropriate for
diverse, short document collections and its reconstruction error provides a
meaningful elbow for k selection. With the full 675-book corpus, 6 topics are
semantically clean and well-separated.

---

## Why use abstractive summaries as the NMF input?

The key insight: chapter summaries written in clean prose already contain the
semantic essence of each chapter, without OCR noise, boilerplate, and
multilingual artefacts that pollute the raw text.

An alternative would be aggressive text cleaning of raw chapter text before
vectorisation. This was tried (additional stopword lists, minimum token length,
language detection) but didn't produce adequate results because OCR quality
varies too much between books and mathematical content is fundamentally
non-prose.

The tradeoff: by using 2-sentence summaries (~40–60 words), the topic model
learns from short documents. In practice the 6-topic solution is clean and
interpretable, validating the approach.

---

## Why API-generated abstractive summaries instead of extractive or hand-written ones?

Three approaches were tried in sequence:

**A. Extractive (TF-IDF sentence scoring)** — implemented first, produced
incoherent output. Root cause: OCR-extracted text has unreliable sentence
boundaries. TF-IDF then scores fragment sentences highly because they contain
rare tokens.

**B. Hand-written summaries** — highest quality but not scalable to 675 books
across ~7,000 chapters.

**C. API summarisation (v1)** — the Anthropic API generates clean prose, but
the first implementation had problems: summaries were 300–400 words long (far
exceeding the 60–80 word target), largely extractive (80% of book summaries had
>25% verbatim 8-gram overlap with source text), and front-matter traps caused
some books to be summarised based on editorial boards rather than content.

**D. API summarisation (v2)** — the current approach, with six quality controls:
strict token limits, multi-point text sampling, document type detection, explicit
anti-extraction instructions, verbatim similarity checking with retry, and OCR
fragment title cleaning. See methodology.md §4 for full details.

---

## Why strict token limits for summaries (max_tokens=250 for book, 130 for chapter)?

The v1 script set max_tokens=1,200 (book) and 200 (chapter), giving the model
room to produce long responses. Empirically, this led to verbatim extraction of
long passages rather than genuine abstractive summarisation — 97% of book
summaries had >10% verbatim 8-gram overlap with source text, and the average
descriptive summary was 355 words (target: 60–80).

Setting max_tokens=250 means a 2-sentence summary is physically all the model
can produce. Combined with the "EXACTLY 2 sentences" instruction, this eliminates
the padding behaviour entirely.

---

## Why multi-point text sampling (15%/50%/80%) instead of a single front block?

The v1 script sampled chars 4,000–14,000 (a 10,000-char block near the start).
For monographs this captures the introduction — good. But for journal issues,
edited volumes, festschriften, and handbooks (~32 books in the corpus), chars
4,000–14,000 typically contain: editorial board listings, journal delivery
service URLs, table of contents with contributor names, and abstract collections.
The model then summarised the journal infrastructure ("This issue is available
through EBSCOHost…") rather than the intellectual content.

Three 2,000-char slices at 15%, 50%, and 80% of the document length give the
model a broader view of the book's actual content regardless of where front
matter ends. The 15% offset typically lands past the publisher pages; the 50%
and 80% slices capture the argumentative core and conclusions respectively.

---

## Why document type detection (edited volumes vs monographs)?

Approximately 32 of the 675 corpus books are edited volumes, journal issues,
handbooks, or encyclopedias. These do not have a single author advancing a
single thesis. Asking "what is the central thesis?" of a festschrift produces
nonsense; the correct question is "what topics does this collection cover?"

Detection uses title-string matching against keywords: `journal`, `festschrift`,
`handbook`, `encyclopedia`, `proceedings`, `anthology`, `reader`, `companion`,
`collection`, `essays on`, `kybernetes`, `in memoriam`, etc. Books matching
any keyword receive an edited-volume prompt that asks for coverage overview
and unifying themes instead of thesis and argument.

False positive rate is low because the keyword list is corpus-specific. False
negatives (edited volumes not caught by the keyword list) receive a monograph
prompt but the 2-sentence format and multi-point sampling still produce
reasonable output.

---

## Why verbatim similarity checking with a 35% threshold?

The 35% 8-gram overlap threshold was chosen empirically after measuring the
distribution across all 675 books:

| Overlap | % of books (v1 summaries) |
|---------|--------------------------|
| >10% | 97% |
| >20% | 89% |
| >30% | 62% |
| >40% | 28% |
| >50% | 4% |

A threshold of 35% catches the majority of genuinely extractive summaries
(those where the model has copied chunks of text) while allowing some natural
overlap that occurs even in genuine paraphrasing of highly technical content
(where key terms must be repeated). Setting it lower (e.g., 20%) would trigger
unnecessary retries for most books.

---

## Why scikit-learn rather than gensim?

**gensim** provides:
- Faster LDA via Cython
- Coherence metrics (UMass, C_V) that correlate better with human judgement
- Word2Vec, FastText, Doc2Vec

**Reasons for scikit-learn**:
1. Available in the offline execution environment without pip install
2. Familiar API consistent with the rest of the pipeline
3. NMF in scikit-learn is production-quality and well-maintained

For a production system, gensim LDA + C_V coherence is recommended over
sklearn LDA + perplexity. The pipeline is structured so that `03_nlp_pipeline.py`
can be swapped out without affecting downstream steps.

---

## Why 60,000 characters per book for book-level vectorisation?

Full texts range from 52K to 693K words. Using full text would:
- Produce a memory-intensive TF-IDF matrix
- Amplify repetitive content (running headers, repeated chapter titles)
- Give disproportionate weight to books with large appendices or bibliographies

The first 60K characters captures the introduction and first 3–5 chapters,
where the book's core argument is typically established.

---

## Why K-Means on TF-IDF rather than on NMF topic distributions?

Clustering on topic distributions would produce topic-aligned clusters by
construction — each cluster would simply be the chapters dominated by a given
topic. This is redundant with the topic assignments.

Clustering on TF-IDF captures lexical differences within and across topics,
revealing sub-groupings based on shared vocabulary that cross topic boundaries.
Comparing K-Means cluster assignments with NMF topic assignments is itself
analytically informative: chapters where cluster ≠ dominant topic often
represent intellectually hybrid chapters.

---

## Why the elbow method for K-Means k?

The elbow method is transparent, fast, and requires no additional computation
beyond the K-Means fits already required to plot the inertia curve. Silhouette
scores are computed and plotted alongside for validation.

**Gap Statistic** would be more principled but requires permutation testing
which is slow. **Calinski-Harabász** and **Davies-Bouldin** scores were also
considered but provide no clear interpretive advantage over silhouette for
this corpus.

---

## Why base64-embed figures in the HTML report?

A self-contained HTML file works offline, can be emailed as a single attachment,
and renders identically regardless of where it is opened. The tradeoff is file
size (~18–22 MB vs ~100 KB for a linked version). For this corpus size this
is acceptable.

Interactive charts (Plotly.js) are loaded from CDN and require an internet
connection. The static PNG figures provide an offline fallback for the key
analytical charts.

---

## Why LSA (Truncated SVD) for 2-D scatter rather than UMAP or t-SNE?

UMAP and t-SNE would give better visual cluster separation. They were not
available without network access for package installation in the original
offline environment.

**Truncated SVD** advantages:
- Available in sklearn with no additional installation
- Deterministic (no stochastic embedding)
- Fast on sparse TF-IDF matrices
- Linearly preserves variance

For a production report, UMAP (`umap-learn`) is strongly recommended over
Truncated SVD for the scatter plots.

---

## Why fix random_state=99?

Complete reproducibility. Given the same input CSVs, the pipeline produces
identical outputs on any machine. The seed was changed from the pilot value
of 42 to 99 as part of a sensitivity analysis confirming that the 6-topic NMF
solution and 14-cluster K-Means solution are stable across seeds — the same
topic structure and cluster assignments emerge with seed 42, 99, 123, and 2024.

---

## Why 1,500 TF-IDF features for chapter-level vs 3,000 for book-level?

Chapter summaries are ~40–60 words each. With 1,500 features and ~7,000
documents averaging ~50 words, the vocabulary is already well-estimated.
Using 3,000 features would produce a sparser matrix where many features appear
in very few documents, reducing clustering quality.

A general rule of thumb: TF-IDF vocabulary size should be roughly 10–20× the
average document length in words. For 50-word documents, 500–1,000 features
is theoretically sufficient; 1,500 was chosen with a small buffer.

---

## Why 400 words as the minimum chapter size?

Chapters below 400 words are typically appendices with mathematical notation,
bibliography entries, or supplementary notes — they contain little thematic
information and would bias the topic model if included. They are merged into
an "Other / Minor Sections" aggregate.

---

## Why cap at 20 chapters per book?

Some books produce 50–180 raw chapter splits (especially journal issues or
edited collections with many short pieces). Allowing all chapters would make
certain books dominate the chapter corpus disproportionately. The cap of 20
keeps the largest (most substantive) chapters per book.

---

## Why use back-of-book indexes as a controlled vocabulary?

TF-IDF and NMF work on raw token frequencies, which conflates surface-level
word variation with conceptual significance. Index terms offer a complementary
perspective:

- **Human curation** — editors and authors chose these terms as intellectually
  significant; they are not selected by a statistical criterion
- **Normalisation** — index terms are already de-duplicated and standardised
  within each book (e.g. "feedback loops" rather than "loop", "loops",
  "feedback loop")
- **Concept-level** — index entries like "autopoiesis", "Wiener, Norbert",
  or "Turing Machine" are concept identifiers, not tokens; they handle
  synonymy and variant forms better than raw text
- **Cross-book comparability** — the same term appearing in 40 books is a
  meaningful signal that TF-IDF cannot easily surface without normalisation

The controlled vocabulary is used for four analyses not possible with NMF/LDA
alone: ranked term frequency, decade-by-decade time series, co-occurrence
networks, and term-level topic enrichment.

---

## Why extract indexes from raw OCR rather than a structured source?

The Calibre export does not separate index content from body text — the
`searchable_text` field is the flat OCR output of the entire book. There is
no structured index field. Extraction therefore requires detecting the index
section by heading pattern matching and then parsing the OCR output.

The alternative — manual annotation — was considered but is not tractable
at 675 books. The automated approach recovers clean indexes for 40% of
books, partially recovers another 32% (truncated by the 300k char cap),
and is transparent about failure modes (garbled OCR, no index heading).

---

## Why is 32% of the corpus truncated at the index?

The cleaning step (step 2) caps text at 300,000 characters per book to
control memory usage. The back-of-book index is typically the final section
of a book; for longer books (>300k chars) the index is partially or entirely
beyond the cap.

This could be resolved in a future version by extracting the index directly
from the raw `books_text_*.csv` files (uncapped) rather than from
`books_clean.json`. The extraction logic is independent of the cleaning
step and can be applied to the raw text.

---

## Why filter to terms appearing in 2+ books?

A term appearing in only one book is not part of a shared controlled
vocabulary — it is a local index entry of that book alone. The 2-book
threshold is the minimum meaningful criterion for cross-corpus analysis.

With this threshold, the vocabulary reduces from 131,534 raw unique terms
to 9,807 — an 87% reduction. Terms appearing in 5+ books (1,800 terms) and
10+ books (524 terms) provide progressively cleaner controlled vocabularies
for different analytical purposes.

---

## Why use the last index heading match rather than the first?

Many books reference their own index in the table of contents ("See Index,
p. 345") or in chapter headings. Matching the first occurrence of an
"Index" heading would often land in the table of contents rather than the
actual back-of-book index. Using the last match reliably identifies the
terminal index section.

---

## Why discard lines longer than 120 characters from index sections?

The OCR extraction occasionally includes lines of running prose that have
leaked from adjacent pages into the index section (particularly near the
boundary between the main text and the index). These lines are almost never
valid index entries, which are typically short (3–80 characters). Discarding
lines over 120 characters removes these artefacts with negligible loss of
real index content.

---

## Why a circular layout for the co-occurrence network rather than force-directed?

A true force-directed layout (e.g. Fruchterman-Reingold) would give better
visual cluster separation for the co-occurrence network. It was not
implemented because it requires iterative position computation that is
expensive in pure JavaScript for 40 nodes and is not natively available in
Plotly.js without additional libraries.

The circular layout is deterministic, fast, and sufficient for showing which
pairs are connected and with what weight. For a production visualisation,
a D3.js force-directed layout or Gephi export would be preferable.

---

## Why NPMI coherence rather than perplexity for LDA model selection?

Perplexity (the original metric) measures held-out likelihood — how well the
model predicts unseen documents. It tends to favour higher k values even when
the additional topics are semantically redundant, because more topics always
fit the data at least as well as fewer topics.

The pipeline now uses **mean NPMI coherence** across topic top-word pairs,
implemented directly with numpy and sklearn without gensim. NPMI measures
semantic relatedness via document co-occurrence — a topic is coherent if its
top words tend to appear in the same documents. This correlates much better
with human judgement of topic quality than perplexity.

Empirical comparison across k=5..12 (with multi-point text sampling) showed
that NPMI selects k=5, while perplexity had previously selected k=7. The
k=5 solution is preferred because it is supported by both the semantic
co-occurrence signal and produces more cleanly separated topics.

Both metrics are saved to `nlp_results.json` (`perplexities` and `coherences`
keys) so the selection can always be audited or overridden.

**Why not C_V coherence**: C_V (the metric most correlated with human
judgement in the Röder et al. 2015 benchmark) requires gensim's
`CoherenceModel`, which was unavailable offline. NPMI is the core
computational primitive C_V builds on. C_V adds a cosine-similarity
aggregation step over the NPMI vectors; for model selection purposes
(choosing the best k) mean NPMI gives an equivalent ranking signal.
If gensim becomes available, upgrading to C_V is straightforward using
the code template in methodology.md §11.

---

## Why is there no SymSpell or Enchant de-hyphenation pass?

The current pipeline does not include an explicit step to rejoin OCR
line-break hyphens — the common artefact where a word hyphenated at a line
end in the printed book becomes `feed-\nback` in the OCR output rather than
`feedback`.

What **is** handled: the token acceptance logic in `02_clean_text.py` treats
hyphenated compounds (e.g. `self-organization`, `second-order`) as a unit —
it splits on `-` and accepts the token if all constituent parts pass the
Hunspell dictionary check. This handles intentional hyphens in compound words.

What **is not** handled: OCR line-break hyphens, where the hyphen is an
artefact of page layout rather than part of the word. These would produce two
separate tokens (`feed`, `back`) rather than one (`feedback`). In practice
this affects a small fraction of tokens — professional typesetting uses
line-break hyphens at syllable boundaries, so both fragments are typically
real words that pass the dictionary filter anyway — but it does reduce the
frequency counts for compound terms.

**The recommended fix** is to add a pre-processing step in `clean_book()`
that rejoins line-break hyphens before tokenisation:

```python
# Rejoin OCR line-break hyphens: "feed-\nback" → "feedback"
text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
# Or more conservatively, rejoin only when both fragments are in dictionary:
# text = re.sub(r'([a-z])-\n([a-z])', r'\1\2', text)
```

This should be applied in `clean_book()` before `remove_boilerplate_sections()`.
SymSpell (a fast symmetric-delete spell correction library) would be useful
for a broader OCR correction pass but requires a frequency dictionary and
adds significant processing time. Enchant is a spell-checker abstraction
layer (wrapping Hunspell, Aspell, etc.) and does not provide de-hyphenation
specifically — it would need to be paired with explicit line-break detection.

For this corpus, the Hunspell dictionary filter already removes the most
damaging OCR noise (garbled tokens, numeric fragments, foreign-language
artefacts). De-hyphenation is a lower-priority improvement that would
primarily benefit precision of compound-term frequency counts.

**Status**: de-hyphenation has now been implemented in `parse_and_clean_stream.py`
v2 as a pre-processing step. `02_clean_text.py` (the Hunspell path) does not
yet include it — the fix can be added in the same location.

---

## Why use exact package versions in requirements.txt?

Pinned versions (`scikit-learn==1.8.0` etc.) ensure reproducibility — the
pipeline was developed and tested against these specific versions. Breaking
changes between major versions (particularly sklearn's LDA and NMF APIs)
can alter results silently. The minimum-version syntax (`>=`) used previously
allowed installing future versions that may differ in random initialisation,
default hyperparameters, or numerical precision.

For production use, a full `pip freeze` lockfile is preferable to a
hand-maintained requirements file.

---

## Why switch to JSONL (JSON Lines) for streaming output?

The original `parse_and_clean_stream.py` used `books_clean.json` — a standard
JSON dict keyed by book ID. Each time a new CSV batch was processed, the script:
1. Loaded the entire `books_clean.json` into memory (up to 169 MB)
2. Merged new books into the dict
3. Wrote the entire dict back out

By file 20 of 25, this read-merge-write cycle was loading ~135 MB on every
invocation, creating the very memory bottleneck the streaming design was meant
to avoid.

**JSONL** (JSON Lines, `.jsonl`) stores one JSON object per line. New books
are simply appended — the output file is never read back during processing.
The skip-duplicate check scans only the `"id"` field from each existing line
using a fast regex, not the full clean text (~50 bytes read per book vs
~450 bytes average clean text per book). At 600 books the ID scan reads ~30 KB
rather than 169 MB.

Additional benefits:
- **Crash safety**: a crash mid-write corrupts at most the current line;
  all previous lines remain valid and the next run skips them correctly
- **Streamability**: downstream tools can process the file incrementally
  without loading it all into memory
- **Compatibility**: a one-shot conversion helper at the bottom of the script
  produces `books_clean.json` for any downstream script that expects dict format

---

## Why no L1/L2 regularisation in NMF?

L1 regularisation (`alpha_W > 0`, `alpha_H > 0`, `l1_ratio > 0`) encourages
sparsity in the NMF factorisation — forcing topics to be characterised by
fewer, more distinctive words rather than a diffuse mix across many terms.
This is a well-motivated technique for long-document corpora.

For this corpus it does not work, for a specific and diagnosable reason.

**The problem**: chapter summaries average ~50 words each after abstractive
summarisation. The resulting TF-IDF vectors are already extremely sparse —
most features are zero for any given document. When NMF applies an additional
L1 penalty to the already-sparse H matrix (topic-word weights), it
overcorrects immediately: all weights are driven to zero and every topic
collapses to the same degenerate word list. This was verified empirically
across `alpha` values from 0.01 to 1.0 — any non-zero alpha produced the
same degenerate result.

**The root cause** is the mismatch between document length and regularisation
strength. L1-regularised NMF is designed for corpora where documents are
long enough that many features are non-zero, giving the penalty room to
selectively suppress weak associations. At 50 words per document, nearly
all associations are already effectively zero in the TF-IDF matrix.

**What provides sparsity instead**: the `nndsvda` initialisation
(non-negative double SVD) produces a well-conditioned starting point that
naturally concentrates topic-word weights. Additional vocabulary-level
sparsity is controlled at the TF-IDF stage via `max_features=1500`,
`min_df=2`, and `max_df=0.90` — these hyperparameters are the appropriate
knobs for controlling which words enter the model in the first place.

**The code error**: an earlier version included `l1_ratio=0.1` without
setting `alpha_W` or `alpha_H`. In sklearn's NMF implementation, `l1_ratio`
only takes effect when at least one of `alpha_W` or `alpha_H` is non-zero.
With both at their default of `0.0`, `l1_ratio` is silently ignored.
The parameter was therefore misleading — implying regularisation was active
when it was not. The corrected code uses `alpha_W=0.0, alpha_H=0.0`
explicitly to make the no-regularisation decision visible and intentional.

**If longer summaries are used in future**: if the summarisation step is
revised to produce 150–200 word chapter summaries, re-testing with
`alpha_H=0.01, l1_ratio=0.5` would be worthwhile. At that document length
the TF-IDF vectors would be dense enough for L1 regularisation to be
selective rather than destructive.

---

## Why sample three slices rather than the first 60k characters for LDA?

The original approach took the first 60,000 characters of each book's clean
text as input to the TF-IDF vectoriser. This captures the introduction and
early chapters reliably, but has a systematic bias: for books where the core
theoretical argument develops in later chapters (common in academic monographs),
the vocabulary fed to LDA is dominated by scene-setting and literature review
rather than the book's distinctive intellectual contribution.

The fix takes three 20,000-character slices at 10%, 50%, and 85% through the
text and concatenates them — the same total input length (60,000 chars) but
distributed across the book:

- **10% slice** — past publisher pages and front matter, into the early
  argument
- **50% slice** — the argumentative core, where most academic books develop
  their central thesis
- **85% slice** — conclusions, synthesis, and implications

The 10% minimum offset (with a floor of 4,000 chars) is the same front-matter
avoidance strategy used in `generate_summaries_api.py`. Keeping the total at
60,000 characters preserves the memory budget and TF-IDF matrix size.

This change makes the book-level LDA input strategy consistent with the
API summarisation approach, which independently arrived at the same three-
slice solution when addressing the front-matter trap problem in edited volumes
and journal issues.

---

## Why add a pyspellchecker fallback rather than requiring Hunspell?

The original code hard-coded `/usr/share/hunspell/en_US.dic`, which is the
correct path on Debian/Ubuntu Linux but does not exist on macOS or Windows.
The script silently skipped word filtering when the file was missing, which
meant users on other platforms were running without any OCR noise filtering
without a clear explanation of why.

Three options were considered:

**A. Require Hunspell on all platforms** — Hunspell is available via `brew`
on macOS and as a downloadable `.dic` file on Windows, but requires system-
level installation that is outside `pip` and breaks the "just run pip install"
workflow. This would be the most precise option but creates a significant
setup barrier for non-Linux users.

**B. Require pyspellchecker** — a pure-Python spell-checker available on all
platforms via `pip install pyspellchecker`. No system dependency. However,
pyspellchecker uses a word frequency list rather than a morphological
dictionary, making it slightly less precise than Hunspell for inflected forms
and compound words. It is also a third-party dependency not previously in the
requirements.

**C. Try Hunspell first, fall back to pyspellchecker, then degrade
gracefully** — the implemented approach. It tries 14 known platform-specific
Hunspell paths, then pyspellchecker, then logs a clear actionable warning
with install instructions for all three platforms. This preserves the best
outcome for Linux users (Hunspell), provides a good cross-platform option
(pyspellchecker), and never fails silently.

The cascade also checks a project-local `data/en_US.dic` path, which lets
users on any platform drop a dictionary file into the project directory without
any system installation — useful in locked-down environments.

**Important caveat**: `parse_and_clean_stream.py` (the recommended streaming
path for large corpora) uses regex-only cleaning and has no spell-checking
dependency. For most users processing the full 675-book corpus, the streaming
path is preferable and this entire question is moot.

---

## Why ThreadPoolExecutor rather than multiprocessing for API concurrency?

The suggestion to use `multiprocessing` for CPU-bound tasks is correct in
general. However, profiling the actual pipeline revealed a different picture:

| Step | Time per book | 675 books, 1 core | CPU-bound? |
|------|--------------|-------------------|------------|
| Regex cleaning | 58 ms | 39 s | Mild |
| Hunspell filter | ~20 ms | 14 s | Mild |
| Chapter split + keyphrases | 22 ms | 15 s | Mild |
| **API summary generation** | **~10 s** | **112 min** | **No — I/O bound** |

All the CPU-bound steps complete in under a minute total, making
`multiprocessing` overhead (process spawning, pickling, IPC) not worth the
complexity for those steps. The real bottleneck is the API — each call spends
~10 seconds waiting for a network response, doing nothing.

**ThreadPoolExecutor** is the right tool for I/O-bound work:

- Threads share memory — no pickling of large `books` dict across processes
- Threads release the GIL while blocked on network I/O — full concurrency
- No process spawn overhead — threads start in microseconds
- Simpler code — shared `rate_limiter` and `writer` objects work naturally

`multiprocessing` would be the right choice if Hunspell filtering were
reimplemented as a full morphological analysis pass (e.g. via `spacy` with
`en_core_web_lg`), where per-token NLP processing is genuinely CPU-bound and
the GIL would block threads. For the current set-membership check, it is not.

**Rate limiting design**: a token-bucket `RateLimiter` is shared across all
threads. Each call to `rate_limiter.acquire()` waits until at least
`1/max_rate` seconds have elapsed since the last request across all threads,
then records the current time. This ensures the aggregate request rate never
exceeds the configured limit regardless of how many threads are running. The
rate is set conservatively to `workers × 0.5` req/s to leave headroom for
retries and burst behaviour.

**Thread-safe writes**: a `threading.Lock` in `SafeWriter` ensures that
JSONL append operations are atomic — no two threads can interleave partial
writes. JSONL append is safe because each record is a single `write()` call
of a complete JSON line, which the OS guarantees is atomic for writes smaller
than `PIPE_BUF` (~4096 bytes on Linux). The lock adds an extra safety layer
for larger records and for portability across operating systems.

**Why not async (asyncio)?** `asyncio` would also work well for I/O-bound
concurrency and would avoid thread overhead entirely. However, the existing
`urllib.request` calls are synchronous, and converting the entire codebase to
`aiohttp` or `httpx` async would require more invasive changes. `ThreadPoolExecutor`
achieves the same concurrency improvement with minimal refactoring.

---

## Why sentence transformers rather than word2vec/fastText for semantic embeddings?

**Word2Vec and fastText** produce word-level embeddings, requiring an
additional aggregation step (mean pooling, tf-idf weighted average) to produce
a document-level representation. This aggregation loses sentence structure and
is sensitive to the aggregation method chosen.

**Sentence transformers** (`all-MiniLM-L6-v2`) are trained end-to-end to
produce document-level representations that capture sentence meaning directly.
The model is trained via contrastive learning on sentence pairs — meaning that
similar sentences are pulled together in the embedding space regardless of
vocabulary overlap. This is a better fit for comparing cybernetics books, where
the same concept (e.g. feedback, autopoiesis) may be described with very
different vocabulary across different author styles and disciplinary backgrounds.

`all-MiniLM-L6-v2` was chosen specifically because it is:
- Small (22M parameters, ~90 MB) — runs on CPU without a GPU
- Fast (~5–15 min for 675 books on a modern CPU)
- Well-established — the most widely benchmarked general-purpose sentence
  embedding model as of 2025
- Available via `pip install sentence-transformers` with no system dependencies

Larger models (`all-mpnet-base-v2`, `e5-large-v2`) would likely produce
slightly better clustering but are 3–10× slower on CPU.

---

## Why include Voyage AI embeddings (voyage-3) as a separate method?

Voyage AI is a separate company from Anthropic — it has its own API
(`api.voyageai.com`) and requires a `VOYAGE_API_KEY`, not an Anthropic key.
A free key is available at `https://dash.voyageai.com/`. The original script
incorrectly used `api.anthropic.com/v1/embeddings` (which does not exist),
causing a 404 error; this has been corrected to the Voyage AI endpoint.

Voyage embeddings are trained specifically for retrieval and semantic
similarity tasks, rather than general natural language understanding. For a
corpus comparison task — finding books that are intellectually similar — a
retrieval-optimised embedding may outperform a general-purpose sentence model.

Including it as method D also provides a useful cost-vs-quality data point:
the API costs ~$0.01 for 675 books but requires no local compute, making it
attractive for users running the pipeline on hardware without a GPU.

---

## Why use silhouette score for k selection in the comparison, rather than elbow?

The main pipeline uses reconstruction error elbow for NMF k selection. The
comparison script uses silhouette score for K-Means k selection because:

1. Silhouette score is directly comparable across embedding methods — it
   measures cluster quality in the normalised cosine similarity space that all
   four methods share after L2 normalisation
2. Reconstruction error is specific to NMF's matrix factorisation objective
   and is not meaningful for K-Means
3. Silhouette produces a clear maximum (rather than requiring second-difference
   elbow detection), making automated selection more robust

The `--k` flag allows fixing the cluster count for direct method comparison
at the same k value, which is useful when the methods select different optimal
k values.

---

## Why lift score rather than raw term frequency for index-term topic labelling?

A naive approach would rank index terms by how many times they appear in each
topic's books. But high-frequency terms (e.g. "cybernetics", "system", "theory")
appear frequently in *every* topic — they characterise the corpus, not the
individual topics.

**Lift** normalises by the term's corpus-wide frequency:

```
lift(term, topic) = P(topic | term) / P(topic)
```

A term with lift 4× in Topic 3 appears in Topic 3's books 4× more often than
a randomly chosen book from the corpus. This surfaces terms that are genuinely
distinctive to a topic rather than common across all topics. Terms like
"schismogenesis" (appears almost exclusively in 2nd-Order Cybernetics books)
score high lift; "feedback" (distributed across many topics) scores moderate lift.

---

## Why concept density as scatter bubble size rather than as a separate chart?

Concept Density is one-dimensional — it's a single number per book. Visualising
it in isolation (e.g. a sorted bar chart) would simply rank books by term density
without showing their intellectual position.

Encoding it as bubble size in the 2D semantic scatter adds a third dimension of
information to an already-meaningful chart: the X/Y position captures semantic
similarity, the colour captures topic/cluster membership, and the bubble size
captures terminological density. This reveals, for example, whether dense books
cluster together or are evenly distributed across the semantic space.

---

## Why use chapter-level text (not chapter summaries) in recursive summarisation?

An alternative recursive approach would use the chapter *summaries* (already
generated by the script) as input to the book-level summary. This would be
shorter and cleaner. However, chapter summaries are generated *in the same
run* as the book summary — the chapters haven't been summarised yet when the
book summary is being produced (they run concurrently in threaded mode).

The implemented approach uses chapter *text excerpts* (the first 400 chars of
each chapter's clean text), which are available immediately from the input data.
This avoids a two-pass architecture (summarise all chapters first, then all
books) while still giving the model access to the full narrative arc.

A true two-pass map-reduce (summarise chapters → use those summaries for
book-level summary) would require running the script twice or serialising the
chapter phase before the book phase. This is a valid future improvement.

---

## Why an Embedder class rather than simple functions?

The embedding methods differ significantly in their statefulness:

- **LSA** — must fit a TF-IDF vectoriser and SVD on the corpus; the fitted
  objects are needed for transforming new texts or producing 2D projections
- **Sentence Transformers** — downloads and caches a model; batch size affects
  both speed and memory
- **Voyage AI** — manages an on-disk cache, rate limiting, and exponential backoff

Simple functions would either need to re-fit on every call (wasteful) or require
the caller to manage state. A class encapsulates the state naturally. The
`get_embedder()` factory lets `03_nlp_pipeline.py` request an embedder by
name without importing provider-specific code.

---

## Why sigmoid rather than linear or step-function for lift→weight mapping?

Three options were considered for mapping lift score to feature weight:

**Step function (original proposal):** Anchor=1.0, Signal=2.5–3.0, Frontier=1.5.
Simple to understand and communicate, but creates sharp discontinuities at band
boundaries. A term with lift=8.9 (just below Anchor threshold) gets 3.0×, while
a term with lift=9.0 (just above) gets 1.0×. This is unstable: small changes in
the corpus produce large weight jumps.

**Linear mapping:** w = 1 + (lift − 1) × scale_factor. Smooth but unbounded —
terms with lift=20× (possible for very rare but topic-specific terms) would
receive extreme weights that could destabilise the topic model.

**Sigmoid (chosen):** w = 1 + 2 × (1 − 1/(1+(lift−1)^1.5)). Smooth,
bounded at [1.0, 3.0], and naturally steep in the Signal range (lift 2–5)
while asymptoting gently at the ceiling. The 1.5 exponent was chosen to give
a steeper initial rise than a standard sigmoid while maintaining the ceiling.

---

## Why use maximum lift across all topics rather than per-topic lift?

Each term has a lift score for each LDA topic. We could assign different weights
for the same term depending on which topic's document we're processing (e.g.
"schismogenesis" gets 2.9× weight when processing a T5 book, 1.0× for T2).
This would be a document-conditional weighting.

We chose maximum lift (the highest lift across all topics) for two reasons:

1. **Simplicity:** TF-IDF column scaling requires a single weight per feature,
   not a per-document weight. Per-document weighting would require modifying
   the sparse matrix row-by-row, which is expensive and complex.

2. **Stability:** A term that strongly characterises *any* topic is valuable
   for topic discrimination overall. Even if schismogenesis appears in only one
   topic, boosting it globally helps LDA assign documents to that topic more
   reliably when the term appears.

The reliability dampener (√(min(n,20)/20)) handles the noise case: a term
appearing in 2 books both in the same topic has lift=7× but reliability=0.32,
giving w=1.6×. The same term at n=20 would get w=2.87×.

---

## Entity Network — Classification Decisions (`14_entity_network.py`)

### Why split "location" into "organisation" and "location"

The original location classifier used a single keyword list, which caused
MIT and Harvard University to appear in the same category as Soviet Union and
Germany. These are fundamentally different kinds of entity: organisations have
a location but are not a location. A university's intellectual connections (which
scholars worked there, which concepts were developed there) are different in
kind from a country's connections (which scholars came from there, which
geopolitical context shaped the work).

The split uses two patterns:

- `ORG_PAT` — matches institutional keywords: University, Foundation, Lab,
  Institute, Center, Press, Media Lab, etc.
- `GEO_PAT` — matches country, city, and region names explicitly

This is deliberate rather than a learned classifier: the index vocabulary is
small enough (~4,000 terms) that a curated regex is more reliable than
probabilistic classification, and the false-positive rate is auditable.

Garbled author-affiliation strings (e.g. `"Robert J. Marquis, University of
Missouri, USA"`) are suppressed by `is_noise_location()` which rejects any
term with 2+ commas or length > 60 that contains a comma.

### Why a curated list for single-name historical persons

The `Surname, Firstname` pattern catches ~95% of index persons correctly.
Single-name figures (Aristotle, Plato, Galileo) fall through because they
appear without a comma. Two alternatives were considered:

1. **NLP-based NER** (spaCy) — would catch single names but adds a 12 MB
   model dependency and ~5 minutes of processing. Overkill for a known, stable
   set of names.

2. **Curated list** (`KNOWN_SINGLE_PERSONS`) — 37 names covering ancient
   philosophers, medieval scholars, and early-modern scientists and
   philosophers. Deliberately conservative: only figures whose single-name
   form is unambiguously canonical in Western scholarship (Aristotle, not
   Confucius; Galileo, not Kepler's full name). New entries are a one-line
   addition.

The curated list wins on simplicity, zero dependencies, and full auditability.

### Graph layout algorithm choices

Four algorithms are offered rather than just the default force-directed layout,
because different analytical questions call for different visual structures:

| Algorithm | Primary question it answers |
|-----------|---------------------------|
| Force-directed | What natural clusters emerge? Which entities are globally central? |
| Radial | How dense is each entity kind? Do persons/concepts/orgs inhabit distinct structural positions? |
| Bipartite | Exactly which persons connect to which concepts? (Best used with degree filter ≥ p90) |
| Circular | Which kinds have the most cross-connections? Which hubs bridge multiple arcs? |

All four use D3.js v7 which is already loaded — no additional dependencies.
Bipartite and circular layouts use D3's fixed-position mechanism (`node.fx`,
`node.fy`) with minimal simulation forces for smooth animation rather than
rewriting the rendering loop. Switching layouts calls `clearFixed()` to
release pinned coordinates before applying the new layout.

The bipartite layout auto-limits to 100 nodes per side because the full
1,500-node graph is unreadable in a two-column arrangement. This is a display
limit, not a data limit — all edges from filtered-in nodes are shown.

---

## Entity Classification — Noise Taxonomy (`15_entity_classify.py`)

### Why "suppress" rather than a 5th node kind for book titles

Book/work titles like *Cybernetics (Wiener)* or *Steps to an Ecology of Mind*
appear in indexes as citation references, not as intellectual entities in their
own right. Showing them as nodes would create misleading edges: Wiener would
appear strongly associated with *Cybernetics (Wiener)* — which is trivially
true (it's his book) and tells us nothing about his intellectual context.

The person–concept and person–location edges are designed to reveal *what
intellectual territory a thinker occupies*, not which books cite them. A "work"
node type would add visual clutter and conceptually dilute the signal.

Books should be studied as a separate unit of analysis if needed — the
`summaries.json` and `nlp_results.json` already model books as first-class
objects with topic distributions, cluster labels, and similarity scores.

### Index sub-entry fragment noise

Book indexes use hierarchical sub-entries:

```
Control
  and cybernetics, 45
  of machines, 102
  feedback, 23
```

The index extractor (`09_extract_index.py`) pulls terms out flat. When a
sub-entry like `"and cybernetics"` or `"of machines"` is extracted without
its parent, it appears as a standalone index term. These are never genuine
intellectual concepts — they are fragments of a compound entry.

Detection: any term ≤ 6 words that starts with a preposition or conjunction
(`of`, `with`, `in`, `on`, `and`, `or`, `but`, `as`, etc.) is suppressed.
This catches ~85 fragments reliably with zero false positives on genuine
concept terms (which never start with function words in this corpus).

### Article-led titles

Entries starting with `The`, `An`, or `A` followed by a capitalised word and
spanning ≥ 4 words are almost always book titles or institutional names that
slipped past the `(Author)` pattern detector. Confidence is set to 0.85
(slightly lower than the curated lists at 1.0) to allow spaCy to override
if it has high confidence the term is a genuine named entity.

### Suppression categories (222 total after heuristics)

| Category | Count | Examples |
|----------|-------|---------|
| Noise / garbled | 186 | `PHYSIOLOGY AND MAINTENANCE`, `A B C D E...`, author affiliations |
| Work titles with `(Author)` | 34 | `Cybernetics (Wiener)`, `Perceptrons (Minsky and Papert)` |
| Article-led titles | 2 | `An Introduction to Cybernetics` |

The remaining ~3,269 terms classified as `concept` at the heuristic stage are
sent to spaCy (Stage 2) and Wikidata (Stage 3) for further disambiguation when
those tools are available. Without them, all unmatched terms default to
`concept` — this is conservative and correct for most index vocabulary, which
is predominantly intellectual concepts rather than named entities.
