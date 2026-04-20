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

---

## Why use the SCOWL en_US-large dictionary (76,959 words) rather than the standard hunspell-en-us package?

The standard `hunspell-en-us` system package on Debian/Ubuntu contains approximately
50,000 words. The SCOWL `en_US-large` dictionary contains 76,959 words.

The difference matters because cybernetics as a discipline has a specialised
technical vocabulary — terms like `autopoiesis`, `homeostasis`, `affordance`,
`equifinality`, `teleonomy`, `synaptic`, `morphogenesis`, and `allostasis`
appear frequently in the corpus but are absent from the smaller dictionary.
When the standard package is used, `02_clean_text.py`'s Hunspell word filter
incorrectly rejects these valid technical terms as non-words, causing them to
be stripped from the cleaned text before topic modelling.

This is particularly damaging because these are precisely the high-discriminating
terms that distinguish cybernetics topics from each other. Over-filtering at this
stage silently degrades topic model quality without any diagnostic error.

**Reproducibility requirement:** Both AshbyX and NorbertX must use the same
dictionary file. A word present in one machine's dictionary and absent in the
other's would produce systematically different cleaned corpora, making results
irreproducible across machines. The `requirements.txt` includes a verification
command (`wc -l en_US.dic` expecting ~76,959) to confirm the correct dictionary
is installed on any new machine.

The `requirements.txt` file specifies installation paths for Linux, macOS, and
Windows, and documents a project-local `data/en_US.dic` drop-in path for locked
environments. See also: the `pyspellchecker` fallback decision above, which
handles environments where Hunspell itself is unavailable.

---

## Why regenerate `books_clean.json` from scratch rather than patching it?

During the 3 April 2026 pipeline run, `03_nlp_pipeline.py` failed to load
`books_clean.json` because the script expected a `"clean_text"` key per book
record, but the existing file used a `"text"` key. This key mismatch had been
present silently since the streaming infrastructure was rearchitected: the JSONL
streamer (`parse_and_clean_stream.py`) writes `"clean_text"`, but `books_clean.json`
had been generated in an earlier pass that wrote `"text"`.

Two repair options were considered:

**A. In-place key rename (patch):** Read each line of `books_clean.json`, rename
`"text"` → `"clean_text"`, write out a corrected file. This is technically correct
but requires loading and rewriting the full file (169 MB in streaming form,
previously 758 MB). The 758 MB legacy file would have caused OOM failures in
the sandbox; the streaming read avoids this but still requires careful handling
of the large output write.

**B. Full regeneration from `books_clean.jsonl`:** The authoritative source of
truth is `books_clean.jsonl`, which already used the correct `"clean_text"` key
and was fully re-streamed to 695 books in the same session. Regenerating
`books_clean.json` from `books_clean.jsonl` guarantees:
- Correct key (`clean_text`)
- All 695 books (vs the legacy file's 675)
- No stale entries from pre-reindex OCR failures
- Consistent encoding throughout

Regeneration was chosen. The `books_clean.json` conversion helper at the bottom
of `parse_and_clean_stream.py` was used: it reads `books_clean.jsonl`
line-by-line (avoiding full-file memory load) and writes the dict-format
`books_clean.json`. The legacy file was backed up as `books_clean.json.bak3`
before being replaced. File size dropped from 758 MB to 169 MB because the
legacy file had stored full raw text under `"text"` while the new file stores
only the cleaned text under `"clean_text"`.

**Lesson:** The JSONL file (`books_clean.jsonl`) is the authoritative streaming
source; `books_clean.json` is a derived artefact for downstream scripts that
cannot read JSONL. Any future re-streaming should be followed immediately by
regeneration of `books_clean.json` from the updated JSONL to keep both files
in sync.

---

## Why per-step pipeline flags rather than a global include/exclude boolean?

The initial exclusion design stored a single boolean per book — include in
pipeline or exclude. This is too coarse because different pipeline steps have
different assumptions, and a book that violates one step's assumptions may be
valuable input for another.

The clearest example: a **glossary** or **concept companion** (e.g. a
festschrift organised alphabetically around concept keywords) should be excluded
from LDA topic modelling (no unified authorial argument) but is *high value* for
the index extraction pipeline — its chapter titles are a hand-curated controlled
vocabulary, more reliable than back-of-book index terms extracted by heuristic.
Similarly, a **bibliography** is useless for index extraction but potentially
valuable for future citation network analysis. A **proceedings** volume is
excluded from LDA but its index terms and entity mentions are still valid for
the entity network pipeline.

The implementation therefore stores a vector of per-step flags rather than a
single boolean. Each pipeline script queries the dimensions relevant to its own
assumptions, ignoring the rest.

---

## Why a multi-dimensional signal vector rather than a publication type label?

Publication types are not mutually exclusive — a book can be simultaneously a
monograph and a textbook, or collected works and a monograph. With 5+ base
labels and non-disjoint combinations, the theoretical label space is 2⁵ = 32
combinations, of which 7 distinct combinations appear in the current 160-book
labeled set. Forcing a single type label misrepresents this structure.

More fundamentally, the publication type labels are readouts of underlying
independent dimensions:

- **`single_author`** — single authorial voice vs. assembled contributions
- **`unified_argument`** — sustained cumulative argument vs. independent pieces
- **`lookup_format`** — alphabetical/reference structure vs. narrative structure
- **`pedagogical`** — instructional framing vs. research/scholarly framing
- **`assembled_contributions`** — chapters independently authored vs. single author

Each pipeline step cares about a specific subset of these dimensions, not the
type label. LDA cares about `unified_argument` and `assembled_contributions`;
index extraction cares about `lookup_format`; the entity network is largely
agnostic to all of them. Storing dimensions directly avoids the translation step
from type label to pipeline-relevant property.

The schema is **extensible**: new dimensions can be added as the collection grows
or new pipeline steps are introduced. Existing books default to `null` for new
dimensions (not yet assessed), which is explicitly distinct from `false`
(assessed as absent). A `schema_version` field per book tracks which generation
of signals has been assessed, so assessments can be revisited when the signal
inventory evolves.

---

## Why three states (true / false / null) rather than two (true / false)?

A two-state model conflates "this signal is absent" with "this signal has not
been assessed." When a new dimension is added to the schema, all existing books
would default to `false` — wrongly claiming they have been checked and found
lacking. `null` explicitly records the epistemic state "unknown", allowing
pipeline steps to handle it appropriately (skip the book, treat as a soft
exclusion, or flag for manual review) rather than acting on a false negative.

---

## Why carry confidence and source fields on every signal?

Signals in the vector are derived from sources of very different reliability:

| Source | Example | Typical confidence |
|--------|---------|-------------------|
| Human curation | Paul's 160 labeled books | 1.0 — ground truth |
| Structured metadata | Author count from Calibre | ~0.95 — deterministic |
| Text extraction (strong) | "Edited by\n[Name]" in first 400 chars | ~0.85 |
| Text extraction (weak) | "edited by" in running body text | ~0.55 |
| Classifier inference | Predicting `assembled_contributions` | Model probability |

Storing confidence alongside each signal value allows downstream consumers to
threshold by reliability — using only high-confidence signals for classifier
training, flagging medium-confidence predictions for human review, and leaving
low-confidence signals as `null` pending further assessment.

The source field (e.g. `manual`, `calibre:google`, `calibre:amazon`,
`text_extraction`, `classifier`) records *why* a signal has the confidence it
does, and identifies which signals are appropriate as classifier training labels
(manual only) vs. predictions to be validated before promotion to ground truth.

Example schema entry:

```json
{
  "1829": {
    "schema_version": 1,
    "single_author": false,
    "single_author_confidence": 0.95,
    "single_author_source": "calibre:google",
    "has_editor": true,
    "has_editor_confidence": 0.87,
    "has_editor_source": "text_extraction",
    "unified_argument": null,
    "unified_argument_confidence": null,
    "unified_argument_source": null
  }
}
```

---

## Why use Calibre identifier types to assess metadata source reliability?

Calibre's metadata download facility queries external APIs (Google Books,
Amazon, Goodreads, and user-configured sources) and stores each source's
identifier for the book in the `identifiers` table (`type` = `google`,
`amazon`, `goodreads`, etc.). The presence of an identifier type shows which
source was consulted during metadata retrieval.

