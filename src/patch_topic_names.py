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
# ─────────────────────────────────────────────────────────────────────────────
# CURRENT: names finalised 20 September 2026 (single rater) against the 575-book
# run `runlog20260920-2` — 742 full-text rows from the enlarged Calibre collection
# (755 books in metadata.db), 26 books newly gaining full text since 19 July.
#
# This is a NEW equivalence class (575 books, not the 566 of 19 July). Topic
# positions did NOT merely permute this time — the clusters recombined. Provenance,
# measured as where each July topic's top-10 books are now dominant:
#
#     July T3  → T4  (10/10)   clean transfer
#     July T5  → T2  ( 9/10)   clean transfer
#     July T7  → T3  (10/10)   clean transfer
#     July T6  → T6  (10/10) ┐ MERGE: formal/mathematical + control engineering
#     July T8  → T6  ( 8/10) ┘        (T6 now has 5 books at loading 1.000)
#     July T4  → T7  (10/10) ┐ MERGE: self/therapy + popular history & biography
#     July T1  → T7  ( 6/10) ┘
#     July T9  → T8  ( 6/10) ┐ SPLIT: architecture strand → T8, arts/media → T5
#     July T9  → T5  ( 4/10) ┘
#     July T2  → dispersed   (3/10 → T1, 4/10 → T5, remainder scattered)
#
# T9 has NO July parent: no July top-10 book is dominant there, yet it is the
# largest topic in the run (110 books, 68 at loading ≥0.50). It cohered out of
# material that sat mid-loading across the July solution.
#
# T1 is retained as an UNNAMED RESIDUAL — excluded from interpretation and from
# reader-facing topic lists, but kept in the k=9 solution. It is NOT a dead topic:
# 09c's dead_topic() returns False for it (top-10 loadings 1.00, 0.99, 0.76, 0.63,
# 0.61, …), so the zero-dead-topics basis for canonical k=9 in docs/decisions.md
# §"Dead-topic count" is unaffected. It was dropped on incoherence between its word
# list (Sinophone: qian, chinese, xuesen) and its book list (3 of its 7 books have
# no China content; the top loading at 1.000 is about speaking and singing), at
# 0.159 stability over 7 books.
#
# Reporting framing (decided): "nine topics, one residual" — the k=9 model is stated
# as fitted, with T1 named as residual rather than silently omitted. Reader-facing
# counts are 9 topics / 8 interpreted.
#
# Because positions recombine when the corpus grows, the positional mapping below is
# only valid for THIS equivalence class. Re-derive it against the landing matrix
# before reusing these names on any future run — see ROADMAP: patch_topic_names.py
# should align by word overlap rather than by position.
#
# Provisional, single-rater, single-run; the multi-rater protocol (sprint item 4,
# ≥3 runs × ≥2 raters) remains outstanding.
#
# PRIOR: names finalised by Paul Wong, 19 July 2026, against the 566-book
# re-canonicalisation run (post-Calibre-reconstruction, KI-13); superseded above.
# ─────────────────────────────────────────────────────────────────────────────
TAXONOMY = {
    'T1': {
        'proposed_name': 'Residual — uninterpreted',
        'notes': (
            'UNNAMED RESIDUAL — retained in the k=9 solution, excluded from '
            'interpretation and from reader-facing topic lists. Not a dead '
            'topic: dead_topic() returns False (top-10 loadings 1.00, 0.99, '
            '0.76, 0.63, 0.61), so the zero-dead-topics basis for canonical '
            'k=9 is unaffected. Dropped on incoherence between word list '
            '(Sinophone: qian, chinese, xuesen, china) and book list — 3 of '
            'its 7 books have no China content and the 1.000 top loading is '
            'A Cybernetic Study of Speaking and Singing. Residue of July T2, '
            'which dispersed. Stability 0.159 over 7 books; lowest in the run.'
        ),
    },
    'T2': {
        'proposed_name': 'Social Systems and Second-Order Constructivism',
        'notes': (
            'Discursive register: Luhmannian social systems theory and '
            'second-order/constructivist epistemology. Luhmann anchors '
            'strongly (Theory of Society 0.930, Social Systems 0.927, '
            'Theories of Distinction 0.914, Law as a Social System 0.876); '
            'The Making of Meaning, actor-network and constructivist '
            'currents. Most stable topic this run (0.586), 100 books. '
            'Clean transfer from July T5 (9/10 of its top-10 land here).'
        ),
    },
    'T3': {
        'proposed_name': 'Management and Organisational Cybernetics',
        'notes': (
            'Discursive register: organisational and managerial cybernetics, '
            'VSM lineage and system dynamics. The Cybernetics of Workplace '
            'Conflict (1.000), Democracy at Work (0.998), Structural '
            'Cybernetics (0.983), The Fractal Organization (0.980), '
            'project/construction management. Stable (0.430), 69 books. '
            'Clean transfer from July T7 (10/10).'
        ),
    },
    'T4': {
        'proposed_name': 'Biological and Ecological Regulation: Homeostasis & Allostasis',
        'notes': (
            'Discursive register: biological and ecological regulation. '
            'Rethinking Homeostasis (0.994), What Is Health? Allostasis '
            '(0.990), The Communication Systems of the Body (0.936), Social '
            'Allostasis, Principles of Neural Design. Stable (0.368), 37 '
            'books — the smallest interpreted topic. Clean transfer from '
            'July T3 (10/10).'
        ),
    },
    'T5': {
        'proposed_name': 'Cybernetics and Digital Culture',
        'notes': (
            'Discursive register: digital media arts, music, performance and '
            'posthuman culture. The Composer\'s Black Box (0.884), Digital '
            'Performance (0.866), History of Computer Art (0.858), '
            'Cybernethisms (0.852), Experimenting the Human. Stable (0.320), '
            '45 books. Recombination with no majority parent: July T2 (4/10), '
            'July T9 (4/10), July T1 (2/10). NOTE the architecture strand of '
            'July T9 did NOT come here — 6 of 7 architecture-titled books are '
            'now in T8, so this topic is the arts/media half only.'
        ),
    },
    'T6': {
        'proposed_name': 'Formal Foundation and Control Engineering',
        'notes': (
            'Discursive register: mathematical formalism and control '
            'engineering, merged. MERGE of July T6 (formal/mathematical, '
            '10/10) and July T8 (control/feedback, 8/10) — the merged topic '
            'is tighter than either parent, with five books at loading 1.000 '
            '(Marine Control Systems, Engineering Cybernetics, Cybernetical '
            'Physics, Random Wavelets, Mathematical Structure of Finite '
            'Random Cybernetic Systems) spanning 1954-2007. Stable (0.413), '
            '59 books, median loading 0.70 — the most concentrated topic. '
            'PCT engineering vocabulary anchors here: the methodology.md '
            'PCT-dispersion worked example needs re-checking against this '
            'equivalence class.'
        ),
    },
    'T7': {
        'proposed_name': 'Cybernetics of Self and Reimagination of Self',
        'notes': (
            'Discursive register: the personal and narrative voice — self-'
            'help, memoir, fiction and popular history sharing an anecdotal, '
            'second-person address. MERGE of July T4 (self/therapy, 10/10) '
            'and July T1 (popular history and biography, 6/10). R.U.R. '
            '(0.995), Psycho-Cybernetics franchise (0.989, 0.975, 0.912), '
            '@Heaven (0.979), The Cyberiad (0.965, 0.956), With a Daughter\'s '
            'Eye (0.929). Stable (0.334), 81 books. Word list still reads '
            'Bateson/family-therapy, but that material is now a minority of '
            'the top loadings — the register, not the subject, is what unites '
            'it.'
        ),
    },
    'T8': {
        'proposed_name': 'Political Economy of Cybernetics',
        'notes': (
            'Discursive register: Cold War and postcolonial political '
            'history, political economy, and the architectural imaginary of '
            'cybernetics. The Cybernetic Border (0.918), The Internet '
            'Revolution (0.904), Imaginary Futures (0.904), Constructing '
            'Soviet Cultural Policy (0.902), Balkan Cyberia (0.853), How Not '
            'to Network a Nation, Cybernetic Circulation Complex. Inherits '
            'the majority of July T9 (6/10) including its architecture '
            'strand — Architectural Principles in the Age of Cybernetics, '
            'Architecture in Digital Culture, Last Futures. Stable (0.455), '
            '67 books, median year 2017 — the most contemporary topic, '
            'grown by recent critical scholarship.'
        ),
    },
    'T9': {
        'proposed_name': 'Cognition and Cybernetics',
        'notes': (
            'Discursive register: philosophy of mind, behaviour and machine — '
            'purposive explanation, perception, language and the cybernetic '
            'account of cognition. Philosophical Foundations of Cybernetics '
            '(0.988), The Discovery of the Artificial (0.953), Purposive '
            'Explanation in Psychology (0.923), Cybernetics and Biology '
            '(0.919), The Foundations of Cybernetics (0.907). LARGEST topic '
            'in the run (110 books, 68 at loading >=0.50) yet it has NO July '
            'parent — no July top-10 book is dominant here; it cohered out of '
            'material that sat mid-loading across the July solution. '
            'Moderate stability (0.237), the lowest of the interpreted eight, '
            'and it holds no vocabulary exclusive to itself — both worth '
            'watching on the next run.'
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
