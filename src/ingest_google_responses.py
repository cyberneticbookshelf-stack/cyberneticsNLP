#!/usr/bin/env python3
"""
ingest_google_responses.py — Fetch Google Form responses into pipeline.db.

Reads form configuration from data/pipeline.db (written by generate_google_form.py),
fetches all current responses via the Google Forms API, and inserts new submissions
into naming_sessions + topic_ratings.  Duplicate-safe: responses already ingested
(tracked by Google response ID in google_form_responses) are silently skipped.

Can be run repeatedly — it is fully idempotent.

Usage:
    python src/ingest_google_responses.py               # ingest from newest form
    python src/ingest_google_responses.py --form FORM_ID
    python src/ingest_google_responses.py --run  RUN_ID  # form for a specific run
    python src/ingest_google_responses.py --dry-run     # preview without writing
    python src/ingest_google_responses.py --list-forms  # show all forms in DB

Requirements:
    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib --break-system-packages
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_db import DB_PATH, open_db

BASE_DIR   = Path(__file__).resolve().parent.parent
CREDS_PATH = BASE_DIR / "credentials.json"
TOKEN_PATH = BASE_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive.file",
]


# ── Auth ───────────────────────────────────────────────────────────────────────

def get_credentials():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from urllib.parse import urlparse, parse_qs

    creds = None
    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception:
            creds = None

    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
            return creds
        except Exception:
            pass

    # Headless OAuth via SSH port forwarding — same as generate_google_form.py.
    # token.json is shared between both scripts (same SCOPES).
    # On the browser machine run:  ssh -L 8085:localhost:8085 <user>@<nlp-host> -N
    flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
    print("\n" + "─" * 62)
    print("  Google authorisation required (one-time).")
    print("  Open an SSH tunnel from a machine with a browser:")
    print("    ssh -L 8085:localhost:8085 <user>@<nlp-host> -N")
    print("  Then open  http://localhost:8085  in that browser.")
    print("─" * 62 + "\n")
    creds = flow.run_local_server(port=8085, open_browser=False)
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    print(f"  token.json saved → {TOKEN_PATH}")
    return creds


# ── Form config lookup ─────────────────────────────────────────────────────────

def get_form_config(con, form_id: str = None, run_id: str = None):
    """
    Return the google_form_configs row to ingest from.
    If neither form_id nor run_id is given, uses the most recently created form.
    """
    if form_id:
        row = con.execute(
            "SELECT * FROM google_form_configs WHERE form_id = ?", (form_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"Form '{form_id}' not found in pipeline.db.")
        return row
    if run_id:
        rows = con.execute(
            "SELECT * FROM google_form_configs WHERE run_id = ? ORDER BY created_at DESC",
            (run_id,),
        ).fetchall()
        if not rows:
            raise ValueError(
                f"No form found for run '{run_id}'. "
                "Create one with: python src/generate_google_form.py"
            )
        if len(rows) > 1:
            print(f"  Note: {len(rows)} forms exist for run '{run_id}'; "
                  f"using most recent ({rows[0]['form_id']}).")
        return rows[0]
    # Default: most recently created form
    row = con.execute(
        "SELECT * FROM google_form_configs ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    if not row:
        raise ValueError(
            "No forms found in pipeline.db. "
            "Create one with: python src/generate_google_form.py"
        )
    return row


def cmd_list_forms(db_path: Path):
    con = open_db(db_path)
    rows = con.execute(
        """SELECT gc.form_id, gc.run_id, gc.created_at, gc.share_url,
                  COUNT(gfr.response_id) AS ingested
           FROM google_form_configs gc
           LEFT JOIN google_form_responses gfr
                  ON gfr.session_id IN (
                      SELECT id FROM naming_sessions WHERE run_id = gc.run_id
                  )
           GROUP BY gc.form_id
           ORDER BY gc.created_at DESC"""
    ).fetchall()
    con.close()
    if not rows:
        print("No forms in pipeline.db.")
        return
    print(f"\n{'Form ID':<36}  {'Run ID':<30}  {'Created':<16}  {'Ingested':>8}")
    print("─" * 96)
    for r in rows:
        ts = (r["created_at"] or "")[:16]
        print(f"{r['form_id']:<36}  {r['run_id']:<30}  {ts:<16}  {r['ingested']:>8}")
    print()


# ── API calls ──────────────────────────────────────────────────────────────────

def fetch_responses(service, form_id: str) -> list:
    """Fetch all responses, handling pagination."""
    responses  = []
    page_token = None
    while True:
        kwargs = {"formId": form_id}
        if page_token:
            kwargs["pageToken"] = page_token
        result     = service.forms().responses().list(**kwargs).execute()
        responses += result.get("responses", [])
        page_token = result.get("nextPageToken")
        if not page_token:
            break
    return responses


# ── Response parsing ───────────────────────────────────────────────────────────

def parse_response(response: dict, config_row) -> dict | None:
    """
    Parse a raw Google Form response dict into a DB-ready structure.
    Returns None if unparseable (e.g. no rater name).
    """
    qmap        = json.loads(config_row["question_id_map"] or "{}")
    topic_meta  = json.loads(config_row["topic_meta"]      or "[]")
    n_topics    = len(topic_meta)
    answers     = response.get("answers", {})
    response_id = response.get("responseId")
    submitted   = response.get("lastSubmittedTime",
                               datetime.now(timezone.utc).isoformat())

    def get_answer(field: str, default: str = "") -> str:
        qid  = qmap.get(field)
        if not qid or qid not in answers:
            return default
        vals = answers[qid].get("textAnswers", {}).get("answers", [])
        return vals[0].get("value", default) if vals else default

    rater = get_answer("rater").strip()
    if not rater:
        return None

    topics = []
    for t_idx in range(n_topics):
        meta  = topic_meta[t_idx] if t_idx < len(topic_meta) else {}
        name  = get_answer(f"topic_{t_idx}_name").strip()
        conf  = get_answer(f"topic_{t_idx}_confidence", "medium").strip().lower()
        notes = get_answer(f"topic_{t_idx}_notes").strip()
        if conf not in ("high", "medium", "low"):
            conf = "medium"
        topics.append({
            "topic_idx":       t_idx,
            "topic_label":     f"T{t_idx + 1}",
            "proposed_name":   name or "(no answer)",
            "confidence":      conf,
            "notes":           notes,
            "stability_score": meta.get("stability_score", 0.0),
            "top_words":       json.dumps(meta.get("top_words", [])),
            "top_books":       json.dumps(meta.get("top_books", [])),
        })

    return {
        "response_id":   response_id,
        "rater":         rater,
        "session_at":    submitted,
        "session_notes": get_answer("session_notes").strip(),
        "topics":        topics,
    }


# ── DB insertion ───────────────────────────────────────────────────────────────

def ingest_response(con, parsed: dict, run_id: str, dry_run: bool) -> str:
    """
    Insert one parsed response.
    Returns 'inserted', 'duplicate', 'would_insert', or 'error: <msg>'.
    """
    response_id = parsed["response_id"]

    existing = con.execute(
        "SELECT response_id FROM google_form_responses WHERE response_id = ?",
        (response_id,),
    ).fetchone()
    if existing:
        return "duplicate"
    if dry_run:
        return "would_insert"

    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        cur = con.execute(
            """INSERT INTO naming_sessions
               (run_id, rater, session_at, session_notes, is_test)
               VALUES (?, ?, ?, ?, 0)""",
            (run_id, parsed["rater"], parsed["session_at"], parsed["session_notes"]),
        )
        session_id = cur.lastrowid

        for t in parsed["topics"]:
            con.execute(
                """INSERT INTO topic_ratings
                   (session_id, topic_idx, topic_label, proposed_name,
                    confidence, notes, stability_score, top_words, top_books)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    t["topic_idx"], t["topic_label"], t["proposed_name"],
                    t["confidence"], t["notes"], t["stability_score"],
                    t["top_words"], t["top_books"],
                ),
            )

        con.execute(
            "INSERT INTO google_form_responses (response_id, session_id, ingested_at) "
            "VALUES (?, ?, ?)",
            (response_id, session_id, now_iso),
        )
        con.commit()
        return "inserted"

    except Exception as exc:
        con.rollback()
        return f"error: {exc}"


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--db",         type=Path, default=DB_PATH,
                   help="Path to pipeline.db")
    p.add_argument("--form",       default=None, metavar="FORM_ID",
                   help="Google Form ID to ingest from")
    p.add_argument("--run",        default=None, metavar="RUN_ID",
                   help="Ingest from the form associated with this run")
    p.add_argument("--dry-run",    action="store_true",
                   help="Fetch and parse without writing to DB")
    p.add_argument("--list-forms", action="store_true",
                   help="List all forms stored in pipeline.db and exit")
    args = p.parse_args()

    if args.list_forms:
        cmd_list_forms(args.db)
        return

    if not CREDS_PATH.exists():
        print(f"ERROR: credentials.json not found at {CREDS_PATH}.", file=sys.stderr)
        sys.exit(1)
    try:
        from googleapiclient.discovery import build  # noqa: F401
    except ImportError:
        print("ERROR: google-api-python-client not installed.\n"
              "Run:  pip install google-api-python-client google-auth-httplib2 "
              "google-auth-oauthlib --break-system-packages", file=sys.stderr)
        sys.exit(1)
    from googleapiclient.discovery import build

    # ── Load form config from DB ───────────────────────────────────────────────
    con = open_db(args.db)
    try:
        config_row = get_form_config(con, form_id=args.form, run_id=args.run)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        con.close()
        sys.exit(1)

    form_id = config_row["form_id"]
    run_id  = config_row["run_id"]
    print(f"Form ID  : {form_id}")
    print(f"Run ID   : {run_id}")
    print(f"Database : {args.db}")
    if args.dry_run:
        print("  ⚠  DRY RUN — nothing will be written")
    print()

    # ── Fetch responses ────────────────────────────────────────────────────────
    print("Authenticating with Google…")
    creds   = get_credentials()
    service = build("forms", "v1", credentials=creds)

    print("Fetching responses…")
    raw_responses = fetch_responses(service, form_id)
    print(f"  {len(raw_responses)} response(s) found on Google Forms")
    if not raw_responses:
        print("Nothing to ingest.")
        con.close()
        return

    # ── Ingest ────────────────────────────────────────────────────────────────
    counts = {"inserted": 0, "duplicate": 0, "would_insert": 0,
              "unparseable": 0, "error": 0}

    for resp in raw_responses:
        rid    = resp.get("responseId", "?")
        parsed = parse_response(resp, config_row)
        if parsed is None:
            print(f"  ⚠  {rid[:12]}… — no rater name, skipping")
            counts["unparseable"] += 1
            continue

        status = ingest_response(con, parsed, run_id, args.dry_run)
        short  = rid[:12] + "…"

        if status == "inserted":
            print(f"  ✓ Inserted  — {parsed['rater']:<20} ({len(parsed['topics'])} topics)"
                  f"  [{short}]")
            counts["inserted"] += 1
        elif status == "duplicate":
            print(f"  —  Duplicate — {parsed['rater']:<20}  [{short}]  (skipped)")
            counts["duplicate"] += 1
        elif status == "would_insert":
            print(f"  ·  Would ins — {parsed['rater']:<20} ({len(parsed['topics'])} topics)"
                  f"  [{short}]")
            counts["would_insert"] += 1
        else:
            print(f"  ✗  Error    — {status}  [{short}]")
            counts["error"] += 1

    con.close()
    print()
    if args.dry_run:
        print(f"Dry run — {counts['would_insert']} would be inserted, "
              f"{counts['duplicate']} already in DB, {counts['unparseable']} unparseable.")
    else:
        print(f"Done — {counts['inserted']} inserted, {counts['duplicate']} duplicate(s), "
              f"{counts['unparseable']} unparseable, {counts['error']} error(s).")


if __name__ == "__main__":
    main()
