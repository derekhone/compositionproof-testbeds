#!/usr/bin/env python3
"""
CompositionProof-2 - ZENODO DEPOSIT PUBLISHER (GATED).

Minting a DOI is permanent and public. Consistent with RF's hardware-gate
culture, this script will NOT create or publish a Zenodo deposit unless BOTH
gates are satisfied on the command line:

    1. --go-token "PUBLISH COMPOSITIONPROOF-2"   (exact, case-sensitive)
    2. --i-have-ceo-authorization                (explicit acknowledgement flag)

Two-stage safety on top of the gates:
    * Default action is DRAFT ONLY: it creates an unpublished draft deposit and
      uploads the files, then STOPS and prints the draft URL for human review.
    * The deposit is only PUBLISHED (DOI minted, irreversible) if you ALSO pass
      --publish-final. Without it, nothing is minted.

To publish a NEW VERSION under an existing concept record (adding epochs later),
pass --new-version-of <existing_record_id>.

Usage:
    # Stage a reviewable draft (no DOI minted):
    python3 publish_zenodo.py --go-token "PUBLISH COMPOSITIONPROOF-2" \
        --i-have-ceo-authorization

    # Only after reviewing the draft, mint the DOI (irreversible):
    python3 publish_zenodo.py --go-token "PUBLISH COMPOSITIONPROOF-2" \
        --i-have-ceo-authorization --publish-final

Credentials: reads the Zenodo access token from the RF auth-secrets file.
"""

import argparse
import json
import os
import sys

GO_TOKEN_REQUIRED = "PUBLISH COMPOSITIONPROOF-2"
ZENODO_API = "https://zenodo.org/api"
SECRETS_PATH = "/home/ubuntu/.config/abacusai_auth_secrets.json"

# Files uploaded to the deposit (all must live next to this script).
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


def load_metadata():
    with open(os.path.join(os.path.dirname(__file__) or ".", ".zenodo.json")) as f:
        return json.load(f)


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
    ap.add_argument("--publish-final", action="store_true",
                    help="Irreversibly mint the DOI. Without this, a draft only.")
    ap.add_argument("--new-version-of", default="",
                    help="Existing Zenodo record id to add a new version to.")
    args = ap.parse_args()

    print("=" * 68)
    print("CompositionProof-2 - Zenodo publisher (GATED)")
    print("=" * 68)

    if not check_gates(args):
        print("\nGATED. No deposit created. Awaiting explicit CEO authorization.")
        sys.exit(2)

    import requests  # noqa: E402

    here = os.path.dirname(__file__) or "."
    for fn in RELEASE_FILES:
        if not os.path.exists(os.path.join(here, fn)):
            print(f"[ABORT] Missing release file: {fn}")
            sys.exit(3)

    token = load_zenodo_token()
    meta = load_metadata()
    params = {"access_token": token}

    if args.new_version_of:
        print(f"\nCreating a new version of record {args.new_version_of}...")
        nv = requests.post(
            f"{ZENODO_API}/deposit/depositions/{args.new_version_of}/actions/newversion",
            params=params,
        )
        nv.raise_for_status()
        latest_draft = nv.json()["links"]["latest_draft"]
        dep = requests.get(latest_draft, params=params).json()
    else:
        print("\nCreating draft deposit...")
        r = requests.post(f"{ZENODO_API}/deposit/depositions", params=params, json={})
        r.raise_for_status()
        dep = r.json()

    dep_id = dep["id"]
    bucket = dep["links"]["bucket"]
    print(f"  Draft deposit id: {dep_id}")

    print("Uploading files...")
    for fn in RELEASE_FILES:
        with open(os.path.join(here, fn), "rb") as fp:
            ur = requests.put(f"{bucket}/{fn}", data=fp, params=params)
            ur.raise_for_status()
        print(f"  uploaded {fn}")

    print("Attaching metadata...")
    mr = requests.put(
        f"{ZENODO_API}/deposit/depositions/{dep_id}",
        params=params,
        json={"metadata": meta},
    )
    mr.raise_for_status()

    draft_url = dep["links"].get("html", f"{ZENODO_API}/deposit/depositions/{dep_id}")
    print(f"\nDRAFT staged for review: {draft_url}")

    if not args.publish_final:
        print("\nDRAFT ONLY. DOI NOT minted (pass --publish-final to mint, "
              "irreversible). Review the draft first.")
        sys.exit(0)

    print("\n--publish-final set. Minting DOI (IRREVERSIBLE)...")
    pr = requests.post(
        f"{ZENODO_API}/deposit/depositions/{dep_id}/actions/publish",
        params=params,
    )
    pr.raise_for_status()
    published = pr.json()
    doi = published.get("doi") or published.get("metadata", {}).get("doi")
    concept = published.get("conceptdoi") or published.get("metadata", {}).get("conceptdoi")
    print(f"PUBLISHED. Version DOI: {doi}")
    print(f"Concept DOI: {concept}")
    print(f"Record: {published['links'].get('record_html', '')}")
    with open(os.path.join(here, "ZENODO_PUBLISHED.json"), "w") as f:
        json.dump({"record_id": dep_id, "version_doi": doi,
                   "concept_doi": concept,
                   "record_html": published["links"].get("record_html", "")}, f, indent=2)


if __name__ == "__main__":
    main()
