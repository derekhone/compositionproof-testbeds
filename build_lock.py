"""
CompositionProof-2 — SHA-256 lock builder
Remnant Fieldworks Inc. — ExecutionProof / CIF research corpus

Hashes each frozen artifact, writes SHA256_MANIFEST.txt (sorted, deterministic),
then hashes the manifest itself to produce the single composite lock hash.
Writes lock_candidate.json. Submits NO hardware.

This is a LOCK CANDIDATE. It becomes FROZEN only on explicit CEO
"GO COMPOSITIONPROOF-2"; until then the package is staged and hardware-gated.
"""
import hashlib
import json
import datetime

# Frozen artifacts, in canonical order. SHA256_MANIFEST.txt and
# lock_candidate.json are excluded (a manifest cannot contain its own hash;
# the composite hash covers the manifest). Transient logs are excluded.
FROZEN = [
    "PREREGISTRATION.md",
    "PREREGISTRATION.pdf",
    "PREREGISTRATION.docx",
    "composition2_sim.py",
    "verifier2.py",
    "control_validate2.py",
    "submit_epoch.py",
    "composition2_sim_result.json",
    "control_validation2_output.json",
    "series_example_sim.json",
    "verifier2_output_example.json",
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    per_file = {}
    for name in sorted(FROZEN):
        per_file[name] = sha256_file(name)

    manifest_lines = ["# CompositionProof-2 SHA-256 MANIFEST — LOCK CANDIDATE\n",
                      "# Each line: <sha256>  <filename>\n"]
    for name in sorted(per_file):
        manifest_lines.append(f"{per_file[name]}  {name}\n")
    with open("SHA256_MANIFEST.txt", "w") as f:
        f.writelines(manifest_lines)

    composite = sha256_file("SHA256_MANIFEST.txt")

    lock = {
        "experiment": "CompositionProof-2",
        "title": "Multi-Epoch Cross-Witness Correlation of Two Nonclassicality Witnesses on One Device",
        "family": "Proof Composition (RF Proof Family — Deep Research Question #5)",
        "relationship_to_prior_work": (
            "Multi-epoch extension of CompositionProof-1's exact witnesses. "
            "OMNI-1 (DOI 10.5281/zenodo.21436092) and CompositionProof-1 are both "
            "SINGLE-EPOCH (simultaneous composition in one recorded state). "
            "CompositionProof-2 tests whether the two witnesses' epoch-to-epoch "
            "FLUCTUATIONS are correlated across many DISTINCT calibration epochs — "
            "a question neither prior result could address."),
        "lock_prepared_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "backend_primary": "ibm_marrakesh (Heron r2, 156 qubits)",
        "backend_backups": ["ibm_fez", "ibm_kingston"],
        "design": "LONGITUDINAL: one 8-circuit battery (CHSH + Mermin-3) per DISTINCT calibration epoch",
        "epoch_definition": "distinct device calibration state (backend.properties().last_update_date); shared-calibration batteries are NOT independent epochs",
        "witnesses": {
            "W1_CHSH": {"classical": 2.0, "quantum": 2.828, "single_epoch_threshold": 2.2, "circuits": 4},
            "W2_Mermin3": {"classical": 2.0, "quantum": 4.0, "single_epoch_threshold": 2.6, "circuits": 4},
        },
        "shots_per_circuit": 4000,
        "circuits_per_epoch": 8,
        "shots_per_epoch": 32000,
        "seed": 20260908,
        "n_epochs_target": 30,
        "n_epochs_min": 20,
        "correlation_analysis": {
            "primary_estimator": "Spearman rank correlation (rho_s)",
            "secondary_estimator": "Pearson r (reported, not decisive)",
            "ci_method": "epoch bootstrap, N_BOOT=5000, BOOT_SEED=20260908, 95%",
            "effect_band": 0.30,
            "drift_guard_z": 2.0,
            "shot_floor_formula": "2/sqrt(shots)",
            "verdicts": ["CORRELATED", "UNCORRELATED", "INCONCLUSIVE", "INCONCLUSIVE_NO_DRIFT"],
        },
        "power_analysis": {
            "detect_correlation_n": "~30 epochs reliable at true rho ~0.75",
            "certify_absence_n": "~150 epochs to certify UNCORRELATED (equivalence within +/-0.30 at true rho=0)",
            "two_stage_design": "Stage 1 n=30 to detect; extend toward n~150 ONLY if Stage 1 INCONCLUSIVE and certifying absence is desired (fresh GO required)",
        },
        "est_qpu_seconds_per_epoch": [8, 12],
        "est_qpu_seconds_total_30_epochs": [240, 360],
        "budget_note": (
            "~30 epochs span weeks across MULTIPLE 28-day rolling windows "
            "(~1 epoch per calibration cycle); the ~330 total QPU-seconds is "
            "spread across windows and does NOT consume 330s from one window."),
        "control_validation": "PASS (6/6 cases: CORRELATED, UNCORRELATED, INCONCLUSIVE x2, INCONCLUSIVE_NO_DRIFT, shared-calibration->INCONCLUSIVE)",
        "verifier": "independent SciPy re-derivation; agrees with sim hand-rolled estimator on example series (CORRELATED, CI excludes 0)",
        "feasibility_sim": "common_mode->CORRELATED (Spearman 0.80), independent->INCONCLUSIVE at n=24, static->INCONCLUSIVE_NO_DRIFT",
        "file_hashes_sha256": per_file,
        "manifest_file": "SHA256_MANIFEST.txt",
        "composite_lock_sha256": composite,
        "hardware_submitted": False,
        "qpu_seconds_spent_this_session": 0,
        "sha_lock_decision": "CANDIDATE — awaiting CEO GO",
        "hardware_execution_decision": "GATED",
        "status": ("LOCK CANDIDATE. No IBM Quantum job has been submitted. "
                   "Hardware execution gated on explicit CEO 'GO COMPOSITIONPROOF-2'."),
        "hardware_release_condition": (
            "Derek Hone explicit authorization 'GO COMPOSITIONPROOF-2'. On GO: freeze "
            "this manifest as the composite lock, then submit ONE 8-circuit battery per "
            "distinct calibration epoch via submit_epoch.py (~1/day), collect >= N_min "
            "epochs, run verifier2.py on the assembled series, and publish a signed "
            "ProofRecord + Zenodo DOI with honesty bounds and the frozen verdict."),
        "permitted_claim": (
            "Across N distinct measured calibration epochs on one named IBM device over "
            "the measured window, the CHSH and Mermin-3 epoch-to-epoch fluctuations were "
            "[correlated / uncorrelated within +/-0.30 / inconclusive], with the stated "
            "Spearman estimate and 95% epoch-bootstrap CI."),
        "forbidden_claims": [
            "proved the witnesses are independent",
            "proved a causal common cause (correlation != causation)",
            "device-independent / loophole-free",
            "universal / for all devices / for all witness pairs",
            "first/only beyond cited DOIs",
        ],
        "honesty_bounds": [
            "Device-dependent witnesses on co-located qubits.",
            "Locality + detection loopholes OPEN; NOT device-independent; NOT loophole-free.",
            "Cross-epoch correlation is an OBSERVED association on one device over the measured window; NOT a causal common cause; NOT universal.",
            "'Epoch' = distinct calibration state; shared-calibration batteries are not independent epochs.",
            "All simulator numbers are feasibility values; no hardware has run.",
        ],
    }
    with open("lock_candidate.json", "w") as f:
        json.dump(lock, f, indent=2)

    print("Frozen files hashed:", len(per_file))
    print("Composite lock SHA-256:", composite)
    print("Wrote SHA256_MANIFEST.txt and lock_candidate.json")


if __name__ == "__main__":
    main()
