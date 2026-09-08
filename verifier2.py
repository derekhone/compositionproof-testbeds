#!/usr/bin/env python3
"""
CompositionProof-2 — INDEPENDENT VERIFIER (from scratch, no shared code).

Given a multi-epoch series of per-epoch witness statistics (S_i, M_i) — produced
either by the Aer feasibility sim or by the gated hardware campaign — this
verifier independently:

  1. re-derives the cross-witness correlation (Pearson + Spearman) using SciPy
     (a different implementation from the sim's hand-rolled estimators, so
     agreement is meaningful, not tautological),
  2. computes a 95% epoch-bootstrap CI on the primary (Spearman) estimator,
  3. applies the preregistered SHOT-NOISE-FLOOR DRIFT GUARD (you cannot estimate
     the correlation of fluctuations that are indistinguishable from shot noise),
  4. checks that epochs are INDEPENDENT (distinct calibration timestamps),
  5. emits the frozen verdict: CORRELATED / UNCORRELATED / INCONCLUSIVE /
     INCONCLUSIVE_NO_DRIFT,
  6. verifies the frozen SHA-256 manifest if present.

Input (--series series.json):
  {
    "shots_per_circuit": 4000,
    "epochs": [
       {"epoch_id": 1, "calibration_ts": "2026-09-10T04:00:00Z", "S": 2.71, "M": 3.62},
       ...
    ]
  }

No hardware, no network. Pure arithmetic + SciPy stats.
"""

import argparse
import hashlib
import json
import math
import os

import numpy as np
from scipy import stats

# Frozen preregistered constants (must match PREREGISTRATION.md §4).
EFFECT_BAND = 0.30       # |rho| >= 0.30 is a material correlation
DRIFT_GUARD_Z = 2.0      # epoch std must exceed this many shot-noise floors
N_EPOCHS_MIN = 20        # below this, verdict is capped at INCONCLUSIVE
N_BOOT = 5000
BOOT_SEED = 20260908


def shot_floor(shots):
    """Shot-noise std of a 4-correlator witness statistic ~ 2/sqrt(shots)."""
    return 2.0 / math.sqrt(shots)


def drift_detectable(series, shots):
    obs = float(np.std(series, ddof=1))
    floor = shot_floor(shots)
    return (obs > DRIFT_GUARD_Z * floor), round(obs, 4), round(floor, 4)


def bootstrap_spearman_ci(x, y, alpha=0.05):
    rng = np.random.default_rng(BOOT_SEED)
    x = np.asarray(x, float); y = np.asarray(y, float); n = len(x)
    ests = []
    for _ in range(N_BOOT):
        idx = rng.integers(0, n, n)
        if np.std(x[idx]) == 0 or np.std(y[idx]) == 0:
            continue
        ests.append(stats.spearmanr(x[idx], y[idx]).statistic)
    ests = sorted(e for e in ests if not math.isnan(e))
    lo = ests[int((alpha / 2) * len(ests))]
    hi = ests[min(len(ests) - 1, int((1 - alpha / 2) * len(ests)))]
    return round(lo, 4), round(hi, 4)


def classify(rho, ci_lo, ci_hi, drift_ok, n_epochs):
    if not drift_ok:
        return ("INCONCLUSIVE_NO_DRIFT",
                "Epoch-to-epoch variation is not detectably above the shot-noise "
                "floor for at least one witness; there is no fluctuation signal "
                "whose correlation could be estimated.")
    if n_epochs < N_EPOCHS_MIN:
        return ("INCONCLUSIVE",
                f"Only {n_epochs} independent epochs (< preregistered minimum "
                f"{N_EPOCHS_MIN}); estimate not powered for a directional verdict.")
    ci_excludes_zero = (ci_lo > 0) or (ci_hi < 0)
    if ci_excludes_zero and abs(rho) >= EFFECT_BAND:
        return ("CORRELATED",
                "95% CI excludes 0 and |rho| >= effect band; cross-witness "
                "fluctuations are materially associated over the measured window.")
    if ci_lo >= -EFFECT_BAND and ci_hi <= EFFECT_BAND:
        return ("UNCORRELATED",
                "95% CI lies entirely within the +/- effect band; no material "
                "cross-witness correlation over the measured window.")
    return ("INCONCLUSIVE",
            "95% CI is too wide to separate 'no material correlation' from "
            "'material correlation'; more epochs needed.")


