#!/usr/bin/env python3
"""
log_pipeline_run.py — Manual tool for logging a pipeline run to pipeline.db.

Run this after reviewing a completed run_all.sh output.  It hashes the current
nlp_results.json, extracts input parameters, computes the equivalence class
(run_hash), and writes a permanent record to data/pipeline.db.

Surveys (Google Forms) can only be created for logged, non-test runs.

Usage:
    python src/log_pipeline_run.py                     # interactive log of current run
    python src/log_pipeline_run.py --test              # log as test run (survey-ineligible)
    python src/log_pipeline_run.py --runlog PATH       # ingest specific runlog CSV
    python src/log_pipeline_run.py --run-id ID         # override auto-generated run ID
    python src/log_pipeline_run.py --notes "..."       # attach note without interactive prompt
    python src/log_pipeline_run.py --yes               # skip confirmation prompt

    python src/log_pipeline_run.py --list              # list all logged runs
    python src/log_pipeline_run.py --list-classes      # list equivalence classes
    python src/log_pipeline_run.py --show RUN_ID       # show full detail for a run

Options:
    --nlp PATH        Path to nlp_results.json (default: json/nlp_results.json)
    --db  PATH        Path to pipeline.db       (default: data/pipeline.db)
"""

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_db import DB_PATH, open_db, compute_file_hash, compute_run_hash

