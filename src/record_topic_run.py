#!/usr/bin/env python3
"""
record_topic_run.py — Interactive HTML form for naming LDA topics.

THREE MODES — choose based on how raters will access the form:

  1. SERVER MODE (default)
     Serves the form on localhost. Best when raters have SSH access to the NLP machine
     or when you expose the port via a tunnel.

     python src/record_topic_run.py                  # serve, write to DB
     python src/record_topic_run.py --test           # serve, do NOT write to DB
     python src/record_topic_run.py --port 8080      # custom port (default 7474)

     To share with remote raters, expose the port via a tunnel (e.g. ngrok):
       ngrok http 7474
     Share the printed URL. Submissions go straight into the DB.
     Stop the tunnel when the session is complete.

  2. OFFLINE FORM (--generate)
     Generates a single self-contained HTML file with all topic data embedded.
     Send the file to raters — they open it in any browser, fill in names, and
     click "Download JSON". They send the .json file back to you.
     No server, no network access, no accounts required.

     python src/record_topic_run.py --generate
     python src/record_topic_run.py --generate --out /path/to/naming_form.html

  3. INGEST (--ingest)
     Reads a JSON file returned by a rater from the offline form and inserts
     the naming session into the SQLite database on the NLP machine.

     python src/record_topic_run.py --ingest rater_response.json
     python src/record_topic_run.py --ingest *.json   # ingest multiple files

Other commands:
    python src/record_topic_run.py --query          # print recent sessions
    python src/record_topic_run.py --export json    # export all records as JSON
    python src/record_topic_run.py --export csv     # export all records as CSV

Options:
    --nlp       Path to nlp_results.json  (default: json/nlp_results.json)
    --db        Path to SQLite database   (default: data/topic_naming.db)
    --port      Port to serve on          (default: 7474)
    --top       Top books per topic to show (default: 10)
    --test      Test mode — form is live but nothing is written to the database
    --generate  Write a self-contained offline HTML form and exit
    --out       Output path for --generate (default: data/outputs/topic_naming_form_RUNID.html)
    --ingest    Path(s) to JSON file(s) returned by offline raters
    --query     Print recent naming sessions and exit
    --export    Export format: json or csv (writes to data/outputs/)
    --run-id    Override the auto-generated run ID

Database:
    Three tables (data/topic_naming.db):
      runs            — one row per pipeline run (full LDA params for audit)
      naming_sessions — one row per rater session (rater name, timestamp, notes)
      topic_ratings   — one row per topic per session (name, confidence, notes)

    All submissions are kept permanently. Use --query or --export to review.
"""

import argparse
import csv
import json
import os
import sqlite3
import subprocess
import sys
import urllib.parse
import webbrowser
from collections import Counter
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# ── Shared DB module ───────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline_db import DB_PATH, open_db, compute_file_hash

# ── Paths and defaults ─────────────────────────────────────────────────────────

BASE_DIR     = Path(__file__).resolve().parent.parent
NLP_PATH     = BASE_DIR / "json" / "nlp_results.json"
DEFAULT_PORT = 7474
TOP_BOOKS    = 10


# ══════════════════════════════════════════════════════════════════════════════
# Data loading and preparation
# ══════════════════════════════════════════════════════════════════════════════

def load_nlp(nlp_path: Path) -> dict:
    return json.loads(nlp_path.read_text(encoding="utf-8"))


def get_git_commit(repo_dir: Path) -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_dir), capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def compute_top_books(nlp: dict, n_topics: int, top_n: int) -> list:
    """
    Return list[list[dict]]: for each topic, the top_n books sorted by loading.
    Derived from the doc_topic matrix in nlp_results.json.
    """
    doc_topic = nlp.get("doc_topic", [])
    titles    = nlp.get("titles",    [])
    authors   = nlp.get("authors",   [])
    book_ids  = nlp.get("book_ids",  [])
    pub_years = nlp.get("pub_years", [None] * len(titles))
    n_books   = len(doc_topic)

    result = []
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


def word_seed_counts(nlp: dict, topic_idx: int) -> list:
    """
    For topic_idx, return [(word, count_across_seeds)] sorted by count desc
    then alphabetically. Used to show word stability within the current run.
    """
    all_seeds = nlp.get("stability", {}).get("all_seed_words", [])
    c = Counter()
    for seed_data in all_seeds:
        if topic_idx < len(seed_data):
            for w in seed_data[topic_idx]:
                c[w] += 1
    return sorted(c.items(), key=lambda x: (-x[1], x[0]))


def make_run_id(nlp: dict) -> str:
    stab = nlp.get("stability", {})
    k    = nlp.get("n_topics", "?")
    ns   = stab.get("n_seeds", "?")
    date = datetime.now().strftime("%Y%m%d")
    return f"run_{date}_k{k}_s{ns}"