def verify_manifest(manifest="SHA256_MANIFEST.txt"):
    if not os.path.exists(manifest):
        return None, "no manifest present (package not locked)"
    bad = []
    for line in open(manifest):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        expected, path = parts
        if not os.path.exists(path):
            bad.append(f"{path} missing"); continue
        got = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if got != expected:
            bad.append(f"{path} mismatch")
    return (len(bad) == 0), ("all match" if not bad else "; ".join(bad))


def verify(bundle):
    shots = bundle.get("shots_per_circuit", 4000)
    epochs = bundle["epochs"]
    S = [e["S"] for e in epochs]
    M = [e["M"] for e in epochs]
    n = len(epochs)

    # Independence: count DISTINCT calibration timestamps.
    ts = [e.get("calibration_ts") for e in epochs if e.get("calibration_ts")]
    distinct_ts = len(set(ts))
    independence_ok = (distinct_ts == n) if ts else None

    pear = stats.pearsonr(S, M)
    spear = stats.spearmanr(S, M)
    rho_s = float(spear.statistic)
    ci_lo, ci_hi = bootstrap_spearman_ci(S, M)

    dS_ok, dS_obs, floor = drift_detectable(S, shots)
    dM_ok, dM_obs, _ = drift_detectable(M, shots)
    drift_ok = dS_ok and dM_ok

    # Effective independent epoch count: if timestamps present, use distinct.
    n_eff = distinct_ts if ts else n
    verdict, reason = classify(rho_s, ci_lo, ci_hi, drift_ok, n_eff)

    # If timestamps present and NOT all distinct, downgrade honesty note.
    if independence_ok is False and verdict in ("CORRELATED", "UNCORRELATED"):
        verdict = "INCONCLUSIVE"
        reason = (f"Only {distinct_ts} distinct calibration epochs among {n} "
                  f"batteries; batteries sharing a calibration are not independent "
                  f"epochs, so a directional verdict is not warranted.")

    return {
        "experiment": "CompositionProof-2",
        "n_batteries": n,
        "n_distinct_calibration_epochs": distinct_ts if ts else "not_provided",
        "epochs_independent": independence_ok,
        "pearson_rho": round(float(pear.statistic), 4),
        "pearson_p": round(float(pear.pvalue), 5),
        "spearman_rho": round(rho_s, 4),
        "spearman_p": round(float(spear.pvalue), 5),
        "spearman_ci95": [ci_lo, ci_hi],
        "primary_estimator": "spearman",
        "effect_band": EFFECT_BAND,
        "drift_guard": {
            "shot_floor": floor,
            "guard_z": DRIFT_GUARD_Z,
            "S_obs_std": dS_obs, "S_detectable": bool(dS_ok),
            "M_obs_std": dM_obs, "M_detectable": bool(dM_ok),
            "both_detectable": bool(drift_ok),
        },
        "VERDICT": verdict,
        "verdict_reason": reason,
        "honesty_bounds": [
            "Device-dependent witnesses on co-located qubits; locality + detection loopholes OPEN.",
            "Correlation is an OBSERVED association on ONE device over the measured window; not causal, not universal.",
            "Correlation of fluctuations is only estimable when epoch drift exceeds the shot-noise floor.",
            "Two batteries in the same calibration cycle are NOT two independent epochs.",
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--series", required=True)
    ap.add_argument("--out", default="verifier2_output.json")
    args = ap.parse_args()

    bundle = json.load(open(args.series))
    result = verify(bundle)
    mok, mmsg = verify_manifest()
    result["manifest_check"] = {"verified": mok, "detail": mmsg}

    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