Different sources have different reliability profiles for academic books:
Google Books is generally more reliable for academic monographs and edited
volumes; Amazon is more reliable for popular titles but less precise about
editorial roles; Goodreads community metadata is variable in quality.

This means the `source` field in the signal vector can encode which Calibre
metadata source contributed a given signal (e.g. `calibre:google+amazon` for
a book where both identifiers are present), informing the confidence assigned
to metadata-derived dimensions.

**Limitation:** Calibre stores the *merged* metadata result without recording
which source provided which individual field. The identifier types show which
sources were queried, not which source "won" for each field. Per-field
provenance would require re-querying the APIs directly.

---

## Why `has_editor` as an explicit signal dimension?

The presence of editor attribution at the front of a book is one of the
strongest observable signals for `assembled_contributions` — an edited volume
is by definition assembled rather than authored by a single voice. However,
Calibre's metadata schema stores no author role distinction: the
`books_authors_link` table has no role field, and none of the author name
entries in the corpus carry `(ed.)` annotations.

The signal must therefore be extracted from book text. Scanning the first
~400 characters of clean text for standalone "Edited by [Name]" patterns
(distinct from "edited by" in running body prose or "Series editor" credits)
recovers the signal for most books where the title page OCR is clean, with
confidence ~0.85 when the pattern occurs on its own line in the title page
region. Books where the title page is garbled or the editor credit appears
later in the front matter will miss the signal (returning `null`) rather than
falsely reporting `false`.

---

## Why multi-label (binary relevance) classification rather than multi-class?

Publication type labels are non-disjoint — a book can simultaneously be a
monograph and a textbook, collected works and a monograph, etc. A multi-class
classifier that assigns exactly one label per book cannot represent this.

Binary relevance trains one independent binary classifier per dimension
(is_monograph, is_textbook, is_anthology, etc.), each outputting a probability
score. A book receives a label set by thresholding each classifier independently.
This correctly models the non-disjoint structure and allows each classifier to
be trained, evaluated, and improved independently.

**Confidence tiers for predictions:**
- > 0.90 — auto-accept; add to training set for next iteration
- 0.65–0.90 — flag for human review
- < 0.65 — leave as `null`; not confident enough to assert

**Active learning:** rather than reviewing unlabeled books randomly, prioritise
those where classifier confidence is nearest 0.5 (maximum uncertainty). These
cases yield the most information per review and improve the model fastest.

**Small-class caveat:** minority classes (textbook: 10 examples, collected
works: 6, proceedings: 6, journal special issue: 1) produce poorly calibrated
probability scores. Treat their outputs as rankings rather than true
probabilities until training sets grow to ≥ 30 examples per class.

---

