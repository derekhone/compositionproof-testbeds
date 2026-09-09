# CompositionProof-2 - Public Research Record

**Cross-Witness Correlation Across Quantum Hardware Calibration Epochs**

Derek Hone - Remnant Fieldworks Inc.
Family: Proof Composition (RF Proof Family - Deep Research Question #5)

**DOI (this version):** [10.5281/zenodo.22666466](https://doi.org/10.5281/zenodo.22666466)
**DOI (concept, all versions):** [10.5281/zenodo.22666465](https://doi.org/10.5281/zenodo.22666465)

---

## STATUS: LONGITUDINAL HARDWARE CAMPAIGN IN PROGRESS - 1 / >=20 DISTINCT CALIBRATION EPOCHS COLLECTED - NO FINAL VERDICT

Epoch 1 was executed on IBM `ibm_marrakesh` under the frozen, preregistered
protocol. **CHSH S = 2.7205; Mermin-3 |M| = 3.7710.** These values describe
**Epoch 1 only.** CompositionProof-2 has not yet reached its preregistered
minimum sample (N_min = 20 distinct calibration epochs, N_target = 30), and
**no CORRELATED / UNCORRELATED / INCONCLUSIVE campaign verdict is claimed or
implied by this record.** A single epoch has no fluctuation series, so no
cross-witness correlation can be estimated from it.

> **Prior authorization does not constitute current execution permission.**
> Each hardware epoch requires fresh authorization after verification of
> calibration state, package integrity, remaining QPU allocation, and
> prior-epoch count. See `GOVERNANCE.md`.

---

## What this record is

This is a **preregistered, longitudinal hardware research campaign**. The
experimental design, the sampling plan, the correlation estimator, the effect
band, the drift guards, and the exact wording of the permitted claim were
**frozen and SHA-256 hash-locked BEFORE any quantum hardware ran**. The record
is published in progress so that anyone looking later can prove that the
protocol, thresholds, governance rules, and early data existed **before** the
final outcome was known.

That is the scientific point. The value is not any single epoch number. It is
that the design and its stopping rules are cryptographically fixed, and that
each epoch's verdict components can be re-derived from raw counts by an
independent verifier that shares nothing with the code that sized or submitted
the experiment.

Preregistration and post-execution evidence are kept as **separate layers**.
The frozen preregistration is **not** rewritten to incorporate Epoch 1.

---

## The question (frozen, verbatim from the lock)

When CHSH and Mermin-3 (CompositionProof-1's exact witnesses, byte-compatible)
are run repeatedly across many **distinct calibration epochs** on one named
device, are their epoch-to-epoch **fluctuations** correlated?

- Correlated -> common-mode device dependence.
- Uncorrelated (within +/-0.30) -> independent drift, within the tested bounds.

"Epoch" = a distinct calibration state (`backend.properties().last_update_date`).
Batteries that share a calibration state are **not** independent epochs.

---

## Permitted claim (verbatim, as preregistered) - applies only after N >= N_min

> Across N distinct measured calibration epochs on one named IBM device over the
> measured window, the CHSH and Mermin-3 epoch-to-epoch fluctuations were
> [correlated / uncorrelated within +/-0.30 / inconclusive], with the stated
> Spearman estimate and 95% epoch-bootstrap CI.

**No permitted campaign claim is available yet.** N = 1 < N_min = 20.

---

## What this does NOT show

- It does **not** prove the witnesses are independent.
- It does **not** prove a causal common cause (correlation != causation).
- It is **not** device-independent and **not** loophole-free.
- It is **not** universal (not for all devices, not for all witness pairs).
- It claims **no** first/only status beyond the cited DOIs.

### Honesty bounds (frozen)

- Device-dependent witnesses on co-located qubits.
- Locality and detection loopholes are OPEN; NOT device-independent; NOT loophole-free.
- Any future cross-epoch correlation is an OBSERVED association on one device over the measured window; NOT a causal common cause; NOT universal.
- "Epoch" = distinct calibration state; shared-calibration batteries are not independent epochs.
- Detecting a correlation is reliable at n ~ 30; **certifying the absence** of one needs n ~ 150 (two-stage design). This record cannot certify absence.

---

## Epoch 1 evidence (collected 2026-09-08)

| Field | Value |
|---|---|
| Job ID | `dag4fnfi3e6s738ltnpg` |
| Backend | `ibm_marrakesh` (IBM Heron r2, 156 qubits) |
| Calibration timestamp | `2026-09-08T16:59:31+00:00` (`last_update_date`) |
| Circuits x shots | 8 x 4000 = 32,000 shots |
| CHSH S | 2.7205 (classical <= 2, Tsirelson 2.828, threshold 2.2) |
| Mermin-3 \|M\| | 3.7710 (classical <= 2, quantum 4, threshold 2.6) |
| Actual QPU charge | 11 s |
| Status | COLLECTED - NO FINAL VERDICT |

Per-setting CHSH E: a0b0 = 0.6770, a0b1 = -0.6745, a1b0 = 0.6630, a1b1 = 0.7060.
Per-setting Mermin E: XYY = -0.9495, YXY = -0.9415, YYX = -0.9355, XXX = 0.9445.
Calibration snapshot medians: T1 = 168.87 us, T2 = 66.95 us, readout error = 0.011475.

Full machine-readable record: `epoch_series.json`. Human record: `EPOCH1_RECORD.md`.

---

## Repository contents

| File | What it is |
|---|---|
| `PREREGISTRATION.md` / `.pdf` | Frozen preregistered protocol (design, sampling, estimator, verdict rules) |
| `lock_candidate.json` | Frozen design object (question, witnesses, thresholds, permitted/forbidden claims, honesty bounds) |
| `SHA256_MANIFEST.txt` | Per-file SHA-256 manifest of the frozen package |
| `GOVERNANCE.md` | Fresh-GO-each-cycle epoch submission protocol |
| `EPOCH1_RECORD.md` / `.pdf` | Epoch 1 human-readable record |
| `epoch_series.json` | Machine-readable epoch series (currently 1 of >= 20) |
| `composition2_sim.py` | Locked simulation + estimators (`parity_expectation`, `chsh_S`, `mermin_M`) |
| `submit_epoch.py` | Gated hardware submitter (token "GO COMPOSITIONPROOF-2" + independence guard) |
| `retrieve_epoch.py` | Offline retrieval + estimator computation (no submit, no verdict) |
| `verifier2.py` | Independent verifier |
| `control_validate2.py` | Control suite |
| `CITATION.cff` | Citation metadata |

**Frozen composite lock:** `ebe0919b997341569670ccd27b2a8ff754599d242489a2b06ff4db20c8872fd6`
(11 files; verified INTACT before the Epoch 1 submission).

---

## Relationship to prior RF work

CompositionProof-2 addresses the genuinely new question that **OMNI-1**
(DOI [10.5281/zenodo.21436092](https://doi.org/10.5281/zenodo.21436092)) and
CompositionProof-1 could not: both are **single-epoch**. Single-epoch records
certify *simultaneous* composition only; the **correlation of witness
fluctuations across calibration epochs** is the open longitudinal question this
campaign tests. CompositionProof-1 is retained internally as the validated
single-epoch replication and the frozen substrate CP-2 reuses unchanged.

---

## Reproduce an epoch's numbers offline

```
python3 retrieve_epoch.py --job-id <IBM_JOB_ID> --epoch-id <N>
```

This retrieves the preserved counts and recomputes S and M with the locked
estimators. It does not submit anything and does not emit a verdict.

---

## Citation

See `CITATION.cff`. Cite as: Hone, Derek (2026). *CompositionProof-2:
Cross-Witness Correlation Across Quantum Hardware Calibration Epochs -
Preregistered Protocol and Epoch 1 Evidence.* Remnant Fieldworks Inc.

License: CC-BY-4.0 (documents/data). Code under MIT unless noted.
