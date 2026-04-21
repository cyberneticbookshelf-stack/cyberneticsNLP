#!/usr/bin/env python3
"""
generate_google_form.py — Create a Google Form for CyberneticsNLP topic naming.

Reads topic data from nlp_results.json and creates a Google Form populated with
per-topic keywords, stability scores, and top books.  Form config (form_id,
question mapping, topic metadata) is stored in data/pipeline.db so that
ingest_google_responses.py can retrieve it without a separate JSON file.

Prerequisites:
  1. The current nlp_results.json must be logged in pipeline.db first:
       python src/log_pipeline_run.py
  2. credentials.json must be in the project root (~/CyberneticsNLP/).

Usage:
    python src/generate_google_form.py
    python src/generate_google_form.py --nlp json/nlp_results.json
    python src/generate_google_form.py --top 10       # top N books per topic
    python src/generate_google_form.py --force        # allow creating a second form for same run

Requirements (install once on the NLP machine):
    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib --break-system-packages

OAuth scopes (add all three to your Google Cloud consent screen):
    https://www.googleapis.com/auth/forms.body
    https://www.googleapis.com/auth/forms.responses.readonly
    https://www.googleapis.com/auth/drive.file
"""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_db import DB_PATH, open_db, compute_file_hash, find_run_by_nlp_hash

BASE_DIR   = Path(__file__).resolve().parent.parent
NLP_PATH   = BASE_DIR / "json" / "nlp_results.json"
CREDS_PATH = BASE_DIR / "credentials.json"
TOKEN_PATH = BASE_DIR / "token.json"
TOP_BOOKS  = 10

# Full scope set — shared with ingest_google_responses.py.
# Both scripts use the same token.json; scopes must agree.
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

    # Headless OAuth via SSH port forwarding.
    # On the browser machine run:  ssh -L 8085:localhost:8085 <user>@<nlp-host> -N
    # Then open http://localhost:8085 in the browser when prompted.
    # The local server on the NLP machine handles the callback automatically.
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


# ── Data helpers ───────────────────────────────────────────────────────────────

