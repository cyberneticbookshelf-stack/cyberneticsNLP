#!/usr/bin/env python3
"""
check_clean_cache.py — guard against a stale books_clean.jsonl (KI-13).

The streaming clean (parse_and_clean_stream.py) skips books by id. That makes
incremental runs fast, but it means a reconstructed or re-sharded Calibre
corpus is silently ignored: new / re-IDed books never get cleaned, and
re-extracted text on an *unchanged* id keeps its stale cleaned version. The
pipeline then fits topics on stale text with no warning.

A timestamp comparison is not enough — the cache can be rewritten *after* the
shards (e.g. a partial re-clean) yet still be missing books. This helper
fingerprints each shard by SHA-256 of its raw bytes and compares against a
manifest recorded at the last full rebuild. Any change to a shard (new /
re-IDed books, re-extracted text) changes its hash and is caught.

Contract (called from run_all.sh):
    python3 src/check_clean_cache.py            # verify: exit 0 fresh, 3 stale
    python3 src/check_clean_cache.py --write-manifest   # record current shards

The manifest is written only by --write-manifest, which run_all.sh calls at the
end of a --rebuild-clean run — the one moment the cache provably matches the
shards (it was rebuilt from them). On a normal run the guard verifies and, if a
shard has changed since that rebuild, aborts with an instruction to re-run with
--rebuild-clean.
"""
import glob
import hashlib
import json
import os
import sys

SHARD_GLOB = 'csv/books_text_*.csv'
CACHE = 'json/books_clean.jsonl'
MANIFEST = 'json/books_clean.manifest.json'


def shard_hashes() -> dict:
    """SHA-256 of each shard's raw bytes, keyed by basename."""
    out = {}
    for path in sorted(glob.glob(SHARD_GLOB)):
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1 << 20), b''):
                h.update(chunk)
        out[os.path.basename(path)] = h.hexdigest()
    return out


def write_manifest() -> int:
    hashes = shard_hashes()
    with open(MANIFEST, 'w', encoding='utf-8') as f:
        json.dump({'shards': hashes}, f, indent=2, sort_keys=True)
    print(f'check_clean_cache: wrote manifest for {len(hashes)} shard(s) -> {MANIFEST}')
    return 0


def verify() -> int:
    # No cache yet — a fresh start will build it; nothing to guard.
    if not os.path.exists(CACHE):
        print('check_clean_cache: no clean cache yet — fresh start, nothing to verify.')
        return 0

    cur = shard_hashes()
    if not cur:
        # No shards to compare against — don't block; let the run surface it.
        print('check_clean_cache: WARNING — no shards found; cannot verify cache.',
              file=sys.stderr)
        return 0

    if not os.path.exists(MANIFEST):
        print('check_clean_cache: STALE — clean cache exists but no shard manifest.\n'
              '  Cannot prove the cache matches the current shards (first run after\n'
              '  the KI-13 guard was added, or a manually rebuilt cache).',
              file=sys.stderr)
        return 3

    with open(MANIFEST, encoding='utf-8') as f:
        man = json.load(f).get('shards', {})

    changed = sorted(k for k in cur if man.get(k) != cur[k])
    removed = sorted(k for k in man if k not in cur)
    if changed or removed:
        print('check_clean_cache: STALE clean cache (KI-13) — shards changed since '
              'last rebuild.', file=sys.stderr)
        for k in changed:
            print(f'  changed shard: {k}', file=sys.stderr)
        for k in removed:
            print(f'  shard in manifest no longer present: {k}', file=sys.stderr)
        return 3

    print(f'check_clean_cache: OK — {len(cur)} shard(s) match manifest.')
    return 0


if __name__ == '__main__':
    if '--write-manifest' in sys.argv[1:]:
        sys.exit(write_manifest())
    sys.exit(verify())
