#!/usr/bin/env python3
"""
text_matter.py — front matter, back matter, and publisher boilerplate.

Single source of truth for the text-trimming helpers. `strip_front_matter`,
`strip_back_matter` and `prepare_full_text` were previously defined inside
`03_nlp_pipeline.py`, where nothing else could import them — the module name
starts with a digit — so the chapter path had no way to reuse them and simply
did not trim at all.

WHY THIS MATTERS (ROADMAP #35, 21 September 2026)
─────────────────────────────────────────────────
The book-level path strips front and back matter at fit time (`--full-text`),
so publisher pages never reach the book LDA. The chapter path had no such step:
`04_summarize.py` splits a book at chapter headings, and everything before the
first heading becomes an "Opening" chapter — which is, by construction, the
title page, copyright page, Library of Congress data and digitisation notices.
Small leftover fragments are merged into "Other / Minor Sections", which
collects more of the same.

Those pseudo-chapters were then summarised and fed to the chapter NMF, which
spent an entire topic of eight on copyright language: *part, electronic, minor,
retrieval, minor sections, sections, permission, information, rights, storage,
reproduced, recording* — 297 chapters across 225 books. Of those, 137 were
titled "Other / Minor Sections" and 76 "Opening", confirming the mechanism.

Per the standing "fix upstream" principle the fix belongs where chapters are
constructed, not in relabelling the resulting topic. This module provides the
trimming; `04_summarize.py` applies it before splitting.

Note the asymmetry this preserves deliberately: cleaning (02) still keeps full
text, because the book path needs it and strips at fit time. Trimming at clean
time would invalidate the clean cache and force a re-canonicalisation.
"""
import re

# ── Front / back matter ──────────────────────────────────────────────────────
# Moved verbatim from 03_nlp_pipeline.py — behaviour must not change, since the
# book-level canonical run depends on it.
FRONT_SKIP_MIN_CHARS = 3000    # Never start before this offset
FRONT_SKIP_FRAC      = 0.05    # Fallback: skip first 5% if no body marker found
BACK_MIN_FRAC        = 0.50    # Only truncate if back-matter marker >= 50% in

_BODY_START_RE = re.compile(
    r'^\s*(?:'
    r'chapter\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|'
    r'eleven|twelve|[1-9][0-9]?)\b'
    r'|part\s+(?:one|two|three|i{1,4}|v?i{0,3}|[1-9])\b'
    r'|introduction\b'
    r'|prologue\b'
    r'|[1-9][0-9]?\s*\n'     # bare chapter number on its own line
    r')',
    re.IGNORECASE | re.MULTILINE
)

_BACK_START_RE = re.compile(
    r'^\s*(?:'
    r'references?\s*$'
    r'|bibliography\s*$'
    r'|works\s+cited\s*$'
    r'|further\s+reading\s*$'
    r'|notes?\s+and\s+references?\s*$'
    r'|selected\s+bibliography\s*$'
    r'|bibliographical\s+notes?\s*$'
    r'|index\s*$'
    r'|general\s+index\s*$'
    r'|subject\s+index\s*$'
    r'|author\s+index\s*$'
    r'|name\s+index\s*$'
    r')',
    re.IGNORECASE | re.MULTILINE
)


def strip_front_matter(text: str):
    """Remove front matter. Returns (body_text, chars_skipped)."""
    n = len(text)
    m = _BODY_START_RE.search(text, FRONT_SKIP_MIN_CHARS)
    if m and m.start() < n * 0.30:
        return text[m.start():], m.start()
    offset = max(FRONT_SKIP_MIN_CHARS, int(n * FRONT_SKIP_FRAC))
    return text[offset:], offset


def strip_back_matter(text: str):
    """Remove back matter. Returns (body_text, chars_removed)."""
    n = len(text)
    min_offset = int(n * BACK_MIN_FRAC)
    last_match = None
    for m in _BACK_START_RE.finditer(text):
        if m.start() >= min_offset:
            last_match = m
    if last_match:
        return text[:last_match.start()], n - last_match.start()
    return text, 0


def prepare_full_text(text: str):
    """Front- and back-matter stripped body text. Returns (text, stats)."""
    original_chars = len(text)
    stripped_front, front_chars = strip_front_matter(text)
    stripped_body,  back_chars  = strip_back_matter(stripped_front)
    body_chars = len(stripped_body)
    stats = {
        'original_chars': original_chars,
        'front_stripped':  front_chars,
        'back_stripped':   back_chars,
        'body_chars':      body_chars,
        'body_pct':        round(100 * body_chars / original_chars, 1)
                           if original_chars else 0,
    }
    return stripped_body, stats


# ── Publisher boilerplate (ROADMAP #35) ──────────────────────────────────────
# Phrases that only occur in copyright / imprint / digitisation notices. Each is
# matched case-insensitively against a sentence; a sentence carrying any of them
# is publisher apparatus, not authored content.
#
# Chosen to be specific rather than broad. "rights", "information" and "part"
# are the NMF topic's top words, but each is an ordinary word in cybernetics
# prose — matching on them would delete real text. The multi-word phrases below
# do not occur outside imprint pages.
_BOILERPLATE_PHRASES = [
    r'no part of this (?:publication|book|work)',
    r'may(?: not)? be reproduced',
    r'stored in a retrieval system',
    r'all rights reserved',
    r'prior (?:written )?permission of the (?:publisher|copyright)',
    r'photocopying,? recording',
    r'library of congress catalog',
    r'cataloging[- ]in[- ]publication',
    r'cataloguing[- ]in[- ]publication',
    r'british library catalogu',
    r'printed (?:and bound )?in the united',
    r'printed (?:and bound )?in great britain',
    r'digitized by the internet archive',
    r'with funding from',
    r'isbn[- ]?(?:1[03])?[:\s]',
    r'issn[:\s]',
    r'first published (?:in )?\d{4}',
    r'copyright\s*(?:©|\(c\))',
    r'©\s*\d{4}',
    r'typeset (?:by|in)',
    r'a catalogue record for this book',
]
_BOILERPLATE_RE = re.compile('|'.join(_BOILERPLATE_PHRASES), re.IGNORECASE)

# Sentence split that tolerates the ragged punctuation of OCR'd imprint pages.
_SENT_SPLIT_RE = re.compile(r'(?<=[.!?])\s+|\n{2,}')


def boilerplate_ratio(text: str) -> float:
    """Fraction of words that sit in sentences carrying a boilerplate phrase."""
    if not text.strip():
        return 0.0
    total = boiler = 0
    for sent in _SENT_SPLIT_RE.split(text):
        w = len(sent.split())
        if not w:
            continue
        total += w
        if _BOILERPLATE_RE.search(sent):
            boiler += w
    return boiler / total if total else 0.0


def strip_publisher_boilerplate(text: str):
    """Drop sentences that are publisher apparatus.

    Returns (text, chars_removed). Sentence-level rather than whole-block so a
    genuine preface that merely mentions an ISBN is not discarded wholesale.
    """
    kept, removed = [], 0
    for sent in _SENT_SPLIT_RE.split(text):
        if _BOILERPLATE_RE.search(sent):
            removed += len(sent)
        else:
            kept.append(sent)
    return ' '.join(kept), removed
