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

echo "=== Book Corpus NLP Pipeline ==="
echo "Starting: $(date)"
echo "Mode: $([ $STREAM -eq 1 ] && echo 'streaming (large corpus)' || echo 'standard')"

run() { echo ""; echo "── $1 ──"; python3 "$SCRIPT_DIR/$1"; }

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

# Standard LDA run (unweighted — always runs first)
# NOTE: --weighted requires index_analysis.json + a prior nlp_results.json
#       and cannot run on a clean start. See the optional second-pass
#       section at the bottom of this script.
# ── Book-level topics ────────────────────────────────────────────────────────
run 03_nlp_pipeline.py
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

# ── Entity relations (optional, needs 09b first) ─────────────────────────────

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
