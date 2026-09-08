#!/usr/bin/env python3
"""
CompositionProof-2 — FEASIBILITY SIMULATION (Aer only, ZERO QPU time).

Question (the genuinely new science, which OMNI-1 and CompositionProof-1 could
NOT address because both are single-epoch):

    When two nonclassicality witnesses (CHSH and Mermin-3) are executed
    REPEATEDLY across many DISTINCT calibration epochs on the same device,
    are their epoch-to-epoch FLUCTUATIONS statistically CORRELATED?

Why it matters
--------------
CompositionProof-1 certified that both witnesses pass SIMULTANEOUSLY in ONE
recorded state. It explicitly did NOT estimate whether a "good epoch" for CHSH
is also a "good epoch" for Mermin-3. That cross-witness correlation is the
empirical content of the RF "Proof composition" candidate law (Deep Research
Question #5):

  * If the fluctuations are strongly CORRELATED -> the two witnesses share a
    common-mode device dependence; composition on one chip is NOT a clean
    combination of independent evidence channels.
  * If the fluctuations are UNCORRELATED -> the witnesses drift independently;
    composition behaves like independent evidence channels (within tested bounds).

This is a LONGITUDINAL design: one 8-circuit battery (identical to
CompositionProof-1) per distinct calibration epoch, repeated across N epochs.
This simulation does NOT run hardware. It (a) confirms the witnesses reproduce,
(b) shows the correlation estimator recovers an injected correlation, and
(c) validates the shot-noise-floor guard that prevents us from "finding"
correlation in fluctuations that are actually just shot noise.

The witness circuits and single-epoch estimators below are BYTE-COMPATIBLE with
CompositionProof-1 (copied verbatim): CompositionProof-2 is the multi-epoch
extension of the SAME witnesses, not a redesign.

Honesty bounds (carry into every artifact)
------------------------------------------
- Device-dependent witnesses on co-located qubits. Locality + detection
  loopholes OPEN. NOT device-independent; NOT loophole-free.
- Correlation across epochs is an OBSERVED association on ONE device over the
  measured window. It is NOT a proof of a causal common cause, and NOT a
  general statement about all devices or all witness pairs.
- "Epoch" = a DISTINCT device calibration state. Two batteries submitted inside
  the same calibration cycle are NOT two independent epochs.
"""

import json
import math
import hashlib
import time
from datetime import datetime, timezone

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

SEED = 20260908
np.random.seed(SEED)

SHOTS = 4000
# Preregistered single-epoch pass thresholds (identical to CompositionProof-1).
THRESHOLDS = {"CHSH_S_min": 2.2, "MERMIN_M_min": 2.6}

# CompositionProof-2 preregistered correlation-analysis constants.
N_EPOCHS_TARGET = 30       # design target number of distinct calibration epochs
N_EPOCHS_MIN = 20          # minimum for a reportable (possibly INCONCLUSIVE) result
EFFECT_BAND = 0.30         # |rho| >= 0.30 counts as a material correlation
DRIFT_GUARD_Z = 2.0        # epoch-to-epoch variance must exceed shot-noise floor by this z


# ---------------------------------------------------------------------------
# Witness circuits + single-epoch estimators (VERBATIM from CompositionProof-1)
# ---------------------------------------------------------------------------
def parity_expectation(counts, shots):
    total = 0
    for bitstring, n in counts.items():
        bits = bitstring.replace(" ", "")
        parity = (-1) ** (sum(int(b) for b in bits))
        total += parity * n
    return total / shots


def chsh_circuits():
    settings = {
        "a0_b0": (0.0, math.pi / 4),
        "a0_b1": (0.0, 3 * math.pi / 4),
        "a1_b0": (math.pi / 2, math.pi / 4),
        "a1_b1": (math.pi / 2, 3 * math.pi / 4),
    }
    circs = []
    for label, (ta, tb) in settings.items():
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.ry(-ta, 0)
        qc.ry(-tb, 1)
        qc.measure([0, 1], [0, 1])
        circs.append((label, qc))
    return circs