## Why "journal special issue" as a distinct label from "anthology" or "proceedings"?

A journal special issue sits between proceedings and anthology in the pipeline
space. Like proceedings it is assembled and multi-author; like anthology it
typically features longer, more developed contributions than conference papers.
It is distinguished by structural signals that neither anthology nor proceedings
share: ISSN/journal identifiers in Calibre metadata, volume/issue numbering,
uniform article formatting with individual abstracts, and guest editor
attribution rather than book editor attribution.

The distinction matters for downstream analysis beyond the pipeline exclusion
decision — journal special issues represent a specific mode of knowledge
circulation in cybernetics (the journal *Kybernetes*, for example, ran many
themed issues that function as de facto edited volumes) and may warrant separate
treatment in bibliometric analysis.

For current pipeline purposes: exclude from LDA (assembled, multi-author);
treat equivalently to proceedings. Revisit if journal-level analysis is added.

---

## Why split "reference" into glossary/dictionary vs. bibliography subtypes?

The label "reference" covers structurally distinct book types with opposite
pipeline utility profiles:

**Glossary / dictionary / concept companion** — alphabetically organised entries
defining or meditating on concepts. *High value* for the index extraction
pipeline: the entry headings are a hand-curated controlled vocabulary, more
reliable than heuristically extracted back-of-book index terms. Exclude from
LDA; include in index/entity pipelines with elevated weight.

**Bibliography** — a structured list of citations to other works. *Low value*
for index extraction (no concept terms, only author/title strings); potentially
valuable for future citation network analysis. Exclude from LDA and index
pipelines.

The single-label "reference" cannot distinguish these. Books should be
sub-typed as `reference:glossary` or `reference:bibliography` in
`book_styles.json` so each pipeline step can query the relevant sub-type.

Three corpus examples illustrate the distinction:

| ID | Title | Labels | Subtype | Index pipeline |
|----|-------|--------|---------|----------------|
| 1914 | *Bateson's Alphabet* | monograph, reference | concept companion | High value — chapter titles are curated Bateson vocabulary |
| 1918 | *A More Developed Sign* | anthology, reference | concept companion | High value — ~70 concept keywords as chapter titles |
| 1988 | *GSR Bibliography 1977–84* (Trappl et al.) | reference | bibliography | Low value for index; potential citation analysis value |

**Note on IDs 1914 and 1918:** Both are alphabetically organised around
concept keywords — *Bateson's Alphabet* as a single-author monograph, *A More
Developed Sign* as a multi-author festschrift for Jesper Hoffmeyer. Both carry
"reference" as a secondary label alongside their primary structural type.
Their chapter titles constitute hand-curated controlled vocabularies directly
relevant to the cybernetics corpus and should be treated as high-priority input
for index extraction, weighted similarly to glossary entries.

---

## Why normalise label strings before parsing (sort alphabetically)?

Multi-label entries are stored as comma-separated strings in Calibre's
`custom_column_5` field. Entry order is not guaranteed — "monograph, textbook"
and "textbook, monograph" are semantically identical but would be treated as
different keys by naive string comparison.

Normalisation rule: split on comma, strip whitespace from each part, sort
alphabetically, rejoin. Applied consistently at read time, this ensures label
set identity is order-independent. The current 160-book labeled set happens to
be consistently ordered (alphabetical), but the normalisation is required for
robustness as the labeled set grows.

---

## Why k=9 as the canonical LDA topic count?

**Date:** 3 April 2026 | **Session:** Chat

Topic count selection uses three criteria applied in dependency order:

**1. Coherence sweep** identifies the feasible region. Run over k=2–12 on the
695-book post-overhaul corpus (seeds 42, 7, 123, 256, 999). Provides a rough
indication of meaningful structure but is insufficient alone — coherence can
increase with k due to topic fragmentation without interpretive gain.

**2. Dead-topic count** bounds the ceiling of k. A dead topic has a near-uniform
word distribution — arising structurally when k exceeds the corpus's data
capacity, not from initialisation. Zero dead topics at k=9 confirms the data
capacity is not exceeded. This criterion has higher epistemic standing than
stability scores because it is less seed-dependent.

**3. Stability scores** characterise solution consistency within the fixed seed
set. Computed as mean Jaccard overlap of top-N word sets across all seed pairs,
aligned by Hungarian algorithm.

Post-overhaul results at relevant k values:

| k | Coherence | Dead topics | Stable (≥0.3) | Mean stability |
|---|---|---|---|---|
| 9 | 0.0668 | 0 | 7/9 (78%) | 0.382 |
| 10 | 0.0721 | 0 | 6/10 (60%) | 0.383 |

k=9 selected because: zero dead topics; 78% stable topics vs k=10's 60%; two
unstable topics (T3, T9) are interpretable, not noise. k=10 redistributed
instability across more topics without resolving the T9 residual.

**Epistemic caveat:** stability scores are seed-set-relative. "T1 is stable
across seeds 42, 7, 123, 256, 999 at k=9" is the valid claim. A different
seed set might rank topics differently.

**Canonical solution restoration:** `topic_stability.json` always reflects the
most recently run k. After any comparison run, restore with:
```
python3 src/03_nlp_pipeline.py --min-chars 10000 --lemmatize --topics 9 --seeds 5
python3 src/09c_validate_topics.py --top 10 --md
python3 patch_topic_names.py
```
`run_all.sh` now calls `03_nlp_pipeline.py --topics 9 --seeds 5` explicitly.

---

## Why the alpha-ratio front-matter fix?

