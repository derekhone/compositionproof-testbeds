#!/usr/bin/env python3
"""CompositionProof-2 - offline retrieval + S/M computation for ONE epoch.

Reads a completed job's counts, computes CHSH S and Mermin-3 M using the EXACT
preregistered estimators from composition2_sim.py (parity_expectation, chsh_S,
mermin_M), and fills S/M for the matching epoch in epoch_series.json.

This does NOT submit anything and does NOT emit a final cross-witness verdict.
A final verdict requires >= N_MIN=20 distinct calibration epochs.
"""
import argparse, json, os, sys

# Reuse the FROZEN estimators, not re-implementations.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from composition2_sim import parity_expectation, chsh_S, mermin_M, SHOTS

CHSH_LABELS = ["a0_b0", "a0_b1", "a1_b0", "a1_b1"]
MER_LABELS = ["XYY", "YXY", "YYX", "XXX"]
SERIES_FILE = "epoch_series.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--job-id", required=True)
    ap.add_argument("--epoch-id", type=int, required=True)
    args = ap.parse_args()

    with open(os.path.expanduser("~/.config/abacusai_auth_secrets.json")) as f:
        sec = json.load(f)
    tok = None
    for k in sec:
        if "ibm" in k.lower():
            for sk, sv in sec[k]["secrets"].items():
                if "token" in sk.lower():
                    tok = sv["value"]; break
    from qiskit_ibm_runtime import QiskitRuntimeService
    svc = QiskitRuntimeService(channel="ibm_quantum_platform", token=tok)
    job = svc.job(args.job_id)
    print("job status:", job.status())
    res = job.result()

    # SamplerV2: 8 pubs in submit order [CHSH x4, Mermin x4].
    def counts_for(idx):
        pub = res[idx]
        data = pub.data
        # get the single classical register regardless of its name
        reg = next(iter(data.__dict__.values())) if hasattr(data, "__dict__") else None
        # robust: use get_counts via BitArray
        for attr in dir(data):
            obj = getattr(data, attr)
            if hasattr(obj, "get_counts"):
                return obj.get_counts()
        raise RuntimeError("no counts found in pub data")

    chsh_res = {CHSH_LABELS[i]: counts_for(i) for i in range(4)}
    mer_res = {MER_LABELS[i]: counts_for(4 + i) for i in range(4)}

    S = chsh_S(chsh_res)
    M = mermin_M(mer_res)
    E_chsh = {k: round(parity_expectation(v, SHOTS), 5) for k, v in chsh_res.items()}
    E_mer = {k: round(parity_expectation(v, SHOTS), 5) for k, v in mer_res.items()}
    print(f"CHSH  S = {S:.4f}  (classical<=2, quantum~2.828, single-epoch thr 2.2)")
    print(f"Mermin M = {M:.4f}  (classical<=2, quantum 4, single-epoch thr 2.6)")
    print("CHSH E:", E_chsh)
    print("Mermin E:", E_mer)

    # capture usage if available
    usage_s = None
    try:
        m = job.metrics()
        usage_s = m.get("usage", {}).get("quantum_seconds") or m.get("usage", {}).get("seconds")
    except Exception:
        pass

    with open(SERIES_FILE) as f:
        series = json.load(f)
    hit = False
    for e in series["epochs"]:
        if e.get("epoch_id") == args.epoch_id and e.get("job_id") == args.job_id:
            e["S"] = round(S, 6)
            e["M"] = round(M, 6)
            e["E_chsh"] = E_chsh
            e["E_mermin"] = E_mer
            e["raw_counts"] = {"CHSH": chsh_res, "Mermin3": mer_res}
            if usage_s is not None:
                e["qpu_usage_seconds"] = usage_s
            hit = True
    if not hit:
        print("WARN: matching epoch/job not found; not modifying series.")
        sys.exit(4)
    with open(SERIES_FILE, "w") as f:
        json.dump(series, f, indent=2)
    n = len(series["epochs"])
    print(f"\nRecorded S/M for epoch {args.epoch_id}. Series now has {n} epoch(s).")
    print("NO FINAL VERDICT: cross-witness correlation needs N_MIN=20 distinct epochs.")


if __name__ == "__main__":
    main()