def build_lda_params(nlp: dict) -> dict:
    """
    Extract the full reproducible parameter set from nlp_results.json.
    Stored as a JSON blob in runs.lda_params for audit purposes.
    """
    stab = nlp.get("stability", {})
    return {
        "n_topics":            nlp.get("n_topics"),
        "n_seeds":             stab.get("n_seeds"),
        "seeds_used":          stab.get("seeds_used"),
        "max_features":        nlp.get("max_features"),
        "pipeline_mode":       nlp.get("pipeline_mode"),
        "gpu_used":            nlp.get("gpu_used"),
        "n_books_analysed":    len(nlp.get("doc_topic", [])),
        "perplexities":        nlp.get("perplexities"),
        "coherences":          nlp.get("coherences"),
        "stability_thresholds": stab.get("thresholds"),
        "stability_scores":    stab.get("stability_scores"),
        "mean_stability":      stab.get("mean_stability"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# HTML / CSS
# ══════════════════════════════════════════════════════════════════════════════

CSS = """
:root {
  --bg:#f8f7f4; --surface:#fff; --border:#e2ddd8; --accent:#3a5a8c;
  --accent-light:#eef2f8; --warn:#b85c00; --warn-light:#fff4e8;
  --green:#2d6a4f; --green-light:#eef7f2; --red:#b00020; --red-light:#fdecea;
  --amber:#7a4f00; --amber-light:#fff8e6; --muted:#6b6560; --text:#1a1816;
  --test-bg:#6b0080;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: 13px; background: var(--bg); color: var(--text); line-height: 1.5;
}

/* ── Header ── */
.app-header {
  background: var(--accent); color: white; padding: 18px 32px 14px;
}
.app-header h1 { font-size: 17px; font-weight: 600; margin-bottom: 2px; }
.app-header .sub { font-size: 12px; opacity: 0.75; }

/* ── Test banner ── */
.test-banner {
  background: var(--test-bg); color: white; text-align: center;
  padding: 8px 16px; font-size: 13px; font-weight: 700; letter-spacing: .04em;
}

/* ── Run metadata strip ── */
.meta-strip {
  background: var(--surface); border-bottom: 2px solid var(--border);
  padding: 12px 32px; display: flex; flex-wrap: wrap; gap: 18px;
}
.meta-item { font-size: 12px; color: var(--muted); }
.meta-item strong { color: var(--text); }

/* ── Notice ── */
.notice {
  background: var(--warn-light); border: 1px solid #e8c97a; border-radius: 4px;
  margin: 14px 32px; padding: 10px 14px; font-size: 12px; color: var(--warn);
}

/* ── Session fields (rater, session notes) ── */
.session-section {
  background: var(--surface); border-bottom: 1px solid var(--border);
  padding: 16px 32px; display: flex; gap: 20px; flex-wrap: wrap; align-items: flex-end;
}
.field-group { display: flex; flex-direction: column; gap: 5px; }
.field-group label {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .05em; color: var(--muted);
}
.field-group input, .field-group textarea {
  border: 1px solid var(--border); border-radius: 4px; padding: 7px 10px;
  font-size: 13px; font-family: inherit; background: white; color: var(--text);
  transition: border-color .15s;
}
.field-group input:focus, .field-group textarea:focus {
  outline: none; border-color: var(--accent);
}
.rater-input  { width: 220px; }
.session-notes { width: 380px; height: 52px; resize: vertical; }
.required { color: var(--red); }

/* ── Topic cards ── */
.topics-section { padding: 24px 32px; }
.topic-card {
  border: 1px solid var(--border); border-radius: 6px; overflow: hidden;
  background: var(--surface); margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.topic-hdr {
  display: flex; align-items: center; gap: 10px; padding: 10px 14px;
  background: var(--accent-light); border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}
.tid {
  font-size: 11px; font-weight: 700; color: var(--accent); background: white;
  border: 1px solid #c5d4e8; border-radius: 3px; padding: 2px 9px; white-space: nowrap;
}
.stab-score { font-size: 12px; color: var(--muted); }

/* Badges */
.badge {
  display: inline-block; padding: 2px 8px; border-radius: 3px;
  font-size: 10.5px; font-weight: 700;
}
.b-green  { background: var(--green-light);  color: var(--green); }
.b-amber  { background: var(--amber-light);  color: var(--amber); }
.b-red    { background: var(--red-light);    color: var(--red);   }
.b-grey   { background: #f0f0f0;             color: var(--muted); }

/* ── Two-column body (words | books) ── */
.topic-body {
  display: grid; grid-template-columns: 1fr 1fr; gap: 0;
  border-bottom: 1px solid var(--border);
}
.col-words { padding: 14px 16px; border-right: 1px solid var(--border); }
.col-books { padding: 14px 16px; }
.col-label {
  font-size: 11px; font-weight: 700; color: var(--muted);
  text-transform: uppercase; letter-spacing: .05em; margin-bottom: 8px;
}

/* Word chips */
.word-chips { display: flex; flex-wrap: wrap; gap: 4px; }
.wchip {
  display: flex; align-items: center; gap: 3px; padding: 3px 7px;
  border-radius: 3px; font-size: 11.5px; border: 1px solid transparent;
}
.wchip .wct {
  font-size: 9.5px; font-weight: 700; padding: 1px 4px;
  border-radius: 2px; min-width: 22px; text-align: center;
}
.w-all  { background: var(--green-light); border-color: #a8d5b8; }
.w-most { background: #f1f8f2;            border-color: #c8e6c9; }
.w-some { background: #fffde7;            border-color: #f9e4a0; }
.w-one  { background: #f8f7f4;            border-color: #ddd; color: var(--muted); }
.wct-all  { background: var(--green); color: white; }
.wct-most { background: #c8e6c9; color: #1b5e20; }
.wct-some { background: #fff9c4; color: #6d4c00; }
.wct-one  { background: #ddd;    color: #888;    }
.word-legend { font-size: 10.5px; color: var(--muted); margin-top: 7px; }

/* Books table */
table.books { width: 100%; border-collapse: collapse; font-size: 11.5px; }
table.books th {
  text-align: left; padding: 4px 8px; font-weight: 600; font-size: 10.5px;
  color: var(--muted); border-bottom: 1px solid var(--border);
}
table.books td {
  padding: 5px 8px; border-bottom: 1px solid #f0eeeb; vertical-align: top;
}
table.books tr:last-child td { border-bottom: none; }
.load-badge {
  display: inline-block; padding: 1px 5px; border-radius: 2px;
  font-size: 10px; font-weight: 700;
  background: var(--accent-light); color: var(--accent);
  white-space: nowrap;
}
.bk-author { font-size: 10.5px; color: var(--muted); }

/* ── Naming row (name input + confidence + notes) ── */
.naming-row {
  padding: 14px 16px; display: flex; gap: 14px;
  align-items: flex-start; flex-wrap: wrap;
}
.name-wrap label {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .05em; color: var(--muted); display: block; margin-bottom: 5px;
}
.name-input {
  width: 300px; border: 1px solid var(--border); border-radius: 4px;
  padding: 8px 10px; font-size: 14px; font-weight: 500; font-family: inherit;
  color: var(--text); background: white; transition: border-color .15s;
}
.name-input:focus { outline: none; border-color: var(--accent); }
.name-input.error { border-color: var(--red); }

.conf-group { display: flex; flex-direction: column; gap: 5px; }
.conf-label-text {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .05em; color: var(--muted);
}
.conf-options { display: flex; gap: 6px; }
.conf-options label {
  display: flex; align-items: center; gap: 5px; font-size: 12px; cursor: pointer;
  padding: 6px 11px; border: 1px solid var(--border); border-radius: 4px;
  background: white; transition: background .12s, border-color .12s; user-select: none;
}
.conf-options label:has(input:checked) {
  border-color: var(--accent); background: var(--accent-light); font-weight: 600;
}
.conf-options input[type=radio] { accent-color: var(--accent); }

.notes-wrap { flex: 1; min-width: 200px; }
.notes-wrap label {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .05em; color: var(--muted); display: block; margin-bottom: 5px;
}
.topic-notes {
  width: 100%; border: 1px solid var(--border); border-radius: 4px;
  padding: 7px 10px; font-size: 12px; font-family: inherit; color: var(--text);
  background: white; resize: vertical; height: 58px; transition: border-color .15s;
}
.topic-notes:focus { outline: none; border-color: var(--accent); }

/* ── Submit section ── */
.submit-section {
  padding: 20px 32px; border-top: 2px solid var(--border);
  background: var(--surface); display: flex; align-items: center; gap: 16px;
}
.submit-btn {
  padding: 11px 28px; background: var(--accent); color: white; border: none;
  border-radius: 4px; font-size: 14px; font-weight: 600; cursor: pointer;
  font-family: inherit; transition: background .15s;
}
.submit-btn:hover { background: #2d4a7a; }
.submit-btn.test-mode { background: var(--test-bg); }
.submit-btn.test-mode:hover { background: #540065; }
.submit-note { font-size: 12px; color: var(--muted); }

/* ── Responsive ── */
@media (max-width: 700px) {
  .topic-body { grid-template-columns: 1fr; }
  .col-words  { border-right: none; border-bottom: 1px solid var(--border); }
  .name-input { width: 100%; }
}
"""


def stab_badge_html(score: float) -> str:
    if score >= 0.45:
        return '<span class="badge b-green">High stability</span>'
    elif score >= 0.30:
        return '<span class="badge b-amber">Moderate</span>'
    else:
        return '<span class="badge b-red">Low stability — review</span>'


def render_word_chips(wc_pairs: list, n_seeds: int) -> str:
    chips = []
    for word, count in wc_pairs:
        if count == n_seeds:
            wc, cc = "w-all",  "wct-all"
        elif count >= n_seeds - 1:
            wc, cc = "w-most", "wct-most"
        elif count >= 2:
            wc, cc = "w-some", "wct-some"
        else:
            wc, cc = "w-one",  "wct-one"
        chips.append(
            f'<div class="wchip {wc}">'
            f'<span class="wct {cc}">{count}/{n_seeds}</span>'
            f'{word}</div>'
        )
    legend = (
        f'<div class="word-legend">'
        f'Chip label = appearances across {n_seeds} seeds — '
        f'{n_seeds}/{n_seeds}: stable core &nbsp;·&nbsp; '
        f'{n_seeds-1}/{n_seeds}: near-stable &nbsp;·&nbsp; 1/{n_seeds}: run-specific'
        f'</div>'
    )
    return '<div class="word-chips">' + "".join(chips) + "</div>" + legend


def render_books_table(books: list) -> str:
    rows = []
    for b in books:
        yr = f" ({b['year']})" if b.get("year") else ""
        rows.append(
            f"<tr>"
            f"<td><span class='load-badge'>{b['loading']:.3f}</span></td>"
            f"<td>{b['title']}"
            f"<div class='bk-author'>{b.get('author','')}{yr}</div></td>"
            f"</tr>"
        )
    return (
        '<table class="books">'
        "<thead><tr><th>Load</th><th>Title / Author</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    )


def render_topic_card(
    t_idx: int,
    canonical_words: list,
    wc_pairs: list,
    top_books: list,
    stability_score: float,
    n_seeds: int,
) -> str:
    label     = f"T{t_idx + 1}"
    badge_html = stab_badge_html(stability_score)
    # Serialise for hidden fields — HTML-escape the quotes
    words_json = json.dumps(canonical_words[:10]).replace('"', '&quot;')
    books_json = json.dumps(top_books).replace('"', '&quot;')

    return f"""
<div class="topic-card" id="topic-{t_idx}">
  <div class="topic-hdr">
    <div class="tid">{label}</div>
    <span class="stab-score">Stability score: {stability_score:.3f}</span>
    {badge_html}
  </div>
  <div class="topic-body">
    <div class="col-words">
      <div class="col-label">Keywords — frequency across {n_seeds} seeds</div>
      {render_word_chips(wc_pairs, n_seeds)}
    </div>
    <div class="col-books">
      <div class="col-label">Top books by topic loading</div>
      {render_books_table(top_books)}
    </div>
  </div>
  <div class="naming-row">
    <div class="name-wrap">
      <label>Proposed name <span class="required">*</span></label>
      <input type="text" class="name-input" name="name_{t_idx}" id="name_{t_idx}"
             placeholder="Enter proposed topic name…"
             autocomplete="off" spellcheck="true">
    </div>
    <div class="conf-group">
      <div class="conf-label-text">Confidence</div>
      <div class="conf-options">
        <label><input type="radio" name="conf_{t_idx}" value="high"> High</label>
        <label><input type="radio" name="conf_{t_idx}" value="medium" checked> Medium</label>
        <label><input type="radio" name="conf_{t_idx}" value="low"> Low</label>
      </div>
    </div>
    <div class="notes-wrap">
      <label>Notes (optional)</label>
      <textarea class="topic-notes" name="notes_{t_idx}"
                placeholder="Observations, ambiguities, alternative names considered…"></textarea>
    </div>
  </div>
  <input type="hidden" name="stab_{t_idx}"  value="{stability_score}">
  <input type="hidden" name="words_{t_idx}" value="{words_json}">
  <input type="hidden" name="books_{t_idx}" value="{books_json}">
</div>"""


def build_form_html(nlp: dict, run_id: str, top_books_per_topic: list, test_mode: bool) -> str:
    stab        = nlp.get("stability", {})
    n_topics    = nlp.get("n_topics", 9)
    n_seeds     = stab.get("n_seeds", 5)
    seeds_used  = stab.get("seeds_used", [])
    mean_stab   = stab.get("mean_stability", 0.0)
    stab_scores = stab.get("stability_scores", [0.0] * n_topics)
    top_words   = nlp.get("top_words", [[] for _ in range(n_topics)])
    n_books     = len(nlp.get("doc_topic", []))
    max_feat    = nlp.get("max_features", "?")
    pipeline_mode = nlp.get("pipeline_mode", "?")
    date_str    = datetime.now().strftime("%Y-%m-%d")
    seeds_str   = ", ".join(str(s) for s in seeds_used) if seeds_used else "?"

    test_banner = (
        '<div class="test-banner">🧪  TEST MODE — form is active but nothing will be '
        'written to the database</div>' if test_mode else ""
    )
    btn_class = "submit-btn test-mode" if test_mode else "submit-btn"
    btn_label = "Submit (test — not saved)" if test_mode else "Submit naming session"

    cards = ""
    for t_idx in range(n_topics):
        canonical = top_words[t_idx] if t_idx < len(top_words) else []
        wc        = word_seed_counts(nlp, t_idx)
        books     = top_books_per_topic[t_idx] if t_idx < len(top_books_per_topic) else []
        score     = stab_scores[t_idx] if t_idx < len(stab_scores) else 0.0
        cards    += render_topic_card(t_idx, canonical, wc, books, score, n_seeds)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CyberneticsNLP — Topic Naming</title>
  <style>{CSS}</style>
</head>
<body>
<div class="app-header">
  <h1>CyberneticsNLP — Topic Naming Session</h1>
  <div class="sub">record_topic_run.py &nbsp;·&nbsp; {date_str} &nbsp;·&nbsp; Run: {run_id}</div>
</div>

{test_banner}

<div class="meta-strip">
  <div class="meta-item">k = <strong>{n_topics} topics</strong></div>
  <div class="meta-item">Corpus = <strong>{n_books} books analysed</strong></div>
  <div class="meta-item">Seeds = <strong>{n_seeds}</strong> ({seeds_str})</div>
  <div class="meta-item">Mean stability = <strong>{mean_stab:.3f}</strong></div>
  <div class="meta-item">Max features = <strong>{max_feat:,}</strong></div>
  <div class="meta-item">Pipeline mode = <strong>{pipeline_mode}</strong></div>
</div>

<div class="notice">
  <strong>Instructions:</strong> For each topic, review the keyword distribution and top
  books, then enter a proposed name. All name fields are required — if you genuinely cannot
  name a topic, enter a placeholder (e.g. "Uncertain / review") and explain in the Notes
  field. Names are provisional until confirmed across ≥3 runs and ≥2 independent raters.
</div>

<form method="POST" action="/submit" id="naming-form">
  <input type="hidden" name="run_id" value="{run_id}">

  <div class="session-section">
    <div class="field-group">
      <label>Rater name <span class="required">*</span></label>
      <input type="text" name="rater" id="rater" class="rater-input"
             placeholder="Your name" autocomplete="name">
    </div>
    <div class="field-group">
      <label>Session notes (optional)</label>
      <textarea name="session_notes" class="session-notes"
                placeholder="Overall notes on this naming session — run conditions, uncertainties, etc."></textarea>
    </div>
  </div>

  <div class="topics-section">
    {cards}
  </div>

  <div class="submit-section">
    <button type="submit" class="{btn_class}">{btn_label}</button>
    <span class="submit-note">All {n_topics} topic name fields must be filled before submitting.</span>
  </div>
</form>

<script>
(function () {{
  var form = document.getElementById('naming-form');
  form.addEventListener('submit', function (e) {{
    var missing = [];
    // Check rater
    var rater = document.getElementById('rater');
    if (!rater.value.trim()) {{
      rater.style.borderColor = '#b00020';
      missing.push('Rater name');
    }} else {{
      rater.style.borderColor = '';
    }}
    // Check each topic name
    for (var i = 0; i < {n_topics}; i++) {{
      var inp = document.getElementById('name_' + i);
      if (!inp.value.trim()) {{
        inp.classList.add('error');
        missing.push('T' + (i + 1));
      }} else {{
        inp.classList.remove('error');
      }}
    }}
    if (missing.length > 0) {{
      e.preventDefault();
      alert('Please fill in: ' + missing.join(', '));
    }}
  }});
}})();
</script>
</body>
</html>"""


def build_success_html(rater: str, run_id: str, n_topics: int, test_mode: bool) -> str:
    suffix = " (TEST — not saved)" if test_mode else ""
    color  = "#6b0080" if test_mode else "#2d6a4f"
    icon   = "🧪" if test_mode else "✓"
    msg    = "Test submitted — nothing written to database." if test_mode else \
             f"{n_topics} topic names saved to database."
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Session recorded{suffix}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f8f7f4; display: flex; align-items: center;
      justify-content: center; min-height: 100vh; margin: 0;
    }}
    .card {{
      background: white; border-radius: 8px; padding: 40px 48px;
      max-width: 500px; text-align: center; border: 1px solid #e2ddd8;
    }}
    h2   {{ font-size: 20px; color: {color}; margin-bottom: 12px; }}
    p    {{ color: #6b6560; font-size: 13px; margin-bottom: 6px; }}
    .run {{ font-size: 12px; color: #aaa; margin-top: 14px; font-family: monospace; }}
    a    {{ color: #3a5a8c; text-decoration: none; font-weight: 600; }}
    a:hover {{ text-decoration: underline; }}
    .back {{ margin-top: 20px; }}
  </style>
</head>
<body>
  <div class="card">
    <h2>{icon} {('Test submitted' if test_mode else 'Naming session recorded')}</h2>
    <p>Rater: <strong>{rater}</strong></p>
    <p>{msg}</p>
    <p class="back"><a href="/">Name another session ↗</a></p>
    <div class="run">Run ID: {run_id}</div>
  </div>
</body>
</html>"""


def build_error_html(message: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Error</title>
<style>body{{font-family:sans-serif;background:#f8f7f4;padding:40px;}}
.err{{background:#fdecea;border:1px solid #f5a0a0;border-radius:6px;
padding:20px 24px;max-width:500px;color:#b00020;}}</style>
</head>
<body><div class="err"><strong>Error:</strong> {message}
<p style="margin-top:10px;"><a href="/">← Back to form</a></p></div></body>
</html>"""


# ══════════════════════════════════════════════════════════════════════════════
# HTTP request handler
# ══════════════════════════════════════════════════════════════════════════════

class NamingHandler(BaseHTTPRequestHandler):
    # These are injected by make_handler_class():
    nlp:                 dict
    run_id:              str
    top_books_per_topic: list
    test_mode:           bool
    db_path:             Path
    n_topics:            int
    nlp_path:            Path

    def log_message(self, fmt, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  [{ts}] {fmt % args}")

    # ── GET ───────────────────────────────────────────────────────────────────
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            html = build_form_html(
                self.nlp, self.run_id, self.top_books_per_topic, self.test_mode
            )
            self._respond(200, html)
        else:
            self.send_error(404)

    # ── POST ──────────────────────────────────────────────────────────────────
    def do_POST(self):
        if self.path != "/submit":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))
        raw    = self.rfile.read(length).decode("utf-8")
        params = urllib.parse.parse_qs(raw, keep_blank_values=True)

        def get(key, default=""):
            return (params.get(key) or [default])[0]

        rater         = get("rater").strip()
        session_notes = get("session_notes").strip()
        run_id        = get("run_id", self.run_id)

        if not rater:
            self._respond(400, build_error_html("Rater name is required."))
            return

        now_iso = datetime.now(timezone.utc).isoformat()

        topic_records = []
        for t_idx in range(self.n_topics):
            name  = get(f"name_{t_idx}").strip()
            conf  = get(f"conf_{t_idx}", "medium")
            notes = get(f"notes_{t_idx}").strip()
            stab  = float(get(f"stab_{t_idx}", "0"))
            # Decode the HTML-escaped JSON back to plain JSON strings
            words_raw = get(f"words_{t_idx}", "[]").replace("&quot;", '"')
            books_raw = get(f"books_{t_idx}", "[]").replace("&quot;", '"')
            topic_records.append({
                "topic_idx":      t_idx,
                "topic_label":    f"T{t_idx + 1}",
                "proposed_name":  name,
                "confidence":     conf,
                "notes":          notes,
                "stability_score": stab,
                "top_words":      words_raw,
                "top_books":      books_raw,
            })

        if not self.test_mode:
            err = self._save(run_id, rater, session_notes, now_iso, topic_records)
            if err:
                self._respond(500, build_error_html(f"Database error: {err}"))
                return

        html = build_success_html(rater, run_id, self.n_topics, self.test_mode)
        self._respond(200, html)

    # ── DB write ──────────────────────────────────────────────────────────────
    def _save(self, run_id, rater, session_notes, now_iso, topic_records) -> str:
        """Insert session and per-topic records. Returns error string or ''."""
        try:
            con = open_db(self.db_path)

            # Resolve run_id: look up the logged run by nlp_hash so the session
            # is linked to the correct pipeline_runs row regardless of what
            # run_id was auto-generated at server start.
            nlp_hash = compute_file_hash(self.nlp_path)
            logged_run = con.execute(
                "SELECT run_id, is_test FROM pipeline_runs WHERE nlp_hash = ?",
                (nlp_hash,),
            ).fetchone()
            if not logged_run:
                con.close()
                return (
                    f"Run not found in pipeline_runs (nlp_hash={nlp_hash}). "
                    "Log this run first: python src/log_pipeline_run.py"
                )
            if logged_run["is_test"]:
                con.close()
                return (
                    f"Run '{logged_run['run_id']}' is a test run — "
                    "naming sessions cannot be attached to test runs."
                )
            run_id = logged_run["run_id"]

            # Naming session
            cur = con.execute(
                """
                INSERT INTO naming_sessions
                  (run_id, rater, session_at, session_notes, is_test)
                VALUES (?, ?, ?, ?, 0)
                """,
                (run_id, rater, now_iso, session_notes),
            )
            session_id = cur.lastrowid

            # Per-topic ratings
            for tr in topic_records:
                con.execute(
                    """
                    INSERT INTO topic_ratings
                      (session_id, topic_idx, topic_label, proposed_name,
                       confidence, notes, stability_score, top_words, top_books)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        tr["topic_idx"],
                        tr["topic_label"],
                        tr["proposed_name"],
                        tr["confidence"],
                        tr["notes"],
                        tr["stability_score"],
                        tr["top_words"],
                        tr["top_books"],
                    ),
                )

            con.commit()
            con.close()
            print(f"  ✓ Saved session {session_id} — rater: {rater}, run: {run_id}")
            return ""
        except Exception as exc:
            print(f"  ✗ DB error: {exc}", file=sys.stderr)
            return str(exc)

    # ── Helper ────────────────────────────────────────────────────────────────
    def _respond(self, status: int, html: str):
        data = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def make_handler_class(nlp, run_id, top_books, test_mode, db_path, n_topics, nlp_path):
    """Return a NamingHandler subclass with the given state injected as class vars."""
    return type("Handler", (NamingHandler,), {
        "nlp":                 nlp,
        "run_id":              run_id,
        "top_books_per_topic": top_books,
        "test_mode":           test_mode,
        "db_path":             db_path,
        "n_topics":            n_topics,
        "nlp_path":            nlp_path,
    })


# ══════════════════════════════════════════════════════════════════════════════
# Query and export modes
# ══════════════════════════════════════════════════════════════════════════════

def cmd_query(db_path: Path, n: int = 15):
    if not db_path.exists():
        print(f"No database found at {db_path}\nRun the server and submit at least one session first.")
        return
    con = open_db(db_path)
    sessions = con.execute(
        """
        SELECT s.id, s.run_id, s.rater, s.session_at, s.is_test,
               COUNT(tr.id) AS n_topics
        FROM naming_sessions s
        LEFT JOIN topic_ratings tr ON tr.session_id = s.id
        GROUP BY s.id
        ORDER BY s.session_at DESC
        LIMIT ?
        """,
        (n,),
    ).fetchall()
    # (pipeline_runs replaces old `runs` table; query unchanged — run_id FK still works)
    con.close()

    if not sessions:
        print("No sessions recorded yet.")
        return

    print(f"\nMost recent naming sessions in {db_path.name}:\n")
    hdr = f"{'ID':>4}  {'Run ID':<30}  {'Rater':<18}  {'Timestamp (UTC)':<28}  {'Topics':>6}  Test"
    print(hdr)
    print("-" * len(hdr))
    for s in sessions:
        test_flag = "yes" if s["is_test"] else "—"
        ts = s["session_at"][:25]
        print(f"{s['id']:>4}  {s['run_id']:<30}  {s['rater']:<18}  {ts:<28}  {s['n_topics']:>6}  {test_flag}")
    print()


def cmd_export(db_path: Path, fmt: str):
    if not db_path.exists():
        print(f"No database at {db_path}")
        return
    output_dir = db_path.parent.parent / "data" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    con = open_db(db_path)
    rows = con.execute(
        """
        SELECT
            r.run_id, r.logged_at     AS run_recorded_at,
            r.git_commit, r.k AS n_topics, r.n_books,
            r.mean_stability,         r.lda_params,
            s.id      AS session_id,  s.rater,
            s.session_at,             s.session_notes,
            s.is_test,
            t.topic_idx,              t.topic_label,
            t.proposed_name,          t.confidence,
            t.notes   AS topic_notes, t.stability_score,
            t.top_words,              t.top_books
        FROM pipeline_runs r
        JOIN naming_sessions s ON s.run_id = r.run_id
        JOIN topic_ratings   t ON t.session_id = s.id
        ORDER BY s.session_at, t.topic_idx
        """
    ).fetchall()
    con.close()

    if not rows:
        print("No records to export.")
        return

    if fmt == "json":
        data = [dict(r) for r in rows]
        out_path = output_dir / f"topic_naming_export_{ts}.json"
        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Exported {len(data)} rows → {out_path}")

    elif fmt == "csv":
        out_path = output_dir / f"topic_naming_export_{ts}.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows([dict(r) for r in rows])
        print(f"Exported {len(rows)} rows → {out_path}")


# ══════════════════════════════════════════════════════════════════════════════
# Offline form generation  (--generate)
# ══════════════════════════════════════════════════════════════════════════════

# JSON schema version — bump if the format changes in a breaking way
OFFLINE_FORMAT_VERSION = "topic_naming_v1"


def build_offline_form_html(nlp: dict, run_id: str, top_books_per_topic: list) -> str:
    """
    Return a fully self-contained HTML string.  The file requires no server:
    the rater opens it locally, fills in names, and clicks "Download JSON".
    The downloaded JSON is ingested back into the DB via --ingest.
    """
    stab        = nlp.get("stability", {})
    n_topics    = nlp.get("n_topics", 9)
    n_seeds     = stab.get("n_seeds", 5)
    seeds_used  = stab.get("seeds_used", [])
    mean_stab   = stab.get("mean_stability", 0.0)
    stab_scores = stab.get("stability_scores", [0.0] * n_topics)
    top_words   = nlp.get("top_words", [[] for _ in range(n_topics)])
    n_books     = len(nlp.get("doc_topic", []))
    max_feat    = nlp.get("max_features", "?")
    pipeline_mode = nlp.get("pipeline_mode", "?")
    seeds_str   = ", ".join(str(s) for s in seeds_used) if seeds_used else "?"
    date_str    = datetime.now().strftime("%Y-%m-%d")

    # ── Build topic cards (same visual style, no hidden fields needed) ─────
    cards = ""
    for t_idx in range(n_topics):
        canonical = top_words[t_idx] if t_idx < len(top_words) else []
        wc        = word_seed_counts(nlp, t_idx)
        books     = top_books_per_topic[t_idx] if t_idx < len(top_books_per_topic) else []
        score     = stab_scores[t_idx] if t_idx < len(stab_scores) else 0.0
        cards    += render_topic_card(t_idx, canonical, wc, books, score, n_seeds)

    # ── Embed topic metadata for the JS download handler ─────────────────────
    topic_meta = []
    for t_idx in range(n_topics):
        canonical = top_words[t_idx][:10] if t_idx < len(top_words) else []
        books     = top_books_per_topic[t_idx] if t_idx < len(top_books_per_topic) else []
        score     = stab_scores[t_idx] if t_idx < len(stab_scores) else 0.0
        topic_meta.append({
            "topic_idx":      t_idx,
            "topic_label":    f"T{t_idx + 1}",
            "stability_score": score,
            "top_words":      canonical,
            "top_books":      books,
        })

    lda_params  = build_lda_params(nlp)
    run_meta_js = json.dumps({
        "format":         OFFLINE_FORMAT_VERSION,
        "run_id":         run_id,
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "n_topics":       n_topics,
        "n_books":        n_books,
        "mean_stability": mean_stab,
        "lda_params":     lda_params,
        "topics":         topic_meta,
    }, ensure_ascii=False)

    # ── JS: collect form → build JSON → trigger download ──────────────────────
    js = f"""
(function () {{
  var RUN = {run_meta_js};
  var N   = RUN.n_topics;

  document.getElementById('download-btn').addEventListener('click', function () {{
    // Validate
    var missing = [];
    var rater = document.getElementById('rater').value.trim();
    if (!rater) {{
      document.getElementById('rater').style.borderColor = '#b00020';
      missing.push('Rater name');
    }} else {{
      document.getElementById('rater').style.borderColor = '';
    }}
    for (var i = 0; i < N; i++) {{
      var inp = document.getElementById('name_' + i);
      if (!inp || !inp.value.trim()) {{
        if (inp) inp.classList.add('error');
        missing.push('T' + (i + 1));
      }} else {{
        if (inp) inp.classList.remove('error');
      }}
    }}
    if (missing.length > 0) {{
      alert('Please fill in: ' + missing.join(', '));
      return;
    }}

    // Build payload
    var now = new Date().toISOString();
    var topics = [];
    for (var j = 0; j < N; j++) {{
      var meta = RUN.topics[j];
      topics.push({{
        topic_idx:      meta.topic_idx,
        topic_label:    meta.topic_label,
        proposed_name:  document.getElementById('name_' + j).value.trim(),
        confidence:     document.querySelector('input[name="conf_' + j + '"]:checked').value,
        notes:          (document.getElementById('notes_' + j) || {{}}).value || '',
        stability_score: meta.stability_score,
        top_words:      meta.top_words,
        top_books:      meta.top_books,
      }});
    }}

    var payload = {{
      format:        RUN.format,
      run_id:        RUN.run_id,
      generated_at:  RUN.generated_at,
      session_at:    now,
      rater:         rater,
      session_notes: document.getElementById('session_notes').value.trim(),
      n_topics:      RUN.n_topics,
      n_books:       RUN.n_books,
      mean_stability: RUN.mean_stability,
      lda_params:    RUN.lda_params,
      topics:        topics,
    }};

    // Trigger download
    var blob = new Blob([JSON.stringify(payload, null, 2)],
                        {{type: 'application/json'}});
    var url  = URL.createObjectURL(blob);
    var a    = document.createElement('a');
    a.href   = url;
    a.download = 'topic_naming_' + RUN.run_id + '_' + rater.replace(/\\s+/g, '_') + '.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    // Show confirmation
    document.getElementById('submit-section').innerHTML =
      '<div style="background:#eef7f2;border:1px solid #a8d5b8;border-radius:6px;' +
      'padding:16px 20px;color:#2d6a4f;font-size:13px;">' +
      '<strong>✓ JSON file downloaded.</strong> ' +
      'Please send it to the session coordinator to be ingested into the database.' +
      '</div>';
  }});
}})();
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CyberneticsNLP — Topic Naming (Offline)</title>
  <style>{CSS}
  .offline-notice {{
    background: #eef2f8; border: 1px solid #c5d4e8; border-radius: 4px;
    margin: 14px 32px; padding: 10px 14px; font-size: 12px; color: #3a5a8c;
  }}
  </style>
</head>
<body>
<div class="app-header">
  <h1>CyberneticsNLP — Topic Naming Session (Offline Form)</h1>
  <div class="sub">record_topic_run.py --generate &nbsp;·&nbsp; {date_str} &nbsp;·&nbsp; Run: {run_id}</div>
</div>

<div class="meta-strip">
  <div class="meta-item">k = <strong>{n_topics} topics</strong></div>
  <div class="meta-item">Corpus = <strong>{n_books} books analysed</strong></div>
  <div class="meta-item">Seeds = <strong>{n_seeds}</strong> ({seeds_str})</div>
  <div class="meta-item">Mean stability = <strong>{mean_stab:.3f}</strong></div>
  <div class="meta-item">Max features = <strong>{max_feat:,}</strong></div>
  <div class="meta-item">Pipeline mode = <strong>{pipeline_mode}</strong></div>
</div>

<div class="offline-notice">
  <strong>Offline form.</strong> Fill in names below, then click
  <em>Download JSON</em>. Send the downloaded file back to the session
  coordinator — do not modify it. You do not need an internet connection
  to complete this form.
</div>

<div class="notice">
  <strong>Instructions:</strong> For each topic, review the keyword distribution and top
  books, then enter a proposed name. All name fields are required — if you genuinely cannot
  name a topic, enter a placeholder (e.g. "Uncertain / review") and explain in the Notes
  field. Names are provisional until confirmed across ≥3 runs and ≥2 independent raters.
</div>

<div class="session-section">
  <div class="field-group">
    <label>Rater name <span class="required">*</span></label>
    <input type="text" id="rater" class="rater-input"
           placeholder="Your name" autocomplete="name">
  </div>
  <div class="field-group">
    <label>Session notes (optional)</label>
    <textarea id="session_notes" class="session-notes"
              placeholder="Overall notes — run conditions, uncertainties, etc."></textarea>
  </div>
</div>

<div class="topics-section">
  {cards}
</div>

<div class="submit-section" id="submit-section">
  <button type="button" id="download-btn" class="submit-btn">
    Download JSON
  </button>
  <span class="submit-note">
    All {n_topics} topic name fields must be filled. The downloaded file
    goes back to the session coordinator for ingestion into the database.
  </span>
</div>

<script>{js}</script>
</body>
</html>"""


def cmd_generate(nlp: dict, run_id: str, top_books_per_topic: list, out_path: Path):
    """Write the self-contained offline HTML form."""
    html = build_offline_form_html(nlp, run_id, top_books_per_topic)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    size_kb = out_path.stat().st_size / 1024
    print(f"\n✓ Offline form written ({size_kb:.0f} KB):")
    print(f"  {out_path}")
    print(f"\nSend this file to raters. They open it in any browser, fill in names,")
    print(f"click 'Download JSON', and return the .json file to you.")
    print(f"Ingest returned files with:  python src/record_topic_run.py --ingest <file.json>")


# ══════════════════════════════════════════════════════════════════════════════
# Offline ingest  (--ingest)
# ══════════════════════════════════════════════════════════════════════════════

def cmd_ingest(json_paths: list, db_path: Path):
    """
    Read one or more JSON files returned by offline raters and insert each
    naming session into the SQLite database.
    """
    results = {"ok": 0, "skipped": 0, "errors": 0}

    for path in json_paths:
        path = Path(path)
        print(f"\nIngesting: {path.name}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"  ✗ Cannot read file: {exc}")
            results["errors"] += 1
            continue

        # Basic validation
        fmt = payload.get("format")
        if fmt != OFFLINE_FORMAT_VERSION:
            print(f"  ✗ Unknown format '{fmt}' (expected '{OFFLINE_FORMAT_VERSION}'). Skipping.")
            results["errors"] += 1
            continue

        rater         = payload.get("rater", "").strip()
        run_id        = payload.get("run_id", "")
        session_at    = payload.get("session_at") or payload.get("generated_at", "")
        session_notes = payload.get("session_notes", "")
        topics        = payload.get("topics", [])
        lda_params    = payload.get("lda_params", {})
        n_topics      = payload.get("n_topics")
        n_books       = payload.get("n_books")
        mean_stab     = payload.get("mean_stability")

        if not rater:
            print("  ✗ No rater name in file. Skipping.")
            results["errors"] += 1
            continue
        if not run_id:
            print("  ✗ No run_id in file. Skipping.")
            results["errors"] += 1
            continue
        if not topics:
            print("  ✗ No topic data in file. Skipping.")
            results["errors"] += 1
            continue

        # Check for duplicate (same run_id + rater + session_at)
        con = open_db(db_path)
        existing = con.execute(
            "SELECT id FROM naming_sessions WHERE run_id=? AND rater=? AND session_at=?",
            (run_id, rater, session_at),
        ).fetchone()
        if existing:
            print(f"  ⚠  Already ingested (run_id={run_id}, rater={rater}, "
                  f"session_at={session_at[:19]}). Skipping.")
            con.close()
            results["skipped"] += 1
            continue

        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            # Upsert run
            con.execute(
                """
                INSERT OR IGNORE INTO runs
                  (run_id, recorded_at, source_file, git_commit,
                   n_topics, n_books, mean_stability, lda_params,
                   notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id, now_iso,
                    f"offline_form:{path.name}",
                    "",          # no git commit available from offline form
                    n_topics, n_books, mean_stab,
                    json.dumps(lda_params),
                    f"Ingested from offline form: {path.name}",
                ),
            )

            # Insert naming session (is_test=0; offline forms are real submissions)
            cur = con.execute(
                """
                INSERT INTO naming_sessions
                  (run_id, rater, session_at, session_notes, is_test)
                VALUES (?, ?, ?, ?, 0)
                """,
                (run_id, rater, session_at, session_notes),
            )
            session_id = cur.lastrowid

            # Insert per-topic ratings
            for t in topics:
                top_words_j = (json.dumps(t["top_words"])
                               if isinstance(t.get("top_words"), list)
                               else t.get("top_words", "[]"))
                top_books_j = (json.dumps(t["top_books"])
                               if isinstance(t.get("top_books"), list)
                               else t.get("top_books", "[]"))
                con.execute(
                    """
                    INSERT INTO topic_ratings
                      (session_id, topic_idx, topic_label, proposed_name,
                       confidence, notes, stability_score, top_words, top_books)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        t.get("topic_idx"),
                        t.get("topic_label", f"T{t.get('topic_idx', 0)+1}"),
                        t.get("proposed_name", ""),
                        t.get("confidence", ""),
                        t.get("notes", ""),
                        t.get("stability_score"),
                        top_words_j,
                        top_books_j,
                    ),
                )

            con.commit()
            print(f"  ✓ Ingested — rater: {rater}, {len(topics)} topics, "
                  f"session_id: {session_id}")
            results["ok"] += 1

        except Exception as exc:
            con.rollback()
            print(f"  ✗ DB error: {exc}")
            results["errors"] += 1
        finally:
            con.close()

    print(f"\nDone — {results['ok']} ingested, "
          f"{results['skipped']} skipped (duplicate), "
          f"{results['errors']} errors.")


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--nlp",      type=Path, default=NLP_PATH,    help="Path to nlp_results.json")
    p.add_argument("--db",       type=Path, default=DB_PATH,     help="Path to pipeline.db")
    p.add_argument("--port",     type=int,  default=DEFAULT_PORT, help="Port to serve on")
    p.add_argument("--top",      type=int,  default=TOP_BOOKS,   dest="top_books",
                   help="Top books per topic to display")
    p.add_argument("--test",     action="store_true",
                   help="Test mode — serve form but do NOT write to database")
    p.add_argument("--generate", action="store_true",
                   help="Write a self-contained offline HTML form and exit")
    p.add_argument("--out",      type=Path, default=None,
                   help="Output path for --generate (default: data/outputs/topic_naming_form_RUNID.html)")
    p.add_argument("--ingest",   nargs="+", metavar="FILE", default=None,
                   help="Ingest one or more offline JSON files into the database")
    p.add_argument("--query",    action="store_true",
                   help="Print recent naming sessions and exit")
    p.add_argument("--export",   choices=["json", "csv"], default=None,
                   help="Export all records and exit")
    p.add_argument("--run-id",   default=None, dest="run_id",
                   help="Override the auto-generated run ID")
    p.add_argument("--host",     default="localhost",
                   help="Interface to bind to (default: localhost; use 0.0.0.0 for Docker/external access)")
    return p.parse_args()


def main():
    args = parse_args()

    # ── Non-data commands ─────────────────────────────────────────────────────
    if args.query:
        cmd_query(args.db)
        return

    if args.export:
        cmd_export(args.db, args.export)
        return

    if args.ingest:
        cmd_ingest(args.ingest, args.db)
        return

    # ── Load NLP data (required for all remaining modes) ──────────────────────
    print(f"Loading {args.nlp} …")
    if not args.nlp.exists():
        print(f"ERROR: {args.nlp} not found.\nRun the NLP pipeline first.", file=sys.stderr)
        sys.exit(1)

    nlp       = load_nlp(args.nlp)
    n_topics  = nlp.get("n_topics", 9)
    run_id    = args.run_id or make_run_id(nlp)
    top_books = compute_top_books(nlp, n_topics, args.top_books)

    stab = nlp.get("stability", {})
    print(f"  k={n_topics} topics · {len(nlp.get('doc_topic', []))} books · "
          f"mean stability={stab.get('mean_stability', 0):.3f} · "
          f"seeds={stab.get('n_seeds', '?')}")
    print(f"  Run ID : {run_id}")

    # ── Offline form generation ───────────────────────────────────────────────
    if args.generate:
        out_path = args.out or (
            BASE_DIR / "data" / "outputs" / f"topic_naming_form_{run_id}.html"
        )
        cmd_generate(nlp, run_id, top_books, out_path)
        return

    # ── Server mode ───────────────────────────────────────────────────────────
    if args.test:
        print("  ⚠  TEST MODE — submissions will NOT be written to the database.")
    else:
        print(f"  Database : {args.db}")

    display_host = "localhost" if args.host == "0.0.0.0" else args.host
    url = f"http://{display_host}:{args.port}"
    print(f"  Binding  : {args.host}:{args.port}")
    print(f"  URL      : {url}")
    print(f"\nServing — open {url} in your browser.  Press Ctrl+C to stop.\n")

    HandlerClass = make_handler_class(
        nlp, run_id, top_books, args.test, args.db, n_topics, args.nlp
    )
    server = HTTPServer((args.host, args.port), HandlerClass)

    # webbrowser.open() is a no-op on headless machines; suppress cleanly
    if "DISPLAY" in os.environ or sys.platform == "darwin":
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
