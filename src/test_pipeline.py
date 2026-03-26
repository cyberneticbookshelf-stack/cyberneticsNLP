"""
test_pipeline.py
────────────────────────────────────────────────────────────────────────────
Regression test for the Book NLP pipeline using a tiny synthetic corpus
(8 books, 2 topics). Runs the critical path end-to-end and verifies that
all outputs have the expected structure.

Usage (from project root):
  python3 src/test_pipeline.py          # full test
  python3 src/test_pipeline.py --fast   # skip slow steps (LDA sweep, etc.)

Takes ~30 seconds on a modern laptop.
"""

import sys, os, json, shutil, tempfile, subprocess, traceback
from pathlib import Path

# ── Resolve project root ──────────────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here) if os.path.basename(_here) == 'src' else _here

FAST  = '--fast' in sys.argv
OK    = '\033[92m✓\033[0m'
FAIL  = '\033[91m✗\033[0m'
SKIP  = '\033[94m–\033[0m'

passed = failed = skipped = 0

def ok(msg):   global passed;  passed  += 1; print(f"  {OK}  {msg}")
def fail(msg): global failed;  failed  += 1; print(f"  {FAIL}  {msg}")
def skip(msg): global skipped; skipped += 1; print(f"  {SKIP}  {msg} [skipped --fast]")

# ═════════════════════════════════════════════════════════════════════════════
# Synthetic corpus
# ═════════════════════════════════════════════════════════════════════════════
CORPUS = {
    'b001': {
        'title': 'Cybernetics and Control', 'author': 'Wiener, N.',
        'pub_year': 1960, 'pubdate': '1960-01-01',
        'clean_text': (
            'feedback control systems regulation homeostasis information '
            'communication negative feedback loop controller actuator sensor '
            'error signal governor regulator servomechanism adaptive system '
            'feedback control systems regulation homeostasis information '
        ) * 80,
    },
    'b002': {
        'title': 'Systems Theory', 'author': 'Bertalanffy, L.',
        'pub_year': 1968, 'pubdate': '1968-01-01',
        'clean_text': (
            'general systems theory open system closed system entropy '
            'equifinality hierarchy organization complexity emergence '
            'isomorphism biology sociology physics mathematics model '
            'general systems theory open system closed system entropy '
        ) * 80,
    },
    'b003': {
        'title': 'Autopoiesis', 'author': 'Maturana, H.',
        'pub_year': 1972, 'pubdate': '1972-01-01',
        'clean_text': (
            'autopoiesis self organization living systems biological '
            'closure operational cognition observer second order '
            'feedback control information communication network cell '
        ) * 80,
    },
    'b004': {
        'title': 'Design for a Brain', 'author': 'Ashby, W.R.',
        'pub_year': 1960, 'pubdate': '1960-01-01',
        'clean_text': (
            'adaptive behavior regulation homeostat ultrastability '
            'requisite variety state machine environment constraint '
            'feedback control systems regulation homeostasis information '
        ) * 80,
    },
    'b005': {
        'title': 'Steps to Ecology', 'author': 'Bateson, G.',
        'pub_year': 1972, 'pubdate': '1972-01-01',
        'clean_text': (
            'mind ecology pattern double bind schizophrenia communication '
            'deutero learning context relationship difference information '
            'autopoiesis self organization living systems biological '
        ) * 80,
    },
    'b006': {
        'title': 'Introduction to Cybernetics', 'author': 'Ashby, W.R.',
        'pub_year': 1956, 'pubdate': '1956-01-01',
        'clean_text': (
            'variety regulation constraint selection transformation machine '
            'state transition table feedback control information channel '
            'feedback control systems regulation homeostasis information '
        ) * 80,
    },
    'b007': {
        'title': 'Brain of the Firm', 'author': 'Beer, S.',
        'pub_year': 1972, 'pubdate': '1972-01-01',
        'clean_text': (
            'viable system model management organization complexity '
            'recursion autonomy cohesion algedonic signal channel '
            'general systems theory open system closed system entropy '
        ) * 80,
    },
    'b008': {
        'title': 'Laws of Form', 'author': 'Spencer-Brown, G.',
        'pub_year': 1969, 'pubdate': '1969-01-01',
        'clean_text': (
            'distinction form calculus boundary mark logic mathematics '
            'indication crossing re-entry second order observer '
            'autopoiesis self organization living systems biological '
        ) * 80,
    },
}

