#!/usr/bin/env python3
"""
CompositionProof-2 — GATED PER-EPOCH HARDWARE SUBMISSION.

CompositionProof-2 is a LONGITUDINAL experiment: the SAME 8-circuit battery
(CHSH + Mermin-3, byte-compatible with CompositionProof-1) is submitted ONCE per
DISTINCT device calibration epoch, and the epoch-to-epoch fluctuations of the two
witnesses are later tested for cross-witness correlation by verifier2.py.

This is the ONLY script in the package that can touch IBM hardware. Like
CompositionProof-1 it is locked behind independent gates so it cannot fire by
accident, by import, or by a stray run. ALL must be satisfied on the command
line for a single epoch to be submitted:

    1. --go-token "GO COMPOSITIONPROOF-2"    (exact, case-sensitive)
    2. --i-have-ceo-authorization            (explicit acknowledgement flag)
    3. --epoch-id N                          (integer epoch index)
    4. frozen SHA-256 manifest must verify   (hardware only ever runs the
                                              exact preregistered package)

Additionally, to protect the core scientific requirement that each epoch is an
INDEPENDENT calibration state, the script reads the live backend calibration
timestamp (backend.properties().last_update_date) and REFUSES to record a new
epoch whose calibration timestamp already appears in epoch_series.json — two
batteries inside the same calibration cycle are NOT two independent epochs.

Until Derek issues "GO COMPOSITIONPROOF-2", a bare run only prints gate status
and exits non-zero. NO job is created on import or on a bare run.

Usage (only after CEO GO, once per distinct calibration epoch, ~1/day):
    python3 submit_epoch.py \
        --go-token "GO COMPOSITIONPROOF-2" \
        --i-have-ceo-authorization \
        --epoch-id 1 \
        --backend ibm_marrakesh

After a job completes, run retrieve_epoch.py (or feed job results into
verifier2.py) to fill in S and M for that epoch. When >= N_EPOCHS_MIN distinct
epochs are collected, verifier2.py emits the frozen cross-witness verdict.

Honesty bounds: device-dependent witnesses on co-located qubits; locality and
detection loopholes OPEN; NOT device-independent; NOT loophole-free. Any
cross-epoch correlation is an OBSERVED association on one device over the
measured window — NOT a causal common cause, NOT a universal statement.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

GO_TOKEN_REQUIRED = "GO COMPOSITIONPROOF-2"
MANIFEST = "SHA256_MANIFEST.txt"
SERIES_FILE = "epoch_series.json"
SHOTS = 4000
SEED = 20260908


# ---------------------------------------------------------------------------
# Gate helpers
# ---------------------------------------------------------------------------
def verify_manifest():
    """Return (ok, message). Recompute every hash in SHA256_MANIFEST.txt."""
    if not os.path.exists(MANIFEST):
        return False, f"missing {MANIFEST} — package not locked yet."
    bad = []
    with open(MANIFEST) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            expected, path = parts
            if not os.path.exists(path):
                bad.append(f"{path} (missing)")
                continue
            got = hashlib.sha256(open(path, "rb").read()).hexdigest()
            if got != expected:
                bad.append(f"{path} (hash mismatch)")
    if bad:
        return False, "manifest verification FAILED: " + "; ".join(bad)
    return True, "manifest verified — all frozen artifacts intact."


def check_gates(args):
    reasons = []
    if args.go_token != GO_TOKEN_REQUIRED:
        reasons.append(
            f'gate 1 FAILED: --go-token must be exactly "{GO_TOKEN_REQUIRED}".'
        )
    if not args.i_have_ceo_authorization:
        reasons.append(
            "gate 2 FAILED: --i-have-ceo-authorization flag not supplied."
        )
    if args.epoch_id is None or args.epoch_id < 1:
        reasons.append(
            "gate 3 FAILED: --epoch-id must be a positive integer."
        )
    ok_manifest, msg = verify_manifest()
    if not ok_manifest:
        reasons.append(f"gate 4 FAILED: {msg}")
    return reasons


# ---------------------------------------------------------------------------
# Circuits (identical to CompositionProof-1 / the preregistered design)
# ---------------------------------------------------------------------------
def build_all_circuits():
    """Import qiskit lazily so a bare/blocked run has zero heavy side effects."""
    import math
    from qiskit import QuantumCircuit

    circs = []  # (witness, label, qc)

    # W1 CHSH
    chsh = {
        "a0_b0": (0.0, math.pi / 4),
        "a0_b1": (0.0, 3 * math.pi / 4),
        "a1_b0": (math.pi / 2, math.pi / 4),
        "a1_b1": (math.pi / 2, 3 * math.pi / 4),
    }
    for label, (ta, tb) in chsh.items():
        qc = QuantumCircuit(2, 2)
        qc.h(0); qc.cx(0, 1)
        qc.ry(-ta, 0); qc.ry(-tb, 1)
        qc.measure([0, 1], [0, 1])
        circs.append(("CHSH", label, qc))

    # W2 Mermin-3
    for basis in ("XYY", "YXY", "YYX", "XXX"):
        qc = QuantumCircuit(3, 3)
        qc.h(0); qc.cx(0, 1); qc.cx(0, 2)
        for q, b in enumerate(basis):
            if b == "X":
                qc.h(q)
            elif b == "Y":
                qc.sdg(q); qc.h(q)
        qc.measure(range(3), range(3))
        circs.append(("Mermin3", basis, qc))

    # TWO-WITNESS design, byte-compatible with CompositionProof-1: CHSH +
    # Mermin-3 only. Total submitted per epoch: 8 circuits.
    assert len(circs) == 8, f"expected 8 two-witness circuits, got {len(circs)}"
    return circs


# ---------------------------------------------------------------------------
# Calibration snapshot (defines what an "epoch" is)
# ---------------------------------------------------------------------------
def calibration_snapshot(backend):
    """Capture the live calibration state that MAKES this an independent epoch."""
    props = backend.properties()
    last_update = props.last_update_date
    cal_ts = last_update.isoformat() if last_update is not None else None

    # Summarize a few representative calibration metrics (median across qubits).
    import statistics as st
    t1s, t2s, ro_errs = [], [], []
    for q in range(backend.num_qubits):
        try:
            t1s.append(props.t1(q))
            t2s.append(props.t2(q))
            ro_errs.append(props.readout_error(q))
        except Exception:
            pass
    snap = {
        "calibration_ts": cal_ts,
        "median_t1_s": round(st.median(t1s), 8) if t1s else None,
        "median_t2_s": round(st.median(t2s), 8) if t2s else None,
        "median_readout_error": round(st.median(ro_errs), 6) if ro_errs else None,
        "num_qubits": backend.num_qubits,
    }
    return cal_ts, snap


def load_series():
    if os.path.exists(SERIES_FILE):
        with open(SERIES_FILE) as f:
            return json.load(f)
    return {"experiment": "CompositionProof-2", "shots_per_circuit": SHOTS,
            "epochs": []}


# ---------------------------------------------------------------------------
# Submission (only reached after all gates pass)
# ---------------------------------------------------------------------------
def submit(args):
    from qiskit import transpile
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    with open(os.path.expanduser("~/.config/abacusai_auth_secrets.json")) as f:
        sec = json.load(f)
    tok = None
    for k in sec:
        if "ibm" in k.lower():
            for sk, sv in sec[k]["secrets"].items():
                if "token" in sk.lower():
                    tok = sv["value"]; break
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok)
    backend = service.backend(args.backend)

    # Independence guard: refuse to record two epochs with the SAME calibration.
    cal_ts, snap = calibration_snapshot(backend)
    series = load_series()
    existing_ts = {e.get("calibration_ts") for e in series["epochs"]}
    existing_ids = {e.get("epoch_id") for e in series["epochs"]}
    if args.epoch_id in existing_ids:
        print(f"REFUSED: epoch_id {args.epoch_id} already recorded in {SERIES_FILE}.")
        sys.exit(3)
    if cal_ts is not None and cal_ts in existing_ts:
        print("REFUSED: this calibration timestamp already appears in "
              f"{SERIES_FILE}.\n  calibration_ts = {cal_ts}\n"
              "  Two batteries inside the same calibration cycle are NOT two "
              "independent epochs. Wait for the next calibration cycle.")
        sys.exit(3)

    circs = build_all_circuits()
    tqcs = [transpile(c[2], backend, seed_transpiler=42) for c in circs]

    sampler = SamplerV2(mode=backend)
    job = sampler.run(tqcs, shots=SHOTS)
    print(f"SUBMITTED epoch {args.epoch_id}: job {job.job_id()} to "
          f"{args.backend} ({len(tqcs)} circuits x {SHOTS} shots)")

    series["epochs"].append({
        "epoch_id": args.epoch_id,
        "calibration_ts": cal_ts,
        "calibration_snapshot": snap,
        "job_id": job.job_id(),
        "backend": args.backend,
        "n_circuits": len(tqcs),
        "shots": SHOTS,
        "submitted_utc": datetime.now(timezone.utc).isoformat(),
        "S": None,   # filled by retrieve_epoch.py / verifier from job results
        "M": None,
    })
    with open(SERIES_FILE, "w") as f:
        json.dump(series, f, indent=2)
    n = len(series["epochs"])
    print(f"Recorded epoch {args.epoch_id} in {SERIES_FILE} "
          f"({n} epoch(s) so far; N_MIN=20, N_target=30).")
    print("When the job completes, fill in S and M for this epoch, then run "
          "verifier2.py --series epoch_series.json once enough epochs exist.")


def main():
    ap = argparse.ArgumentParser(
        description="CompositionProof-2 gated per-epoch hardware submission")
    ap.add_argument("--go-token", default="",
                    help='must be exactly "GO COMPOSITIONPROOF-2"')
    ap.add_argument("--i-have-ceo-authorization", action="store_true")
    ap.add_argument("--epoch-id", type=int, default=None,
                    help="positive integer epoch index (distinct calibration)")
    ap.add_argument("--backend", default="ibm_marrakesh")
    args = ap.parse_args()

    reasons = check_gates(args)
    print("=" * 64)
    print(" CompositionProof-2 — PER-EPOCH HARDWARE SUBMISSION GATE")
    print("=" * 64)
    if reasons:
        print(" STATUS: BLOCKED — no job will be submitted.\n")
        for r in reasons:
            print("  - " + r)
        print('\n To run (only after CEO GO), once per distinct calibration:')
        print('   python3 submit_epoch.py --go-token "GO COMPOSITIONPROOF-2" \\')
        print('       --i-have-ceo-authorization --epoch-id N --backend ibm_marrakesh')
        sys.exit(2)

    print(" STATUS: ALL GATES PASSED — proceeding to submit ONE epoch.\n")
    submit(args)


if __name__ == "__main__":
    main()
