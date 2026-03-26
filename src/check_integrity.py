"""
check_integrity.py
────────────────────────────────────────────────────────────────────────────
Session-start integrity checker for the Book NLP pipeline.

Verifies that every script defines its required names, that inter-script
file dependencies exist, and that nlp_results.json contains all expected
fields. Run this at the start of every session before editing anything.

Usage (from project root):
  python3 src/check_integrity.py           # check everything
  python3 src/check_integrity.py --scripts # scripts only (no data files)
  python3 src/check_integrity.py --data    # data files only
"""

import ast, sys, os, re, json
from pathlib import Path

# ── Resolve project root ──────────────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here) if os.path.basename(_here) == 'src' else _here
os.chdir(_root)

import pathlib as _plci
CSV_DIR  = _plci.Path('csv')
JSON_DIR = _plci.Path('json')

SCRIPTS_ONLY = '--scripts' in sys.argv
DATA_ONLY    = '--data'    in sys.argv

OK   = '\033[92m✓\033[0m'
FAIL = '\033[91m✗\033[0m'
WARN = '\033[93m!\033[0m'

errors   = []
warnings = []

def ok(msg):   print(f"  {OK}  {msg}")
def fail(msg): print(f"  {FAIL}  {msg}"); errors.append(msg)
def warn(msg): print(f"  {WARN}  {msg}"); warnings.append(msg)

