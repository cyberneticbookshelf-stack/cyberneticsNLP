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

# ── Full-text canonical taxonomy (541-book corpus, 25 April 2026) ─────────────
# First genuine full-text canonical run (--full-text --max-features 15000).
# Names derived from seed-42 top-loading books in the 25 April run after
# diagnostic established that doc_topic argmax assignments are unreliable
# across the seed-42 / seed-99 split (see docs/methodology.md §"LDA topics
# as discursive registers, not subject domains" and ROADMAP #26).
#
# Per session startup protocol (CLAUDE.md): names are provisional pending
# Paul Wong's validation of the full-text canonical run. Stability scores
# below should be refreshed from json/topic_stability.json after each run;
# the literals here are intentionally omitted to avoid stale figures.
#
# All names should be read as discursive registers ("how cybernetics gets
# written about"), not as subject domains ("what cybernetics is about").
# See docs/methodology.md for the full reframe and the PCT-dispersion
# worked example.
TAXONOMY = {
    'T1': {
        'proposed_name': 'History and Historiography of Cybernetics',
        'notes': (
            'Discursive register: historical and historiographical writing '
            'about the cybernetics tradition itself. Wiener and Bateson '
            'biographies, Macy Conferences history, accounts of the rise and '
            'fall of cybernetics as a discipline. Top loadings include '
            'Wiener-biography volumes and field-history monographs. '
            'Provisional name agreed 25 April 2026 (full-text canonical run).'
        ),
    },
    'T2': {
        'proposed_name': 'Techno-political Complexes',
        'notes': (
            'Discursive register: political, economic, and geopolitical '
            'analysis of cybernetic and computational systems. Cold War '
            'computing, surveillance, big tech, multinationals, internet '
            'capitalism — not necessarily drawn on state-level boundaries. '
            'Provisional name agreed 25 April 2026 (full-text canonical run).'
        ),
    },
    'T3': {
        'proposed_name': 'Engineering Control',
        'notes': (
            'Discursive register: classical control engineering and applied '
            'feedback systems. State-space models, transfer functions, '
            'controller design, plant dynamics. PCT books with strong '
            'engineering vocabulary anchor here (see methodology.md §PCT '
            'dispersion). '
            'Provisional name agreed 25 April 2026 (full-text canonical run).'
        ),
    },
    'T4': {
        'proposed_name': 'Social and Organisational Cybernetics',
        'notes': (
            'Discursive register: organisational and managerial cybernetics, '
            'VSM lineage. Stafford Beer (Viability of Organizations, '
            'Diagnosing the System), Luhmann, applied systems theory, '
            'intelligent organisation design. '
            'Provisional name agreed 25 April 2026 (full-text canonical run).'
        ),
    },
    'T5': {
        'proposed_name': 'Formal Foundations of Cybernetics',
        'notes': (
            'Discursive register: mathematical, symbolic, and computational '
            'methods. Information theory, Spencer-Brown (Laws of Form), '
            'Rosen (relational biology), semantic communication, formal '
            'control mathematics. PCT books that develop the formal '
            'apparatus also anchor here — the largest single sub-cluster of '
            '21 PCT-adjacent books in the corpus (see methodology.md §PCT '
            'dispersion). '
            'Provisional name agreed 25 April 2026 (full-text canonical run).'
        ),
    },
    'T6': {
        'proposed_name': 'Reinventing Selves and Others, Past and Future',
        'notes': (
            'Discursive register: self-help, popular psychology, and pop '
            'cultural application of cybernetics. Maltz lineage '
            '(Psycho-Cybernetics and descendants), success / wellbeing '
            'monographs, cybernetics-flavoured personal-development texts. '
            'PCT books written for a general audience also anchor here. '
            'Provisional name agreed 25 April 2026 (full-text canonical run).'
        ),
    },
    'T7': {
        'proposed_name': 'Psychological and Behavioural Regulation and Control',
        'notes': (
            'Discursive register: affect-, allostasis- and stress-regulation '
            'literature. Sapolsky-adjacent, Damasio-adjacent. NB: PCT '
            'literature does NOT anchor here despite the topic name '
            'suggesting it should — PCT vocabulary disperses to T5/T6/T8/T3 '
            'by register. The mismatch between the topic name a PCT scholar '
            'would expect and the topic content actually computed is itself '
            'the worked example in docs/methodology.md §"LDA topics as '
            'discursive registers, not subject domains". '
            'Provisional name agreed 25 April 2026 (full-text canonical run).'
        ),
    },
    'T8': {
        'proposed_name': 'Biological and Neural Cybernetics',
        'notes': (
            'Discursive register: homeostatic biology, neuroscience, '
            'evolutionary perspectives. Rethinking Homeostasis, Information '
            'Theory and Evolution, neural-cybernetic monographs. PCT books '
            'that emphasise homeostatic and biological grounding anchor '
            'here. '
            'Provisional name agreed 25 April 2026 (full-text canonical run).'
        ),
    },
    'T9': {
        'proposed_name': 'Extensions of Cybernetics',
        'notes': (
            'Discursive register: cybernetics extended into adjacent domains '
            'rather than developed within its classical core. Multiple '
            'extension paths anchor here — ecology and environment, '
            'posthumanism and more-than-human systems, second-order '
            'cybernetics and autopoiesis, digital ontology and cosmotechnics. '
            'Yuk Hui (digital ontology, recursivity), Maturana/Varela in '
            'their philosophical mode, constructivist and posthuman currents. '
            'Replaces the previous "Residual / Outlier Cluster" reading from '
            'the 18 April 542-book sampled run; the full-text canonical run '
            'of 25 April assigns coherent extension-domain content to this '
            'position. Provisional name agreed 26 April 2026 (revised from '
            '"Ecology, Posthumanism and Digital Ontology" — those are three '
            'specific extensions; the topic accommodates more).'
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
    # Also write notes so 09c_validate_topics.py can overlay them onto
    # topic_validation.json (fixed 26 April 2026, ROADMAP #27 — 09c had
    # been clobbering proposed_name/notes that this script wrote).
    ordered_notes = [
        TAXONOMY.get(f'T{i+1}', {}).get('notes', '') for i in range(n_topics)
    ]
    nlp['topic_notes'] = ordered_notes
    json.dump(nlp, open(nlp_path, 'w'), ensure_ascii=False)
    print(f"Updated nlp_results.json topic_names: {ordered_names}")
    print(f"Updated nlp_results.json topic_notes ({len(ordered_notes)} entries)")
else:
    print("WARNING: json/nlp_results.json not found — skipping nlp update")
