# FEMALE TORSO FORM2 — bust + glute (chat A of 07b/08b)

**GATE: FEMALE_TORSO_FORM2 PASS** — all 35 binary lines in `checks.json` pass (groups: ZONE_OUTSIDE, TOPOLOGY, SIDE_SIL, SEAM_CLEAN, BUST_VOLUME, GLUTE_FORM).
Read "Honest notes" first: the form gate lines are this chat's definitions (plate-anchored), and Adnan's eye on `proof/04`, `proof/05`, `proof/01` is the real test — chat 7's PASS was rejected on form.

* Start: `work/female-parallel-torso/export/HeroBase_Female_torso_candidate.blend` — SHA `696e1be4…945310e9` (verified; byte copy `START_torso_candidate.blend`).
* ArtDir `HeroBase_Female.blend` = `200dc3b9…b22685cd` before and after → **nothing installed** (staged only; install rule).
* Staged result: `export/HeroBase_Female_torso_form2_candidate.blend` — SHA `6859d958…66a65f27`.
* Drop-in delta, relative to the ORIGINAL start 200dc3b9 (supersedes chat 7's delta): `export/torso_form2_delta.npz` — SHA `f76a2974…912db10d`, 3,082 vertices. `export/README_MERGE.md` has the commands.

## Why chat 7 was rejected (root causes found)
1. **Arm-taper weights strangled the bust.** Chat 7 faded displacement over 7.5 cm toward the arm junction, cutting the lateral half of each mound; the chest ring became a trapezoid ("shield") and the remains were pinched V creases (`data/xsec.png`, `proof/06`).
2. **Bust centre ~5 cm too low** (chat 7: z 1.19; plate: apex z≈1.21–1.22, dark underbust crescent z≈1.18–1.19, highlight z≈1.26, mound centres x≈±0.07–0.085).
3. **Glutes were one ellipse with an 11 mm Gaussian cleft.** The original pelvis ring already had the plate's glute depth (+0.1185 at z .86) but as a symmetric slab: no lobes, no shelf.

## What changed (zone = chat 7's 3,320-vertex torso mask, z 0.795–1.37, arms excluded)
Positions only; topology, UVs, materials, custom-normal raw codes, Hair, plates, lights identical. **The 238 zone border vertices (neck / arm junction / leg tops) are bit-identical to the original start** — the arms chat pinned its arm vertices to exactly those positions.

Method (`tools/torso2.py`, `build2`; parameters `export/form2_params.json`):
* Taubin-denoised surface (the 13.5 mm surface-nets lattice jitters ±0.5 mm); geodesic border weights (sstep5; feature tapers arm 4.5 / legs 3.5 / neck 4 cm, remap tapers 5 / 7 / 5 cm); the displacement diffusion pins the border vertices (Dirichlet 0).
* Per-ring depth remap to the plate side-profile envelope (chat 7's accepted depth, kept): front wall at the sternum line, back base at the cleft line; neck fade z 1.27→1.345.
* **Bust** = two *wall-relative* ellipsoid caps (cap height above the local chest wall = R_y·√rad − e, R_y 0.053, e 0.021 → 32 mm at the cap centre) smooth-min'd into the wall (a constant-depth ellipsoid left a ~38 mm cliff at the lateral edge against the pinned arm border). Centre x ±0.076, z 1.236; radii 0.056/0.048 (x medial/lateral), 0.056/0.062 (z down/up) → footprint 90 × 112 mm; sternum line recessed 22 mm with a wide transition; 2 diffusion passes keep a crisp underbust lip.
* **Glutes** = two ellipsoid lobes (centre x ±0.078, z 0.863; semi-axes 0.074/0.068 (x medial/lateral) × 0.065 (y) × 0.104/0.112 (z down/up)) smooth-max'd onto a base whose centre line is recessed by up to 42 mm below the plate envelope (full below z≈0.89, fading to 0 at z 0.965) — **the cleft is the base**; a lateral window (|x| 0.10→0.155) ends the lobes before the hip roll-over; 10-pass displacement diffusion removed the hard rim along the top of the lobes; the lumbar→shelf knee is softened to σ 14 mm in the modelling target.
* Parameters were fitted to the plate envelope (`tools/fit.py`); footprint sizes/positions were fixed by design from plate grids and band-pass maps (`data/grid_*.png`, `proof/scratch/foot_*.png`).

## Gate results (`checks.json`; evaluated by `tools/gates.py` from `export/form2_*.json`)
| group | line | value | limit |
|---|---|---|---|
| ZONE_OUTSIDE | moved outside zone vs chat-7 candidate | 0 — PASS | == 0 |
| ZONE_OUTSIDE | moved outside zone vs ORIGINAL start 200dc3b9 | 0 — PASS | == 0 |
| ZONE_OUTSIDE | zone border vertices moved (seam with arms/neck/legs) | 0 — PASS | == 0 |
| TOPOLOGY | poly/loop/edge/material/smooth/UV/custom-normal raw codes/Hair/other objects identical | True — PASS | all True |
| TOPOLOGY | triangles (budget 35-50k) | 44708 — PASS | unchanged, <=50k |
| TOPOLOGY | flipped zone triangles vs original | 0 — PASS | == 0 |
| TOPOLOGY | zone triangles turned >60 deg vs original | 0 — PASS | <= 2 |
| SIDE_SIL | side-profile torso-band XOR vs plate (chat-7 gate script, z .82-1.30) | 0.025 — PASS | <= 0.05 |
| SIDE_SIL | front torso visible-edge XOR vs bald plate (rows z .82-1.165) | 0.034 — PASS | <= 0.05 |
| SIDE_SIL | back torso visible-edge XOR vs bald plate | 0.044 — PASS | <= 0.05 |
| SEAM_CLEAN | displacement step at a pinned border edge, legs (mm) | 7.54 — PASS | <= 8 |
| SEAM_CLEAN | ... arm junction (mm) | 9.44 — PASS | <= 10 |
| SEAM_CLEAN | ... neck/shoulder top (mm) | 0.73 — PASS | <= 1 |
| SEAM_CLEAN | zone edges with dihedral >40 deg (count) | 36 — PASS | <= original (36) |
| SEAM_CLEAN | worst zone dihedral (deg) | 80 — PASS | <= original (80.0) |
| SEAM_CLEAN | bi-Laplacian roughness mean (mm), zone interior | 0.232 — PASS | <= chat 7 (0.240) |
| SEAM_CLEAN | bi-Laplacian roughness p95 (mm) | 1.265 — PASS | <= chat 7 (1.438) |
| BUST_VOLUME | mound apex envelope vs plate side profile (mm) | -1 — PASS | |err| <= 4 |
| BUST_VOLUME | sternal valley: apex front vs sternum strip (mm) | 17.4 — PASS | 8..20 |
| BUST_VOLUME | mound footprint width (mm) | 92 — PASS | 70..110 |
| BUST_VOLUME | mound footprint height (mm) | 112 — PASS | 100..130 |
| BUST_VOLUME | underbust edge: footprint lower z | 1.182 — PASS | 1.17..1.20 |
| BUST_VOLUME | mound height above the local chest wall at the apex (mm) | 23.5 — PASS | >= 15 |
| BUST_VOLUME | mound footprint centre |x| (m) | 0.069 — PASS | 0.060..0.090 |
| GLUTE_FORM | two lobes: apex |x| (m) | 0.073 — PASS | 0.060..0.090 |
| GLUTE_FORM | lobe apex z (m) | 0.86 — PASS | 0.85..0.89 |
| GLUTE_FORM | lobe apex depth vs plate side profile (mm) | -2.4 — PASS | |err| <= 4 |
| GLUTE_FORM | cleft depth at z .86/.88/.90 (mm) | [24.7, 24.6, 24.3] — PASS | 18..32 |
| GLUTE_FORM | cleft start z (depth reaches 5 mm) | 0.958 — PASS | 0.93..0.965 |
| GLUTE_FORM | cleft depth at z .98 (mm) - no slit in the lumbar | 0.2 — PASS | <= 3 |
| GLUTE_FORM | upper shelf rise z1.00->0.94 (mm) vs plate table | 31.2 — PASS | plate 32.1 +- 8 |
| GLUTE_FORM | lobe horizontal curvature radius at the apex (cm) | 5.9 — PASS | 5..11 |
| GLUTE_FORM | underbutt fold: back surface rise z .808 -> .852 at |x|=.07 (mm) | 20.3 — PASS | >= 15 |
| GLUTE_FORM | no hard rim: worst dihedral at the lobe upper rim z .92-1.0 (deg) | 24.9 — PASS | <= 30 |
| GLUTE_FORM | no hard rim: worst dihedral INCREASE vs original there (deg) | 18.8 — PASS | <= 25 |

Context numbers: side contour error front 2.9 mm mean / 10.0 max, back 2.8 / 17.4 (chat 7: 3.5/12, 2.5/16 by its own table); max vertex move 43 mm; dihedral stats (zone edges): mean 5.0°, p95 14.8° (original 4.5° / 13.2°); roughness mean 0.232 mm (original 1.01, chat 7 0.240).
Whole-body front/back silhouette (7.9 / 11.0 %) is **not** a torso-zone quantity and is unchanged (head, arms, legs). Chat 7's own `final_metrics.py` / `mesh_quality.py` were run unchanged on the new coordinates (`gate7/`). Edge-stretch max 22× is an inherited degenerate original edge (identical to chat 7).

## Proof (`proof/`)
`01_torso_before_after_soft.png` / `_clay.png` (chat 7 vs form2, same cameras) · `02_side_profile_overlay.png` · `03_front_back_silhouette_overlay.png` · `04_plate_vs_model_3q.png` (plate | chat 7 | form2) · `05_chest_glute_closeups.png` / `_clay.png` · `06_smoothness_mirror_test.png` (chat 7 vs form2 mirror stripes) · `08_merged_preview_torso_limbs_arms_UNOFFICIAL.png` · `09_armpit_seam_check_merged_vs_arms_candidate.png`.
Mirror-stripe test: chat 7's chest is broken stripes + pinched rings; form2 shows two clean concentric ring systems at the domes and two at the lobes. "Soft light" = plate-like matcap (`tools/soft_plate_matcap.png`); "clay" = chat 7's original matcap.

## Install / merge
* Validated on a copy: **ArtDir blend + delta** → 3,082 applied, 0 conflicts, vertex arrays bit-identical to the staged candidate.
* Onto the arms chat's candidate (torso+limbs+arms, limbs order) the merge needs `--vmap … --force` (its torso vertices still hold chat 7's positions): 3,082 applied → `export/PREVIEW_form2_torso_plus_limbs_plus_arms_UNOFFICIAL.blend` (preview only; `proof/08`, `proof/09`).
* Not done: Unity import / prefab / FBX refresh; no clothes, no hair change, no rig.

## Honest notes / limits
* **Form gate lines are my definitions**, anchored to plate measurements (mound/lobe positions and sizes measured from the plate grids and band-pass maps before tuning; cleft range, shelf tolerance and rim angle chosen knowing the result). Close to a limit: arm border step 9.4/10 mm, legs border step 7.5/8 mm, back torso-edge XOR 4.45/5 %, lobe apex error -2.4/4 mm.
* **Bust prominence is bounded by the plate profile**: the belly line below the bust is only ~5.5 mm behind the mound apex in the side view, so mounds read through shading (the plate has AO/crescents). Under plate-like light the mounds are soft and clear (see `proof/04`, `proof/05`) but still *less pronounced than the plate's in a straight front view*; under harsh clay light the dome flanks show V-shaped highlights.
* **Glutes**: round lobes + cleft + shelf now, but the buttock still reads **boxier than the plate in the 3/4 back view**: the zone floor (z 0.795) and the **fixed leg-top ring** form a horizontal ledge, so the plate's underbutt arc/overhang (fold z≈0.805–0.835) can only be approximated by the lobes' lower flank (20 mm rise z .808→.852). That needs the legs chat to flare the thigh tops.
* Neck seam: the front envelope is still 5–16 mm forward of the plate table at z 1.30–1.32 (chat 7 had up to 14 mm); the neck chat should blend z 1.34–1.40.
* Arm-junction columns (|x|≈0.12, z 1.16–1.29) stay noisy in the mirror test (inherited from the original mesh; not worse than before). The arms chat faired its armpit against chat 7's torso: border vertices are identical, the first interior ring differs — re-check `proof/09` after merging.
* Plate-lit shading correlation (SH2 lighting fitted on legs/arms) was explored and **not used as a gate**: the fit explains only R² 0.57–0.67, doesn't transfer between body parts, and biases peak positions ~2 cm high for both mounds and lobes (`tools/platelit.py`, `tools/corr*.py`).

## Files
`export/`: staged blend, delta, `merge_torso_delta.py`, `README_MERGE.md`, `form2_params.json`, `form2_checks.json`, `form2_gate_scripts_checks.json`, `form2_feature_metrics.json`, PREVIEW blend. `checks.json` (this gate). `tools/`: `torso2.py` (build), `fit.py`, `make_final.py` (build+export+audit), `gates.py`, `featmetrics.py`, `seam.py`, `rough.py`, `make_proofs2.py`, `render_merged.sh`, `write_results.py`, plate/shading helpers. `gate7/`: chat 7's metric scripts, paths patched. Reproduce everything: `bash run_all.sh && bash tools/render_merged.sh && python3 tools/write_results.py`.
