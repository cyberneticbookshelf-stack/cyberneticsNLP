"""
llm_summarize_lib.py — shared plumbing for the local-vLLM summarisers.

Used by:
  summarize.py           — standalone file -> summary CLI (format styles)
  04b_llm_summarize.py   — corpus book-level pipeline stage (content styles)

Only mechanical plumbing lives here — token estimate, paragraph-boundary
chunking, a retrying chat call, and API-key resolution. Prompt / style logic
stays in each caller so the two tools can frame summaries differently.

Security: never hardcode the real vLLM API key in a tracked file (standing
security principle — no credential values in committed files). `resolve_api_key`
reads it from the CLI flag or the $API_KEY environment variable, falling back to
the non-secret placeholder "EMPTY" (which works when the server is launched
without auth).
"""
import os
import sys
import textwrap
import time


# ── Chunking (token-aware, cheap heuristic) ───────────────────────────────────
def approx_tokens(text: str) -> int:
    # ~4 chars/token is a fine heuristic for English; avoids a tokenizer dep.
    return max(1, len(text) // 4)


def chunk_text(text: str, max_tokens: int, overlap_tokens: int = 128):
    """Split on paragraph boundaries into ~max_tokens chunks with small overlap."""
    paras = [p for p in text.split("\n\n") if p.strip()]
    chunks, cur, cur_tok = [], [], 0
    for para in paras:
        ptok = approx_tokens(para)
        if ptok > max_tokens:  # a single giant paragraph -> hard-wrap it
            for piece in textwrap.wrap(para, width=max_tokens * 4):
                if cur_tok + approx_tokens(piece) > max_tokens and cur:
                    chunks.append("\n\n".join(cur))
                    cur, cur_tok = [], 0
                cur.append(piece)
                cur_tok += approx_tokens(piece)
            continue
        if cur_tok + ptok > max_tokens and cur:
            chunks.append("\n\n".join(cur))
            tail = "\n\n".join(cur)[-overlap_tokens * 4:]
            cur, cur_tok = ([tail], approx_tokens(tail)) if overlap_tokens else ([], 0)
        cur.append(para)
        cur_tok += ptok
    if cur:
        chunks.append("\n\n".join(cur))
    return chunks


# ── LLM call (retrying) ───────────────────────────────────────────────────────
def chat(client, model, role, prompt, max_tokens, temperature=0.2, retries=4):
    """One chat completion with exponential-backoff retry on transient errors."""
    messages = [{"role": "system", "content": role},
                {"role": "user", "content": prompt}]
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model=model, messages=messages,
                temperature=temperature, max_tokens=max_tokens,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:  # noqa: BLE001 — surface then back off
            if attempt == retries - 1:
                raise
            wait = 2 ** attempt
            print(f"    ! API error ({e}); retry {attempt + 1}/{retries - 1} "
                  f"in {wait}s", file=sys.stderr)
            time.sleep(wait)


# ── API key (never hardcode the real one in a tracked file) ───────────────────
def resolve_api_key(cli_value=None):
    """CLI flag > $API_KEY env > 'EMPTY' placeholder. See module docstring."""
    return cli_value or os.environ.get("API_KEY") or "EMPTY"
