# CompositionProof-2 Governance Protocol

**Authority Model: FRESH GO EACH CYCLE**

Established 2026-09-08 by Derek Hone, CEO. Applies to all future CompositionProof-2 epoch submissions.

---

## Epoch Submission Protocol

**Do NOT create standing authorization.** Each consequential hardware execution under a new calibration state requires authority re-established at the moment of execution, not inherited from prior GO.

For every future CompositionProof-2 epoch:

1. **Verify** genuinely new `ibm_marrakesh` calibration timestamp (`backend.properties().last_update_date`)
   - Compare against all prior epochs in `epoch_series.json`
   - If timestamp matches any existing epoch, STOP - not a distinct calibration state

2. **Verify** frozen manifest remains intact
   - Run: `python3 build_lock.py --verify`
   - Composite hash must match: `ebe0919b997341569670ccd27b2a8ff754599d242489a2b06ff4db20c8872fd6`
   - If verification fails, STOP - do not submit on altered design

3. **Report** to Derek before any hardware submission:
   - Current QPU allocation (consumed / remaining / total, 28-day window dates)
   - Prior epoch count (N of ≥20 target)
   - New calibration timestamp vs most recent prior epoch timestamp
   - Manifest verification status (INTACT / ALTERED)

4. **STOP** and await explicit authorization
   - Required token: **"GO COMPOSITIONPROOF-2 EPOCH N"** where N = next epoch number
   - No hardware submission until Derek explicitly replies with this token

5. **Submit** only after receiving explicit GO
   - Exactly one epoch battery (8 circuits × 4000 shots)
   - Use `submit_epoch.py` with `--go-token "GO COMPOSITIONPROOF-2" --i-have-ceo-authorization --epoch-id N --backend ibm_marrakesh`

6. **Preserve** every epoch regardless of result
   - Record to `epoch_series.json`
   - Create `EPOCHN_RECORD.md` (+ .pdf/.docx)
   - Git commit
   - No deletion, no polishing, no reruns of same calibration state

7. **Verdict discipline**
   - No final CP-2 verdict before N_MIN=20 distinct calibration epochs
   - Epoch-level records state "COLLECTED - NO FINAL VERDICT"
   - Only after ≥20 epochs: compute Spearman ρ_s, bootstrap CI, apply classification rules per `lock_candidate.json`

---

## Rationale (Derek Hone, 2026-09-08)

> Each CP-2 epoch is a new consequential hardware execution under a new calibration state, so authority should be re-established at the moment of execution rather than inherited from Epoch 1. It also gives you a chance to review remaining QPU budget, calibration timestamp, prior-epoch integrity, and whether anything in the campaign has changed before another irreversible submission.

**Proof Before Power applied to the experiment itself:** prior authorization does not automatically become current execution permission.

---

## Current State

- **Epoch 1**: COLLECTED 2026-09-08, job `dag4fnfi3e6s738ltnpg`, cal `2026-09-08T16:59:31+00:00`, S=2.7205, M=3.7710, 11s QPU
- **Next epoch**: Awaits fresh `ibm_marrakesh` recalibration + explicit GO COMPOSITIONPROOF-2 EPOCH 2
- **QPU remaining**: ~352s of 600s (as of 2026-09-08, window 2026-08-11 to 2026-09-09)
- **Manifest lock**: INTACT `ebe0919b...72fd6` (verified pre-Epoch-1)

---

**Protocol status: ACTIVE**
