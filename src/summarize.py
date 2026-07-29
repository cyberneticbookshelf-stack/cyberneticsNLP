#!/usr/bin/env python3
"""
Map-reduce document summarizer for the local single-GPU vLLM service.

Talks to the OpenAI-compatible endpoint served by serve_summarize.sh. Handles
documents longer than the model's context window by chunking -> summarizing each
chunk (map) -> summarizing the summaries (reduce), recursing until the combined
summary fits in one pass. This is how you summarize a 300-page PDF on ONE GPU.

Text extraction:
  .txt / .md   -> read directly
  .pdf         -> pdftotext (poppler-utils) if present, else pypdf
  .docx        -> python-docx if present
  (anything else is read as UTF-8 text)

Usage:
  conda activate ingest-env        # or any env with the optional extractors
  python summarize.py report.pdf
  python summarize.py notes.txt --style bullets --words 300
  python summarize.py big.pdf --port 8004 --model summarizer --map-tokens 6000

Env/flags mirror serve_summarize.sh defaults (port 8004). API key: $API_KEY or
--api-key (falls back to the non-secret placeholder "EMPTY" when the server has
no auth) — never hardcode the real key here (security principle: no credential
values in committed files).

Shared chunking / map-reduce plumbing lives in llm_summarize_lib.py, imported
below; this file owns text extraction and the format-style prompts.
No RAG stack needed: summarization feeds the document straight in.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling imports from src/
from llm_summarize_lib import approx_tokens, chunk_text, chat, resolve_api_key

try:
    from openai import OpenAI
except ImportError:
    sys.exit("Missing dep: pip install openai  (in your client env)")


# ---------- text extraction ----------
def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md", ".markdown", ".rst", ".csv", ".json", ".log"):
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix == ".docx":
        return _extract_docx(path)
    # fall back to raw text
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_pdf(path: Path) -> str:
    # Prefer poppler's pdftotext (fast, in Tier-1 apt list); fall back to pypdf.
    from shutil import which
    if which("pdftotext"):
        out = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            capture_output=True, text=True,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("PDF support needs poppler-utils (pdftotext) or `pip install pypdf`.")
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _extract_docx(path: Path) -> str:
    try:
        import docx  # python-docx
    except ImportError:
        sys.exit("DOCX support needs `pip install python-docx`.")
    document = docx.Document(str(path))
    return "\n".join(p.text for p in document.paragraphs)


# ---------- LLM calls ----------
STYLE_HINTS = {
    "prose": "Write flowing prose in paragraphs.",
    "bullets": "Write as concise bullet points.",
    "exec": "Write a tight executive summary: key findings first, then supporting detail.",
}


def summarize_once(client, model, text, style, words, is_reduce=False):
    role = ("You are combining several partial summaries of ONE document into a "
            "single coherent summary. Remove redundancy; preserve every distinct fact."
            if is_reduce else
            "You are summarizing part of a larger document. Be faithful and specific; "
            "keep names, numbers, and conclusions.")
    prompt = (f"{STYLE_HINTS.get(style, STYLE_HINTS['prose'])} "
              f"Target about {words} words.\n\n---\n{text}\n---")
    return chat(client, model, role, prompt, max_tokens=min(4096, words * 3))


def map_reduce(client, model, text, args):
    chunks = chunk_text(text, args.map_tokens)
    print(f"  -> {len(chunks)} chunk(s) at ~{args.map_tokens} tok each", file=sys.stderr)
    if len(chunks) == 1:
        return summarize_once(client, model, chunks[0], args.style, args.words)

    # MAP: summarize each chunk (shorter target so summaries recombine cleanly)
    partials = []
    per = max(120, args.words // max(1, len(chunks) // 2))
    for i, ch in enumerate(chunks, 1):
        print(f"  map {i}/{len(chunks)}", file=sys.stderr)
        partials.append(summarize_once(client, model, ch, args.style, per))

    # REDUCE: recurse on the concatenated summaries until it fits one pass
    combined = "\n\n".join(partials)
    if approx_tokens(combined) > args.map_tokens:
        print("  reduce: summaries still large, recursing", file=sys.stderr)
        return map_reduce(client, model, combined, args)
    print("  reduce: final pass", file=sys.stderr)
    return summarize_once(client, model, combined, args.style, args.words, is_reduce=True)


def main():
    ap = argparse.ArgumentParser(description="Map-reduce summarizer for local vLLM.")
    ap.add_argument("file", type=Path, help="document to summarize")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8004)))
    ap.add_argument("--api-key", default=None,
                    help="vLLM API key; falls back to $API_KEY then 'EMPTY'")
    ap.add_argument("--model", default="summarizer", help="served-model-name")
    ap.add_argument("--style", choices=list(STYLE_HINTS), default="prose")
    ap.add_argument("--words", type=int, default=400, help="target length of final summary")
    ap.add_argument("--map-tokens", type=int, default=6000,
                    help="chunk size; keep well under the served --max-model-len")
    ap.add_argument("-o", "--out", type=Path, help="write summary to a file")
    args = ap.parse_args()

    if not args.file.exists():
        sys.exit(f"No such file: {args.file}")

    print(f"Extracting text from {args.file.name} ...", file=sys.stderr)
    text = extract_text(args.file).strip()
    if not text:
        sys.exit("No extractable text (scanned PDF? that needs the VLM/ColPali path, not this).")
    print(f"  {approx_tokens(text)} approx tokens", file=sys.stderr)

    client = OpenAI(base_url=f"http://{args.host}:{args.port}/v1",
                    api_key=resolve_api_key(args.api_key))
    summary = map_reduce(client, args.model, text, args)

    if args.out:
        args.out.write_text(summary, encoding="utf-8")
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        print("\n" + summary)


if __name__ == "__main__":
    main()
