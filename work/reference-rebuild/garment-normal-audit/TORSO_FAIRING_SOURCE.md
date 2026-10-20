# Localized torso target

Accepted in actual Unity cloth14 against matching control14. This is a bounded improvement of the existing `male_intro` and `female_intro` corrective targets. Every other anchor and source construction remains exact. It does not complete garment quality or stroke coverage.

Editable posed source plates: `Male_LocalizedTorsoFairing.blend`, `Female_LocalizedTorsoFairing.blend`. Matching plain before-left/after-right front and three-quarter PNGs share this directory. Exact inverse-LBS target arrays are in `*_torso_fairing_target.json`; complete installable profiles are under `stage/`.

Author: `fair_existing_torso.py`; constraint repair: `repair_torso_constraints.py`; exact pinned-data restoration: `finalize_torso_candidate.py`. The final staged arrays are authoritative, with SHA provenance in `stage-manifest.json`; do not rerun the whole smoothing author as a new art iteration.

Actual gate/provenance is `actual-cloth14-gate.json`, independent pose comparisons are `actual-cloth14-pose-deltas.json`. Body and bottoms remain exactly unchanged. Other observed motion shirt displacement is at most0.559 mm; IntroWave target changes reach11.8 mm male /22 mm female. Existing visible Serve/Forehand breakthroughs remain failed and are recorded separately in `stroke-coverage-diagnosis.json`.
