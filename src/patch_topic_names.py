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

TAXONOMY = {
    'T1': {
        'proposed_name': 'Management Cybernetics',
        'notes': (
            'VSM lineage and operational cybernetics. Mathematical vocabulary '
            '(function, equation, input, output, value) reflects Operations '
            'Research heritage that Beer drew on explicitly. Covers structural '
            'design and viable systems applications. Temporally spans 1986–2022 '
            'showing tradition remains active.'
        ),
    },
    'T2': {
        'proposed_name': 'Second-Order Cybernetics Applied to Social Systems',
        'notes': (
            'Dominated by Luhmann but reflects appropriation of second-order '
            'cybernetics (von Foerster) into sociology and constructivism. '
            'Luhmann is not himself a second-order cybernetician — he applied '
            'the concepts to social systems theory. Also picks up autopoiesis '
            '(Maturana), constructivism, and actor-network theory. Represents '
            'the downstream social-scientific reception of second-order '
            'cybernetics. Contrast with T6 (mathematical origins).'
        ),
    },
    'T3': {
        'proposed_name': 'Dynamical Systems, Homeostasis & Biological Regulation',
        'notes': (
            'Forrester system dynamics, allostasis research, systems biology, '
            'positive feedback in natural systems. Intellectually coherent '
            'despite low stability (0.049) — instability reflects vocabulary '
            'overlap with T1 (systems design) and T5 (engineering cybernetics). '
            'Cross-topic instability is itself a finding: dynamical systems '
            'thinking appears across multiple cybernetics traditions '
            'simultaneously. Not a model failure — a field characteristic.'
        ),
    },
    'T4': {
        'proposed_name': 'Psychological Cybernetics',
        'notes': (
            'Two co-located traditions sharing register: Perceptual Control '
            'Theory (Powers and derivatives — Making Sense of Behavior, Method '
            'of Levels) and popular/self-help cybernetics (Psycho-Cybernetics, '
            'Freedom From Stress, Volleyball Cybernetics). Both use plain '
            'everyday language by design — PCT for psychological accessibility, '
            'popular books for general audiences. Share vocabulary register '
            'rather than necessarily concepts. Potential split candidate if k '
            'is ever increased.'
        ),
    },
    'T5': {
        'proposed_name': 'Non-Anglophone Engineering Cybernetics',
        'notes': (
            'Cybernetics from non-English national traditions: Soviet/Ukrainian '
            '(Glushkov), Soviet/Latvian (Yakubaitis), Chinese (Qian Xuesen), '
            'Polish (Lange), Romanian (Guiasu), Czechoslovak (Kovar & Valach), '
            'German (Cruse), Japanese (Kimura). Parallel cybernetics development '
            'largely independent of Wiener/American lineage (T6). Vocabulary '
            'clustering may partly reflect shared translation artefacts as well '
            'as genuine intellectual tradition. Note: Qian Xuesen appears in '
            'T5 (technical works) and T9 (biography) — consistent with '
            'corpus split between an author\'s work and their reception.'
        ),
    },
    'T6': {
        'proposed_name': 'Mathematical Foundations of Cybernetics',
        'notes': (
            'Wiener cluster: biography, intellectual history, and his '
            'mathematical works (Generalized Harmonic Analysis, Hopf-Wiener '
            'Integral). Both books *about* Wiener and Wiener\'s own technical '
            'publications. The Cybernetics Moment (2015) correctly placed here '
            'as historical account of the cybernetics founding. Represents '
            'the Anglophone mathematical origin of cybernetics — contrast with '
            'T5 (non-Anglophone engineering tradition) and T2 (social systems '
            'downstream application).'
        ),
    },
    'T7': {
        'proposed_name': 'Cultural Cybernetics, Posthumanism & Digital Media',
        'notes': (
            'Humanities reception of cybernetics: performance studies, Latin '
            'American posthumanism, science fiction studies, avant-garde art, '
            'digital culture, anime studies. Temporally concentrated 2005–2024 '
            '— the recent cultural turn in cybernetics reception. Heavily '
            'weighted toward curated_pure inclusion stratum: books that engage '
            'cybernetics as cultural phenomenon without doing cybernetics '
            'research. Evidence of cybernetic concept diffusion into humanities '
            'and cultural studies.'
        ),
    },
    'T8': {
        'proposed_name': 'Applied Cybernetics & Computers in Society',
        'notes': (
            'Applied period 1959–1989: management cybernetics, automation, '
            'computers and society. Beer\'s applied works (Diagnosing the '
            'System, Heart of Enterprise) sit here rather than T1 — T1 has '
            'the structural/theoretical VSM; T8 has the applied/historical '
            'VSM and broader social context. Whole Earth Software Catalog '
            'correctly placed at intersection of cybernetics and personal '
            'computing culture. Tight temporal range is itself a finding.'
        ),
    },
    'T9': {
        'proposed_name': 'Residual / Outlier Cluster',
        'notes': (
            'Not a genuine intellectual tradition. [249] Reflexion and Control: '
            'Mathematical Models dominates at stability=1.000 — idiosyncratic '
            'vocabulary not absorbed by any of the nine main topics. Remaining '
            'books (marine control, Qian Xuesen biography, Lem fiction, Rise '
            'of the Machines) are diverse outliers. Document in paper as model '
            'residual. [249] warrants individual inspection — possible '
            'translation artefact or genuinely peripheral mathematical work. '
            'Lem fiction vocabulary (helena, trurl, klapaucius) confirms '
            'science fiction register does not cleanly separate at k=9.'
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
