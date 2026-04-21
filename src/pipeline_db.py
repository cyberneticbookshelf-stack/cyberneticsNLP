"""
pipeline_db.py — Shared database module for CyberneticsNLP pipeline.

All scripts that read or write pipeline.db import from here:
    from pipeline_db import DB_PATH, open_db, compute_file_hash, compute_run_hash

Database: data/pipeline.db
"""

import hashlib
import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / "data" / "pipeline.db"


# ══════════════════════════════════════════════════════════════════════════════
# Schema
# ══════════════════════════════════════════════════════════════════════════════

SCHEMA = """
-- ── Equivalence classes ───────────────────────────────────────────────────────
-- One row per unique combination of input parameters.
-- Two runs with the same run_hash are equivalent up to topic reordering.
-- Created automatically by log_pipeline_run.py on first encounter.
CREATE TABLE IF NOT EXISTS equivalence_classes (
    run_hash        TEXT PRIMARY KEY,
    k               INTEGER NOT NULL,
    n_books         INTEGER NOT NULL,
    max_features    INTEGER,
    pipeline_mode   TEXT,
    seeds_json      TEXT,           -- JSON array of sorted seed ints
    first_seen_at   TEXT NOT NULL,
    notes           TEXT
);

-- ── Pipeline runs ─────────────────────────────────────────────────────────────
-- One row per manually logged canonical (or test) pipeline run.
-- Populated by log_pipeline_run.py, never by survey scripts.
-- Surveys require a matching pipeline_runs row to exist first.
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id          TEXT PRIMARY KEY,
    run_hash        TEXT NOT NULL REFERENCES equivalence_classes(run_hash),
    nlp_hash        TEXT NOT NULL,   -- SHA-256 prefix of nlp_results.json at log time
    logged_at       TEXT NOT NULL,
    git_commit      TEXT,
    is_test         INTEGER NOT NULL DEFAULT 0,  -- 1 = test run, survey-ineligible
    k               INTEGER NOT NULL,
    n_books         INTEGER NOT NULL,
    max_features    INTEGER,
    pipeline_mode   TEXT,
    seeds_used      TEXT,            -- JSON array
    mean_stability  REAL,
    stability_scores TEXT,           -- JSON array
    topic_names     TEXT,            -- JSON array of provisional names at log time
    lda_params      TEXT,            -- full JSON blob for reproducibility
    runlog_path     TEXT,            -- original CSV path (may be NULL if ingested to DB)
    notes           TEXT
);

-- ── Runlog entries ────────────────────────────────────────────────────────────
-- Stores pipeline stdout/stderr lines, replacing per-run CSV files.
CREATE TABLE IF NOT EXISTS runlog_entries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT NOT NULL REFERENCES pipeline_runs(run_id),
    line_num        INTEGER NOT NULL,
    content         TEXT NOT NULL
);

-- ── Naming sessions ───────────────────────────────────────────────────────────
-- One row per rater × pipeline run.
CREATE TABLE IF NOT EXISTS naming_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT NOT NULL REFERENCES pipeline_runs(run_id),
    rater           TEXT NOT NULL,
    session_at      TEXT NOT NULL,   -- ISO-8601 UTC
    session_notes   TEXT,
    is_test         INTEGER NOT NULL DEFAULT 0
);

-- ── Topic ratings ─────────────────────────────────────────────────────────────
-- One row per topic per naming session.
CREATE TABLE IF NOT EXISTS topic_ratings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER NOT NULL REFERENCES naming_sessions(id),
    topic_idx       INTEGER NOT NULL,   -- 0-based
    topic_label     TEXT    NOT NULL,   -- "T1" … "T9"
    proposed_name   TEXT    NOT NULL,
    confidence      TEXT    CHECK(confidence IN ('high','medium','low','')),
    notes           TEXT,
    stability_score REAL,
    top_words       TEXT,               -- JSON array
    top_books       TEXT                -- JSON array
);

-- ── Google Form configurations ────────────────────────────────────────────────
-- One row per created Google Form.  A form is always tied to a specific run.
CREATE TABLE IF NOT EXISTS google_form_configs (
    form_id         TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL REFERENCES pipeline_runs(run_id),
    created_at      TEXT NOT NULL,
    share_url       TEXT,
    question_id_map TEXT,   -- JSON: field_name → question_id
    topic_meta      TEXT    -- JSON array of per-topic metadata snapshots
);

-- ── Google Form response deduplication ────────────────────────────────────────
-- Tracks ingested Google Form response IDs to prevent double-counting.
CREATE TABLE IF NOT EXISTS google_form_responses (
    response_id     TEXT PRIMARY KEY,
    session_id      INTEGER REFERENCES naming_sessions(id),
    ingested_at     TEXT NOT NULL
);

-- ── Indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_runs_hash        ON pipeline_runs(run_hash);
CREATE INDEX IF NOT EXISTS idx_runs_nlp_hash    ON pipeline_runs(nlp_hash);
CREATE INDEX IF NOT EXISTS idx_runs_is_test     ON pipeline_runs(is_test);
CREATE INDEX IF NOT EXISTS idx_sessions_run     ON naming_sessions(run_id);
CREATE INDEX IF NOT EXISTS idx_ratings_sess     ON topic_ratings(session_id);
CREATE INDEX IF NOT EXISTS idx_ratings_topic    ON topic_ratings(topic_idx);
CREATE INDEX IF NOT EXISTS idx_runlog_run       ON runlog_entries(run_id);
CREATE INDEX IF NOT EXISTS idx_gform_run        ON google_form_configs(run_id);
"""


# ══════════════════════════════════════════════════════════════════════════════
# DB connection
# ══════════════════════════════════════════════════════════════════════════════

def open_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Open (and initialise) pipeline.db.  Returns a connection with row_factory set."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    con.commit()
    return con


# ══════════════════════════════════════════════════════════════════════════════
# Hashing helpers
# ══════════════════════════════════════════════════════════════════════════════

def compute_file_hash(path: Path, prefix_len: int = 16) -> str:
    """SHA-256 of file contents, truncated to prefix_len hex chars."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65_536), b""):
            h.update(chunk)
    return h.hexdigest()[:prefix_len]


def compute_run_hash(
    k: int,
    n_books: int,
    max_features,
    pipeline_mode: str,
    seeds_used: list,
    prefix_len: int = 16,
) -> str:
    """
    Stable hash of the input parameters that define an equivalence class.
    Two runs with the same run_hash are equivalent up to topic reordering.
    """
    params = {
        "k":             int(k),
        "n_books":       int(n_books),
        "max_features":  int(max_features) if max_features is not None else None,
        "pipeline_mode": str(pipeline_mode) if pipeline_mode else None,
        "seeds_used":    sorted(int(s) for s in seeds_used),
    }
    canonical = json.dumps(params, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:prefix_len]


# ══════════════════════════════════════════════════════════════════════════════
# Convenience lookup
# ══════════════════════════════════════════════════════════════════════════════

def find_run_by_nlp_hash(nlp_hash: str, db_path: Path = DB_PATH):
    """
    Return the pipeline_runs row whose nlp_hash matches, or None.
    Raises ValueError if multiple rows match (shouldn't happen).
    """
    con = open_db(db_path)
    rows = con.execute(
        "SELECT * FROM pipeline_runs WHERE nlp_hash = ?", (nlp_hash,)
    ).fetchall()
    con.close()
    if len(rows) > 1:
        raise ValueError(f"Multiple runs with nlp_hash={nlp_hash}: {[r['run_id'] for r in rows]}")
    return rows[0] if rows else None
