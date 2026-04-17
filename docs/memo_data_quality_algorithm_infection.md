# Memo: Data Quality and Algorithm Infection
**CyberneticsNLP — 17 April 2026**  
*Status: methodology documentation — to be integrated into paper methods section*

---

## Overview

This memo documents data quality issues identified in the CyberneticsNLP corpus and their observable effects on downstream algorithmic outputs. It is framed as a methodological principle rather than a list of bugs: **without a characterised distribution of input errors, every algorithm that consumes those inputs is subject to infection** — meaning its outputs will carry systematic distortions whose direction and magnitude are unknown. Transparency about known error sources and their propagation pathways is a necessary condition for interpreting analytic results.

The issues documented here were identified through active investigation of anomalous outputs (specifically, the anomalous prominence of entities such as "Google" in the entity co-occurrence network as an associate of Norbert Wiener). The investigation produced both specific findings and a set of standing principles for interpreting results from this pipeline.

---

## 1. OCR quality as a primary error source

### 1.1 The OCR signal

The corpus of 726 books was assembled from digitised sources of varying provenance: commercial ebook formats (EPUB, PDF), open-access academic repositories, and Google Books digitisations of public-domain works. These sources have substantially different text quality profiles.

A four-signal OCR likelihood scorer was developed and applied to all books during ingestion (`02_clean_text.py`). The scorer assigns a band — **Low**, **Medium**, or **High OCR likelihood** — based on four signals:

| Signal | Weight | Indicator |
|---|---|---|
| Scanning metadata in text | +0.55 | Page-scan artifacts ("digitized by", library stamps) |
| Low alphabetic ratio | +0.25 | High proportion of non-alphabetic characters |
| OCR error patterns | +0.20 | Character substitution patterns (l→1, 0→o, rn→m) |
| Page artifacts | +0.10 | Running headers, page numbers, catchwords embedded in body text |

Applied to the 542-book Run C corpus (monographs and collected works only):

| Band | N | % | Interpretation |
|---|---|---|---|
| Low OCR likelihood | 148 | 27.3% | Born-digital or high-quality scan |
| Medium OCR likelihood | 322 | 59.4% | Likely scanned; acceptable quality |
| High OCR likelihood | 72 | 13.3% | Probable OCR noise affecting text analysis |

### 1.2 Propagation into NLP outputs

OCR noise propagates into downstream outputs through several pathways:

**TF-IDF keyphrase extraction**: OCR errors introduce non-word character sequences that survive tokenisation and inflate false keyphrase candidates. Books with high OCR scores produce noisier keyphrase lists.

**LDA topic modelling**: Individual OCR errors are unlikely to shift topic assignments substantially, since LDA marginalises over the full vocabulary. However, systematic OCR patterns — consistent character substitutions, page-header injection, running-header text — can introduce vocabulary items that cluster by source artefact rather than intellectual content, potentially inflating within-cluster coherence.

**Index term extraction**: Back-of-book indexes extracted via OCR are especially sensitive, since index structure (indentation, see-also references, page numbers) depends on spatial layout that OCR frequently mis-parses. This produces the phrase fragment issue documented in Section 3.

**Summary generation**: AI summaries generated from OCR text inherit its errors. Several book summaries show evidence of page number fragments and running-header text incorporated into the summary input.

### 1.3 Known specific case

Book 2761 (*What Is Cybernetics?*, Couffignal, 1959, Google Books digitisation) contains the verbatim text `"Digitized by Google / Original from / UNIVERSITY OF CALIFORNIA"` in the extracted clean text. This is a direct injection of digitisation metadata into the book's content. This specific case was caught; similar injections at lower visibility (e.g., a single "Google" token appearing once in a 50,000-word text) may not be systematically detected.

---

## 2. Digitisation metadata contamination

### 2.1 Scope

A targeted scan of the corpus identified 85 books containing the token "Google" in their clean text, and 76 books containing "Internet Archive". These counts include both legitimate references (modern books discussing these organisations) and potential metadata contamination (scan provenance strings embedded in body text).

