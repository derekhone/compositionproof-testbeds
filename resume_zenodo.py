#!/usr/bin/env python3
"""
CompositionProof-2 - RESUME an existing Zenodo draft (idempotent).

The initial publish_zenodo.py run created draft 22666466 and uploaded 14 of 15
files before Zenodo's API tier began returning HTTP 504 (server-side outage).
This script RESUMES that same draft - it does NOT create a new deposit:

  1. GET the draft, list files already present.
  2. Upload only the RELEASE_FILES that are missing (so re-runs are safe).
  3. Attach the .zenodo.json metadata.
  4. STOP as a reviewable draft. It PUBLISHES (mints the DOI, irreversible)
     ONLY if you pass --publish-final.

Gates (same culture as the submitter):
    --go-token "PUBLISH COMPOSITIONPROOF-2"   (exact)
    --i-have-ceo-authorization                (flag)

Usage:
    # Finish the draft, leave it unpublished for review:
    python3 resume_zenodo.py --go-token "PUBLISH COMPOSITIONPROOF-2" \
        --i-have-ceo-authorization

    # After review, mint the DOI (irreversible):
    python3 resume_zenodo.py --go-token "PUBLISH COMPOSITIONPROOF-2" \
        --i-have-ceo-authorization --publish-final
"""

import argparse
import json
import os
import sys

GO_TOKEN_REQUIRED = "PUBLISH COMPOSITIONPROOF-2"
ZENODO_API = "https://zenodo.org/api"
SECRETS_PATH = "/home/ubuntu/.config/abacusai_auth_secrets.json"
DRAFT_ID = 22666466  # the draft created by publish_zenodo.py

RELEASE_FILES = [
    "README.md",
    "CITATION.cff",
    "PREREGISTRATION.md",
    "PREREGISTRATION.pdf",
    "lock_candidate.json",
    "SHA256_MANIFEST.txt",
    "GOVERNANCE.md",
    "EPOCH1_RECORD.md",
    "EPOCH1_RECORD.pdf",
    "epoch_series.json",
    "composition2_sim.py",
    "submit_epoch.py",
    "retrieve_epoch.py",
    "verifier2.py",
    "control_validate2.py",
]


def load_zenodo_token():
    with open(SECRETS_PATH) as f:
        data = json.load(f)
    secrets = data.get("zenodo", {}).get("secrets", {})
    for key in ("access_token", "api_token"):
        if key in secrets and secrets[key].get("value"):
            return secrets[key]["value"]
    raise RuntimeError("No Zenodo token found in auth-secrets file.")


def check_gates(args):
    ok = True
    if args.go_token != GO_TOKEN_REQUIRED:
        print(f"[GATE 1 FAIL] --go-token must be exactly '{GO_TOKEN_REQUIRED}'.")
        ok = False
    else:
        print("[GATE 1 PASS] Go-token correct.")
    if not args.i_have_ceo_authorization:
        print("[GATE 2 FAIL] --i-have-ceo-authorization flag not set.")
        ok = False
    else:
        print("[GATE 2 PASS] CEO authorization acknowledged.")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--go-token", default="")
    ap.add_argument("--i-have-ceo-authorization", action="store_true")
    ap.add_argument("--publish-final", action="store_true")
    ap.add_argument("--draft-id", type=int, default=DRAFT_ID)
    ap.add_argument("--timeout", type=int, default=180)
    args = ap.parse_args()

    print("=" * 68)
    print(f"CompositionProof-2 - RESUME Zenodo draft {args.draft_id} (GATED)")
    print("=" * 68)

    if not check_gates(args):
        print("\nGATED. Nothing done. Awaiting explicit CEO authorization.")
        sys.exit(2)

    import requests  # noqa: E402

    here = os.path.dirname(__file__) or "."
    token = load_zenodo_token()
    params = {"access_token": token}
    to = args.timeout

    print(f"\nFetching draft {args.draft_id}...")
    r = requests.get(f"{ZENODO_API}/deposit/depositions/{args.draft_id}",
                     params=params, timeout=to)
    r.raise_for_status()
    dep = r.json()
    if dep.get("submitted"):
        print("Draft is already published/submitted. Nothing to do.")
        print("Record:", dep["links"].get("record_html", ""))
        sys.exit(0)

    bucket = dep["links"]["bucket"]
    present = {f["filename"] for f in dep.get("files", [])}
    print(f"  Files already present: {len(present)}")
    missing = [fn for fn in RELEASE_FILES if fn not in present]
    print(f"  Missing files to upload: {missing if missing else 'none'}")

    for fn in missing:
        path = os.path.join(here, fn)
        if not os.path.exists(path):
            print(f"[ABORT] Missing local file: {fn}")
            sys.exit(3)
        with open(path, "rb") as fp:
            ur = requests.put(f"{bucket}/{fn}", data=fp, params=params, timeout=to)
            ur.raise_for_status()
        print(f"  uploaded {fn}")

    print("Attaching metadata...")
    with open(os.path.join(here, ".zenodo.json")) as f:
        meta = json.load(f)
    mr = requests.put(f"{ZENODO_API}/deposit/depositions/{args.draft_id}",
                      params=params, json={"metadata": meta}, timeout=to)
    mr.raise_for_status()

    # Re-fetch to confirm final file count
    chk = requests.get(f"{ZENODO_API}/deposit/depositions/{args.draft_id}",
                       params=params, timeout=to).json()
    final = {f["filename"] for f in chk.get("files", [])}
    print(f"\nDraft now holds {len(final)}/{len(RELEASE_FILES)} release files.")
    still = [fn for fn in RELEASE_FILES if fn not in final]
    if still:
        print(f"[WARN] still missing: {still} - re-run before publishing.")

    draft_url = chk["links"].get("html", "")
    print(f"DRAFT ready for review: {draft_url}")

    if not args.publish_final:
        print("\nDRAFT ONLY. DOI NOT minted. Review, then re-run with "
              "--publish-final to mint (irreversible).")
        sys.exit(0)

    if still:
        print("\n[ABORT] Refusing to publish an incomplete file set.")
        sys.exit(4)

    print("\n--publish-final set. Minting DOI (IRREVERSIBLE)...")
    pr = requests.post(
        f"{ZENODO_API}/deposit/depositions/{args.draft_id}/actions/publish",
        params=params, timeout=to)
    pr.raise_for_status()
    published = pr.json()
    doi = published.get("doi") or published.get("metadata", {}).get("doi")
    concept = published.get("conceptdoi") or published.get("metadata", {}).get("conceptdoi")
    print(f"PUBLISHED. Version DOI: {doi}")
    print(f"Concept DOI: {concept}")
    print(f"Record: {published['links'].get('record_html', '')}")
    with open(os.path.join(here, "ZENODO_PUBLISHED.json"), "w") as f:
        json.dump({"record_id": args.draft_id, "version_doi": doi,
                   "concept_doi": concept,
                   "record_html": published["links"].get("record_html", "")},
                  f, indent=2)


if __name__ == "__main__":
    main()
