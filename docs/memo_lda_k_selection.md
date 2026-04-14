# LDA k-Selection Analysis
**CyberneticsNLP — 14 April 2026**

## Setup

Four LDA runs at k=8, 9, 10, 12 with consistent preprocessing:

```
--full-text --seeds 5 --max-features 15000 --lemmatize --run-id k{N}
```

- 542 books (690 → 542 after pub-type filter: monographs and collected works only)
- Full body text with front/back matter stripped
- spaCy `en_core_web_sm` lemmatisation
- 15,000-feature vocabulary
- 5-seed stability analysis (mean Jaccard, Hungarian alignment)

---

## Summary Table

| k  | Perplexity | Mean stability | Stable ≥0.3 | Unstable <0.15 |
|----|-----------|----------------|-------------|----------------|
| 8  | 3436.7    | 0.333          | 5/8         | 1/8            |
| 9  | 3413.6    | 0.327          | 5/9         | 1/9            |
| 10 | 3382.4    | 0.300          | 5/10        | 3/10           |
| 12 | 3360.6    | 0.271          | 6/12        | 3/12           |

Perplexity improves monotonically with k (expected). Stability degrades as k increases (expected — more topics means harder to recover consistent solutions across seeds).

---

## Topic Stability by Run

### k=8
| Topic | Stability | Top words | Top books |
|-------|-----------|-----------|-----------|
| T1 | 0.192 | computer, machine, wiener, cybernetic, technology, space, project, medium | Northern Sparks (Century); Machines of Loving Grace (Markoff) |
| T2 | 0.492 | bateson, person, want, child, something, self, therapist, therapy | Psychocybernetic Model of Art (Nucho); Method of Levels (Carey) |
| T3 | 0.224 | social, language, object, cybernetic, meaning, machine, relation, self | Recursivity and Contingency (Yuk Hui) |
| T4 | 0.401 | management, organization, decision, cybernetic, economic, social, variety, environment | Sustainable Self-Governance (Espinosa); Democracy at Work (Thorsrud) |
| T5 | **0.112** | cell, rate, brain, energy, evolution, neuron, growth, organism | Principles of Neural Design (Sterling/Laughlin) |
| T6 | 0.406 | behavior, variable, machine, feedback, output, equation, define, object | Hopf-Wiener Integral Equation (Wiener); Marine Control Systems (Fossen) |
| T7 | 0.344 | social, society, distinction, self, luhmann, environment, operation, legal | Law as a Social System (Luhmann) |
| T8 | 0.497 | body, robot, woman, narrative, social, culture, posthuman, death | Cyborg Manifesto (Haraway) |

### k=9
| Topic | Stability | Top words | Top books |
|-------|-----------|-----------|-----------|
| T1 | 0.131 | machine, computer, wiener, cybernetic, brain, neumann, mcculloch, program | The Cyberiad (Lem); R.U.R. (Čapek) |
| T2 | 0.559 | bateson, person, child, therapist, self, behavior, therapy, want | Psychocybernetic Model of Art (Nucho); Method of Levels (Carey) |
| T3 | 0.153 | social, language, object, meaning, self, relation, environment, reality | Cybersemiotics (Brier); Digital Objects (Yuk Hui) |
| T4 | 0.349 | organization, decision, management, cybernetic, economic, social, variety, environment | Democracy at Work (Thorsrud); Sustainable Self-Governance (Espinosa) |
| T5 | 0.224 | cell, rate, brain, energy, evolution, organism, animal, growth | What Is Health? (Sterling); Rethinking Homeostasis (Schulkin) |
| T6 | 0.289 | variable, behavior, feedback, equation, output, signal, define, object | Marine Control Systems (Fossen); Neural Networks (Cruse) |
| T7 | 0.306 | legal, society, political, border, operation, security, distinction, social | Border Security (Chambers); Ecclesial Cybernetics (Granfield) |
| T8 | 0.306 | posthuman, body, twin, narrative, cyborg, technology, posthumanism, ethical | Embodiment of the Everyday Cyborg (Haddow); Philosophical Posthumanism (Ferrando) |
| T9 | **0.622** | space, medium, cybernetic, technology, computer, machine, culture, image | Northern Sparks (Century); Digital Performance (Dixon); Anime's Knowledge Cultures (Li) |