def chsh_S(results):
    E = {k: parity_expectation(v, SHOTS) for k, v in results.items()}
    S = E["a0_b0"] - E["a0_b1"] + E["a1_b0"] + E["a1_b1"]
    return abs(S)


def mermin_circuits():
    bases = {"XYY": "XYY", "YXY": "YXY", "YYX": "YYX", "XXX": "XXX"}
    circs = []
    for label, basis in bases.items():
        qc = QuantumCircuit(3, 3)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(0, 2)
        for q, b in enumerate(basis):
            if b == "X":
                qc.h(q)
            elif b == "Y":
                qc.sdg(q)
                qc.h(q)
        qc.measure(range(3), range(3))
        circs.append((label, qc))
    return circs


def mermin_M(results):
    E = {k: parity_expectation(v, SHOTS) for k, v in results.items()}
    M = E["XYY"] + E["YXY"] + E["YYX"] - E["XXX"]
    return abs(M)


# ---------------------------------------------------------------------------
# Per-epoch execution on Aer
# ---------------------------------------------------------------------------
# Circuits are IDENTICAL every epoch, so transpile ONCE and reuse (big speedup).
_SIM = AerSimulator()
_CHSH = chsh_circuits()
_MER = mermin_circuits()
_CHSH_Q = [transpile(c[1], _SIM, seed_transpiler=42) for c in _CHSH]
_MER_Q = [transpile(c[1], _SIM, seed_transpiler=42) for c in _MER]


def run_battery(sim, noise_model, seed):
    """Run the full 8-circuit battery once (one simulated epoch).

    Uses the pre-transpiled circuits; only the per-epoch noise model changes."""
    jc = sim.run(_CHSH_Q, shots=SHOTS, noise_model=noise_model, seed_simulator=seed)
    jm = sim.run(_MER_Q, shots=SHOTS, noise_model=noise_model, seed_simulator=seed + 1)
    rc = jc.result(); rm = jm.result()
    chsh_res = {_CHSH[i][0]: rc.get_counts(i) for i in range(len(_CHSH))}
    mer_res = {_MER[i][0]: rm.get_counts(i) for i in range(len(_MER))}
    return chsh_S(chsh_res), mermin_M(mer_res)


def epoch_noise(p2, p1_ratio=0.125):
    nm = NoiseModel()
    nm.add_all_qubit_quantum_error(depolarizing_error(p2 * p1_ratio, 1),
                                   ["h", "ry", "sdg", "x"])
    nm.add_all_qubit_quantum_error(depolarizing_error(p2, 2), ["cx", "cz"])
    return nm


# ---------------------------------------------------------------------------
# Correlation estimators (Pearson + Spearman) with epoch-bootstrap CI
# ---------------------------------------------------------------------------
def pearson(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def spearman(x, y):
    def rank(v):
        order = np.argsort(v, kind="mergesort")
        r = np.empty(len(v), float)
        r[order] = np.arange(1, len(v) + 1)
        # average ties
        v = np.asarray(v, float)
        _, inv, cnt = np.unique(v, return_inverse=True, return_counts=True)
        sums = np.zeros(len(cnt)); np.add.at(sums, inv, r)
        return (sums / cnt)[inv]
    return pearson(rank(np.asarray(x, float)), rank(np.asarray(y, float)))


def bootstrap_ci(x, y, fn, n_boot=5000, seed=SEED, alpha=0.05):
    rng = np.random.default_rng(seed)
    n = len(x); x = np.asarray(x, float); y = np.asarray(y, float)
    est = [fn(x[idx], y[idx]) for idx in (rng.integers(0, n, n) for _ in range(n_boot))]
    est = [e for e in est if not math.isnan(e)]
    est.sort()
    lo = est[int((alpha / 2) * len(est))]
    hi = est[min(len(est) - 1, int((1 - alpha / 2) * len(est)))]
    return round(lo, 4), round(hi, 4)


def classify(rho, ci_lo, ci_hi, drift_detectable):
    """Frozen classification rule (see PREREGISTRATION.md §4)."""
    if not drift_detectable:
        return ("INCONCLUSIVE_NO_DRIFT",
                "Epoch-to-epoch variation not detectably above the shot-noise floor; "
                "there is no fluctuation signal whose correlation could be estimated.")
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
            "CI too wide to separate 'no material correlation' from 'material "
            "correlation'; more epochs needed.")