def load_nlp(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compute_top_books(nlp: dict, n_topics: int, top_n: int) -> list:
    doc_topic = nlp.get("doc_topic", [])
    titles    = nlp.get("titles",    [])
    authors   = nlp.get("authors",   [])
    book_ids  = nlp.get("book_ids",  [])
    pub_years = nlp.get("pub_years", [None] * len(titles))
    n_books   = len(doc_topic)
    result    = []
    for t_idx in range(n_topics):
        pairs = sorted(
            ((doc_topic[b][t_idx], b) for b in range(n_books)),
            reverse=True,
        )
        books = []
        for loading, b_idx in pairs[:top_n]:
            books.append({
                "id":      book_ids[b_idx] if b_idx < len(book_ids) else str(b_idx),
                "title":   titles[b_idx]   if b_idx < len(titles)   else "",
                "author":  authors[b_idx]  if b_idx < len(authors)  else "",
                "year":    pub_years[b_idx] if b_idx < len(pub_years) else None,
                "loading": round(loading, 4),
            })
        result.append(books)
    return result


def word_seed_counts(nlp: dict, t_idx: int) -> list:
    all_seeds = nlp.get("stability", {}).get("all_seed_words", [])
    c = Counter()
    for seed_data in all_seeds:
        if t_idx < len(seed_data):
            for w in seed_data[t_idx]:
                c[w] += 1
    return sorted(c.items(), key=lambda x: (-x[1], x[0]))


def format_topic_description(
    t_idx: int,
    canonical_words: list,
    stab_score: float,
    books: list,
    n_seeds: int,
    wc_pairs: list,
) -> str:
    """Plain-text description embedded in each Google Form topic section."""
    stable = [w for w, cnt in wc_pairs if cnt >= max(1, n_seeds - 1)][:12]
    lines  = [
        f"Stability score: {stab_score:.3f}",
        f"Top words (canonical): {', '.join(canonical_words[:12])}",
    ]
    if stable:
        lines.append(f"Stable core (≥{n_seeds-1}/{n_seeds} seeds): {', '.join(stable[:10])}")
    lines.append("")
    lines.append("Top books by loading:")
    for b in books[:8]:
        yr   = f" ({b['year']})" if b.get("year") else ""
        auth = f" — {b['author']}" if b.get("author") else ""
        lines.append(f"  {b['loading']:.3f}  {b['title']}{auth}{yr}")
    return "\n".join(lines)


# ── Form creation ──────────────────────────────────────────────────────────────

def create_form(service, run_row, nlp: dict, top_books_per_topic: list) -> tuple:
    """
    Create and populate the Google Form.
    Returns (updated_form_resource, question_id_map).
    """
    run_id      = run_row["run_id"]
    run_hash    = run_row["run_hash"]
    stab        = nlp.get("stability", {})
    n_topics    = nlp.get("n_topics", 9)
    n_seeds     = stab.get("n_seeds", 5)
    n_books     = len(nlp.get("doc_topic", []))
    mean_stab   = stab.get("mean_stability", 0.0)
    stab_scores = stab.get("stability_scores", [0.0] * n_topics)
    top_words   = nlp.get("top_words", [[] for _ in range(n_topics)])
    date_str    = datetime.now().strftime("%Y-%m-%d")

    # Step 1: Create empty form
    form = service.forms().create(body={
        "info": {
            "title":         f"CyberneticsNLP — Topic Naming ({date_str})",
            "documentTitle": f"CyberneticsNLP Topic Naming {run_id}",
        }
    }).execute()
    form_id = form["formId"]
    print(f"  Form created: {form_id}")

    # Step 2: Build batchUpdate requests
    requests  = []
    item_idx  = 0

    form_desc = (
        f"CyberneticsNLP topic naming session.\n"
        f"Run ID: {run_id}  ·  k={n_topics} topics  ·  {n_books} books  ·  "
        f"mean stability={mean_stab:.3f}\n"
        f"Equivalence class: {run_hash}\n\n"
        f"Instructions: For each topic, review the keywords and top books, then enter "
        f"a proposed name. All name fields are required. If you cannot name a topic, "
        f"enter a placeholder (e.g. 'Uncertain / review') and explain in the Notes field. "
        f"Names are provisional until confirmed across ≥3 runs and ≥2 independent raters."
    )
    requests.append({
        "updateFormInfo": {
            "info":       {"description": form_desc},
            "updateMask": "description",
        }
    })

    # Rater name
    requests.append({
        "createItem": {
            "item": {
                "title":       "Your name",
                "description": "Required. This identifies your submission in the database.",
                "questionItem": {"question": {"required": True,
                                              "textQuestion": {"paragraph": False}}},
            },
            "location": {"index": item_idx},
        }
    })
    item_idx += 1

    # Session notes
    requests.append({
        "createItem": {
            "item": {
                "title":       "Session notes (optional)",
                "description": "Overall notes — run conditions, uncertainties, etc.",
                "questionItem": {"question": {"required": False,
                                              "textQuestion": {"paragraph": True}}},
            },
            "location": {"index": item_idx},
        }
    })
    item_idx += 1

    # Per-topic questions
    for t_idx in range(n_topics):
        label  = f"T{t_idx + 1}"
        score  = stab_scores[t_idx] if t_idx < len(stab_scores) else 0.0
        words  = top_words[t_idx]   if t_idx < len(top_words)   else []
        books  = top_books_per_topic[t_idx] if t_idx < len(top_books_per_topic) else []
        wc     = word_seed_counts(nlp, t_idx)
        desc   = format_topic_description(t_idx, words, score, books, n_seeds, wc)

        # Section header (textItem — no question ID)
        requests.append({
            "createItem": {
                "item": {
                    "title":    f"─── Topic {label} ───",
                    "description": desc,
                    "textItem": {},
                },
                "location": {"index": item_idx},
            }
        })
        item_idx += 1

        # Proposed name
        requests.append({
            "createItem": {
                "item": {
                    "title":       f"{label}: Proposed name",
                    "description": "Enter your proposed topic name.",
                    "questionItem": {"question": {"required": True,
                                                  "textQuestion": {"paragraph": False}}},
                },
                "location": {"index": item_idx},
            }
        })
        item_idx += 1

        # Confidence
        requests.append({
            "createItem": {
                "item": {
                    "title": f"{label}: Confidence",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type":    "RADIO",
                                "options": [{"value": "high"},
                                            {"value": "medium"},
                                            {"value": "low"}],
                            },
                        }
                    },
                },
                "location": {"index": item_idx},
            }
        })
        item_idx += 1

        # Notes
        requests.append({
            "createItem": {
                "item": {
                    "title":       f"{label}: Notes (optional)",
                    "description": "Observations, ambiguities, alternative names considered…",
                    "questionItem": {"question": {"required": False,
                                                  "textQuestion": {"paragraph": True}}},
                },
                "location": {"index": item_idx},
            }
        })
        item_idx += 1

    # Step 3: Execute batchUpdate
    print(f"  Adding {len(requests)} items via batchUpdate…")
    service.forms().batchUpdate(
        formId=form_id,
        body={"requests": requests},
    ).execute()

    # Step 4: Re-fetch form to read question IDs
    updated_form = service.forms().get(formId=form_id).execute()
    items        = updated_form.get("items", [])

    question_id_map = {}   # field_name → question_id
    for item in items:
        title = item.get("title", "")
        q     = item.get("questionItem", {}).get("question", {})
        qid   = q.get("questionId")
        if not qid:
            continue
        if title == "Your name":
            question_id_map["rater"] = qid
        elif title == "Session notes (optional)":
            question_id_map["session_notes"] = qid
        else:
            for t_idx in range(n_topics):
                lbl = f"T{t_idx + 1}"
                if title == f"{lbl}: Proposed name":
                    question_id_map[f"topic_{t_idx}_name"] = qid
                elif title == f"{lbl}: Confidence":
                    question_id_map[f"topic_{t_idx}_confidence"] = qid
                elif title == f"{lbl}: Notes (optional)":
                    question_id_map[f"topic_{t_idx}_notes"] = qid

    return updated_form, question_id_map


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--nlp",   type=Path, default=NLP_PATH,
                   help="Path to nlp_results.json")
    p.add_argument("--db",    type=Path, default=DB_PATH,
                   help="Path to pipeline.db")
    p.add_argument("--top",   type=int,  default=TOP_BOOKS,
                   help="Top books per topic to show (default 10)")
    p.add_argument("--force", action="store_true",
                   help="Allow creating a second form for the same run")
    args = p.parse_args()

    # ── Pre-flight checks ──────────────────────────────────────────────────────
    if not args.nlp.exists():
        print(f"ERROR: {args.nlp} not found. Run the pipeline first.", file=sys.stderr)
        sys.exit(1)
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

    # ── Verify nlp_results.json is logged ─────────────────────────────────────
    print(f"Loading {args.nlp} …")
    nlp      = load_nlp(args.nlp)
    nlp_hash = compute_file_hash(args.nlp)
    print(f"  nlp_hash: {nlp_hash}")

    run_row = find_run_by_nlp_hash(nlp_hash, args.db)
    if run_row is None:
        print(
            f"\nERROR: This nlp_results.json has not been logged in pipeline.db.\n"
            f"Log it first (after reviewing the run):\n"
            f"  python src/log_pipeline_run.py\n",
            file=sys.stderr,
        )
        sys.exit(1)

    if run_row["is_test"]:
        print(
            f"\nERROR: Run '{run_row['run_id']}' is a test run.\n"
            f"Google Forms cannot be created for test runs.\n"
            f"Re-run the pipeline without --test to produce a canonical run.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"  Run ID  : {run_row['run_id']}")
    print(f"  run_hash: {run_row['run_hash']}")

    # ── Check for existing form for this run ───────────────────────────────────
    con = open_db(args.db)
    existing_form = con.execute(
        "SELECT form_id, share_url, created_at FROM google_form_configs WHERE run_id = ?",
        (run_row["run_id"],),
    ).fetchone()
    con.close()

    if existing_form and not args.force:
        print(
            f"\nA form already exists for run '{run_row['run_id']}':\n"
            f"  Form ID  : {existing_form['form_id']}\n"
            f"  Share URL: {existing_form['share_url']}\n"
            f"  Created  : {existing_form['created_at'][:16]}\n\n"
            f"Use --force to create an additional form for this run.",
        )
        sys.exit(0)

    n_topics  = nlp.get("n_topics", 9)
    top_books = compute_top_books(nlp, n_topics, args.top)
    stab      = nlp.get("stability", {})
    print(f"  k={n_topics}  ·  {len(nlp.get('doc_topic', []))} books  ·  "
          f"mean stability={stab.get('mean_stability', 0):.3f}")

    # ── Auth + create form ─────────────────────────────────────────────────────
    print("\nAuthenticating with Google…")
    creds   = get_credentials()
    service = build("forms", "v1", credentials=creds)

    print("Creating form…")
    updated_form, question_id_map = create_form(service, run_row, nlp, top_books)

    form_id   = updated_form["formId"]
    share_url = updated_form.get("responderUri",
                                 f"https://docs.google.com/forms/d/{form_id}/viewform")

    # ── Verify question mapping completeness ───────────────────────────────────
    expected = (["rater", "session_notes"]
                + [f"topic_{t}_{f}" for t in range(n_topics)
                   for f in ("name", "confidence", "notes")])
    missing = [k for k in expected if k not in question_id_map]
    if missing:
        print(f"  ⚠  Warning: {len(missing)} question(s) not mapped: {missing[:5]}")

    # ── Build topic_meta snapshot for storage ─────────────────────────────────
    stab_scores = stab.get("stability_scores", [])
    top_words   = nlp.get("top_words", [])
    topic_meta  = [
        {
            "topic_idx":       t,
            "topic_label":     f"T{t + 1}",
            "stability_score": stab_scores[t] if t < len(stab_scores) else 0.0,
            "top_words":       top_words[t][:10] if t < len(top_words) else [],
            "top_books":       top_books[t] if t < len(top_books) else [],
        }
        for t in range(n_topics)
    ]

    # ── Store form config in DB ────────────────────────────────────────────────
    now_iso = datetime.now(timezone.utc).isoformat()
    con = open_db(args.db)
    con.execute(
        """INSERT INTO google_form_configs
           (form_id, run_id, created_at, share_url, question_id_map, topic_meta)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            form_id,
            run_row["run_id"],
            now_iso,
            share_url,
            json.dumps(question_id_map),
            json.dumps(topic_meta),
        ),
    )
    con.commit()
    con.close()

    # ── Done ───────────────────────────────────────────────────────────────────
    print(f"\n{'─' * 62}")
    print(f"  Form created successfully!")
    print(f"  Share URL : {share_url}")
    print(f"  Form ID   : {form_id}")
    print(f"  Run ID    : {run_row['run_id']}")
    print(f"  Class     : {run_row['run_hash']}")
    print(f"{'─' * 62}")
    print(f"\nNext steps:")
    print(f"  1. Open the URL above and check the form looks correct.")
    print(f"  2. Share the URL with raters.")
    print(f"  3. After raters submit, ingest responses with:")
    print(f"       python src/ingest_google_responses.py")
    print(f"  4. Preview without writing first:")
    print(f"       python src/ingest_google_responses.py --dry-run")


if __name__ == "__main__":
    main()