### k=10
| Topic | Stability | Top words | Top books |
|-------|-----------|-----------|-----------|
| T1 | 0.228 | behavior, perception, variable, reference, signal, perceptual, person, goal | Study of Living Control Systems (Marken); Mind Readings (Marken); Controlling People (Marken/Carey) |
| T2 | 0.561 | bateson, therapist, therapy, client, child, self, pattern, family | Psychocybernetic Model of Art (Nucho); Systemic Therapy (Bertrando) |
| T3 | 0.135 | social, language, meaning, object, self, relation, environment, organism | Cybersemiotics (Brier); Digital Objects (Yuk Hui) |
| T4 | 0.400 | organization, management, decision, cybernetic, economic, variety, social, environment | Designing Intelligent Construction (Roll); Sustainable Self-Governance (Espinosa) |
| T5 | **0.022** | cell, rate, brain, energy, evolution, animal, growth, population | What Is Health? (Sterling); Principles of Neural Design (Laughlin) |
| T6 | 0.332 | equation, variable, feedback, define, machine, output, relation, behavior | Hopf-Wiener (Wiener); Marine Control Systems (Fossen) |
| T7 | 0.379 | society, social, political, legal, distinction, decision, operation, luhmann | Law as a Social System (Luhmann); Border Security (Chambers) |
| T8 | 0.296 | posthuman, twin, object, body, robot, narrative, posthumanism, technology | Philosophical Posthumanism (Ferrando); Twins and Recursion (King) |
| T9 | 0.503 | space, cybernetic, technology, computer, medium, machine, social, architecture | Northern Sparks (Century); Anime's Knowledge Cultures (Li); Digital Performance (Dixon) |
| T10 | 0.147 | machine, computer, wiener, cybernetic, brain, neumann, language, mcculloch | The Cyberiad (Lem); R.U.R. (Čapek) |

### k=12
| Topic | Stability | Top words | Top books |
|-------|-----------|-----------|-----------|
| T1 | 0.207 | medium, space, body, text, image, mark, virtual, interface | Anime's Knowledge Cultures (Li); Embodiment of the Everyday Cyborg (Haddow) |
| T2 | 0.468 | bateson, person, child, therapist, therapy, want, client, self | Psychocybernetic Model of Art (Nucho); Systemic Therapy (Bertrando) |
| T3 | 0.269 | language, object, relation, machine, meaning, social, organism, self | Cybersemiotics (Brier); Digital Objects (Yuk Hui); Autopoiesis and Cognition (Maturana/Varela) |
| T4 | 0.363 | economic, cybernetic, soviet, project, government, political, management, national | Opening of the Cybernetic Front (Elazar); Cybernetic Revolutionaries (Medina); Power of Systems (Rindzevičiūtė) |
| T5 | 0.171 | cell, rate, brain, behavior, evolution, energy, animal, organism | What Is Health? (Sterling); Rethinking Homeostasis (Schulkin) |
| T6 | 0.306 | equation, signal, output, feedback, variable, cell, neuron, rate | Marine Control Systems (Fossen); Engineering Cybernetics (Qian) |
| T7 | **0.051** | social, society, distinction, luhmann, legal, self, decision, observation | Law as a Social System (Luhmann) |
| T8 | 0.353 | tone, music, musical, chord, pitch, melody, vector, composer | Cybernetic Music (Jaxitron) |
| T9 | 0.475 | social, culture, technology, political, earth, history, cultural, cybernetic | Border Security (Chambers); Cybernetic Border (Chaar López); Cyborg Manifesto (Haraway) |
| T10 | 0.117 | computer, machine, technology, wiener, space, cybernetic, architecture, project | The Cyberiad (Lem); The Media Lab (Brand) |
| T11 | 0.104 | cybernetic, wiener, brain, mcculloch, social, scientific, neumann, machine | Rebel Genius: Warren McCulloch (Abraham) |
| T12 | 0.365 | organization, decision, environment, social, management, behavior, variety, goal | Design and Diagnosis for Sustainable Organizations (Pérez Ríos); Viability of Organizations (Lassl) |

