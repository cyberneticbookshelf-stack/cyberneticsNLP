# LDA Run Comparison — Full-Text Iteration Study
**CyberneticsNLP — 25 April 2026**

Tracking successive full-text canonical runs to compare the effect of increasing
`--max-iter` on topic stability and structure. All runs: 541 books, `--full-text`,
`--max-features 15000`, `--lemmatize`, `--topics 9`, `--seeds 5`.

---

## Run 1 — 25 April 2026 | max-iter: 20 (default at time of run)

**Status:** Non-canonical. `max_iter=20` was the hardcoded default; `--max-iter`
flag did not yet exist. Recorded here as baseline for comparison only.

**Pipeline flags:**
```
--min-chars 10000 --lemmatize --topics 9 --seeds 5 --full-text --max-features 15000
```
*(no --max-iter flag; internal default was 20)*

**Coherence sweep (best k):** k=9 (coherence=0.0845, perplexity=3839.3)

**Stability (5 seeds):**

| Topic | Stability | Status     | Top words                                               | Books |
|-------|-----------|------------|---------------------------------------------------------|-------|
| T1    | 0.282     | moderate   | machine, computer, wiener, cybernetic, brain, neumann   | 168   |
| T2    | 0.400     | stable     | cybernetic, technology, machine, computer, architecture | 165   |
| T3    | 0.523     | stable     | variable, input, equation, output, rate, feedback       | 41    |
| T4    | 0.468     | stable     | social, organization, decision, communication, behavior | 1     |
| T5    | 0.076     | ⚠ unstable | language, entropy, object, sign, probability, semantic  | 71    |
| T6    | 0.360     | stable     | family, therapy, child, tell, feel, person              | 29    |
| T7    | 0.076     | ⚠ unstable | emotion, behavior, brain, social, body, emotional       | 42    |
| T8    | 0.277     | moderate   | machine, brain, cell, neuron, animal, energy            | 18    |
| T9    | 0.386     | stable     | bateson, social, body, technology, cybernetic           | 6     |

**Mean stability:** 0.316 | **Stable (≥0.3):** 5/9 | **Unstable (<0.15):** 2/9

**Top books per topic (dominant loading ≥ 0.8):**

- T1 (168): Organizations: Social Systems; Cybernetics of Human Learning; Management Process; Autopoiesis and Cognition; Reflexion and Control
- T2 (165): Modern Invention of Information; Informational Logic of Human Rights; Indexing It All; Architectural Principles in the Age of Cybernetics
- T3 (41): The Cyberiad [Lem] ⚠ fiction; R.U.R. [Čapek] ⚠ fiction; Cybernetics Within Us
- T4 (1): A Silvan Tomkins Handbook ⚠ collapsed to single book
- T5 (71): Volleyball Cybernetics ⚠; Psycho-Cybernetics; Hypno Cybernetics; Sexual Cybernetics — fringe/popular cluster
- T6 (29): Marine Control Systems; Engineering Cybernetics; Random Wavelets and Cybernetic Systems
- T7 (42): What Is Health? (allostasis); Urban Dynamics; Rethinking Homeostasis; World Dynamics
- T8 (18): Psychocybernetic Model of Art Therapy; Systemic Psychotherapy; Systemic Therapy
- T9 (6): Question Concerning Technology in China [Yuk Hui]; Mathematical Theory of Semantic Communication; Return to China One Day [Qian Xuesen]

**Hardware:** CPU only (no GPU — RAPIDS not yet installed); sequential seeds
**Runtime:** Started 14:31 AEST — completed 15:13 AEST → **41 minutes**

**Observations:**
- T1 and T2 absorb 61% of corpus (333/541 books) — severe over-generalisation
- T4 collapsed to 1 book — model failed to populate this topic
- T5 unstable and capturing fringe popular titles (volleyball, hypnosis, sex)
- T3 fiction-dominated despite engineering word signal
- Old sampled-run names carried forward by patch_topic_names.py — **all mismatched**
- Run not logged to pipeline.db (rejected as non-canonical pending 100-iter rerun)

---

## Run 2 — pending | max-iter: 100

*To be completed after next run_all.sh.*

**Pipeline flags:**
```
--min-chars 10000 --lemmatize --topics 9 --seeds 5 --full-text --max-features 15000 --max-iter 100 --gpu
```

**Hardware:** 5× NVIDIA RTX 3090 (24GB each); CUDA 12.6; RAPIDS cuML (pending verification)
**Runtime:** —

| Topic | Stability | Status | Top words | Books |
|-------|-----------|--------|-----------|-------|
| T1    |           |        |           |       |
| T2    |           |        |           |       |
| T3    |           |        |           |       |
| T4    |           |        |           |       |
| T5    |           |        |           |       |
| T6    |           |        |           |       |
| T7    |           |        |           |       |
| T8    |           |        |           |       |
| T9    |           |        |           |       |

Mean stability: — | Stable (≥0.3): —/9 | Unstable (<0.15): —/9

---

## Run 3 — pending | max-iter: 1000

*Higher-iteration publication-quality run. To be scheduled after Run 2 validation.*

**Pipeline flags:**
```
--min-chars 10000 --lemmatize --topics 9 --seeds 5 --full-text --max-features 15000 --max-iter 1000 --gpu
```

**Runtime:** —

*(table to be filled)*

---

## Notes

- k=9 confirmed as highest coherence in Run 1 sweep but topic structure is poor at max_iter=20
- k may need revisiting after convergence improves at 100+ iterations
- T5 fringe cluster and T3 fiction contamination are corpus composition issues independent of iteration count — likely persist regardless of max_iter
- If structure remains poor at 100 iterations, a k-sweep (k=10–14) at max_iter=100 is the next step before committing to a 1000-iteration run
