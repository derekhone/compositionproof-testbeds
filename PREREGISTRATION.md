# CompositionProof-2 — Preregistration

**Experiment:** CompositionProof-2 — multi-epoch cross-witness correlation
**Program:** Remnant Fieldworks Inc. — ExecutionProof™ / CIF, "Proof composition" candidate law (Deep Research Question #5)
**Author:** Hone, Derek — Remnant Fieldworks Inc.
**Status:** PREREGISTERED — design frozen BEFORE any hardware result. ZERO QPU spent at time of registration.
**Date frozen:** 2026-09-08

> This document is written and SHA-256 locked **before** any hardware epoch is
> collected. The classification rule (§4), power analysis (§5), permitted claim
> (§6) and forbidden claims (§7) are fixed in advance so the eventual verdict
> cannot be steered by the data. Hardware is gated behind an explicit CEO
> authorization token `GO COMPOSITIONPROOF-2` (see §9).

---

## 1. Question and motivation

CompositionProof-1 and OMNI-1 (DOI 10.5281/zenodo.21436092) each certified that
multiple nonclassicality witnesses pass **simultaneously in one recorded state**
(a single calibration epoch). Neither could address a distinct, genuinely new
question, because both are **single-epoch**:

> **When the same two witnesses (CHSH and Mermin-3) are executed repeatedly
> across many DISTINCT calibration epochs on the same device, are their
> epoch-to-epoch FLUCTUATIONS statistically correlated?**

This is the empirical content of the RF "Proof composition" candidate law:

- **Correlated fluctuations** → the two witnesses share a **common-mode device
  dependence**; composition on one chip is *not* a clean combination of
  independent evidence channels.
- **Uncorrelated fluctuations** → the witnesses drift independently;
  composition behaves like independent evidence channels **within tested bounds**.

CompositionProof-2 does not redesign the witnesses. It is the **multi-epoch
extension of CompositionProof-1's exact witnesses.**

## 2. Witnesses (reused verbatim from CompositionProof-1)

Per epoch, one 8-circuit battery, **byte-compatible** with CompositionProof-1:

| Witness | Circuits | Statistic | Single-epoch pass threshold |
|---|---|---|---|
| W1 CHSH (2-qubit Bell) | 4 (`a0_b0,a0_b1,a1_b0,a1_b1`) | S | S ≥ 2.2 |
| W2 Mermin-3 (3-qubit GHZ) | 4 (`XYY,YXY,YYX,XXX`) | M | M ≥ 2.6 |

- Shots per circuit: **4000** (frozen).
- The circuit definitions are identical to `submit_epoch.py::build_all_circuits`
  and `composition2_sim.py`; any change breaks the SHA-256 manifest.

## 3. Longitudinal design

- **One 8-circuit battery per DISTINCT device calibration epoch.**
- **"Epoch" is defined as a distinct device calibration state**, identified by
  `backend.properties().last_update_date`. Two batteries submitted inside the
  same calibration cycle are **NOT** two independent epochs and are rejected by
  the submitter and the verifier.
- **N_target = 30** distinct calibration epochs. **N_min = 20**; below N_min the
  verdict is capped at INCONCLUSIVE.
- Because IBM devices recalibrate roughly once per day, ~30 epochs span **weeks**
  and cross **multiple 28-day rolling QPU windows**. The ~330 QPU-seconds of
  total sampler time is therefore spread across windows and does **not** consume
  330 s from any single window.
- Each epoch records a calibration snapshot (calibration timestamp, median T1,
  median T2, median readout error) so independence is auditable after the fact.

## 4. Estimator and FROZEN classification rule

For each epoch *i* the battery yields (S_i, M_i). Over the N epochs:

- **Primary estimator:** Spearman rank correlation ρ_s between {S_i} and {M_i}.
- **Secondary estimator:** Pearson correlation r (reported, not decisive).
- **Uncertainty:** 95% **epoch-bootstrap** CI on ρ_s (resample epochs with
  replacement, `N_BOOT = 5000`, `BOOT_SEED = 20260908`).
- **Material-effect band:** `EFFECT_BAND = 0.30` (|ρ| ≥ 0.30 is material).
- **Shot-noise drift guard:** the epoch-to-epoch std of each witness must exceed
  the shot-noise floor `2/sqrt(shots)` by `DRIFT_GUARD_Z = 2.0`. You cannot
  estimate the correlation of fluctuations that are indistinguishable from shot
  noise.

Frozen verdicts (evaluated in this order):

| Verdict | Condition |
|---|---|
| **INCONCLUSIVE_NO_DRIFT** | either witness's epoch std does not clear the drift guard (no real drift to correlate). |
| **INCONCLUSIVE** | n_eff < N_min (20), OR epochs not independent (shared calibration timestamps), OR the bootstrap CI straddles both 0 and ±EFFECT_BAND. |
| **CORRELATED** | drift present, epochs independent, n_eff ≥ N_min, and the 95% CI for ρ_s lies **entirely outside** (−EFFECT_BAND, +EFFECT_BAND) (i.e. \|ρ_s\| materially and significantly > 0). |
| **UNCORRELATED** | drift present, epochs independent, n_eff ≥ N_min, and the 95% CI for ρ_s lies **entirely inside** (−EFFECT_BAND, +EFFECT_BAND) (equivalence: correlation certified small). |

These constants are duplicated in `verifier2.py` and `composition2_sim.py` and
are covered by the SHA-256 manifest.

## 5. Power analysis and two-stage adaptive plan

Control simulations (`control_validate2.py`, output
`control_validation2_output.json`) establish an important, honest asymmetry:

- **Detecting** a real correlation (e.g. true ρ ≈ 0.75) is reliable at **n ≈ 30**.
- **Certifying ABSENCE** of correlation — the UNCORRELATED *equivalence* verdict,
  CI entirely within ±0.30 at true ρ = 0 — requires roughly **n ≈ 150** epochs.
  At n = 30 with true ρ = 0 the honest verdict is INCONCLUSIVE, not UNCORRELATED.

Preregistered **two-stage adaptive design**:

- **Stage 1 — n = 30 epochs.** If the verdict is **CORRELATED**, stop: the
  primary hypothesis (common-mode composition) is supported.
- **Stage 2 — extend toward n ≈ 150 epochs** ONLY if Stage 1 is INCONCLUSIVE and
  we wish to certify UNCORRELATED. Stage 2 is itself gated (a fresh
  `GO COMPOSITIONPROOF-2` is required to continue collecting epochs).

## 6. Permitted claim (the ONLY claim this experiment can support)

> Across N distinct measured calibration epochs on one named IBM device over the
> measured window, the epoch-to-epoch fluctuations of the CHSH and Mermin-3
> witnesses were [correlated / uncorrelated within ±0.30 / inconclusive], with
> the stated Spearman estimate and 95% epoch-bootstrap CI.

## 7. Forbidden claims (explicitly out of scope)

- ✗ "Proved the witnesses are independent" (absence needs the Stage-2 equivalence result, and even then only within ±0.30 on one device).
- ✗ "Proved a causal common cause" (correlation ≠ causation).
- ✗ "Device-independent" or "loophole-free" (locality + detection loopholes OPEN).
- ✗ "Universal" / "for all devices" / "for all witness pairs" (one device, one pair, one window).
- ✗ "First / only" anything beyond what is documented by cited DOIs.

## 8. Honesty bounds (carry into every artifact)

- Device-dependent witnesses on **co-located qubits**. Locality and detection
  loopholes **OPEN**. NOT device-independent; NOT loophole-free.
- Any cross-epoch correlation is an **OBSERVED association** on one device over
  the measured window — not a causal common cause, not a universal statement.
- **"Epoch" = a distinct calibration state.** Batteries sharing a calibration
  cycle are not independent epochs.
- The Aer simulation is a **feasibility check only** (that the estimator and
  guard behave), not evidence about real hardware correlation.
- Correlation ≠ causation; a small measured correlation does not prove
  mechanistic independence.

## 9. QPU budget, gating, and timeline

- **Per epoch:** 8 circuits × 4000 shots ≈ ~11 QPU-seconds of sampler time
  (backend-dependent).
- **N_target = 30 epochs → ~330 QPU-seconds total**, spread across weeks and
  multiple 28-day rolling windows (≈ 1 epoch per calibration cycle).
- **Hardware is GATED.** `submit_epoch.py` submits nothing unless ALL gates
  pass: `--go-token "GO COMPOSITIONPROOF-2"`, `--i-have-ceo-authorization`,
  a valid `--epoch-id`, and a verifying SHA-256 manifest. It additionally
  refuses to record an epoch whose calibration timestamp already appears in the
  series (independence guard).
- At preregistration time: **hardware_submitted = false; 0 QPU-seconds spent.**

## 10. Reproducibility artifacts

| File | Role |
|---|---|
| `composition2_sim.py` | Aer feasibility simulation (ZERO QPU). |
| `verifier2.py` | INDEPENDENT verifier (SciPy; distinct implementation). |
| `control_validate2.py` | Synthetic control suite (all verdicts reachable). |
| `submit_epoch.py` | GATED per-epoch hardware submitter. |
| `composition2_sim_result.json` | Feasibility sim output. |
| `control_validation2_output.json` | Control suite output (all_pass). |
| `series_example_sim.json` | Example multi-epoch series (from sim). |
| `verifier2_output_example.json` | Independent verifier run on the example. |
| `SHA256_MANIFEST.txt` | Freezes every artifact above + this document. |
| `lock_candidate.json` | Composite lock + design summary. |