**Date:** 3 April 2026 | **Session:** Chat

**Problem:** Six books with good body text (alpha 0.71–0.78 over full text)
were excluded by the alpha-ratio filter because their first 5,000 characters
contained front matter: publisher metadata, series information, copyright
notices, and in one case ([205] *The Phenomenon of Science*) Cyrillic OCR
fragments from the Russian original. The original `_alpha_ratio()` sampled
the first 5,000 characters unconditionally.

**Root cause:** Front matter is structurally present at the start of every
book and is not representative of intellectual content. The filter was designed
to catch books with genuinely garbled OCR throughout (e.g. [1262] at alpha=0.04
before reindex); sampling from the start conflated this with front-matter
contamination.

**Fix:** Skip the first 10% of text (or at least the first sample window) and
average 3 evenly-spaced windows from the body. Threshold unchanged at 0.40 —
the fix raises the sampling start point, not the threshold. Books with
genuinely garbled OCR throughout still fail.

**Books recovered:** [205], [265], [413], [597], [1261], [1918] — all body
text alpha 0.71–0.78 under the corrected function.

---

## Why exclude proceedings/handbooks/readers from LDA?

**Date:** 3 April 2026 | **Session:** Chat

The pipeline embodies an implicit monograph assumption: all books treated as
single-author, thematically coherent, with end-of-book references and a unified
back-of-book index. This assumption was never stated explicitly. It is
approximately correct for monographs (65.4% of the classified corpus) and
systematically wrong for other types in predictable and consequential ways.

**Conference proceedings — excluded:**
- Thematic coherence fails: proceedings deliberately aggregate diverse
  contributions; low LDA coherence is an epistemic practice, not a model failure
- Reference location fails: references at end of each paper, not volume end;
  end-of-book extraction captures only the last paper's citations
- Index fails: no unified index
- Document unit fails: proceedings is a container for N independent papers;
  treating it as one LDA document is a category error

**Handbooks — excluded:**
- Positional sampling (early/mid/end) catches entirely unrelated chapters by
  different authors on different subtopics
- References often at chapter ends; index aggregates community vocabulary rather
  than one author's concept architecture

**Readers — excluded:**
- No original authorial voice; curation of existing texts without original
  intellectual contribution; no unified concept map

**Anthologies — retained with caveats:**
Structurally closer to monographs; editorial framing may be coherent. Retained
but expected low coherence tolerated and documented. T2 (Luhmann) has 11
anthology books — largest concentration; noted in paper.

**Corpus impact (after 4 manual reclassifications):**
- 22 definite exclusions (3.0%): 12 handbooks, 6 proceedings, 3 readers,
  1 confirmed proceedings [351]
- 704 books retained (97.0%)
- Excluded books are disproportionately `curated_pure` stratum (68% vs 45.5%
  of corpus) — exclusion policy and precision-recall stratification identify
  overlapping populations of methodologically marginal inclusions

**Implementation status:** `book_styles.json` records classifications and
reclassifications (verified=True). Exclusion filter in `03_nlp_pipeline.py`
not yet implemented — pending signal inventory audit and document unit decision.

---

## Why signal inventory rather than categorical ground truth?

**Date:** 3 April 2026 | **Session:** Chat

The plan to validate the classifier against ~150 labeled books was challenged
by two observations:

1. **Book types are not disjoint.** Ashby's *Introduction to Cybernetics* is
   simultaneously a research monograph and a textbook. Single-label ground truth
   presupposes a categorical structure that does not exist in the phenomenon.
   The relevant question changes: not "what type is this book?" but "which
   pipeline assumptions does this book violate?"

2. **Observable structural signals are more tractable and directly relevant.**
   Binary signals (index present/absent, reference location, author count,
   publication era) are verifiable, auditable, and directly drive pipeline
   behaviour decisions without categorical commitment.

**Signal inventory dimensions (initial set):**

| Signal | Type | Observable from | Pipeline implication |
|---|---|---|---|
| `index_present` | binary | index_terms.json status | Include/exclude from index-term analysis |
| `reference_location` | 3-way: end/chapter/none | Text inspection | Reference extraction strategy |
| `author_count` | count | Calibre authors | Vocabulary dilution flag |
| `has_editor` | binary | Calibre/text first 400 chars | Anthology inference |
| `publication_era` | 3-way: pre/early/born-digital | pubdate | Index quality covariate |

**Schema:** Each signal has three fields in `book_styles.json`: value,
confidence (0–1), and source (manual > calibre:google > text_extraction >
classifier). Three-state model: true/false/null. Null propagates gracefully
— unknown signals use default assumption and are flagged in output.

**Relation to Calibre labels:** 159 books already labeled in Calibre
(`custom_column_5`) with multi-label combinations — consistent with binary
relevance approach and confirming the non-disjoint structure in practice.
Signal inventory complements rather than replaces categorical labels: labels
serve interpretive purposes; signals drive pipeline behaviour.

**Implementation status:** Planned. Schema agreed. Moratorium on NLP pipeline
code applies. Implementation is next sprint after document unit decision is
formally recorded.

---

## Why multi-seed stability testing?

**Date:** 3 April 2026 | **Session:** Chat

LDA's EM algorithm finds local optima in a non-convex objective. Different
random initialisations can converge to genuinely different solutions that are
equally valid mathematically. A single-seed run cannot distinguish a stable
topic structure from a seed-dependent artefact.

**5 fixed seeds** (42, 7, 123, 256, 999) are used for all production LDA runs:
- Fixed seeds ensure reproducibility — the same seeds on the same corpus always
  produce the same stability scores
