#!/usr/bin/env bash
# run_all.sh — Run the full Book NLP Pipeline (both book-level and chapter-level)
#
# Usage (from project root):
#   bash src/run_all.sh              # small corpus (<~300 books): standard path
#   bash src/run_all.sh --stream     # large corpus: streaming parse+clean
#
# --stream processes one books_text_*.csv at a time via parse_and_clean_stream.py,
# writing directly to books_clean.json without creating a large books_parsed.json.
# Recommended for corpora over ~300 books.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STREAM=0
for arg in "$@"; do [ "$arg" = "--stream" ] && STREAM=1; done

# ══════════════════════════════════════════════════════════════════════════════
# PRE-PROCESSING: Book style enrichment pipeline (run once before main pipeline)
# ══════════════════════════════════════════════════════════════════════════════
# These scripts enrich book metadata from Calibre and external APIs.
# They are NOT part of the main NLP pipeline and should NOT be run automatically
# in run_all.sh — they have external API dependencies, caching logic, and
# require csv/books_metadata_full.csv (exported from Calibre metadata.db).
#
# Run order (from project root):
#
#   Step 0a — Heuristic style classification (title/author/publisher signals):
#     python3 src/00_classify_book_styles.py
#
#   Step 0b — Google Books + Open Library enrichment (caches to json/external_metadata_cache.json):
#     python3 src/00_fetch_worldcat_metadata.py          # fetch all (first run, ~10 min)
#     python3 src/00_fetch_worldcat_metadata.py --reclassify  # re-run from cache
#
#   Step 0c — ANU Primo catalogue enrichment (caches to json/anu_primo_cache.json):
#     python3 src/00_fetch_anu_primo.py                  # fetch all (first run, ~12 min)
#     python3 src/00_fetch_anu_primo.py --reclassify     # re-run from cache
#
#   Step 0d — Final enriched classification (reads all three enrichment layers):
#     python3 src/00_fetch_worldcat_metadata.py --reclassify
#     python3 src/00_fetch_anu_primo.py --reclassify
#     python3 src/00_classify_book_styles.py --stats
#
# Output: json/book_styles.json — used as covariate in downstream analysis
#
# Note: book types are not disjoint (a book can be monograph AND textbook).
# The classifier produces a single best-guess label as a working approximation.
# Ground truth labelling of ~150 books is planned to validate and improve accuracy.
# See docs/memo_media_aware_nlp_epistemic_affordances.md §13 for methodology.
# ══════════════════════════════════════════════════════════════════════════════

echo "=== Book Corpus NLP Pipeline ==="
echo "Starting: $(date)"
echo "Mode: $([ $STREAM -eq 1 ] && echo 'streaming (large corpus)' || echo 'standard')"

run() { echo ""; echo "── $1 ──"; python3 "$SCRIPT_DIR/$1" "${@:2}"; }

mkdir -p data/outputs figures
mkdir -p csv json   # pipeline expects input CSVs in csv/ and writes JSON to json/

if [ $STREAM -eq 1 ]; then
    echo ""
    echo "── parse_and_clean_stream.py (all books_text_*.csv) ──"
    for csv_file in csv/books_text_*.csv; do
        echo "   $csv_file..."
        python3 "$SCRIPT_DIR/parse_and_clean_stream.py" "$csv_file"
    done
else
    run 01_parse_books.py
    run 02_clean_text.py
fi

# ── CANONICAL TOPIC SOLUTION ─────────────────────────────────────────────────
# Canonical k for this corpus: k=9 (validated 3 April 2026)
# topic_stability.json always reflects the LAST k run — if you run a
# comparison at a different k (e.g. k=10 to compare), you MUST re-run
# at k=9 afterwards to restore the canonical solution before committing.
#
# To restore canonical k=9 after a comparison run:
#   python3 src/03_nlp_pipeline.py --min-chars 10000 --lemmatize --topics 9 --seeds 5
#   python3 src/09c_validate_topics.py --top 10 --md
#   python3 patch_topic_names.py   # re-apply agreed topic taxonomy
#
# The run_all.sh uses --topics 9 explicitly to enforce this:
# ─────────────────────────────────────────────────────────────────────────────
# Standard LDA run (unweighted — always runs first)
# NOTE: --weighted requires index_analysis.json + a prior nlp_results.json
#       and cannot run on a clean start. See the optional second-pass
#       section at the bottom of this script.
# ── Book-level topics ────────────────────────────────────────────────────────
python3 "$SCRIPT_DIR/03_nlp_pipeline.py" --min-chars 10000 --lemmatize --topics 9 --seeds 5
# Validate topics and apply agreed taxonomy names immediately after LDA
# so all downstream reports use named topics rather than Topic 1, Topic 2 etc.
python3 "$SCRIPT_DIR/09c_validate_topics.py" --top 10 --md
python3 "$SCRIPT_DIR/patch_topic_names.py"
run 04_summarize.py
run 05_visualize.py
run 06_build_report.py
run 07_build_excel.py

