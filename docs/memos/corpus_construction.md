# Draft Methods Section: Corpus Construction and Inclusion Criteria

*CyberneticsNLP — draft for paper, 2 April 2026*  
*Status: draft — for review and integration into full paper*

---

## 3.1 Corpus overview

The corpus comprises 726 books spanning the cybernetics intellectual tradition from 1954 to 2025. Books were assembled in Calibre library management software and exported for NLP analysis. The corpus includes monographs, edited volumes, textbooks, handbooks, popular works, and historical studies — a deliberate inclusion of multiple book styles reflecting the breadth of the cybernetics tradition across academic, applied, and popular registers.

---

## 3.2 Corpus construction: a precision-recall trade-off

Corpus construction for a thematic intellectual history collection involves a fundamental precision-recall trade-off inherent to keyword-based information retrieval. We operationalise this trade-off explicitly as a methodological choice rather than treating it as a limitation to be minimised.

**The precision pole** — restricting selection to works with "cybernetic(s)" in the title — produces a corpus of definitively self-identified cybernetics texts. This criterion is maximally reproducible: any researcher can apply it independently to the same source collection and obtain the same result. However, it systematically excludes foundational works whose intellectual centrality to cybernetics is widely recognised but whose titles do not use the term: Ashby's *Design for a Brain* (1952), Shannon and Weaver's *Mathematical Theory of Communication* (1949), Bateson's *Steps to an Ecology of Mind* (1972), Maturana and Varela's *Autopoiesis and Cognition* (1980), and Forrester's *Industrial Dynamics* (1961) would all be excluded from a title-criterion corpus.

**The recall pole** — full-text search for "cybernetic(s)" across the entire text of candidate books — captures the broadest range of works engaging with cybernetic concepts, including passing references, historical mentions, and works in adjacent fields that absorbed cybernetic ideas without adopting the terminology. This criterion maximises recall at the cost of introducing works that engage only superficially with the cybernetics tradition.

**Our approach** sits deliberately between these poles, combining three strategies: (1) title-keyword matching, (2) broader metadata-keyword matching across descriptions and subject tags, and (3) expert curatorial judgement applied to works whose intellectual relationship to cybernetics is established through secondary literature and domain expertise rather than terminological self-identification.

---

## 3.3 Four-level inclusion stratum

To make the precision-recall trade-off empirically tractable and analytically useful, we stratify the corpus by the basis on which each book was included. We searched for "cybernetic(s)" (as a whole-word regular expression, case-insensitive) across all available bibliographic metadata fields: title, description, subject tags, and publisher name.

This analysis reveals four distinct inclusion strata (Table 1):

**Table 1. Inclusion strata for the 726-book corpus**

| Stratum | N | % | Basis of inclusion |
|---|---|---|---|
| Title-corroborated | 183 | 25.2% | "cybernetic(s)" in title and at least one other metadata field |
| Title-only | 55 | 7.6% | "cybernetic(s)" in title only; no corroborating metadata |
| Curated-keyword | 144 | 19.8% | Expert-curated as cybernetics; "cybernetic(s)" in description or tags but not title |
| Curated-pure | 330 | 45.5% | Expert-curated as cybernetics; no "cybernetic(s)" in any metadata field |
| Metadata-search | 14 | 1.9% | Found via metadata search; not expert-curated to cybernetics theme |

The **title-corroborated** and **title-only** strata together (238 books, 32.8%) constitute the highest-precision subset: works that explicitly self-identify with the cybernetics tradition through their titles. These books form the most reproducible stratum — replication using title-keyword criteria alone would recover this group.

The **curated-pure** stratum is the most methodologically significant: **330 books (45.5% of the corpus) contain no instance of "cybernetic(s)" in any bibliographic metadata field** and were included solely on the basis of expert judgement. These books represent the cybernetics tradition's influence on adjacent intellectual fields — biosemiotics, allostasis research, anticipatory systems theory, perceptual control theory, systems biology, Gregory Bateson studies — that absorbed cybernetic concepts and methods without adopting the cybernetics terminology. Their inclusion reflects a curatorial judgement that the intellectual tradition is broader than its nominal boundary, and that a corpus restricted to terminologically self-identified works would systematically misrepresent the tradition's reach and influence.

---

## 3.4 Cybernetics' specific recall problem