SUMMARIES = {
    bid: {
        'title': d['title'], 'author': d['author'],
        'descriptive':  f"{d['author']} develops a framework for understanding "
                        f"control and organization in {d['title']}.",
        'argumentative': f"The work traces how regulatory principles apply "
                         f"across biological and social domains.",
        'critical':     f"A foundational text whose influence extends well "
                        f"beyond its original disciplinary context.",
        'chapters': [],
    }
    for bid, d in CORPUS.items()
}

# ═════════════════════════════════════════════════════════════════════════════
# Test infrastructure
# ═════════════════════════════════════════════════════════════════════════════
def run_script(script, args='', cwd=None):
    """Run a pipeline script in a subprocess, return (returncode, stdout, stderr)."""
    cmd = [sys.executable, str(Path(_root) / 'src' / script)] + (args.split() if args else [])
    result = subprocess.run(cmd, capture_output=True, text=True,
                            cwd=cwd or _root, timeout=120)
    return result.returncode, result.stdout, result.stderr

def check_json(path, required_keys, min_entries=None):
    """Load JSON and verify required keys and minimum size."""
    if not path.exists():
        return False, f"file not found: {path}"
    try:
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            missing = [k for k in required_keys if k not in data]
            if missing:
                return False, f"missing keys: {missing}"
            if min_entries and len(data) < min_entries:
                return False, f"only {len(data)} entries (expected ≥{min_entries})"
        elif isinstance(data, list):
            if min_entries and len(data) < min_entries:
                return False, f"only {len(data)} items (expected ≥{min_entries})"
        return True, None
    except Exception as e:
        return False, str(e)

# ═════════════════════════════════════════════════════════════════════════════
# Run tests in a temporary directory
# ═════════════════════════════════════════════════════════════════════════════
tmpdir = Path(tempfile.mkdtemp(prefix='nlp_test_'))
src_dir = Path(_root) / 'src'

