#!/usr/bin/env python3
"""
migrate_pipeline_db.py — One-shot migration from topic_naming.db to pipeline.db.

Copies all existing data from data/topic_naming.db into the new data/pipeline.db
schema.  Safe to run multiple times (skips already-migrated rows).

What it does:
  1. Creates pipeline.db with the full schema (via pipeline_db.open_db).
  2. Ports the old `runs` table → `pipeline_runs`:
     - Extracts k, n_books, seeds_used, max_features, pipeline_mode from lda_params JSON.
     - Computes run_hash and creates equivalence_classes rows.
     - Sets nlp_hash to '' (unknown — the original nlp_results.json may have changed).
     - Sets is_test = 0 (all old runs assumed canonical).
  3. Copies naming_sessions and topic_ratings verbatim.
  4. Reports counts.

After migration:
  - Keep topic_naming.db as a backup until you've verified pipeline.db.
  - Update record_topic_run.py, generate_google_form.py, ingest_google_responses.py
    to use pipeline.db (handled by importing pipeline_db).

Usage:
    python src/migrate_pipeline_db.py
    python src/migrate_pipeline_db.py --old data/topic_naming.db --new data/pipeline.db
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running from project root or src/
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_db import (
    DB_PATH, open_db, compute_run_hash,
)

OLD_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "topic_naming.db"


def migrate(old_path: Path, new_path: Path, dry_run: bool = False):
    if not old_path.exists():
        print(f"ERROR: source database not found: {old_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Source : {old_path}")
    print(f"Target : {new_path}")
    if dry_run:
        print("  ⚠  DRY RUN — nothing will be written")
    print()

    # Open both databases
    old_con = sqlite3.connect(str(old_path))
    old_con.row_factory = sqlite3.Row
    new_con = open_db(new_path)

    now_iso = datetime.now(timezone.utc).isoformat()

    # ── 1. Migrate runs → pipeline_runs + equivalence_classes ─────────────────
    old_runs = old_con.execute("SELECT * FROM runs").fetchall()
    print(f"Old `runs` rows: {len(old_runs)}")

    runs_migrated = runs_skipped = 0
    classes_created = 0

    for r in old_runs:
        run_id = r["run_id"]

        # Skip if already in pipeline_runs
        existing = new_con.execute(
            "SELECT run_id FROM pipeline_runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        if existing:
            runs_skipped += 1
            continue

        # Extract params from lda_params JSON blob
        lda = {}
        try:
            lda = json.loads(r["lda_params"] or "{}")
        except Exception:
            pass

        k             = lda.get("n_topics") or r["n_topics"] or 9
        n_books       = lda.get("n_books_analysed") or r["n_books"] or 0
        max_features  = lda.get("max_features")
        pipeline_mode = lda.get("pipeline_mode")
        seeds_used    = lda.get("seeds_used") or []
        mean_stab     = lda.get("mean_stability") or r["mean_stability"]
        stab_scores   = lda.get("stability_scores")

        rh = compute_run_hash(k, n_books, max_features, pipeline_mode, seeds_used)

        if not dry_run:
            # Upsert equivalence_classes
            existing_class = new_con.execute(
                "SELECT run_hash FROM equivalence_classes WHERE run_hash = ?", (rh,)
            ).fetchone()
            if not existing_class:
                new_con.execute(
                    """INSERT INTO equivalence_classes
                       (run_hash, k, n_books, max_features, pipeline_mode, seeds_json, first_seen_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (rh, k, n_books, max_features, pipeline_mode,
                     json.dumps(sorted(int(s) for s in seeds_used)), now_iso),
                )
                classes_created += 1

            # Insert pipeline_runs row
            # nlp_hash is unknown for migrated runs (original file may have changed)
            new_con.execute(
                """INSERT OR IGNORE INTO pipeline_runs
                   (run_id, run_hash, nlp_hash, logged_at, git_commit, is_test,
                    k, n_books, max_features, pipeline_mode, seeds_used,
                    mean_stability, stability_scores, lda_params, notes)
                   VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id, rh,
                    "",          # nlp_hash unknown for migrated runs
                    r["recorded_at"] or now_iso,
                    r["git_commit"] or "",
                    k, n_books, max_features, pipeline_mode,
                    json.dumps(sorted(int(s) for s in seeds_used)),
                    mean_stab,
                    json.dumps(stab_scores) if stab_scores else None,
                    r["lda_params"],
                    r["notes"] or "Migrated from topic_naming.db",
                ),
            )
        runs_migrated += 1

    print(f"  pipeline_runs  : {runs_migrated} migrated, {runs_skipped} already present")
    print(f"  equivalence_classes : {classes_created} created")

    # ── 2. Migrate naming_sessions ─────────────────────────────────────────────
    old_sessions = old_con.execute("SELECT * FROM naming_sessions").fetchall()
    print(f"\nOld `naming_sessions` rows: {len(old_sessions)}")
    sess_migrated = sess_skipped = 0

    for s in old_sessions:
        existing = new_con.execute(
            "SELECT id FROM naming_sessions WHERE id = ?", (s["id"],)
        ).fetchone()
        if existing:
            sess_skipped += 1
            continue

        if not dry_run:
            new_con.execute(
                """INSERT OR IGNORE INTO naming_sessions
                   (id, run_id, rater, session_at, session_notes, is_test)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (s["id"], s["run_id"], s["rater"], s["session_at"],
                 s["session_notes"], s["is_test"]),
            )
        sess_migrated += 1

    print(f"  naming_sessions: {sess_migrated} migrated, {sess_skipped} already present")

    # ── 3. Migrate topic_ratings ───────────────────────────────────────────────
    old_ratings = old_con.execute("SELECT * FROM topic_ratings").fetchall()
    print(f"\nOld `topic_ratings` rows: {len(old_ratings)}")
    rat_migrated = rat_skipped = 0

    for t in old_ratings:
        existing = new_con.execute(
            "SELECT id FROM topic_ratings WHERE id = ?", (t["id"],)
        ).fetchone()
        if existing:
            rat_skipped += 1
            continue

        if not dry_run:
            new_con.execute(
                """INSERT OR IGNORE INTO topic_ratings
                   (id, session_id, topic_idx, topic_label, proposed_name,
                    confidence, notes, stability_score, top_words, top_books)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (t["id"], t["session_id"], t["topic_idx"], t["topic_label"],
                 t["proposed_name"], t["confidence"], t["notes"],
                 t["stability_score"], t["top_words"], t["top_books"]),
            )
        rat_migrated += 1

    print(f"  topic_ratings  : {rat_migrated} migrated, {rat_skipped} already present")

    # ── Commit ─────────────────────────────────────────────────────────────────
    if not dry_run:
        new_con.commit()
        print(f"\n✓ Migration complete → {new_path}")
        print()
        print("Next steps:")
        print("  1. Verify pipeline.db looks correct:")
        print("       python src/log_pipeline_run.py --list")
        print("  2. Keep topic_naming.db as backup until verified.")
        print("  3. Note: migrated pipeline_runs rows have nlp_hash='' (unknown).")
        print("     To enable Google Form creation, re-log those runs:")
        print("       python src/log_pipeline_run.py")
    else:
        print("\nDry run complete — no changes written.")

    old_con.close()
    new_con.close()


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--old",     type=Path, default=OLD_DB_PATH,
                   help=f"Source database (default: {OLD_DB_PATH})")
    p.add_argument("--new",     type=Path, default=DB_PATH,
                   help=f"Target database (default: {DB_PATH})")
    p.add_argument("--dry-run", action="store_true",
                   help="Parse and report without writing anything")
    args = p.parse_args()
    migrate(args.old, args.new, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