- 5 seeds provides sufficient coverage to distinguish clearly stable (Jaccard
  ≥ 0.5) from clearly unstable (< 0.15) topics for this corpus size
- Runtime: ~2–3 minutes at k=9; 20 seeds would cost ~8–12 minutes for
  marginal coverage gain

**Stability scores are seed-set-relative.** "T1 is stable across seeds
42, 7, 123, 256, 999" is valid; "T1 is a stable topic for this corpus"
overclaims. A different seed set might produce different rankings.

**Dead-topic count has higher epistemic standing** than stability scores as
a stopping criterion precisely because it is less seed-dependent — degenerate
distributions arise structurally from over-specification regardless of
initialisation. The two criteria play complementary roles: stability
characterises solution quality; dead-topic count bounds k's ceiling.

---

## Why avoid "ground truth" terminology for publication type labels
**Date:** 7 April 2026 | **Session:** Chat

### Decision
Do not use "ground truth" to describe the hand-labelled publication type
data in Calibre (`custom_column_5`). Use "expert labels" or "expert
judgements" instead.

### Rationale
"Ground truth" implies a single correct answer that exists independently
of the observer. Publication type labels do not have this property.
A reasonable expert might classify Ashby's *Introduction to Cybernetics*
as monograph, another as textbook, another as both. The disagreement is
not error — it is genuine ambiguity in the phenomenon, consistent with
the affordance-as-mixture framework (§13 of the epistemic affordances
memo): if types are not disjoint and affordance is continuous, there is
no ground truth to recover, only expert judgements to approximate.

### Terminology substitutions

| Avoid | Use instead |
|---|---|
| Ground truth | Expert labels / expert judgements |
| Accuracy | Agreement with expert judgement |
| Correct/incorrect classification | Agrees/disagrees with expert label |
| Ground truth validation | Reference label validation |
| True label | Expert label / reference label |

When comparing two labellers, use **inter-rater reliability** rather than
accuracy. When describing classifier output, use **label confidence**
rather than correctness.

### Implication for the paper
The publication type classifier should be described as learning to
replicate expert judgement on a specific corpus, not as detecting
objective publication types. This is a weaker and more honest claim,
and is consistent with the theoretical framework.

### Implication for AI-human teaming
This is an instance of a general lesson from this collaboration: AI
systems and pipelines can generate labels, scores, and classifications
fluently and at scale, which creates pressure to treat those outputs as
authoritative. Maintaining terminological discipline — distinguishing
expert judgement from machine inference, reference labels from ground
truth — is a methodological responsibility of the human researcher, not
something the AI will enforce unprompted.

---

## Why use binary relevance with monograph/not-monograph as the first classifier
**Date:** 7 April 2026 | **Session:** Chat

### Decision
The first publication type classifier is a binary classifier:
monograph (positive) vs. not-monograph (negative). Multi-label
classification of the full type space is deferred until more expert
labels are available.

### Rationale
The 153 hand-labelled books have severe class imbalance across the
full label space:
- monograph: 122 (79.7%) — viable
- anthology: 18 (11.8%) — sparse
- textbook: 10 (6.5%) — sparse
- collected works: 6 (3.9%) — too few
- reference: 3 (2.0%) — too few
- journal special issue: 1 (0.7%) — too few

Only the monograph dimension has sufficient positive examples (~20
minimum recommended) for a reliable binary classifier. Attempting
multi-label classification with sparse classes would produce
unreliable probability estimates.

### Positive class definition
Any book with `monograph` in its expert label set, including
combinations: monograph, monograph+textbook, monograph+reference,
collected works+monograph. This reflects the non-disjoint type
structure — a book that is simultaneously monograph and textbook
is still a monograph for pipeline purposes.

### Class imbalance handling
`class_weight='balanced'` in sklearn to compensate for the 4:1
positive/negative ratio.

### Validation approach
1. Train on all 153 expert-labelled books
2. Predict on remaining ~573 unlabelled books
3. Random sample from each predicted class (not cherry-picked)
4. Paul manually reviews samples — these become new expert labels
5. Retrain with expanded label set; repeat until agreement rate stabilises

This is active learning in its simplest and most honest form. Each
iteration uses genuinely new expert labels, not machine output.
The agreement rate (not "accuracy") estimates how well the classifier
replicates expert judgement on unseen books.

### Stopping criterion
When agreement rate from successive random samples stops improving
meaningfully, the classifier has reached its ceiling with available
signal. Additional labelling at that point returns diminishing value
and remaining disagreements likely require better features.

---

## Why machine-inferred labels must never be used as classifier training data
**Date:** 8 April 2026 | **Session:** Chat

### Decision
Labels inferred by `00_classify_book_styles.py` (stored in
`book_styles.json`) must never be used as training data for the
supervised publication type classifier. The only legitimate training
sources are:

1. Paul's expert labels in Calibre `custom_column_5`
2. The 4 manual reclassifications with `verified=True` in
   `book_styles.json` — these represent Paul's expert judgement,
   not machine inference

### Rationale
Using machine-inferred labels as training data would be circular:
the supervised classifier would be learning to replicate the
heuristic classifier, not to replicate expert judgement. Agreement
metrics from such a training run would measure consistency with
the heuristic model, not validity against human knowledge.

The supervised and heuristic classifiers serve different roles and
must be evaluated independently:
- Heuristic classifier (`00_classify_book_styles.py`): corpus
  filtering using metadata signals; evaluated by Paul's qualitative
  review
