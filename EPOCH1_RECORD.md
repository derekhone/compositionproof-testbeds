# CompositionProof-2 - Epoch 1 Record

**Status: EPOCH 1 COLLECTED - NO FINAL VERDICT.** Data collection only. A cross-witness correlation verdict requires at least N_MIN = 20 distinct calibration epochs (target 30). This is 1 of >= 20.

Authorization: Derek Hone, "GO COMPOSITIONPROOF-2 - COLLECT EPOCH 1 ONLY", 2026-09-08. One epoch battery submitted, then stop.

---

## Pre-flight (all gates passed before submission)

| Gate | Result |
|---|---|
| IBM Quantum access | Restored - channel `ibm_quantum_platform`, token from secrets store, verified live (open plan) |
| Frozen manifest / lock | INTACT - composite `ebe0919b997341569670ccd27b2a8ff754599d242489a2b06ff4db20c8872fd6`, 11/11 files verified |
| Calibration independence | PASS - `ibm_marrakesh` calibration 2026-09-08T16:59:31Z; no prior CP-2 epoch existed, so timestamp is distinct |
| Budget (pre) | 363 s remaining of 600 s (28-day rolling) |

Device choice: `ibm_marrakesh` (primary; same named device as CompositionProof-1 - the longitudinal series must stay on one device). Queue was empty (pending_jobs=0).

---

## Epoch 1 result

| Field | Value |
|---|---|
| Epoch ID | 1 |
| Job ID | `dag4fnfi3e6s738ltnpg` |
| Backend | ibm_marrakesh (Heron r2, 156 qubits) |
| Calibration timestamp | 2026-09-08T16:59:31+00:00 |
| Circuits x shots | 8 x 4000 = 32,000 shots |
| Submitted (UTC) | 2026-09-08T17:37:33Z |
| Job status | DONE |
| **Actual QPU charge** | **11 s** (job metrics `qpu_charge_time_seconds`) |
| Budget after | 352 s remaining of 600 s |

### Witness values (locked estimators from composition2_sim.py)

- **CHSH S = 2.7205** - `|E(a0b0) - E(a0b1) + E(a1b0) + E(a1b1)|` (classical <= 2, Tsirelson ~2.828, single-epoch threshold 2.2). Above classical bound and above threshold.
- **Mermin-3 M = 3.7710** - `|E(XYY) + E(YXY) + E(YYX) - E(XXX)|` (classical <= 2, quantum 4, single-epoch threshold 2.6). Above classical bound and above threshold.

Per-setting expectations:
- CHSH E: a0b0 = 0.6770, a0b1 = -0.6745, a1b0 = 0.6630, a1b1 = 0.7060
- Mermin E: XYY = -0.9495, YXY = -0.9415, YYX = -0.9355, XXX = 0.9445

Calibration snapshot (medians across 156 qubits): T1 = 168.87 us, T2 = 66.95 us, readout error = 0.011475.

Replication note (context, not a verdict): CompositionProof-1 on the same device measured S = 2.7765, M = 3.7365. Epoch 1's S = 2.7205, M = 3.7710 are consistent - both witnesses remain strongly nonclassical in this calibration state.

---

## What this is NOT

- This is **NOT** a PASS or FAIL for CompositionProof-2. The experiment tests whether CHSH and Mermin-3 epoch-to-epoch fluctuations are correlated across many distinct calibration epochs. A single epoch has no fluctuation series and no correlation estimate.
- No claim of correlation, independence, or common cause is made or implied from one epoch.
- Honesty bounds (from the frozen lock) hold: device-dependent witnesses on co-located qubits; locality and detection loopholes OPEN; not device-independent; not loophole-free.

## Next step (requires a genuinely new calibration epoch)

The independence guard in `submit_epoch.py` will REFUSE a second battery that shares this calibration timestamp. The next epoch may be submitted only after ibm_marrakesh recalibrates (a new `last_update_date`), typically ~1 per calibration cycle. Collection proceeds ~1 epoch per cycle until >= 20 distinct epochs, then `verifier2.py` emits the frozen cross-witness verdict. No further submission is authorized beyond Epoch 1 under the current GO.