BASE_DIR = Path(__file__).resolve().parent.parent
NLP_PATH = BASE_DIR / "json" / "nlp_results.json"


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_nlp(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def get_git_commit(repo_dir: Path) -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_dir), capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def latest_runlog(outputs_dir: Path) -> Path | None:
    """Return the most recently modified runlog CSV in data/outputs/, or None."""
    candidates = sorted(
        outputs_dir.glob("runlog*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def make_run_id(nlp: dict, is_test: bool) -> str:
    stab   = nlp.get("stability", {})
    k      = nlp.get("n_topics", "?")
    ns     = stab.get("n_seeds", "?")
    date   = datetime.now().strftime("%Y%m%d")
    suffix = "_test" if is_test else ""
    return f"run_{date}_k{k}_s{ns}{suffix}"


def extract_params(nlp: dict) -> dict:
    stab = nlp.get("stability", {})
    return {
        "k":             nlp.get("n_topics", 9),
        "n_books":       len(nlp.get("doc_topic", [])),
        "max_features":  nlp.get("max_features"),
        "pipeline_mode": nlp.get("pipeline_mode"),
        "seeds_used":    stab.get("seeds_used", []),
        "mean_stability": stab.get("mean_stability"),
        "stability_scores": stab.get("stability_scores", []),
        "topic_names":   nlp.get("topic_names", []),
        "lda_params": {
            "n_topics":       nlp.get("n_topics"),
            "n_seeds":        stab.get("n_seeds"),
            "seeds_used":     stab.get("seeds_used"),
            "max_features":   nlp.get("max_features"),
            "pipeline_mode":  nlp.get("pipeline_mode"),
            "gpu_used":       nlp.get("gpu_used"),
            "n_books_analysed": len(nlp.get("doc_topic", [])),
            "perplexities":   nlp.get("perplexities"),
            "coherences":     nlp.get("coherences"),
            "stability_thresholds": stab.get("thresholds"),
            "stability_scores": stab.get("stability_scores"),
            "mean_stability": stab.get("mean_stability"),
        },
    }


# ── Display ────────────────────────────────────────────────────────────────────

def print_run_summary(params: dict, run_hash: str, nlp_hash: str, is_new_class: bool):
    stab_scores = params["stability_scores"]
    names       = params["topic_names"]
    print()
    print("  Run parameters")
    print(f"  {'k':<20} {params['k']}")
    print(f"  {'n_books':<20} {params['n_books']}")
    print(f"  {'max_features':<20} {params['max_features']}")
    print(f"  {'pipeline_mode':<20} {params['pipeline_mode']}")
    print(f"  {'seeds_used':<20} {params['seeds_used']}")
    print(f"  {'mean_stability':<20} {params['mean_stability']:.4f}" if params['mean_stability'] else "")
    print()
    print("  Equivalence class")
    print(f"  {'run_hash':<20} {run_hash}")
    tag = "  ← NEW class" if is_new_class else "  (existing class)"
    print(f"  {'status':<20}{tag}")
    print()
    print("  NLP file hash")
    print(f"  {'nlp_hash':<20} {nlp_hash}")
    print()
    if stab_scores:
        print("  Topic stability")
        for i, (score, name) in enumerate(zip(stab_scores, names or [f"T{i+1}" for i in range(len(stab_scores))])):
            flag = "✓" if score >= 0.45 else ("~" if score >= 0.30 else "✗")
            print(f"    {flag} T{i+1} {score:.3f}  {name}")
        print()


# ── Runlog ingestion ───────────────────────────────────────────────────────────

def ingest_runlog(con, run_id: str, runlog_path: Path) -> int:
    """Read runlog CSV lines into runlog_entries. Returns number of lines inserted."""
    lines = runlog_path.read_text(encoding="utf-8", errors="replace").splitlines()
    count = 0
    for i, line in enumerate(lines, start=1):
        con.execute(
            "INSERT INTO runlog_entries (run_id, line_num, content) VALUES (?, ?, ?)",
            (run_id, i, line),
        )
        count += 1
    return count


# ── List / show commands ───────────────────────────────────────────────────────

def cmd_list(db_path: Path):
    con = open_db(db_path)
    rows = con.execute(
        """SELECT r.run_id, r.run_hash, r.logged_at, r.k, r.n_books,
                  r.mean_stability, r.is_test,
                  (SELECT COUNT(*) FROM naming_sessions s WHERE s.run_id = r.run_id) AS n_sessions
           FROM pipeline_runs r
           ORDER BY r.logged_at DESC"""
    ).fetchall()
    con.close()
    if not rows:
        print("No runs logged yet.  Run: python src/log_pipeline_run.py")
        return
    print(f"\n{'Run ID':<32}  {'Hash':<18}  {'k':>2}  {'books':>5}  "
          f"{'stab':>5}  {'test':>4}  {'sessions':>8}  {'logged'}")
    print("─" * 100)
    for r in rows:
        stab = f"{r['mean_stability']:.3f}" if r['mean_stability'] else "  — "
        test = "yes" if r["is_test"] else "—"
        ts   = (r["logged_at"] or "")[:16]
        print(f"{r['run_id']:<32}  {r['run_hash']:<18}  {r['k']:>2}  "
              f"{r['n_books']:>5}  {stab:>5}  {test:>4}  {r['n_sessions']:>8}  {ts}")
    print()


def cmd_list_classes(db_path: Path):
    con = open_db(db_path)
    rows = con.execute(
        """SELECT ec.run_hash, ec.k, ec.n_books, ec.pipeline_mode, ec.seeds_json,
                  ec.first_seen_at,
                  COUNT(r.run_id)          AS n_runs,
                  SUM(r.is_test)           AS n_test,
                  COUNT(r.run_id) - SUM(r.is_test) AS n_canonical
           FROM equivalence_classes ec
           LEFT JOIN pipeline_runs r ON r.run_hash = ec.run_hash
           GROUP BY ec.run_hash
           ORDER BY ec.first_seen_at DESC"""
    ).fetchall()
    con.close()
    if not rows:
        print("No equivalence classes yet.")
        return
    print(f"\n{'Hash':<18}  {'k':>2}  {'books':>5}  {'mode':<12}  "
          f"{'runs':>5}  {'canonical':>9}  {'first seen'}")
    print("─" * 80)
    for r in rows:
        ts = (r["first_seen_at"] or "")[:10]
        print(f"{r['run_hash']:<18}  {r['k']:>2}  {r['n_books']:>5}  "
              f"{(r['pipeline_mode'] or '—'):<12}  {r['n_runs']:>5}  "
              f"{r['n_canonical']:>9}  {ts}")
    print()


def cmd_show(run_id: str, db_path: Path):
    con = open_db(db_path)
    r = con.execute(
        "SELECT * FROM pipeline_runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    if not r:
        print(f"Run '{run_id}' not found.")
        con.close()
        return
    sessions = con.execute(
        """SELECT s.id, s.rater, s.session_at, COUNT(t.id) AS n_ratings
           FROM naming_sessions s
           LEFT JOIN topic_ratings t ON t.session_id = s.id
           WHERE s.run_id = ?
           GROUP BY s.id ORDER BY s.session_at""",
        (run_id,),
    ).fetchall()
    loglines = con.execute(
        "SELECT COUNT(*) AS n FROM runlog_entries WHERE run_id = ?", (run_id,)
    ).fetchone()["n"]
    con.close()

    print(f"\n{'─'*60}")
    print(f"  Run ID       : {r['run_id']}")
    print(f"  Run hash     : {r['run_hash']}")
    print(f"  NLP hash     : {r['nlp_hash'] or '(unknown — migrated run)'}")
    print(f"  Logged at    : {r['logged_at']}")
    print(f"  Git commit   : {r['git_commit'] or '—'}")
    print(f"  Is test      : {'yes' if r['is_test'] else 'no'}")
    print(f"  k            : {r['k']}")
    print(f"  n_books      : {r['n_books']}")
    print(f"  max_features : {r['max_features']}")
    print(f"  pipeline_mode: {r['pipeline_mode']}")
    print(f"  seeds_used   : {r['seeds_used']}")
    print(f"  mean_stab    : {r['mean_stability']}")
    print(f"  Runlog lines : {loglines}")
    print(f"  Notes        : {r['notes'] or '—'}")
    if sessions:
        print(f"\n  Naming sessions ({len(sessions)}):")
        for s in sessions:
            print(f"    [{s['id']}] {s['rater']:<20} {s['session_at'][:19]}  "
                  f"({s['n_ratings']} topics)")
    else:
        print(f"\n  Naming sessions: none")
    topic_names = json.loads(r["topic_names"] or "[]")
    stab_scores = json.loads(r["stability_scores"] or "[]")
    if topic_names or stab_scores:
        print(f"\n  Topics at log time:")
        for i, (name, score) in enumerate(zip(
            topic_names or [f"T{i+1}" for i in range(len(stab_scores))],
            stab_scores or [None]*len(topic_names),
        )):
            score_str = f"{score:.3f}" if score is not None else "  — "
            print(f"    T{i+1}  {score_str}  {name}")
    print()


# ── Main log command ───────────────────────────────────────────────────────────

def cmd_log(args):
    nlp_path = args.nlp
    db_path  = args.db
    is_test  = args.test

    if not nlp_path.exists():
        print(f"ERROR: {nlp_path} not found. Run the pipeline first.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading {nlp_path} …")
    nlp      = load_nlp(nlp_path)
    nlp_hash = compute_file_hash(nlp_path)
    params   = extract_params(nlp)

    run_hash = compute_run_hash(
        params["k"], params["n_books"], params["max_features"],
        params["pipeline_mode"], params["seeds_used"],
    )

    con = open_db(db_path)

    # ── Check: is this nlp_results.json already logged? ───────────────────────
    existing = con.execute(
        "SELECT run_id, is_test FROM pipeline_runs WHERE nlp_hash = ?", (nlp_hash,)
    ).fetchone()
    if existing:
        con.close()
        tag = " (test run)" if existing["is_test"] else ""
        print(f"\nThis nlp_results.json is already logged as: {existing['run_id']}{tag}")
        print("Nothing to do.")
        return

    # ── Check equivalence class ────────────────────────────────────────────────
    existing_class = con.execute(
        "SELECT * FROM equivalence_classes WHERE run_hash = ?", (run_hash,)
    ).fetchone()
    is_new_class = existing_class is None

    if not is_new_class:
        sibling_runs = con.execute(
            "SELECT run_id, logged_at, is_test FROM pipeline_runs WHERE run_hash = ? ORDER BY logged_at",
            (run_hash,),
        ).fetchall()
    else:
        sibling_runs = []

    # ── Show summary ───────────────────────────────────────────────────────────
    print_run_summary(params, run_hash, nlp_hash, is_new_class)

    if not is_new_class:
        print(f"  Existing runs in this equivalence class ({len(sibling_runs)}):")
        for s in sibling_runs:
            tag = " [test]" if s["is_test"] else ""
            print(f"    {s['run_id']}{tag}  (logged {s['logged_at'][:10]})")
        print()

    if is_test:
        print("  ⚠  This will be logged as a TEST RUN (survey-ineligible).")
        print()

    # ── Run ID ────────────────────────────────────────────────────────────────
    auto_id = make_run_id(nlp, is_test)
    if args.run_id:
        run_id = args.run_id
    elif args.yes:
        run_id = auto_id
    else:
        prompt = f"  Run ID [{auto_id}]: "
        entered = input(prompt).strip()
        run_id = entered if entered else auto_id

    # Check run_id uniqueness
    id_conflict = con.execute(
        "SELECT run_id FROM pipeline_runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    if id_conflict:
        print(f"ERROR: run_id '{run_id}' already exists in pipeline_runs.", file=sys.stderr)
        con.close()
        sys.exit(1)

    # ── Notes ─────────────────────────────────────────────────────────────────
    if args.notes is not None:
        notes = args.notes
    elif args.yes:
        notes = ""
    else:
        notes = input("  Notes (optional): ").strip()

    # ── Confirmation ──────────────────────────────────────────────────────────
    if not args.yes:
        print()
        confirm = input(f"  Log run '{run_id}'? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            con.close()
            return

    # ── Find runlog CSV ───────────────────────────────────────────────────────
    runlog_path = args.runlog
    if runlog_path is None:
        runlog_path = latest_runlog(BASE_DIR / "data" / "outputs")
        if runlog_path:
            print(f"\n  Auto-detected runlog: {runlog_path.name}")
        else:
            print("\n  No runlog CSV found — skipping runlog ingestion.")
    elif not runlog_path.exists():
        print(f"  WARNING: {runlog_path} not found — skipping runlog ingestion.")
        runlog_path = None

    now_iso   = datetime.now(timezone.utc).isoformat()
    git_commit = get_git_commit(BASE_DIR)

    # ── Write to DB ───────────────────────────────────────────────────────────
    # 1. Equivalence class
    if is_new_class:
        con.execute(
            """INSERT INTO equivalence_classes
               (run_hash, k, n_books, max_features, pipeline_mode, seeds_json, first_seen_at, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_hash, params["k"], params["n_books"],
                params["max_features"], params["pipeline_mode"],
                json.dumps(sorted(int(s) for s in params["seeds_used"])),
                now_iso, "",
            ),
        )

    # 2. Pipeline run
    con.execute(
        """INSERT INTO pipeline_runs
           (run_id, run_hash, nlp_hash, logged_at, git_commit, is_test,
            k, n_books, max_features, pipeline_mode, seeds_used,
            mean_stability, stability_scores, topic_names, lda_params,
            runlog_path, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            run_id, run_hash, nlp_hash, now_iso, git_commit,
            1 if is_test else 0,
            params["k"], params["n_books"], params["max_features"],
            params["pipeline_mode"],
            json.dumps(sorted(int(s) for s in params["seeds_used"])),
            params["mean_stability"],
            json.dumps(params["stability_scores"]),
            json.dumps(params["topic_names"]),
            json.dumps(params["lda_params"]),
            str(runlog_path) if runlog_path else None,
            notes or None,
        ),
    )

    # 3. Ingest runlog
    log_count = 0
    if runlog_path:
        log_count = ingest_runlog(con, run_id, runlog_path)

    con.commit()
    con.close()

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n✓ Run logged: {run_id}")
    if is_new_class:
        print(f"  New equivalence class: {run_hash}")
    else:
        print(f"  Equivalence class:     {run_hash}  ({len(sibling_runs)+1} runs total)")
    if log_count:
        print(f"  Runlog lines ingested: {log_count}")
    print()
    if is_test:
        print("  ⚠  Logged as TEST RUN — not eligible for survey.")
    else:
        print("  To create a Google Form for this run:")
        print(f"    python src/generate_google_form.py")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--nlp",     type=Path, default=NLP_PATH,
                   help="Path to nlp_results.json")
    p.add_argument("--db",      type=Path, default=DB_PATH,
                   help="Path to pipeline.db")
    p.add_argument("--runlog",  type=Path, default=None,
                   help="Runlog CSV to ingest (default: auto-detect latest)")
    p.add_argument("--run-id",  default=None, dest="run_id",
                   help="Override auto-generated run ID")
    p.add_argument("--notes",   default=None,
                   help="Annotation for this run (skips interactive prompt)")
    p.add_argument("--test",    action="store_true",
                   help="Log as test run (survey-ineligible)")
    p.add_argument("--yes",     action="store_true",
                   help="Skip confirmation prompts (use defaults)")
    p.add_argument("--list",    action="store_true",
                   help="List all logged runs and exit")
    p.add_argument("--list-classes", action="store_true",
                   help="List equivalence classes and exit")
    p.add_argument("--show",    default=None, metavar="RUN_ID",
                   help="Show full detail for a run and exit")
    args = p.parse_args()

    if args.list:
        cmd_list(args.db)
    elif args.list_classes:
        cmd_list_classes(args.db)
    elif args.show:
        cmd_show(args.show, args.db)
    else:
        cmd_log(args)


if __name__ == "__main__":
    main()