- Supervised classifier (`train_monograph_classifier.py`): learning
  to replicate expert labels on unlabelled books; evaluated by
  agreement rate on random samples reviewed by Paul

Mixing these would corrupt both evaluations.

### Scope
This rule applies at training time only. It is valid to:
- Compare heuristic classifier outputs to expert labels as a
  calibration check
- Use heuristic features (from `heuristic_features.py`) as input
  features to the supervised classifier — these are text signals,
  not labels
- Use heuristic classifier outputs as a baseline for comparison

### Enforcement
No automated enforcement is implemented. The rule must be upheld
by the researcher. Claude's persistent memory records this constraint
to prevent accidental violation in future sessions.

---

## Why language filtering is applied at parse time, not post-hoc
**Date:** 10 April 2026 | **Session:** Cowork

### Decision
Books whose `lang_code` in Calibre is explicitly set to a non-English
ISO 639-2 code (anything other than `eng`) are excluded before they
are written to `books_parsed.json` or `books_clean.jsonl`. Books
with no `lang_code` set pass through (metadata gap ≠ exclusion).

The filter is implemented in three pipeline files:
- `00_export_calibre.py` — adds `lang_code` as a column in
  `books_metadata_full.csv` (queried from Calibre's `languages` /
  `books_languages_link` tables)
- `01_parse_books.py` — skips non-English books at metadata load time
  (standard pipeline path)
- `parse_and_clean_stream.py` — same filter in the streaming path

### Rationale
The earlier `books_lang.csv` file provided an explicit language field.
When `books_metadata_full.csv` replaced it in v0.4.2, that field was
lost. The corpus contains a small number of non-English titles (17 as
of April 2026: 9 German, 5 French, 1 Italian, 1 Polish, 1 Spanish).
Letting them through would introduce non-English vocabulary into LDA
topic models and affect stopword filtering.

Filtering at parse time is preferred over post-hoc removal because:
1. It is cleaner — downstream scripts never need to know a book was
   excluded
2. It is deterministic — no accidental reintroduction if JSON files
   are regenerated
3. It produces an explicit exclusion log at run time, making the
   filter auditable

### Immediate effect
As of April 2026, none of the 17 non-English Calibre books are present
in any `books_text_*.csv` file, so the filter has no immediate effect
on the corpus. It is a preventive measure for future library additions.

### Note on German vocabulary in T5
The German tokens observed in LDA topic T5 (`oder`, `sind`) originate
from English-language books that cite or quote non-Anglophone
cybernetics literature — not from German-language books. Those tokens
survive stopword filtering because they are valid English words in other
contexts (`oder` → not in NLTK stopwords; `sind` → uncommon). The
language filter does not address this; the appropriate fix (if needed)
is to add `oder` and `sind` to the custom stopword list in
`02_clean_text.py`.

---

## Publication type filter: include monograph and collected works only
**Date:** 10 April 2026 | **Session:** Cowork

### Decision
Books are included in the LDA corpus if and only if their manually assigned
`pub_type` (Calibre custom column 5, exported as `pub_type` in
`books_metadata_full.csv`) contains `monograph` or `collected works`.
Books with no `pub_type` label pass through (safe default).

Excluded types: anthology, textbook, proceedings, journal special issue,
reference, catalog — and any compound labels that do not contain the two
anchor types (e.g. `anthology, reference`).

### Rationale
Non-monograph types introduce structural noise into topic modelling:
- **Anthologies** have mixed vocabulary from multiple independent contributors;
  the LDA signal is a union of unrelated author vocabularies, not a coherent
  intellectual position.
- **Textbooks** carry a retrospective, consensus-smoothed vocabulary that lags
  the actual conceptual development of the field by a decade or more.
- **Proceedings, journal special issues** are heterogeneous by construction.
- **Reference works, catalogs** are enumerative, not argumentative.

### Why publication types are non-disjoint
The labelling scheme uses compound labels (e.g. `monograph, textbook`,
`collected works, monograph`) because a book can genuinely instantiate
multiple types simultaneously. Ashby's *Introduction to Cybernetics* is
both a monograph (sustained first-person argument) and a textbook
(explicitly pedagogical, widely used in courses). A collected works volume
may have a unifying editorial argument that makes it function as a monograph.
Treating types as mutually exclusive would force a false categorical choice
on genuinely ambiguous cases.

The filter therefore reads compound labels inclusively: presence of
`monograph` or `collected works` anywhere in the label is sufficient for
inclusion, regardless of co-occurring labels.

### Implementation
- `00_export_calibre.py`: exports `pub_type` from Calibre custom column 5
  into column 22 of `books_metadata_full.csv`
- `03_nlp_pipeline.py`: applies the filter immediately after loading
  `books_clean.json`, before min-chars and alpha-ratio filters

### Source of labels
Manually assigned in Calibre by the corpus curator. All 714 books in the
Calibre library on Cybersonic have a label assigned. Labels are authoritative
— they replace the heuristic `book_styles.json` classifier for pipeline
filtering purposes (the classifier remains useful for analysis and covariates).

---

## Cross-run LDA stability tracking (future work)
**Date:** 10 April 2026 | **Session:** Cowork | **Status:** Deferred

### Problem
The current pipeline measures topic stability *within* a single run across
multiple seeds (Jaccard similarity, reported in `topic_stability.json`).
There is no mechanism to compare topic solutions *across* successive runs —
e.g., to check whether T3 in run N corresponds to T3 (or some other topic)
in run N−1, and whether the word distribution has drifted.