# ---------------------------------------------------------------------------
# Simulated multi-epoch campaign
# ---------------------------------------------------------------------------
def simulate_campaign(mode, n_epochs, base_p2=0.012, drift_sigma=0.045, seed=SEED):
    """Simulate N epochs under a drift model.

    mode = 'common_mode' : one shared drift factor scales BOTH witnesses'
                           two-qubit error each epoch  -> correlated fluctuations.
    mode = 'independent'  : CHSH and Mermin get INDEPENDENT drift draws
                           -> uncorrelated fluctuations.
    mode = 'static'       : no epoch drift (only shot noise) -> drift guard should
                           report NOT detectable -> INCONCLUSIVE_NO_DRIFT.
    """
    rng = np.random.default_rng(seed)
    sim = AerSimulator()
    S_series, M_series = [], []
    for e in range(n_epochs):
        if mode == "static":
            p2c = p2m = base_p2
        elif mode == "common_mode":
            f = max(0.0, rng.normal(0.0, drift_sigma))
            p2c = base_p2 + f
            p2m = base_p2 + f            # SAME drift drives both
        elif mode == "independent":
            p2c = base_p2 + max(0.0, rng.normal(0.0, drift_sigma))
            p2m = base_p2 + max(0.0, rng.normal(0.0, drift_sigma))  # separate draws
        else:
            raise ValueError(mode)
        # separate noise env per witness so the drift model is honest
        S, _ = run_battery(sim, epoch_noise(p2c), seed=int(rng.integers(1, 10**6)))
        _, M = run_battery(sim, epoch_noise(p2m), seed=int(rng.integers(1, 10**6)))
        S_series.append(round(S, 4)); M_series.append(round(M, 4))
    return S_series, M_series


def drift_detectable(series, shots=SHOTS):
    """Is epoch-to-epoch variance above the within-epoch shot-noise floor?

    Shot-noise std of a parity expectation over `shots` is ~1/sqrt(shots) per
    setting; S and M sum 4 such terms, so a conservative shot-noise floor on the
    statistic is ~2/sqrt(shots). We flag drift as detectable if the observed
    epoch std exceeds DRIFT_GUARD_Z * that floor."""
    obs_std = float(np.std(series, ddof=1))
    floor = 2.0 / math.sqrt(shots)
    return obs_std > DRIFT_GUARD_Z * floor, round(obs_std, 4), round(floor, 4)


def analyze(S_series, M_series):
    rho_p = pearson(S_series, M_series)
    rho_s = spearman(S_series, M_series)
    ci_p = bootstrap_ci(S_series, M_series, pearson)
    ci_s = bootstrap_ci(S_series, M_series, spearman)
    dS = drift_detectable(S_series); dM = drift_detectable(M_series)
    drift_ok = dS[0] and dM[0]
    # Primary estimator = Spearman (robust to non-linear drift).
    verdict, reason = classify(rho_s, ci_s[0], ci_s[1], drift_ok)
    return {
        "n_epochs": len(S_series),
        "S_series": S_series,
        "M_series": M_series,
        "pearson_rho": round(rho_p, 4),
        "pearson_ci95": list(ci_p),
        "spearman_rho": round(rho_s, 4),
        "spearman_ci95": list(ci_s),
        "primary_estimator": "spearman",
        "drift_detectable": {
            "both": bool(drift_ok),
            "S": {"detectable": bool(dS[0]), "obs_std": dS[1], "shot_floor": dS[2]},
            "M": {"detectable": bool(dM[0]), "obs_std": dM[1], "shot_floor": dM[2]},
        },
        "effect_band": EFFECT_BAND,
        "VERDICT": verdict,
        "verdict_reason": reason,
    }