# ── Chapter-level topics (uses summaries from 04) ────────────────────────────
run 03_nlp_pipeline_chapters.py
run 05_visualize_chapters.py
run 06_build_report_chapters.py
run 07_build_excel_chapters.py

# ── Index term extraction (must run before 10, 12, and 08 Chart 7) ───────────
run 09_extract_index.py
run 09b_build_index_analysis.py
run 10_build_index_report.py

# ── Index grounding: topic labelling, concept density, velocity ───────────────
# Must run after 09+10 (needs index_analysis.json) and before 08 (Chart 7)
run 12_index_grounding.py

# ── Time series (Chart 7 requires index_analysis.json + concept_velocity.json)
run 08_build_timeseries.py

# ── Embedding comparison (optional) ──────────────────────────────────────────
# Step 11 requires sentence-transformers and/or VOYAGE_API_KEY
# python3 "$SCRIPT_DIR/14_entity_network.py" --no-windows  # fast book-level only
# python3 "$SCRIPT_DIR/14_entity_network.py"               # + paragraph windows
# run 11_embedding_comparison.py --no-voyage --no-st   # A+B only, no deps
run 11_embedding_comparison.py --no-voyage           # A+B+C (needs PyTorch)
# run 11_embedding_comparison.py                       # all methods
# After running 11, rebuild the analysis report:
run build_embed_report.py

# ── Entity relations (needs 09b + 12 first) ──────────────────────────────────
# Step 15 must run before 14 — builds entity_types_cache.json
# Run 15 once; subsequent runs skip already-classified entities (cached).
# Step 14 --no-windows is fast (~30s); omit flag for paragraph-window edges (~5 min)
run 15_entity_classify.py
python3 "$SCRIPT_DIR/14_entity_network.py"                # book-level + paragraph windows


echo ""
echo "=== Pipeline complete: $(date) ==="
echo "Outputs in data/outputs/:"
echo "  book_nlp_analysis.html              book_nlp_results.xlsx"
echo "  book_nlp_analysis_chapters.html     book_nlp_chapters.xlsx"
echo "  book_nlp_timeseries.html            book_nlp_index_analysis.html"
echo "  book_nlp_index_grounding.html       book_nlp_embedding_comparison.html"
# ══════════════════════════════════════════════════════════════════════════════
# OPTIONAL: Index-term weighted second pass
# ══════════════════════════════════════════════════════════════════════════════
# Run ONLY after the full pipeline above has completed at least once.
#
# --weighted boosts topic-discriminating index terms (e.g. schismogenesis,
# autopoiesis) and dampens pervasive terms (e.g. feedback, system).
# Silhouette score improves ~1-2%; variance explained rises ~5pp.
#
# Required files (must already exist):
#   nlp_results.json     — written by step 03 above
#   index_analysis.json  — written by step 09b above
#
# Uncomment the block below to enable:
#
# echo ""
# echo "=== Weighted second pass: $(date) ==="
# python3 "$SCRIPT_DIR/03_nlp_pipeline.py" --weighted
# python3 "$SCRIPT_DIR/04_summarize.py"
# python3 "$SCRIPT_DIR/05_visualize.py"
# python3 "$SCRIPT_DIR/06_build_report.py"
# python3 "$SCRIPT_DIR/07_build_excel.py"
# python3 "$SCRIPT_DIR/03_nlp_pipeline_chapters.py"
# python3 "$SCRIPT_DIR/05_visualize_chapters.py"
# python3 "$SCRIPT_DIR/06_build_report_chapters.py"
# python3 "$SCRIPT_DIR/07_build_excel_chapters.py"
# python3 "$SCRIPT_DIR/12_index_grounding.py"
# python3 "$SCRIPT_DIR/08_build_timeseries.py"
# echo "Weighted second pass complete: $(date)"