This matters because: (a) topic names should not be assigned until stability
across runs is established; (b) corpus changes (new books, exclusions,
re-OCR) may shift topic boundaries in ways not visible from within-run
metrics alone.

### Proposed design
1. After each LDA run, append a snapshot of top-word distributions to
   `json/run_history.jsonl` (one JSON line per run, keyed by ISO timestamp
   + corpus size + k).
2. In `09c_validate_topics.py`, load the last N snapshots and align topics
   across runs using Jaccard similarity + Hungarian algorithm (same maths
   as within-run seed stability).
3. Report a per-topic cross-run stability score alongside the existing
   within-run score.

### Why deferred
Topic naming is blocked on this analysis. The analysis requires at least
3–5 successive clean runs on a stable corpus. The corpus is still being
stabilised (publication-type filter, OCR redos). Implementation should
proceed once the corpus is settled.

### Scope
Touches `03_nlp_pipeline.py` (snapshot write) and `09c_validate_topics.py`
(cross-run comparison). Estimated effort: ~1 session.

---

## Why a manual exclusion list supplements Calibre lang_code
**Date:** 10 April 2026 | **Session:** Cowork

### Decision
A repo-tracked file `csv/lang_exclusions.csv` lists the 17 known
non-English books. It is checked by `01_parse_books.py` and
`parse_and_clean_stream.py` before — and independently of — the
Calibre `lang_code` field. A book in the exclusion list is always
excluded, regardless of what `books_metadata_full.csv` says.

### Rationale
The Calibre library (`metadata.db`) is shared across NorbertX and
AshbyX via OneDrive. Sync divergence has caused the language tags
for the 17 non-English books to appear as `eng` in the exported CSV
on at least one occasion, making the Calibre-based filter silently
ineffective. The exclusion list is version-controlled in the repo and
does not depend on any particular machine's Calibre state.

### Maintenance
When a new non-English book is added to the corpus, add it to
`csv/lang_exclusions.csv` with its Calibre id and ISO 639-2 lang_code.
Setting the lang_code in Calibre correctly is still encouraged — the
Calibre-based filter remains active as a second layer for any books
not yet in the exclusion list.

### Source of the 17 book IDs
Identified from a pipeline run on 10 April 2026 where Calibre language
tags were intact. IDs: 2044, 2063, 2064, 2065, 2066, 2092, 2344, 2460,
2469, 2470, 2471, 2472, 2473, 2474, 2475, 2476, 2477.

---

## Git operations: always run on Cybersonic directly
**Date:** 11 April 2026 | **Session:** Cowork

### Decision
All git operations (commit, merge, push, pull, rebase) must be run
directly on Cybersonic via SSH. Do not run git through the SSHFS
network mount on NorbertX or AshbyX.

### Rationale
macOS writes AppleDouble resource fork files (`._*`) into `.git/objects/`
on SSHFS-mounted directories, corrupting git's object store. The network
mount also causes stale stat information in the git index, making git
falsely report clean files as modified and blocking merges, stashes, and
HEAD detachment. Both failure modes are silent and hard to diagnose.
These problems do not occur on Cybersonic's native filesystem.

### Rule
- Edit files via the SSHFS mount on NorbertX/AshbyX as normal
- SSH into Cybersonic for all git operations
- If `._*` contamination is suspected: `find .git -name "._*" -delete && find .git -name "tmp_obj_*"` to check for stranded temp objects

---

## Why corpus-scale NLP is framed as a qualitatively distinct epistemic mode
**Date:** 15 April 2026 | **Session:** Cowork

### Decision
The paper frames corpus-scale NLP analysis as affording qualitatively different epistemic
access than individual reading — not merely faster or more comprehensive reading, but a
different kind of knowing that reveals patterns invisible at the level of any individual
text. This is the paper's primary theoretical contribution alongside the media-aware
feature selection argument.

### Rationale
Reading one book and reading 695 books over 70 years computationally are not the same
epistemic act performed at different scales. They answer different questions and make
different things visible.

Individual reading produces: argument comprehension, sensitivity to rhetorical register,
awareness of specific intertextual relationships, the tacit context required to interpret
explicit claims. Corpus-scale NLP produces: topic structure across the collection, temporal
evolution of thematic emphasis, concept velocity and migration, network centrality of
persons and concepts. Neither mode is a substitute for the other. They are qualitatively
distinct.

The framing decision is to be explicit about both what the pipeline reveals and what it
cannot see — rather than implying it is a faster substitute for close reading, which would
misrepresent both its capabilities and its limitations.

### Relation to the epistemic affordances memo
This extends the epistemic affordances argument from the level of individual media types
(§1–2 of `memo_media_aware_nlp_epistemic_affordances.md`) to the level of the analytical
method itself. The full development — including the connection to Ashby's Law of Requisite
Variety and the compression trade-offs — is in §15 of that memo.

### Implication for the paper
The contribution statement should be explicit: the paper does not claim to have read the
cybernetics corpus — it claims to have analysed it at scale in a way that reveals structure
unavailable to individual reading. The methodology section should acknowledge both what the
pipeline preserves (vocabulary patterns, concept distribution, temporal trends, network
structure) and what it loses (argument structure, rhetorical register, intertextual
specificity).

---

## KI-09: singular/plural concept node deduplication — design decisions
**Date:** 20 April 2026 | **Session:** Cowork (fifth batch)

