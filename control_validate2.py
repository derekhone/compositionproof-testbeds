#!/usr/bin/env python3
"""
CompositionProof-2 — CONTROL VALIDATION (synthetic, ZERO QPU, fast).

Proves the INDEPENDENT verifier (verifier2.py) lands the correct frozen verdict
on synthetic multi-epoch series with KNOWN injected correlation and KNOWN drift
magnitude. This is the rigorous estimator check; the Aer feasibility sim shows
the real-circuit pipeline. If any case fails, the package is NOT lock-ready.

Cases (each asserts an expected verdict):
  1. correlated_strong  n=30, rho=0.75, drift >> shot floor   -> CORRELATED
  2. uncorrelated       n=30, rho=0.00, drift >> shot floor   -> UNCORRELATED
  3. no_drift           n=30, rho=0.00, drift ~ 0             -> INCONCLUSIVE_NO_DRIFT
  4. underpowered       n=12, rho=0.60, drift >> shot floor   -> INCONCLUSIVE (n<min)
  5. shared_calibration n=30 batteries but only 8 distinct
                        calibration timestamps                 -> INCONCLUSIVE (not independent)
"""

import json
import numpy as np

import verifier2

SHOTS = 4000
S0, M0 = 2.70, 3.60          # plausible means near the CompositionProof-1 result
BASE_SEED = 20260908


def make_series(n, rho, drift_std, seed, n_distinct_ts=None):
    """Bivariate-normal drift injected on top of witness means.

    drift_std is the epoch-to-epoch std of each witness statistic. Shot noise is
    added at the true 2/sqrt(shots) scale so the drift guard is exercised
    honestly."""
    rng = np.random.default_rng(seed)
    cov = np.array([[1.0, rho], [rho, 1.0]])
    L = np.linalg.cholesky(cov)
    z = rng.standard_normal((n, 2)) @ L.T
    shot = 2.0 / np.sqrt(SHOTS)
    S = S0 + drift_std * z[:, 0] + shot * rng.standard_normal(n)
    M = M0 + drift_std * z[:, 1] + shot * rng.standard_normal(n)
    # cap into physical ranges
    S = np.clip(S, 0.0, 2.828); M = np.clip(M, 0.0, 4.0)
    epochs = []
    for i in range(n):
        if n_distinct_ts is None:
            ts = f"2026-09-{10 + i:02d}T04:00:00Z"      # all distinct
        else:
            ts = f"2026-09-{10 + (i % n_distinct_ts):02d}T04:00:00Z"
        epochs.append({"epoch_id": i + 1, "calibration_ts": ts,
                       "S": round(float(S[i]), 4), "M": round(float(M[i]), 4)})
    return {"shots_per_circuit": SHOTS, "epochs": epochs}


CASES = [
    ("correlated_strong", dict(n=30, rho=0.75, drift_std=0.10, seed=BASE_SEED + 1),
     "CORRELATED"),
    # UNCORRELATED (an equivalence claim: CI entirely within +/- effect band)
    # requires MANY more epochs than DETECTING a correlation: at rho=0 the
    # Spearman bootstrap CI only fits inside +/-0.30 around n~150. n=30 (and even
    # n=80) land INCONCLUSIVE at rho=0. This detect-vs-certify-absence asymmetry
    # is documented in PREREGISTRATION.md §5 and drives the two-stage design.
    ("uncorrelated",      dict(n=150, rho=0.00, drift_std=0.10, seed=BASE_SEED + 2),
     "UNCORRELATED"),
    ("uncorrelated_underpowered_n30", dict(n=30, rho=0.00, drift_std=0.10, seed=BASE_SEED + 6),
     "INCONCLUSIVE"),
    ("no_drift",          dict(n=30, rho=0.00, drift_std=0.0005, seed=BASE_SEED + 3),
     "INCONCLUSIVE_NO_DRIFT"),
    ("underpowered",      dict(n=12, rho=0.60, drift_std=0.10, seed=BASE_SEED + 4),
     "INCONCLUSIVE"),
    ("shared_calibration", dict(n=30, rho=0.75, drift_std=0.10, seed=BASE_SEED + 5,
                               n_distinct_ts=8),
     "INCONCLUSIVE"),
]


def main():
    results = []
    all_ok = True
    for name, kwargs, expected in CASES:
        bundle = make_series(**kwargs)
        out = verifier2.verify(bundle)
        got = out["VERDICT"]
        ok = (got == expected)
        all_ok &= ok
        results.append({
            "case": name, "expected": expected, "got": got, "pass": ok,
            "spearman_rho": out["spearman_rho"], "spearman_ci95": out["spearman_ci95"],
            "drift_both_detectable": out["drift_guard"]["both_detectable"],
            "n_distinct_epochs": out["n_distinct_calibration_epochs"],
        })
        flag = "PASS" if ok else "FAIL"
        print(f"[{flag}] {name:20s} expected={expected:24s} got={got:24s} "
              f"rho={out['spearman_rho']:+.3f} CI={out['spearman_ci95']}")

    summary = {"experiment": "CompositionProof-2", "all_pass": all_ok,
               "n_cases": len(CASES), "cases": results}
    with open("control_validation2_output.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nALL CONTROL CASES PASS: {all_ok}")
    print("Wrote control_validation2_output.json")
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