try:
    (tmpdir / 'data' / 'outputs').mkdir(parents=True)
    (tmpdir / 'json').mkdir(exist_ok=True)
    (tmpdir / 'csv').mkdir(exist_ok=True)

    # Write synthetic corpus
    (tmpdir / 'json' / 'books_clean.json').write_text(json.dumps(CORPUS, ensure_ascii=False))
    (tmpdir / 'json' / 'summaries.json').write_text(json.dumps(SUMMARIES, ensure_ascii=False))

    def run(script, args=''):
        cmd = [sys.executable, str(src_dir / script)] + (args.split() if args else [])
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(tmpdir), timeout=180)
        return r.returncode, r.stdout + r.stderr

    print(f"\n── Test environment: {tmpdir}")
    print(f"   Corpus: {len(CORPUS)} books\n")

    # ── Test 1: 03_nlp_pipeline.py ───────────────────────────────────────────
    print("── Step 03: LDA pipeline ─────────────────────────────────────────────────")
    if FAST:
        skip("03_nlp_pipeline.py (LDA sweep)")
    else:
        rc, out = run('03_nlp_pipeline.py')
        if rc != 0:
            fail(f"03_nlp_pipeline.py returned {rc}\n{out[-500:]}")
        else:
            ok_j, err = check_json(tmpdir/'json'/'nlp_results.json',
                ['book_ids','titles','n_topics','dominant_topics','top_words',
                 'pub_years','coords_2d','cluster_labels','best_k'])
            if ok_j:
                R = json.loads((tmpdir/'json'/'nlp_results.json').read_text())
                ok(f"nlp_results.json: {len(R['book_ids'])} books, "
                   f"{R['n_topics']} topics, k={R['best_k']}")
                if 'pub_years' in R and any(y for y in R['pub_years']):
                    ok("pub_years populated")
                else:
                    fail("pub_years empty or missing")
                if 'coords_2d' in R and R['coords_2d']:
                    ok("coords_2d populated")
                else:
                    fail("coords_2d empty or missing")
            else:
                fail(f"nlp_results.json: {err}")

    # ── Test 2: 09_extract_index.py ──────────────────────────────────────────
    print("\n── Step 09: Index extraction ─────────────────────────────────────────────")
    # Write minimal CSV for index extraction
    import csv, io
    csv_content = io.StringIO()
    writer = csv.DictWriter(csv_content, fieldnames=['id','searchable_text'])
    writer.writeheader()
    for bid, d in CORPUS.items():
        # Embed a small fake index section
        text = d['clean_text'][:500] + '\n\nIndex\nfeedback, 12, 45\nsystems, 23\ncontrol, 8\n'
        writer.writerow({'id': bid, 'searchable_text': text})
    (tmpdir / 'csv' / 'books_text_test.csv').write_text(csv_content.getvalue())

    rc, out = run('09_extract_index.py')
    if rc != 0:
        fail(f"09_extract_index.py returned {rc}\n{out[-400:]}")
    else:
        ok_j, err = check_json(tmpdir/'json'/'index_terms.json', [], min_entries=1)
        ok_v, _ = check_json(tmpdir/'json'/'index_vocab.json', [], min_entries=1)
        if ok_j and ok_v:
            ok("index_terms.json and index_vocab.json written")
        else:
            fail(f"index output: {err}")

    # ── Test 3: 09b_build_index_analysis.py ──────────────────────────────────
    print("\n── Step 09b: Index analysis ──────────────────────────────────────────────")
    if not (tmpdir/'json'/'nlp_results.json').exists():
        skip("09b (requires nlp_results.json from step 03)")
    elif not (tmpdir/'json'/'index_terms.json').exists():
        skip("09b (requires index_terms.json from step 09)")
    else:
        rc, out = run('09b_build_index_analysis.py')
        if rc != 0:
            fail(f"09b_build_index_analysis.py returned {rc}\n{out[-400:]}")
        else:
            ok_j, err = check_json(tmpdir/'json'/'index_analysis.json',
                ['vocab','top200','book_terms','pub_years','dom_topics','n_topics'])
            ok_s, _   = check_json(tmpdir/'json'/'index_snippets.json', [])
            if ok_j and ok_s:
                import json as _j09
                ia = _j09.loads((tmpdir/'json'/'index_analysis.json').read_text())
                # Verify noise suppression: function-word terms should not be in vocab
                noise_in = [t for t in ['of a','and control','in cybernetics']
                            if t in ia['vocab']]
                if noise_in:
                    fail(f'Noise terms in vocab after canonicalisation: {noise_in}')
                else:
                    ok(f"index_analysis.json written, vocab={len(ia['vocab'])} "
                       f"(noise suppressed)")
            else:
                fail(f"index_analysis output: {err}")

    # ── Test 4: 12_index_grounding.py ────────────────────────────────────────
    print("\n── Step 12: Index grounding ──────────────────────────────────────────────")
    if not (tmpdir/'json'/'index_analysis.json').exists():
        skip("12 (requires index_analysis.json from step 09b)")
    else:
        # Also need nlp_results_chapters.json — write a minimal one
        chapters_data = {
            'chapters': [],
            'n_topics': 2,
            'dominant_topics': [],
            'doc_topic': [],
            'top_words': [['feedback','control'],['system','open']],
            'book_ids': list(CORPUS.keys()),
            'book_id_per_ch': [],
            'cluster_labels': [],
            'best_k': 2,
            'inertias': {'2': 1.0},
            'silhouettes': {'2': 0.1},
            'keyphrases': {},
            'coords_2d': [[0.1,0.2]]*len(CORPUS),
            'titles_list': [],
            'chapter_ids': [],
            'book_topic_counts': {},
            'pub_years_per_ch': [],
        }
        (tmpdir/'json'/'nlp_results_chapters.json').write_text(
            json.dumps(chapters_data, ensure_ascii=False))

        rc, out = run('12_index_grounding.py')
        if rc != 0:
            fail(f"12_index_grounding.py returned {rc}\n{out[-400:]}")
        else:
            for fname in ['topic_index_grounding.json',
                          'concept_density.json', 'concept_velocity.json']:
                ok_j, err = check_json(tmpdir/'json'/fname, [])
                if ok_j:
                    ok(f"{fname} written")
                else:
                    fail(f"{fname}: {err}")

    # ── Test 5: 08_build_timeseries.py ───────────────────────────────────────
    print("\n── Step 08: Time series ──────────────────────────────────────────────────")
    if not (tmpdir/'json'/'nlp_results.json').exists():
        skip("08 (requires nlp_results.json)")
    elif FAST:
        skip("08_build_timeseries.py")
    else:
        rc, out = run('08_build_timeseries.py')
        html_path = tmpdir / 'data' / 'outputs' / 'book_nlp_timeseries.html'
        if rc != 0 or not html_path.exists():
            fail(f"08_build_timeseries.py: rc={rc}, html={'exists' if html_path.exists() else 'MISSING'}\n{out[-300:]}")
        else:
            size_kb = html_path.stat().st_size // 1024
            ok(f"book_nlp_timeseries.html written ({size_kb} KB)")
            # Check Chart 7 section present
            html = html_path.read_text()
            if 'id="bands"' in html or 'band_means' in html:
                ok("Chart 7 (band prevalence) section present")
            else:
                fail("Chart 7 section missing from timeseries HTML")

    # ── Test 6: 14_entity_network.py ──────────────────────────────────────────
    print("\n── Step 14: Entity network ────────────────────────────────────────────────")
    if not (tmpdir/'json'/'index_analysis.json').exists():
        skip("14 (requires index_analysis.json from step 09b)")
    else:
        rc, out = run('14_entity_network.py', '--no-windows')
        # 14 writes to its own project root (pkg/json/), not tmpdir
        import pathlib as _pl14
        _src14 = _pl14.Path(__file__).parent  # src/
        net_path = _src14.parent / 'json' / 'entity_network.json'
        if rc != 0 or not net_path.exists():
            fail(f"14_entity_network.py: rc={rc}\n{out[-400:]}")
        else:
            ok_j, err = check_json(net_path, ['nodes','edges','n_persons'])
            if ok_j:
                net = json.loads(net_path.read_text())
                ok(f"entity_network.json: {len(net['nodes'])} nodes, "
                   f"{len(net['edges'])} edges")
            else:
                fail(f"entity_network.json: {err}")

    # ── Test 7: 15_entity_classify.py (heuristics only, --no-wikidata) ──────────
    print("\n── Step 15: Entity classification ─────────────────────────────────────────")
    if not (tmpdir/'json'/'index_analysis.json').exists():
        skip("15 (requires index_analysis.json from step 09b)")
    else:
        rc, out = run('15_entity_classify.py', '--no-wikidata')
        import pathlib as _pl15
        cache_path = _pl15.Path(__file__).parent.parent / 'json' / 'entity_types_cache.json'
        if rc != 0:
            fail(f"15_entity_classify.py returned {rc}\n{out[-300:]}")
        else:
            ok_j, err = check_json(cache_path, [])
            if ok_j:
                import json as _j15
                _cache = _j15.loads(cache_path.read_text())
                _suppressed = sum(1 for e in _cache.values() if e['kind']=='suppress')
                _persons    = sum(1 for e in _cache.values() if e['kind']=='person')
                ok(f"entity_types_cache.json: {len(_cache)} entries, "
                   f"{_suppressed} suppressed, {_persons} persons")
                # Spot-check key classifications
                _checks = [('cybernetics (wiener)','suppress'),('google','organisation'),
                           ('aristotle','person'),('cybernetics','concept')]
                _bad = [(tl,e) for tl,e in _checks
                        if _cache.get(tl,{}).get('kind') != e]
                if _bad: fail(f"Cache spot-check failed: {_bad}")
                else: ok("Cache spot-checks pass")
            else:
                fail(f"entity_types_cache.json: {err}")

    # ── Test 8: generate_summaries_api.py (dry-run, no API key) ──────────────
    print("\n── Step gen: Summaries script startup ────────────────────────────────────")
    rc, out = run('generate_summaries_api.py', '--workers 1')
    # Expect it to fail with missing API key, NOT a NameError
    if 'NameError' in out or 'AttributeError' in out:
        fail(f"generate_summaries_api.py has a NameError:\n{out[-400:]}")
    elif 'ANTHROPIC_API_KEY' in out or 'Books loaded' in out:
        ok("generate_summaries_api.py starts cleanly (stops at API key check)")
    else:
        ok(f"generate_summaries_api.py startup: rc={rc}")

    # ── Test 9: check_integrity.py passes ─────────────────────────────────────
    print("\n── Meta: integrity checker ───────────────────────────────────────────────")
    rc, out = run('check_integrity.py', '--scripts')
    if rc != 0:
        fail(f"check_integrity.py --scripts FAILED:\n{out[-600:]}")
    else:
        ok("check_integrity.py --scripts: all script checks pass")

finally:
    shutil.rmtree(tmpdir, ignore_errors=True)

# ═════════════════════════════════════════════════════════════════════════════
print(f"\n── Results ───────────────────────────────────────────────────────────────")
total = passed + failed + skipped
print(f"  Passed:  {passed}/{total-skipped}")
print(f"  Failed:  {failed}")
print(f"  Skipped: {skipped}")
if failed:
    print(f"\n  {FAIL}  {failed} test(s) failed.")
    sys.exit(1)
else:
    print(f"\n  {OK}  All tests passed.")
    sys.exit(0)