### Problem
Index vocabularies routinely contain both singular and plural forms of the same concept
(`algorithm`/`algorithms`, `network`/`networks`, `feedback loop`/`feedback loops`).
Treating them as separate nodes splits their PMI signal — books indexed under the plural
form do not contribute to the singular node's book-set — artificially weakening edge
weights for both. Approximately 150 such pairs were present in the pre-fix network.

### Decision: merge at concept classification time, not post-hoc
Plural forms are removed from the `concepts` dict immediately after classification and
before book-set construction. Their book-sets are unioned into the canonical singular's
set. This is preferable to post-hoc graph merging because: (a) it keeps the data model
clean — the network always has one node per concept, not two with a merge annotation;
(b) book-set union is correct only before book-set construction, not after.

### Decision: conservative "both must exist" guard
A plural–singular merge fires only when BOTH forms are independently present as concept
nodes after all upstream filters (NOISE_TERMS, KNOWN_TECH_PLATFORMS, `_TRAILING_FUNC`,
cache suppression, etc.). No merge is inferred — every pair is confirmed by presence in
the data. This prevents false merges where only one form appears.

### Decision: `_CONCEPT_PLURAL_EXCEPTIONS` for -ics field names
35 discipline/field names ending in `-ics` are exempt from `_singular_form()` derivation:
`cybernetics`, `thermodynamics`, `semantics`, `dynamics`, `linguistics`, etc. These are
not grammatical plurals of their adjectival `-ic` forms — they are mass nouns denoting
fields of study. Treating `cybernetics → cybernetic` as a valid merge would be a category
error. The exceptions list is explicit and documented in source.

### Decision: paragraph-window normalisation
The `target_tls` list for paragraph co-occurrence is normalised through `concept_plural_map`
so that a paragraph containing the plural form is counted as a co-occurrence of the
canonical singular. `dict.fromkeys` deduplication prevents double-counting when a book
indexes both forms.

---

## Why fix `_canonical_term()` in `09_extract_index.py` rather than patching downstream
**Date:** 20 April 2026 | **Session:** Cowork (fifth batch)

### Problem
Multi-word proper names containing English function words (`in`, `and`, `of`, `the`,
`from`, etc.) were being systematically lowercased by `_canonical_term()`. For example:
`Experiments in Art and Technology` → `experiments in art and technology`,
`Laws of Form` → `laws of form`, `Macy Conferences on Cybernetics` → `macy conferences
on cybernetics`. The root cause was that `_ok()` did not recognise function words as
legitimately lowercase in title-case proper nouns.

### Alternative considered: blocklist in `14_entity_network.py`
Individual term-level corrections could have been added to `MANUAL_CORRECTIONS` or a
dedicated `CASING_CORRECTIONS` dict in the entity network script. This would fix the
visible symptom (incorrect casing in the network) for known terms.

### Decision: fix upstream in `09_extract_index.py`
The corpus is designed to grow. A downstream patch applies only to terms already known to
be incorrectly cased — any new book added to the collection that indexes a multi-word
proper name containing a function word would encounter the same casing error, propagate
it through `index_vocab.json`, and reach the entity network uncorrected. The fix in
`_canonical_term()` applies to all present and future index terms without any per-term
maintenance. This is the canonical application of the "fix upstream, not downstream"
engineering principle recorded in CLAUDE.md.

### Fix design
Three changes to `_canonical_term()`:
1. `LOWER_IN_TITLE` set — articles, coordinating conjunctions, and common prepositions
   are now recognised as legitimately lowercase in well-formed title-case proper nouns.
2. All-caps pre-processing — multi-word ALL-CAPS strings (OCR artefacts) are lowercased
   before the canonical check if any word exceeds 3 characters, exempting genuine
   acronym sequences (e.g. `DNA RNA`).
3. "Best casing wins" in vocab builder — if a term is stored in all-lowercase form and a
   later book supplies a mixed-case form, the stored entry is upgraded. Handles cases
   where the first book to index a term rendered it in all-caps or all-lowercase.

---

## Why "University of California" is accepted as a known network artefact
**Date:** 20 April 2026 | **Session:** Cowork (fifth batch)

### Observation
"University of California" appears in the entity network as an isolated organisation node
connected only to Tylor, E. B. (Victorian anthropologist). Both nodes are stranded — no
co-occurrence with any concept, person, or location that survived the network's filters.
Present in the index of *Philosophical Posthumanism* (2019), *Living Systems* (1978), and
*Gregory Bateson: The Legacy of a Scientist* (1982); and separately in *Cyburbia* (2009).

### Alternative considered: upstream filter
Adding "University of California" to a publisher/affiliation blocklist in
`09_extract_index.py` would remove it from index extraction entirely.

### Decision: accept as known artefact, do not filter
"University of California" is a legitimately ambiguous string. In different books it may
appear as: (a) a publisher credit (University of California Press); (b) an institutional
affiliation (Bateson held positions at UC); (c) a genuine subject reference (a book may
discuss UC's role in cybernetics research). A surface-form filter cannot distinguish these
senses because the distinguishing information — sentence context — is absent at the point
of index extraction. Filtering would suppress legitimate institutional references in
future books. The isolated node is a cosmetic artefact and does not affect any analysis.

This decision is an application of the **Principle of Context (incomplete information)**
recorded in CLAUDE.md: when linguistic items are stripped of context, the ability to
determine meaning is degraded for both humans and algorithms. When a filter would
correctly block one sense but incorrectly suppress another, accept the noise and record
the ambiguity as a known artefact rather than introduce a systematic false-negative.

### Status
Recorded in ROADMAP as a known artefact. No action required unless the node count of
isolated pairs grows substantially as the collection expands.