def get_names(src):
    """Return set of all names defined at module or function level."""
    tree = ast.parse(src)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name):
                        names.add(n.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in getattr(node, 'names', []):
                names.add(a.asname or (a.name or '').split('.')[0])
        elif isinstance(node, ast.AugAssign):
            if isinstance(node.target, ast.Name):
                names.add(node.target.id)
    return names

# ── Manifest: script → required names ────────────────────────────────────────
# Format: { script_filename: [required_name, ...] }
REQUIRED = {
    '03_nlp_pipeline.py': [
        # Flags
        'WEIGHTED', 'NAME_TOPICS', '_FIXED_TOPICS',
        # Functions
        'build_index_weights', 'sample_book', 'tokenize',
        'npmi_coherence', 'get_top_words', 'extract_keyphrases',
        'name_topics_via_api',
        # Runtime variables (checked separately via regex since they're
        # computed mid-script, not at module top level)
    ],
    '03_nlp_pipeline_chapters.py': [
        'MAX_FEATURES', 'TOP_WORDS', 'raw_split',
    ],
    '04_summarize.py': [
        'split_into_chapters', 'sent_tokenize', 'score_sentences', 'top_sents',
        'MIN_CHAPTER_WORDS',
    ],
    '06_build_report.py': [
        'img_b64', 'chapter_accordion',
    ],
    '06_build_report_chapters.py': [
        'img_b64', 'chapter_accordion',
    ],
    '08_build_timeseries.py': [
        'LDA_NAMES', '_LDA_BASE', 'TOPIC_NAMES_CH', '_BASE_CH', 'PALETTE',
    ],
    '09_extract_index.py': [
        'quality_score', 'extract_index_terms',
        'INDEX_START', 'ALPHA_HEADER',
    ],
    '09b_build_index_analysis.py': [
        'find_snippet', '_LDA_BASE', 'TOPIC_NAMES',
    ],
    '10_build_index_report.py': [
        'clean_term', '_LDA_BASE', 'TOPIC_NAMES',
    ],
    '11_embedding_comparison.py': [
        'best_k_by_silhouette', 'cluster_metrics', 'top_neighbours',
        'embed_2d', '_LDA_BASE', 'LDA_NAMES',
    ],
    '12_index_grounding.py': [
        'is_clean', '_LDA_BASE', 'LDA_NAMES', '_NMF_BASE', 'NMF_NAMES',
    ],
    '13_weighted_comparison.py': [
        'load_results', 'cluster_purity', '_LDA_BASE', 'LDA_NAMES',
    ],
    '15_entity_classify.py': [
        'wikidata_lookup', 'KNOWN_TECH_ORGS', 'KNOWN_SINGLE_PERSONS',
        'WORK_TITLE_PAT', 'ALL_CAPS_PAT', 'WIKIDATA_KIND_MAP',
        'is_noise', 'CACHE_PATH',
    ],
    '14_entity_network.py': [
        'pmi_score', 'para_cooccur', 'book_set', 'is_person',
        'KNOWN_SINGLE_PERSONS', 'PERSON_PAT',
        'MIN_BOOKS', 'MIN_PMI', 'NO_WINDOWS',
    ],
    'build_embed_report.py': [
        'purity', 'metric_best', 'nbr_html', 'mrow',
    ],
    'embeddings.py': [
        'get_embedder', 'LSAEmbedder', 'SentenceEmbedder', 'VoyageEmbedder',
    ],
    'generate_summaries_api.py': [
        'is_edited_volume', 'sanitise', 'clean_sample', 'get_samples',
        'is_clean', 'ngram_overlap', 'parse_book_response',
        'process_book', 'call_claude', 'RateLimiter', 'SafeWriter',
        'MODEL', 'OVERLAP_RETRY_TH', 'NOISE_RE', 'REPORT_RE', 'PLACEHOLDER_RE',
        'BOOK_PROMPT', 'EDITED_PROMPT', 'CHAPTER_PROMPT',
        'CHAPTER_RETRY_PROMPT',
        # Flags (defined inside main() — checked via regex)
    ],
    'parse_and_clean_stream.py': [
        'clean', 'CLEAN_CAP',
    ],
}

# ── Key variables that must appear in script text (mid-script computed) ───────
REQUIRED_IN_TEXT = {
    '03_nlp_pipeline.py': [
        'pub_years', 'coords_2d', 'results', 'best_n', 'best_lda',
        'top_words', 'dominant_topics', 'cluster_labels',
    ],
    'generate_summaries_api.py': [
        'workers', 'recursive', 'pending', 'jsonl_path',
    ],
    '08_build_timeseries.py': [
        'pub_years', 'pub_years_ch', 'valid', 'all_years',
    ],
    '12_index_grounding.py': [
        'pub_years', 'coords_2d',
    ],
}

# ── Inter-script file dependencies ────────────────────────────────────────────
# Format: { script: [file_it_reads, ...] }
# Only files that MUST exist for the script to run at all.
REQUIRES_FILE = {
    '03_nlp_pipeline.py':           ['json/books_clean.json'],
    '03_nlp_pipeline_chapters.py':  ['json/summaries.json', 'json/books_clean.json'],
    '04_summarize.py':              ['json/books_clean.json', 'json/nlp_results.json'],
    '06_build_report.py':           ['json/nlp_results.json', 'json/summaries.json'],
    '06_build_report_chapters.py':  ['json/nlp_results_chapters.json', 'json/summaries.json'],
    '07_build_excel.py':            ['json/nlp_results.json', 'json/summaries.json'],
    '07_build_excel_chapters.py':   ['json/nlp_results_chapters.json', 'json/summaries.json'],
    '08_build_timeseries.py':       ['json/nlp_results.json', 'json/nlp_results_chapters.json'],
    '09_extract_index.py':          ['json/books_clean.json'],
    '09b_build_index_analysis.py':  ['json/index_terms.json', 'json/index_vocab.json',
                                     'json/nlp_results.json', 'json/books_clean.json'],
    '10_build_index_report.py':     ['json/index_analysis.json', 'json/index_snippets.json',
                                     'json/nlp_results.json'],
    '11_embedding_comparison.py':   ['json/summaries.json', 'json/nlp_results.json',
                                     'json/nlp_results_chapters.json'],
    '12_index_grounding.py':        ['json/index_analysis.json', 'json/nlp_results.json',
                                     'json/nlp_results_chapters.json', 'json/books_clean.json'],
    '15_entity_classify.py':          ['json/index_analysis.json'],
    '14_entity_network.py':          ['json/index_analysis.json',
                                      'json/nlp_results.json'],
    '13_weighted_comparison.py':    ['json/nlp_results_unweighted.json',
                                     'json/nlp_results_weighted.json'],
    'build_embed_report.py':        ['json/embedding_results.json'],
    'generate_summaries_api.py':    ['json/books_clean.json', 'json/nlp_results.json'],
}

# ── nlp_results.json required fields ─────────────────────────────────────────
NLP_RESULTS_FIELDS = [
    'book_ids', 'titles', 'authors', 'n_topics', 'perplexities',
    'top_words', 'doc_topic', 'dominant_topics', 'keyphrases',
    'cos_sim', 'inertias', 'silhouettes', 'best_k', 'cluster_labels',
    'tfidf_matrix', 'feature_names', 'pub_years', 'coords_2d',
]
# These are optional (generated by --name-topics / --weighted)
NLP_RESULTS_OPTIONAL = ['topic_names', 'weighted']

# ═════════════════════════════════════════════════════════════════════════════
# CHECK 1: Script integrity
# ═════════════════════════════════════════════════════════════════════════════
if not DATA_ONLY:
    print("\n── Directory layout ──────────────────────────────────────────────────────")
    for _d, _lbl in [(CSV_DIR,"csv/  (input CSVs)"),(JSON_DIR,"json/ (JSON/JSONL)")]:
        (ok if _d.exists() else warn)(f"{_d}/  {"exists" if _d.exists() else "not found — created by pipeline"}")

if not DATA_ONLY:
    print("\n── Script integrity ──────────────────────────────────────────────────────")

    for fname, required_names in sorted(REQUIRED.items()):
        path = Path('src') / fname
        if not path.exists():
            fail(f"{fname}: FILE MISSING")
            continue

        src = path.read_text()

        # Syntax check
        try:
            ast.parse(src)
        except SyntaxError as e:
            fail(f"{fname}: SYNTAX ERROR at line {e.lineno}: {e.msg}")
            continue

        # Name check
        defined = get_names(src)
        missing = [n for n in required_names if n not in defined]
        if missing:
            fail(f"{fname}: MISSING DEFINITIONS: {missing}")
        else:
            ok(f"{fname}: all {len(required_names)} required names present")

        # Text presence check (mid-script computed variables)
        if fname in REQUIRED_IN_TEXT:
            text_missing = [v for v in REQUIRED_IN_TEXT[fname] if v not in src]
            if text_missing:
                fail(f"{fname}: MISSING FROM TEXT (computed vars): {text_missing}")

# ═════════════════════════════════════════════════════════════════════════════
# CHECK 2: Data file dependencies
# ═════════════════════════════════════════════════════════════════════════════
if not SCRIPTS_ONLY:
    print("\n── Data file dependencies ────────────────────────────────────────────────")

    for fname, required_files in sorted(REQUIRES_FILE.items()):
        missing_files = [f for f in required_files if not Path(f).exists()]
        present_files = [f for f in required_files if Path(f).exists()]
        if missing_files:
            # Check if any are truly critical (vs optional post-09b)
            warn(f"{fname}: MISSING INPUT FILES: {missing_files}")
        else:
            ok(f"{fname}: all {len(required_files)} input files present")

# ═════════════════════════════════════════════════════════════════════════════
# CHECK 3: nlp_results.json field completeness
# ═════════════════════════════════════════════════════════════════════════════
if not SCRIPTS_ONLY:
    print("\n── nlp_results.json fields ───────────────────────────────────────────────")
    nlp_path = Path('json/nlp_results.json')
    if not nlp_path.exists():
        warn("nlp_results.json: NOT FOUND (run 03_nlp_pipeline.py first)")
    else:
        try:
            R = json.loads(nlp_path.read_text())
            missing_fields = [f for f in NLP_RESULTS_FIELDS if f not in R]
            optional_present = [f for f in NLP_RESULTS_OPTIONAL if f in R and R[f]]
            if missing_fields:
                fail(f"nlp_results.json: MISSING FIELDS: {missing_fields}")
            else:
                ok(f"nlp_results.json: all {len(NLP_RESULTS_FIELDS)} required fields present")
            if optional_present:
                ok(f"nlp_results.json: optional fields present: {optional_present}")
            # Sanity check
            n_books = len(R.get('book_ids', []))
            ok(f"nlp_results.json: {n_books} books, "
               f"{R.get('n_topics','?')} topics, k={R.get('best_k','?')}")
        except Exception as e:
            fail(f"nlp_results.json: PARSE ERROR: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# Summary
# ═════════════════════════════════════════════════════════════════════════════
print(f"\n── Summary ───────────────────────────────────────────────────────────────")
if not errors and not warnings:
    print(f"  {OK}  All checks passed.")
else:
    if errors:
        print(f"  {FAIL}  {len(errors)} error(s):")
        for e in errors:
            print(f"       • {e}")
    if warnings:
        print(f"  {WARN}  {len(warnings)} warning(s):")
        for w in warnings:
            print(f"       • {w}")

sys.exit(1 if errors else 0)
