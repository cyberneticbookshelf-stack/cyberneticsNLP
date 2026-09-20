#!/usr/bin/env python3
"""
check_fts_coverage.py — report books that exist in Calibre but have no
full-text row, and are therefore absent from the corpus without warning.

WHY THIS EXISTS (KI-14, 21 September 2026)
──────────────────────────────────────────
`split_books_text.sh` builds the shards with

    SELECT book, searchable_text FROM books_text WHERE format='PDF'

with no bound on which books it expects. A book that Calibre has not indexed —
because FTS indexing had not caught up, or because the PDF is an image-only
scan with no extractable text — simply has no row, so it is absent from the
shards, absent from the corpus, and absent from every count. Nothing fails.

That is the same silent-loss shape as KI-13 (stale clean cache) and as the
stale metadata export that nearly dropped 12 books on 20 September. In each
case the data was missing, the pipeline was content, and the gap was found by
hand afterwards. The lesson each time is the same: make the gap loud at the
boundary where it enters.

On 20 September this cost 13 of 755 books. Four (2824, 2827, 2828, 2832) had
been added to Calibre *before* the FTS snapshot was taken and should have been
indexed; the rest are mostly large scans or non-English works.

WHAT IT DOES NOT DO
───────────────────
It cannot fix the gap. Re-indexing and OCR happen in the Calibre library, which
is not part of this repo — this script tells you precisely which books need it,
and splits them by likely cause so the work is actionable.

Usage:
    python3 src/check_fts_coverage.py                 # report (exit 0)
    python3 src/check_fts_coverage.py --strict        # exit 1 if any gap
    python3 src/check_fts_coverage.py --json PATH     # also write a machine-readable report
    python3 src/check_fts_coverage.py --scan-mb 50    # size above which a PDF is assumed to be a scan
"""
import argparse
import json
import pathlib
import sqlite3
import sys

CALIBRE_DIR = pathlib.Path('data/inputs/calibre')
META_DB = CALIBRE_DIR / 'metadata.db'
FTS_DB = CALIBRE_DIR / 'full-text-search.db'

# A PDF far larger than the corpus norm is almost always an image-only scan:
# there is no text layer to extract, so re-indexing alone will not help — it
# needs OCR first. Corpus mean is ~34 MB; 50 MB is a deliberately conservative
# line, and the field is advisory either way.
DEFAULT_SCAN_MB = 50


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--strict', action='store_true',
                    help='exit 1 if any book lacks full text')
    ap.add_argument('--json', type=pathlib.Path, default=None,
                    help='write a machine-readable report here')
    ap.add_argument('--scan-mb', type=float, default=DEFAULT_SCAN_MB,
                    help=f'PDF size (MB) above which OCR is assumed needed '
                         f'(default {DEFAULT_SCAN_MB})')
    ap.add_argument('--format', default='PDF',
                    help='format the shards are built from (default PDF)')
    args = ap.parse_args()

    for db in (META_DB, FTS_DB):
        if not db.exists():
            print(f"  [fts-coverage] {db} not found — skipping check")
            return 0

    con = sqlite3.connect(f'file:{META_DB}?mode=ro', uri=True)
    con.execute(f"ATTACH DATABASE 'file:{FTS_DB}?mode=ro' AS fts KEY ''")

    total_books = con.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    indexed = con.execute(
        "SELECT COUNT(DISTINCT book) FROM fts.books_text WHERE format=?",
        (args.format,)).fetchone()[0]

    missing = con.execute("""
        SELECT b.id, b.title, COALESCE(d.uncompressed_size, 0),
               COALESCE(b.timestamp, ''), COALESCE(b.author_sort, '')
        FROM books b
        LEFT JOIN data d ON d.book = b.id AND d.format = ?
        WHERE b.id NOT IN (SELECT book FROM fts.books_text WHERE format = ?)
        ORDER BY COALESCE(d.uncompressed_size, 0) DESC
    """, (args.format, args.format)).fetchall()

    # Rows in the FTS index with no surviving metadata row — the reverse gap,
    # which means the FTS snapshot is older than the library.
    orphans = con.execute("""
        SELECT DISTINCT book FROM fts.books_text
        WHERE format = ? AND book NOT IN (SELECT id FROM books)
    """, (args.format,)).fetchall()
    con.close()

    print(f"  [fts-coverage] metadata.db: {total_books} books · "
          f"full-text-search.db: {indexed} with {args.format} text")

    if not missing and not orphans:
        print(f"  [fts-coverage] full coverage ✓")
        return 0

    needs_ocr, needs_index, no_format = [], [], []
    for bid, title, size, ts, author in missing:
        mb = size / 1048576 if size else 0
        rec = {'id': bid, 'title': title, 'author': author,
               'size_mb': round(mb, 1), 'added': ts[:10]}
        if not size:
            no_format.append(rec)
        elif mb >= args.scan_mb:
            needs_ocr.append(rec)
        else:
            needs_index.append(rec)

    print(f"  [fts-coverage] ⚠ {len(missing)} book(s) have no {args.format} text "
          f"and are therefore ABSENT from the corpus:\n")

    def show(label, rows, hint):
        if not rows:
            return
        print(f"    {label} — {len(rows)} book(s). {hint}")
        for r in rows:
            size = f"{r['size_mb']:>6.1f} MB" if r['size_mb'] else "   no file"
            print(f"      {size}  [{r['id']}] {r['title'][:54]}  (added {r['added']})")
        print()

    show(f"Likely image-only scans (>= {args.scan_mb:g} MB)", needs_ocr,
         "OCR first, then re-index — re-indexing alone will not help.")
    show(f"Likely just un-indexed (< {args.scan_mb:g} MB)", needs_index,
         "Re-run Calibre full-text indexing; these should have a text layer.")
    show(f"No {args.format} file recorded at all", no_format,
         "Check the book actually has the format attached in Calibre.")

    if orphans:
        print(f"    {len(orphans)} FTS row(s) reference books absent from "
              f"metadata.db — the FTS snapshot is older than the library: "
              f"{[o[0] for o in orphans][:10]}\n")

    print("    To fix (Calibre library side — not this repo):")
    print("      1. OCR the image-only scans, then re-add or update them in Calibre.")
    print("      2. Re-run Calibre's full-text indexing and let it finish.")
    print("      3. Re-export metadata.db + full-text-search.db to "
          "data/inputs/calibre/.")
    print("      4. bash data/inputs/calibre/split_books_text.sh")
    print("      5. python3 src/00_export_calibre.py")
    print("      6. bash src/run_all.sh --stream --rebuild-clean")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        json.dump({'total_books': total_books, 'indexed': indexed,
                   'missing_count': len(missing), 'needs_ocr': needs_ocr,
                   'needs_index': needs_index, 'no_format': no_format,
                   'orphan_fts_rows': [o[0] for o in orphans]},
                  open(args.json, 'w'), ensure_ascii=False, indent=2)
        print(f"\n  [fts-coverage] report written to {args.json}")

    if args.strict:
        print("\n  [fts-coverage] --strict: failing on incomplete coverage.")
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