The ratio cannot be decomposed with certainty without manual inspection of each case. The known contamination instance (book 2761) is a Google Books digitisation artefact. Internet Archive books may carry similar provenance strings.

### 2.2 Effect on entity co-occurrence network

Digitisation metadata contamination has a specific and measurable effect on the entity co-occurrence network. If a modern organisation name (e.g., "Google") is injected into the index of a book that does not substantively discuss that organisation, the book's index terms will include that entity, and it will appear as a co-occurring entity with all other index terms in that book.

For book 2761 (*What Is Cybernetics?*, 1959), this means Norbert Wiener — who appears extensively in the book on intellectual grounds — is recorded as co-occurring with Google on the basis of digitisation provenance, not intellectual substance.

---

## 3. PMI inflation for small-n entities

### 3.1 The scoring formula

The entity co-occurrence network (`14_entity_network.py`) scores edges using a PMI × reliability formula:

```
PMI   = log( P(A ∩ B) / (P(A) × P(B)) )
weight = PMI × sqrt( min(overlap, 20) / 20 )
```

Where *overlap* is the number of books containing both entities, and the reliability term `sqrt(min(overlap,20)/20)` is intended to dampen scores for small co-occurrence counts.

### 3.2 The inflation mechanism

For rare entities (small `n_books`), the conditional probability P(common entity | rare entity) can approach 1.0 if the rare entity appears in a tightly cohesive set of books that all happen to contain a common entity. This produces inflated PMI scores that are not artefacts of the formula but are artefacts of the *size of the sample* rather than the *strength of the association*.

**Worked example — Google and Wiener (17 April 2026 investigation):**

- Corpus size N = 690 books  
- Google appears in 9 books  
- Wiener appears in 155 books  
- All 9 Google books also contain Wiener (overlap = 9)  
- P(A) = 9/690 = 0.013, P(B) = 155/690 = 0.225  
- P(A ∩ B) = 9/690 = 0.013  
- PMI = log(0.013 / (0.013 × 0.225)) = log(4.44) = 1.49  
- Reliability = sqrt(9/20) = 0.67  
- Weight = 1.49 × 0.67 = **1.00**

This gives a weight of 1.00, making Google the *second strongest* associate of Wiener in the entire network (after Cold War, weight 1.04). The weight is high not because Google and Wiener are intellectually closely related, but because the 9 books that discuss Google are all modern interdisciplinary cybernetics/digital-culture books that also discuss Wiener.

### 3.3 Scope of the inflation problem

The inflation effect is most severe for entities appearing in 3–10 books (the minimum permitted by `MIN_BOOKS = 3`). The top PMI-inflated entities identified on 17 April 2026:

| Entity | n_books | Weighted degree | Note |
|---|---|---|---|
| Google | 9 | 178.7 | #4 hub in network |
| Amazon | ~9 | 180+ | #3 hub |
| Facebook | 11 | ~158 | #6 hub |
| National Security Agency | 5 | 127.2 | Higher than Bateson |
| Bell Laboratories | 6 | 110.3 | — |
| Santa Fe Institute | 4 | 81.0 | — |

Amazon, Google, and Facebook rank in the top 6 hubs of the entire network despite appearing in fewer than 12 books each — above intellectually central figures like Bateson, Shannon, and von Neumann who appear in 27–54 books.

### 3.4 Why the sqrt() dampener is insufficient

The reliability term `sqrt(overlap/20)` reduces linearly in effect for small overlap values, but its square-root form means it remains relatively generous: at overlap=9, reliability=0.67; at overlap=3, reliability=0.39. A linear dampener (`overlap/20`) would give 0.45 and 0.15 respectively — substantially more conservative.

The effect is compounded because the inflation mechanism operates on PMI, which itself grows logarithmically as n_books decreases. The combination produces the counterintuitive result that rare entities can score higher than common ones.

---

## 4. Index extraction artifacts: phrase fragments

### 4.1 Observed fragments