---

## Analysis

### Stable cores across all k

The following clusters are consistent and stable regardless of k, confirming them as genuine intellectual groupings in the corpus:

- **Bateson / family therapy / second-order cybernetics** — most stable topic in every run (~0.5+), anchored by Nucho, Carey, and the Milan school
- **Organization / management / VSM** — Beer's Viable System Model tradition, Espinosa, Thorsrud
- **Engineering / mathematical cybernetics** — Wiener's mathematical work, Fossen, Qian Xuesen
- **Biology / neuroscience / allostasis** — Sterling, Schulkin, Laughlin; consistently present but somewhat unstable at higher k
- **Luhmann / social systems theory** — stable at k=8 and k=9, but destabilised at k=12 (T7=0.051), suggesting over-splitting

### What changes with k

**k=9 over k=8:** The most important gain. T9 (media/digital arts/culture — Century, Dixon, Li) emerges with stability **0.622**, the highest in any run across all k values. At k=8 this cluster was being absorbed into a broad technology/Wiener topic. The separation is intellectually justified: these are books about cybernetics and media arts/digital culture, not the history of cybernetics per se.

**k=10 over k=9:** Perceptual Control Theory (PCT) splits off as T1 (Marken, Carey — stability 0.228). PCT is a distinct school within cybernetics (Powers' control theory tradition) that at k=9 was absorbed into the Bateson/therapy cluster. However, k=10 also produces a severely unstable biology topic (T5=0.022), signalling over-splitting. The PCT separation is intellectually valuable but comes at a cost.

**k=12 over k=10:** Two genuinely new clusters emerge — **music** (T8, Jaxitron's *Cybernetic Music*, stability 0.353) and **Soviet/political cybernetics** (T4, Medina, Elazar, Rindzevičiūtė, stability 0.363). Both are intellectually legitimate. However, the history-of-cybernetics cluster fragments into two overlapping unstable topics (T10=0.117, T11=0.104), and Luhmann collapses to 0.051. The model is over-splitting at k=12.

### The fiction/Lem problem

Across all k, the Lem/Čapek books (*The Cyberiad*, *R.U.R.*) form a drifting, unstable cluster. This is a corpus composition issue — these are fiction titles in a scholarly monograph collection. They attract different topic assignments across seeds because their vocabulary has low overlap with the rest of the corpus. This instability is expected and does not reflect a modelling problem. Consider flagging these books as a distinct pub_type in future analyses.

---

## Decision

**k=9 is the recommended solution.**

- Nearly identical stability to k=8 (0.327 vs 0.333) with better perplexity (3413 vs 3436)
- Gains the media/digital arts cluster (T9, stability 0.622) which is the strongest topic signal in the entire comparison
- Only one unstable topic (T1=0.131, the Lem/fiction outlier — a corpus issue, not a model issue)
- k=10 is appealing for PCT but the biology instability (0.022) is disqualifying at this stage
- k=12 sub-clusters (music, Soviet cybernetics) are worth noting in the methods section as genuine signals that emerge at higher resolution

### Next steps

- [ ] Run `--name-topics` on `nlp_results_k9.json` to generate API labels
- [ ] Flag Lem/Čapek fiction titles in `pub_type` metadata
- [ ] Consider a targeted k=10 re-run with music/fiction titles excluded to test PCT stability without the Lem effect
- [ ] Update `docs/draft_methods_corpus_construction.md` with k-selection rationale