def main():
    t0 = time.time()
    # Feasibility uses a smaller N to stay fast; the hardware design target is 30.
    n = 24
    scenarios = {}
    for mode in ("common_mode", "independent", "static"):
        S, M = simulate_campaign(mode, n)
        scenarios[mode] = analyze(S, M)

    out = {
        "experiment": "CompositionProof-2",
        "title": "Multi-Epoch Cross-Witness Correlation of Two Nonclassicality Witnesses",
        "maps_to": "RF Proof Family 'Proof composition' candidate law; Deep Research Question #5 (multi-epoch)",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "shots_per_circuit": SHOTS,
        "design_target_epochs": N_EPOCHS_TARGET,
        "min_epochs": N_EPOCHS_MIN,
        "feasibility_epochs_simulated": n,
        "scenarios": scenarios,
        "hardware_budget_estimate": {
            "circuits_per_epoch": 8,
            "shots_per_circuit": SHOTS,
            "shots_per_epoch": 8 * SHOTS,
            "epochs_target": N_EPOCHS_TARGET,
            "est_qpu_seconds_per_epoch": 11,          # measured in CompositionProof-1
            "est_qpu_seconds_total_target": 11 * N_EPOCHS_TARGET,
            "note": ("Longitudinal: ONE battery per distinct calibration epoch. Epochs "
                     "span real recalibration boundaries (~1/day), so the ~330 QPU-s "
                     "total is spread across weeks and multiple 28-day rolling windows; "
                     "it does NOT consume 330 s from a single window."),
        },
        "honesty_bounds": [
            "Device-dependent witnesses on co-located qubits; locality + detection loopholes OPEN.",
            "Correlation is an OBSERVED association on ONE device over the measured window; not a causal or universal claim.",
            "If epoch-to-epoch drift is not detectable above shot noise, correlation is NOT estimable (INCONCLUSIVE_NO_DRIFT).",
            "Simulation only; NO IBM hardware job submitted. Hardware gated on explicit 'GO COMPOSITIONPROOF-2'.",
        ],
        "hardware_submitted": False,
        "status": "FEASIBILITY SIMULATION COMPLETE — awaiting explicit 'GO COMPOSITIONPROOF-2' before any hardware.",
    }
    out["record_hash"] = hashlib.sha256(
        json.dumps(out, sort_keys=True).encode()).hexdigest()
    out["sim_wall_seconds"] = round(time.time() - t0, 1)

    with open("composition2_sim_result.json", "w") as f:
        json.dump(out, f, indent=2)

    print("=" * 70)
    print(" CompositionProof-2 — FEASIBILITY SIMULATION (Aer, ZERO QPU)")
    print("=" * 70)
    for mode, r in scenarios.items():
        print(f"\n[{mode.upper()}]  (n={r['n_epochs']} simulated epochs)")
        print(f"  Spearman rho = {r['spearman_rho']:+.3f}  CI95 {r['spearman_ci95']}")
        print(f"  Pearson  rho = {r['pearson_rho']:+.3f}  CI95 {r['pearson_ci95']}")
        print(f"  drift detectable (S/M): {r['drift_detectable']['S']['detectable']}"
              f"/{r['drift_detectable']['M']['detectable']}")
        print(f"  VERDICT: {r['VERDICT']}")
    print(f"\n  wall {out['sim_wall_seconds']}s   record_hash {out['record_hash'][:16]}...")
    print("  Wrote composition2_sim_result.json")


if __name__ == "__main__":
    main()