Back-of-book index extraction occasionally produces phrase fragments rather than complete terms, particularly from see-also references, multi-line index entries, and entries where OCR mis-parses the hierarchical structure. The following fragment nodes were identified in the entity network on 17 April 2026:

| Fragment | n_books | Degree | Source |
|---|---|---|---|
| `cybernetics and` | 10 | 15 | Truncated see-also entry |
| `free will and` | 3 | 47 | Truncated entry |
| `ai and` | 3 | 39 | Truncated entry |
| `consciousness and` | 7 | 10 | Truncated entry |
| `language and` | 6 | 2 | — |
| `wiener and` | 4 | 3 | — |
| `knowledge and` | 4 | 2 | — |
| `brain and` | 4 | 4 | — |

The fragment `"free will and"` (degree 47) and `"ai and"` (degree 39) are particularly consequential — they create spurious edges to nearly every entity that appears in those 3 books, polluting the network topology.

### 4.2 Mechanism

Index entries of the form:
```
Cybernetics
    and communication theory, 45–67
    and control systems, 12–19
```
are sometimes extracted as the fragment `"cybernetics and"` rather than the full subentry. This is a structural parsing failure in `09_extract_index.py` rather than an OCR error.

---

## 5. Methodological principles

The findings above support the following standing principles for interpreting results from this pipeline:

**5.1 Error distribution precedes algorithm interpretation**  
Before attributing an analytic result to intellectual structure (e.g., "Google is strongly associated with Wiener in the cybernetics corpus"), the result must be checked against known error distributions. The Google-Wiener association is substantially (possibly entirely) explained by PMI inflation and the cohort structure of modern interdisciplinary books, not by intellectual affinity.

**5.2 Small-n results require explicit flagging**  
Any entity, term, or association that derives its prominence from fewer than 10–15 books should be treated as potentially unreliable until its provenance is verified. The `is_person` flag, OCR band, and n_books count are now exposed in all report interfaces for this reason.

**5.3 Algorithm outputs are proxies, not measurements**  
PMI scores measure conditional co-occurrence probability, not intellectual association. LDA topic assignments measure vocabulary distributions, not intellectual content. OCR-derived text is a proxy for the original document. Each transformation step introduces a specific error mode; the pipeline's analytic claims are bounded by the weakest link in that chain.

**5.4 Known errors are preferable to unknown errors**  
The OCR scoring system, entity classifier, and phrase-fragment suppressor are imperfect mitigations, not solutions. Their value is that they make the error sources *visible* — to the researcher and to the reader — rather than hiding them inside a black-box output. An analysis that reports "72 books carry high OCR likelihood, which may affect keyphrase quality for those books" is more trustworthy than one that silently includes them without comment.

**5.5 Targeted fixes should be documented before deployment**  
Fixes to the PMI formula (stronger reliability dampener, higher `MIN_BOOKS` threshold), fragment suppression improvements, and entity network refinements are planned but not yet implemented as of this memo. Implementing them will change network outputs, potentially substantially. Results reported before and after these fixes are not directly comparable without noting the change.

---

## 6. Planned mitigations (pending implementation)

| Issue | Planned fix | Script | Status |
|---|---|---|---|
| PMI inflation | Change reliability from `sqrt(overlap/20)` to `overlap/20`; raise `MIN_BOOKS` from 3 to 5 | `14_entity_network.py` | Not yet implemented |
| Phrase fragments | Add filter suppressing terms ending with ` and`, ` or`, ` of` | `09b_build_index_analysis.py` | Not yet implemented |
| Digitisation metadata | Extend OCR scorer to flag provenance-string injection; add to clean-text strip | `02_clean_text.py` | Not yet implemented |
| Index structure parsing | Improve hierarchical index parsing to suppress sub-entry fragments | `09_extract_index.py` | Not yet implemented |

---

*Prepared: Paul Wong / Claude Sonnet 4.6, 17 April 2026*  
*This memo should be cited in the paper's methods section when discussing entity network and index term analysis results.*
