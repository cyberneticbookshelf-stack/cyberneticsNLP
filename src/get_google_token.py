#!/usr/bin/env python3
"""
get_google_token.py — One-time Google OAuth token generation.

Run this on a machine that HAS a browser.
It reads credentials.json, opens the browser for OAuth, and saves
token.json to the same directory.  Both generate_google_form.py and
ingest_google_responses.py then use that token silently on the NLP machine.

Usage (run from the CyberneticsNLP project root, e.g. via sshfs mount):
    python src/get_google_token.py
    python src/get_google_token.py --creds /path/to/credentials.json

After token.json is saved, copy it to the NLP machine if needed:
    scp token.json <user>@<nlp-host>:~/CyberneticsNLP/token.json

Requirements:
    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""

import argparse
import sys
from pathlib import Path

BASE_DIR   = Path(__file__).resolve().parent.parent
CREDS_PATH = BASE_DIR / "credentials.json"
TOKEN_PATH = BASE_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive.file",
]


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--creds", type=Path, default=CREDS_PATH,
                   help=f"Path to credentials.json (default: {CREDS_PATH})")
    p.add_argument("--out",   type=Path, default=TOKEN_PATH,
                   help=f"Where to save token.json (default: {TOKEN_PATH})")
    args = p.parse_args()

    if not args.creds.exists():
        print(f"ERROR: credentials.json not found at {args.creds}", file=sys.stderr)
        sys.exit(1)

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("ERROR: google-auth-oauthlib not installed.", file=sys.stderr)
        print("Run: pip install google-api-python-client google-auth-httplib2 "
              "google-auth-oauthlib", file=sys.stderr)
        sys.exit(1)

    print(f"Reading credentials from: {args.creds}")
    print(f"Token will be saved to:   {args.out}")
    print()
    print("A browser window will open for Google authorisation.")
    print("Sign in with the Google account linked to this project and click Allow.")
    print()

    flow  = InstalledAppFlow.from_client_secrets_file(str(args.creds), SCOPES)
    creds = flow.run_local_server(port=0)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(creds.to_json(), encoding="utf-8")
    print(f"\n✓ token.json saved → {args.out}")

    if args.out != TOKEN_PATH:
        print(f"\nCopy to the NLP machine:")
        print(f"  scp {args.out} <user>@<nlp-host>:~/CyberneticsNLP/token.json")
    else:
        print("Token is already in the project directory.")
        print("If running via sshfs mount, it is already on the NLP machine.")


if __name__ == "__main__":
    main()