The precision-recall trade-off is particularly acute for cybernetics because the tradition exhibits a characteristic pattern of intellectual diffusion without terminological adoption. The field's founding generation explicitly labelled their work as cybernetics; subsequent generations absorbed its concepts, methods, and research programmes into adjacent disciplines while progressively shedding the label. This created a terminological gap between the cybernetics tradition as an intellectual heritage and cybernetics as a self-identifying disciplinary community.

This pattern is visible in the corpus. Of the 726 books assembled by expert curation as belonging to the cybernetics intellectual tradition, 330 (45.5%) contain no cybernetics keyword in any metadata field. This is not a sampling artefact but a substantive characteristic of the tradition: cybernetics diffused its intellectual programme — feedback, control, homeostasis, self-organisation, second-order observation — into systems theory, cognitive science, organisational theory, ecology, psychotherapy, and biosemiotics, typically without preserving the cybernetics label in those downstream fields.

A keyword-retrieval corpus would recover only the terminologically self-identified portion of this tradition (approximately 32.8% of the curated collection, or 238 of 726 books). The recall cost of keyword restriction is therefore not merely a matter of boundary cases but affects nearly half the corpus.

---

## 3.5 Stratum as analytical covariate

The inclusion stratum is used as an analytical covariate throughout the analysis rather than treated as a limitation to be controlled for. Specifically:

**Robustness analysis**: We examine whether the topic structure identified by LDA is consistent across strata. If the same intellectual clusters appear in the title-corroborated stratum (highest precision) and the curated-pure stratum (lowest reproducibility), the findings are robust to the precision-recall trade-off. If topics appear predominantly in lower-precision strata, they may represent peripheral influence rather than core tradition.

**Temporal analysis**: The distribution of inclusion strata across publication decades reveals how the terminological-intellectual gap evolved over time. We hypothesise that the curated-pure stratum will be concentrated in post-1980 publications, reflecting the progressive shedding of the cybernetics label as its concepts diffused into adjacent fields.

**Topic validation**: The inclusion stratum is used as one signal in the triangulation framework for topic validation (see Section 3.7). Topics dominated by curated-pure books are interpreted differently from topics dominated by title-corroborated books — the former may represent the tradition's intellectual legacy in adjacent fields; the latter its active self-identifying core.

---

## 3.6 Reproducibility and limitations

The title-corroborated and title-only strata (238 books) are fully reproducible from bibliographic metadata. The curated-keyword stratum (144 books) is reproducible with access to the same metadata sources used during corpus assembly. The curated-pure stratum (330 books) is not reproducible from metadata alone and depends on domain expertise that is not fully formalised.

We address this limitation in two ways. First, the `books_metadata_full.csv` file accompanying this paper records the inclusion stratum and keyword-presence flags for all 726 books, enabling readers to reproduce the keyword-based strata independently and to inspect the expert-judgement stratum. Second, we treat the stratum variable analytically, so that claims which depend on the curated-pure stratum are explicitly flagged as depending on expert judgement rather than reproducible criteria.

The curated-pure stratum also introduces a potential source of researcher bias: works included on the basis of expert judgement may reflect the curator's intellectual priors about what cybernetics is and where its boundaries lie. We note this as a limitation and encourage replication using alternative curatorial frameworks.

---

## 3.7 Media-type dependence

The precision-recall trade-off and its management through stratification is itself corpus-type-dependent. For a book corpus, the trade-off is navigable because books have rich metadata — titles that summarise arguments, subject classifications assigned by professional cataloguers, publisher categories, and back-of-book indexes — that carry strong signals about intellectual content. Title informativeness is particularly high for books: titles are deliberate, argumentative, and stable across editions and databases.

For a journal article corpus, the trade-off operates differently. Titles are shorter and less reliably informative; subject classifications are available but discipline-specific; abstracts provide keyword-rich metadata but are more recent as a convention. For a social media corpus, metadata is minimal and the trade-off collapses toward full-text search as the only viable strategy.

The stratification approach developed here is calibrated to the epistemic affordances of book corpora. Its applicability to other corpus types requires adaptation to the metadata structures those media provide.

---

*Draft prepared 2 April 2026. For integration into full paper methods section.*  
*Related: `docs/memos/memo_media_aware_nlp_epistemic_affordances.md` §12*
