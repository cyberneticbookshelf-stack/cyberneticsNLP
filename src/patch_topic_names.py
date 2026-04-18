"""
patch_topic_names.py
────────────────────
Writes agreed topic names and notes into topic_validation.json.
Run from project root:
    python3 patch_topic_names.py
"""
import json, pathlib, sys

target = pathlib.Path('json/topic_validation.json')
if not target.exists():
    sys.exit(f"ERROR: {target} not found — run from project root")

data = json.load(open(target))

# ── Run C canonical taxonomy (542-book corpus, agreed 14 April 2026) ──────────
# Names agreed by Paul Wong via title-sweep inspection of top-loading books.
# Stability scores from 5-seed run: mean=0.327 (superseded by sixth-batch
# rerun mean=0.357, 6/9 stable — 18 April 2026).
# Notes are provisional; full rationale in docs/memo_lda_k_selection.md.
TAXONOMY = {
    'T1': {
        'proposed_name': 'Cybernetics of Political Economy',
        'notes': (
            'Cybernetics applied to political and economic contexts: Cold War '
            'computing history, governance, tech policy, internet capitalism, '
            'cybernetics and state power. Top words: decision, border, '
            'investment, security, price, market, stock. Stability 0.232. '
            'Name agreed 18 April 2026 (title-sweep, run_all 18 Apr).'
        ),
    },
    'T2': {
        'proposed_name': 'Cybernetics and Circularity',
        'notes': (
            'Philosophical and theoretical cybernetics: second-order '
            'cybernetics, recursion, autopoiesis, posthumanism, systems '
            'ontology. Bateson, Yuk Hui, Maturana, constructivism. Top words: '
            'information, function, element, value, number, probability, '
            'entropy. Stability 0.224. '
            'Name agreed 18 April 2026 (title-sweep, run_all 18 Apr).'
        ),
    },
    'T3': {
        'proposed_name': 'Biological Systems Cybernetics',
        'notes': (
            'Biological and physiological cybernetics: homeostasis, allostasis, '
            'evolution, neuroscience. Top books: Rethinking Homeostasis, '
            'Information Theory and Evolution, Minds and Machines (1954). '
            'Top words: control, model, behavior, variable, input, cell, output. '
            'Stability 0.551. '
            'Name agreed 18 April 2026 (title-sweep, run_all 18 Apr).'
        ),
    },
    'T4': {
        'proposed_name': 'Applied Engineering Cybernetics',
        'notes': (
            'Engineering and applied cybernetics: PCT (Perceptual Control '
            'Theory), neural networks, bioreaction, marine control, von '
            'Foerster. Mix of formal control engineering and applied biological '
            'cybernetics. Top words: wiener, bateson, science, cybernetic, '
            'theory, world. Stability 0.437. '
            'Name agreed 18 April 2026 (title-sweep, run_all 18 Apr).'
        ),
    },
    'T5': {
        'proposed_name': 'Cultural Applications of Cybernetics',
        'notes': (
            'Cybernetics in cultural and artistic domains: computer art, '
            'digital performance, music, Lem (trurl vocabulary). Top books: '
            'History of Computer Art, Digital Performance, Relational '
            'Improvisation. Top words: year, people, look, right, trurl, tell. '
            'Stability 0.374. '
            'Name agreed 18 April 2026 (title-sweep, run_all 18 Apr).'
        ),
    },
    'T6': {
        'proposed_name': 'Formal Foundations of Cybernetics',
        'notes': (
            'Mathematical and formal foundations: information theory, '
            'Spencer-Brown (Laws of Form), Rosen (relational biology), '
            'semantic communication. Top words: machine, human, computer, '
            'brain, problem, control, language, program. Stability 0.349. '
            'Held stable from Run C. Name confirmed 18 April 2026.'
        ),
    },
    'T7': {
        'proposed_name': 'History and Biography of Cybernetics',
        'notes': (
            'Biographical and historical accounts of cybernetics figures: '
            'Wiener biographies (Dark Hero, Life in Cybernetics), Mary '
            'Catherine Bateson memoirs, popular cybernetics (Volleyball '
            'Cybernetics, Success Cybernetics). Top words: human, theory, '
            'social, world, concept, self. Stability 0.464. '
            'Name agreed 18 April 2026 (title-sweep, run_all 18 Apr).'
        ),
    },
    'T8': {
        'proposed_name': 'Cybernetic Management Theory',
        'notes': (
            'VSM lineage and organisational cybernetics: Beer (Viability of '
            'Organizations, Diagnosing the System), Luhmann (Health as Social '
            'System), applied systems theory, intelligent construction. '
            'Top words: cybernetic, social, information, organization, '
            'technology, design, management. Stability 0.319. '
            'Name agreed 18 April 2026 (title-sweep, run_all 18 Apr).'
        ),
    },
    'T9': {
        'proposed_name': 'Residual / Outlier Cluster',
        'notes': (
            'Not a genuine intellectual tradition. Lem\'s Cyberiad dominates '
            '(loading=1.000 for two editions); R.U.R. (Čapek), Qian Xuesen '
            'biography, Uexküll. Therapy vocabulary (people, family, person, '
            'life, experience, therapy) suggests PCT/behavioural outliers also '
            'present. Top words: people, family, person, life, experience, '
            'therapy, child, client. Stability 0.261. '
            'Provisional name — pending confirmation 18 April 2026.'
        ),
    },
}

# Apply to validation data
topics = data.get('topics', data.get('validation', []))
if not topics:
    # Try top-level keys
    print("Keys in topic_validation.json:", list(data.keys()))
    sys.exit("ERROR: could not find topics list — check structure")

updated = 0
for topic in topics:
    label = topic.get('topic_label', '')
    if label in TAXONOMY:
        topic['proposed_name'] = TAXONOMY[label]['proposed_name']
        topic['notes']         = TAXONOMY[label]['notes']
        updated += 1
        print(f"  {label} → {TAXONOMY[label]['proposed_name']}")

if updated == 0:
    print("No topics updated — checking structure:")
    print(json.dumps(data, indent=2)[:500])
    sys.exit("ERROR: topic_label field not found")

json.dump(data, open(target, 'w'), ensure_ascii=False, indent=2)
print(f"\nUpdated {updated}/9 topics in {target}")

# Also write topic names into nlp_results.json so report-building scripts
# (06_build_report.py, 07_build_excel.py) pick up agreed names rather than
# defaulting to generic 'Topic 1', 'Topic 2' etc.
nlp_path = pathlib.Path('json/nlp_results.json')
if nlp_path.exists():
    nlp = json.load(open(nlp_path))
    # Build ordered name list: index 0 = T1, index 1 = T2, etc.
    n_topics = nlp.get('n_topics', len(topics))
    ordered_names = []
    for i in range(n_topics):
        label = f'T{i+1}'
        name = TAXONOMY.get(label, {}).get('proposed_name', label)
        ordered_names.append(name)
    nlp['topic_names'] = ordered_names
    json.dump(nlp, open(nlp_path, 'w'), ensure_ascii=False)
    print(f"Updated nlp_results.json topic_names: {ordered_names}")
else:
    print("WARNING: json/nlp_results.json not found — skipping nlp update")
