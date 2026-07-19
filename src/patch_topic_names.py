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
# Names finalised by Paul Wong, 19 July 2026, against the 566-book re-canonicalisation
# run (post-Calibre-reconstruction, KI-13). This is a NEW equivalence class (566 books,
# not the 541 of 26 April): topic positions permuted, so these are NOT a relabelling of
# the April taxonomy — the clusters themselves moved (e.g. the old single "Social and
# Organisational Cybernetics" split into social-systems T5 vs management T7). Provisional,
# single-rater; the multi-rater stability protocol (sprint item 4) still applies.
TAXONOMY = {
    'T1': {
        'proposed_name': 'History of Information Age and Cybernetics',
        'notes': (
            'Discursive register: popular history and biography of computing, '
            'information, and the cybernetics tradition. Top loadings: Stewart '
            'Brand (Whole Earth, The Media Lab), Gleick (The Information), '
            'Dark Hero of the Information Age (Wiener biography), Waldrop '
            '(The Dream Machine), Markoff, Mayor (Gods and Robots). '
            'Least stable topic this run (0.145).'
        ),
    },
    'T2': {
        'proposed_name': 'Extensions and Exploration of Cybernetics',
        'notes': (
            'Heterogeneous exploration/extension cluster: voice, sound and '
            'singing (A Cybernetic Study of Speaking and Singing anchors at '
            '1.00), Sinophone cybernetics (Yuk Hui on technology in China, '
            'Qian Xuesen), interdisciplinary "exploring cybernetics" volumes, '
            'avatars and machine sensation. Moderate stability (0.173); the '
            'most mixed of the nine.'
        ),
    },
    'T3': {
        'proposed_name': 'Biological and Ecological Regulation: Homeostasis & Allostasis',
        'notes': (
            'Discursive register: biological and ecological regulation. '
            'Homeostasis/allostasis (Schulkin, Sterling — What Is Health?), '
            'evolutionary and ecological systems (Corning, Holistic Darwinism; '
            'Lovelock, Gaia; positive feedback in natural systems). '
            'Stable (0.325).'
        ),
    },
    'T4': {
        'proposed_name': 'Cybernetics of Self',
        'notes': (
            'Discursive register: psycho-cybernetics, self-help, and applied '
            'personal psychology. Maltz Psycho-Cybernetics franchise (multiple '
            'editions), stress/self-regulation and counselling texts, '
            'cybernetics-flavoured self-improvement (incl. Sexual/Volleyball '
            'Cybernetics). Stable (0.322).'
        ),
    },
    'T5': {
        'proposed_name': 'Social Systems and Second-Order Constructivism',
        'notes': (
            'Discursive register: Luhmannian social systems theory and '
            'second-order/constructivist epistemology. Luhmann anchors '
            'strongly (Social Systems, Theory of Society, Theories of '
            'Distinction, Essays on Self-Reference); Varela (Principles of '
            'Biological Autonomy), actor-network and constructivist currents. '
            'Stable (0.514). Splits, with T7, the April single "Social and '
            'Organisational Cybernetics" topic.'
        ),
    },
    'T6': {
        'proposed_name': 'Foundations of Cybernetics',
        'notes': (
            'Discursive register: mathematical and formal foundations. '
            'Information theory, probability/entropy, formal control '
            'mathematics and relational-biology formalism (Guiasu; '
            'Mathematical Theory of Semantic Communication; Reflexion and '
            'Control; Lange, Wholes and Parts; Louie, relational biology). '
            'Moderate stability (0.225).'
        ),
    },
    'T7': {
        'proposed_name': 'Management and Organisational Cybernetics',
        'notes': (
            'Discursive register: organisational and managerial cybernetics, '
            'VSM lineage and system dynamics. Espinosa (self-governance), '
            'Lassl (Viability of Organizations), Emery/Thorsrud (Democracy at '
            'Work), project/construction management, Forrester (Urban '
            'Dynamics). Most stable topic this run (0.566).'
        ),
    },
    'T8': {
        'proposed_name': 'Control and Feedback Systems',
        'notes': (
            'Discursive register: control engineering, feedback systems and '
            'neural networks. Neural Networks as Cybernetic Systems, marine/'
            'plant control (Fossen), Qian Xuesen (Engineering Cybernetics), '
            'Powers (Living Control Systems, PCT). Stable (0.523). PCT '
            'engineering vocabulary anchors here — the methodology.md §PCT '
            'dispersion worked example should be re-checked against this new '
            'equivalence class.'
        ),
    },
    'T9': {
        'proposed_name': 'Digital Arts, Architecture, Design and Posthumanism',
        'notes': (
            'Discursive register: digital media arts, architecture/design, and '
            'posthuman culture. Ascott (Telematic Embrace), Dixon (Digital '
            'Performance), digital-culture architecture (Yiannoudes, Hight, '
            'Vrachliotis), Situationist and posthumanist currents, cybernetic '
            'poetics. Stable (0.495).'
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
