# FEMALE TORSO FORM3 - bust + glute likeness (Sonnet 5.5)

**GATE: FEMALE_TORSO_FORM3 PASS**  (group results: {'ZONE_OUTSIDE': 'PASS', 'TOPOLOGY': 'PASS', 'SIDE_SIL': 'PASS', 'FRONT_BACK_TORSO_EDGE': 'PASS', 'SEAM_CLEAN': 'PASS', 'NO_SELF_INTERSECT': 'PASS', 'BUST_LIKENESS': 'PASS', 'GLUTE_LIKENESS': 'PASS', 'MIRROR_SOFT': 'PASS'})

## Honest notes - what still differs from the plate (read first)

**Verdict basis.** Zone, topology, silhouettes, seams, self-intersection and normals are measured. The two LIKENESS gates mix (a) objective plate-agreement and anti-box measurements that I fixed *before* looking at the final result, and (b) **my own reading** of the plate-vs-model proofs (`proof/04-07`, flagged *eye check* in `checks.json`). **Adnan's eye on `proof/05`, `06`, `04` is the real test** - FORM2 passed its own lines and was still rejected. I read FORM3 as no longer boxy and as plate-like in the *shape language* (soft mounds + crescent, round buttock + soft V cleft), but **clearly less pronounced than the plate in the bust and without the plate's long underbutt overhang**.

**Bust - what still differs**
1. **Prominence / definition.** Central mound columns (|x| 0.075-0.09) match the plate's underbust-crescent depth and highlight rise within roughly +-30 % (`proof/08`). At the lateral ends (|x| ~ 0.105) the model is weaker (highlight rise ~28 vs plate ~48-59 grey levels): the arm-junction ring is pinned bit-identical and the base depth remap already uses 9.3 of the 10 mm arm-seam budget, so there is no room for lateral relief. In 3/4 views the plate's breasts read rounder and fuller than mine.
2. **Upper chest is too thick vs the plate table** (front contour, model minus plate: -2 mm z 1.24, -5 mm z 1.26, -9 mm z 1.28, **-15 mm z 1.30, -21 to -25 mm z 1.32-1.36**; negative = model further forward). Reason: the plate's chest slopes back steeply to a neck ~25 mm thinner than the model's original neck (plate front at z 1.36 = -0.050 m, model -0.075 m), and the neck is not mine. A wall that follows the plate and then joins the thick neck makes a horizontal *shelf* band at z ~ 1.30 in clay (tested: constrained spline ramp, `data/co_sp0/sp3.npy`), which is exactly what the brief forbids, so I kept a smooth Hermite ramp (z 1.24 -> 1.345). Cost: the bust reads less prominent relative to the upper chest than in the plate. The gated torso-band XOR (z .82-1.30) is still 2.4 %. **Hand-off: neck chat slims the neck front by ~20-25 mm at z 1.34-1.40; then re-run FORM3 with the ramp following the plate (`ramp_z1` -> 1.37).**
3. **Soft diagonal highlight line** from each shoulder toward the sternum (along the mound's upper-medial flank) is visible in clay in the 3/4 views. Ablation: it disappears when the mound height is 0, and does not disappear with tilt 0 / longer upper slope / no recess / no ramp, i.e. it is the mound's own flank under a hot clay light, not a crease (max dihedral 29.5 deg, 21.8 deg above the original; mirror stripes are clean rings). The plate shows a broad flat highlight there.
4. **The plate carries AO-like contact darkening** in the crescents and the cleft; my proofs use normal-based matcaps without AO, so my crescents look softer than the plate's. In Unity (URP + SSAO / baked AO) they will deepen.

**Glutes - what still differs**
1. **Underbutt.** The fold crescent sits ~2 cm higher than the plate's (z ~ 0.825 vs ~ 0.805) because the model's thigh backs below the zone floor (z 0.795) are 8-13 mm deeper than the plate's (z 0.72-0.78, legs zone): the plate's long underside slope/overhang cannot exist inside my zone. In-zone I added a +4 mm underbutt bump starting at the floor ring (silhouette deficit at z .81-.83 3.3 mm instead of 4.5 mm; legs seam step 7.52 / 8 mm - the limit is the constraint). The fold therefore still reads as a nearly straight horizontal band; the plate's folds are two curved 'smiles'. **Hand-off: legs chat thins/flares the thigh backs at z 0.72-0.80 by ~10 mm.**
2. **Cleft.** Soft V (width ratio W50/W10 0.58), depth 17 / 13 / 9 / 3.5 mm at z .86 / .88 / .90 / .92, gone by z 0.94-0.95 like the plate's faint line. In the plate the cleft is darker near the crotch (plate centre-vs-flank shading at z .85 = 21 grey levels, mine 3) because of the crotch roof / AO; a narrower, deeper cleft there makes 29 deg creases on the 11 mm mesh (my own crease gate: <= 30 deg absolute, <= 25 deg above the original), so I kept it soft.
3. **Lobe separation.** Mirror stripes show nested rings around both lobes together with a notch at the cleft, not two fully separate ring systems; the buttock reads as one round form with a soft V rather than two peaches. The plate also reads that way from the back, but its lobes separate more in 3/4.

**How the shapes were fitted - and its limits**
* Feature fields are hand-designed smooth families on chat 7's depth remap; a photometric CMA-ES optimiser (`tools/opt3.py`) tuned parameters inside bounds I set. Unconstrained, it cheated (deleted the mound, flattened the cleft); a *relief-aware* optimiser run (1-D crescent/highlight profile term, `bust6`) matched the six profile columns better (0.355 -> 0.17-0.19) **but made the 2-D look flatter, so I rejected it** - a metric that is not the picture. Bounds and constraints are part of the result.
* Plate lighting = linear-shading regression on the *unedited* regions of the plate (lit from above and the viewer's right, low contrast; gain x2.5 front / x2.0 back calibrated so unedited regions have amplitude ratio ~1). Approximate (no AO / SSS).
* Held-out check on the multi-angle sheet panels (different render, 5.9 mm/px): bust 0.592 vs FORM2 0.596 (no measured gain), glute 0.771 vs 0.712. Band-pass NCC cannot see blockiness, which is what Adnan rejected in FORM2 - so the proofs, not the NCC, carry the case.
* Proof framing differs from FORM2's: my FORM2-era soft matcap was lit from the viewer's LEFT (the plate is lit from the right) and used 25 deg 3/4 yaws; now fitted light, front +-20 / back +-30 deg yaws (matched by eye; the sheet panels are not exactly those angles). FORM2's soft proofs therefore overstated its gap to the plate in some views; its boxy clay shapes were real.
* The torso-zone self-intersection count is 0 (original 0, FORM2 0); the 4,444 whole-mesh intersecting pairs (identical in all three files) are eyes/teeth/ears/hands. Decoded custom normals follow the new surface (median 0.6 deg, p95 3.5 deg off geometric normals, same as the original).
* Not touched: hair, head, neck, arms, hands, legs, feet, clothes, rig, Unity (no prefab/FBX refresh). ArtDir untouched.


## Provenance
* Start: `work/female-torso-form2/export/HeroBase_Female_torso_form2_candidate.blend` SHA `6859d958...66a65f27` (verified; byte copy `START_form2_candidate.blend`). ArtDir `HeroBase_Female.blend` = `200dc3b93e65491a...` (unchanged; 200dc3b9... expected) -> **nothing installed**.
* Staged result: `export/HeroBase_Female_torso_form3_candidate.blend` SHA `a0f69f9d0e8ee4cf...c420dd46`.
* Drop-in delta relative to the ORIGINAL 200dc3b9 (supersedes FORM2 and chat-7 deltas): `export/torso_form3_delta.npz` SHA `3831988e457fd358...`, 3,082 vertices. `export/README_MERGE.md`, `export/merge_torso_delta.py`.
* Parameters: `export/form3_params.json` (as run) / `export/form3_params_full.json` (incl. defaults of `tools/torso3.py`) + `export/form3_wall_corrections.npy`. Reproduce everything: `bash finalize3.sh data/P_final.json` (blend, delta, audits, gates, proofs, integration preview, this file).

## Why FORM2 failed (root causes this pass removed)
1. **Bust = ellipsoid caps on a cylinder.** Hard footprints (compact support) + a constant-height cap left flat fronts, a shelf at the underbust and a second shelf at the upper edge; two eggs on a tube.
2. **Glutes = lobe union + recessed base.** The cleft was the recessed base (a pit with vertical walls), the lobes had a lateral window / upper rim -> a rectangular slab with a square cavity and a ledge.
3. **My own proof lighting was wrong.** The plate-like matcap inherited from FORM2 is lit from the viewer's LEFT; a regression of the plate's luminance on the model normals (unedited regions, front and back views) says the plate is lit from above and the viewer's RIGHT, with low contrast (`data/plate_light_fit.json`: I = 181.8 + 18.2 n_right + 28.5 n_up + 11 n_toward, contrast under-estimated by regression dilution -> calibrated gain 2.5 front / 2.0 back on the unedited regions). All proofs here use the fitted light (`tools/matcap_platefit_g22.png`) plus clay studio and mirror-stripe matcaps. The sheet's 3/4 panels are NOT 25 deg: front panels look ~15-20 deg, back panels ~30 deg; proofs use +-20 (front) / +-30 (back).

## What changed (zone = chat 7's 3,320-vertex torso mask, z 0.795-1.37, arms excluded)
Positions only; topology, UVs, materials, custom-normal raw codes, Hair, plates, lights identical; the 238 zone border vertices bit-identical to the original; 3,082 vertices move (max 42 mm).
* All features are smooth Gaussian-type fields on chat 7's depth remap (no compact-support footprints, no hard windows). `tools/torso3.py` (`build3`):
  * **bust** = one asymmetric Gaussian-type mound per side (steeper below, long gentle slope above) with an underbust groove, a localized wall dip behind it (`b_rec`) and a mound-centred moat (`mo_*`) so the 12 mm relief fits inside the plate's side envelope, a light flatten band (`fl_k`), and a smooth Hermite ramp of the front wall from the mound's upper edge to the original neck (`ramp_*`; removes the slope-kink shelf of chat 7 / FORM2);
  * **glutes** = Gaussian lobes + lobe moat (strong medially/below, none above) + a separately carved soft V cleft (`cl_*`, widening/fading into the lumbar) + a +4 mm underbutt bump from the floor ring (`ub_*`).
* Parameters were fitted against the plate with a photometric optimiser (`tools/opt3.py`, CMA-ES: 1 - NCC of band-passed plate vs model luminance + amplitude term + penalties for silhouette envelope, seam steps, creases, minimum mound height, cleft depth/V-shape), then hand-tuned against the proofs; `tools/photo3.py` rasterises the model at the plate's pixel grid with the fitted light.
* Front/back wall tables are re-fitted so the side-silhouette envelope tracks the plate table (`fit_walls`), as in chat 7.

## Gate results (`checks.json`; evaluated by `tools/gates3.py`)
| group | line | value | limit | result |
|---|---|---|---|---|
| ZONE_OUTSIDE | moved outside zone vs FORM2 start (6859d958) | 0 | == 0 | PASS |
| ZONE_OUTSIDE | moved outside zone vs ORIGINAL ArtDir 200dc3b9 | 0 | == 0 | PASS |
| ZONE_OUTSIDE | zone border vertices moved (238; neck / arm junction / leg tops) vs ArtDir | 0 | == 0 | PASS |
| ZONE_OUTSIDE | zone border vertices moved vs FORM2 start | 0 | == 0 | PASS |
| TOPOLOGY | poly/loop/edge/material/smooth/UV/custom-normal raw codes/Hair/other objects identical (vs FORM2 start AND vs ArtDir) | True | all True | PASS |
| TOPOLOGY | triangles (budget 35-50k) | 44708 | unchanged, <=50k | PASS |
| TOPOLOGY | flipped zone triangles vs original | 0 | == 0 | PASS |
| TOPOLOGY | zone triangles turned >60 deg vs original | 0 | <= 2 | PASS |
| SIDE_SIL | side-profile torso-band XOR vs plate (z .82-1.30) | 0.0239 | <= 0.05 | PASS |
| FRONT_BACK_TORSO_EDGE | front torso visible-edge XOR vs bald plate | 0.0342 | <= 0.05 | PASS |
| FRONT_BACK_TORSO_EDGE | back torso visible-edge XOR vs bald plate | 0.0445 | <= 0.05 | PASS |
| SEAM_CLEAN | displacement step at a pinned border edge, legs (mm) | 7.52 | <= 8 (FORM2 limit) | PASS |
| SEAM_CLEAN | ... arm junction (mm) | 9.34 | <= 10 (FORM2 limit) | PASS |
| SEAM_CLEAN | ... neck/shoulder top (mm) | 0.09 | <= 1 (FORM2 limit) | PASS |
| SEAM_CLEAN | zone edges with dihedral >40 deg (count) | 36 | <= original (36) | PASS |
| SEAM_CLEAN | worst zone dihedral (deg) | 80.0 | <= original (80.0) | PASS |
| SEAM_CLEAN | bi-Laplacian roughness mean (mm), zone interior | 0.219 | <= 1.15 x FORM2 (0.232) | PASS |
| SEAM_CLEAN | bi-Laplacian roughness p95 (mm) | 1.258 | <= 1.15 x FORM2 (1.265) | PASS |
| NO_SELF_INTERSECT | no NaN/inf coordinates | 0 | == 0 | PASS |
| NO_SELF_INTERSECT | exact triangle-triangle intersecting pairs touching the torso zone (original / FORM2 / FORM3) | [0, 0, 0] | <= original (0) | PASS |
| NO_SELF_INTERSECT | whole-mesh intersecting pairs unchanged vs original | [4444, 4444] | <= original | PASS |
| NO_SELF_INTERSECT | decoded custom normals still follow the geometry in the zone (median / p95 deg, FORM3 vs original) | [0.62, 3.52, 0.61, 3.52] | within 0.5 / 1.0 deg of the original | PASS |
| BUST_LIKENESS | plate-lit band-pass NCC in the bust ROI (front, |x|<.115, z 1.14-1.30) vs plate | 0.644 | FORM2 0.516 + 0.10 and >= mean NCC of unedited regions (0.50: {'abdomen front': 0.453, 'thighs front': 0.684, 'thighs back': 0.428, 'upper arm L front': 0.428}) | PASS |
| GLUTE_LIKENESS | plate-lit band-pass NCC in the glute ROI (back, |x|<.14, z .80-.97) vs plate | 0.723 | FORM2 0.550 + 0.10 and >= 0.50 | PASS |
| BUST_LIKENESS | held-out check on the multi-angle SHEET front panel (different render/scale): NCC not worse than FORM2 by > 0.05 | [0.592, 0.596] | form3 >= form2 - 0.05 | PASS |
| GLUTE_LIKENESS | held-out check on the multi-angle SHEET back panel: NCC not worse than FORM2 by > 0.05 | [0.771, 0.712] | form3 >= form2 - 0.05 | PASS |
| BUST_LIKENESS | mound apex curvature radius, horizontal / vertical (cm): round, not flat or pointed | [5.4, 9.1] | both 3..20 | PASS |
| BUST_LIKENESS | no hard shelf / crease: worst dihedral on the front surface, bust region (deg) | 29.5 | <= 30 (interior edges that were smooth, <=15 deg, in the original) | PASS |
| BUST_LIKENESS | no hard shelf / crease: dihedral increase vs original, bust region (deg) | 21.8 | <= 25 | PASS |
| BUST_LIKENESS | mound height above the local wall at the apex (mm): real mounds, not a flat pancake | 12.4 | >= 8 | PASS |
| BUST_LIKENESS | two separate mounds with a sternal valley: front surface at the sternum strip is behind the apex (mm) | 6.1 | >= 3 | PASS |
| GLUTE_LIKENESS | two distinct round lobes: apex |x| (m) / z (m) | [0.059, 0.865] | |x| .045..095, z .84..90 | PASS |
| GLUTE_LIKENESS | lobe horizontal curvature radius at the apex (cm): round cheeks, not flat pads | 6.5 | 4..14 | PASS |
| GLUTE_LIKENESS | cleft is a soft V (not a box/pit): width(50% depth)/width(10% depth), worst over z | {"0.86": {"depth_mm": 17.3, "ratio": 0.57}, "0.88": {"depth_mm": 13.1, "ratio": 0.58}, "0.9": {"depth_mm": 8.5, "ratio": 0.58}, "0.92": {"depth_mm": 3.5, "ratio | <= 0.80 (vertical-walled pit ~1.0) | PASS |
| GLUTE_LIKENESS | cleft depth monotone, deepening downward (mm at z .86 .88 .90 .92 .94) | [17.3, 13.1, 8.5, 3.5, 0.8] | monotone, >=12 at z .86, <=12 at z .94 | PASS |
| GLUTE_LIKENESS | no hard rim / flat-top ledge: worst dihedral on the upper glute region z .80-1.02 (deg) | 24.6 | <= 30 (interior edges smooth in the original) | PASS |
| GLUTE_LIKENESS | no hard rim: dihedral increase vs original, glute region (deg) | 21.6 | <= 25 | PASS |
| GLUTE_LIKENESS | upper shelf rise z1.00->0.94 (mm) vs plate table | 28.8 | plate 32.1 +- 8 | PASS |
| BUST_LIKENESS | VISUAL plate B/A (proof/05 soft+clay, proof/04): soft rounded mounds, underbust blend, no box/cylinder/flat front *(eye check)* | PASS | author reading of the proofs | PASS |
| GLUTE_LIKENESS | VISUAL plate B/A (proof/06 soft+clay, proof/04): twin round lobes, soft V cleft, no box/square cavity/hard ledge *(eye check)* | PASS | author reading of the proofs | PASS |
| MIRROR_SOFT | mirror-stripe test (proof/07): bust/glute rings organic, stripe breaks no worse than FORM2 *(eye check)* | PASS | author reading of proof/07 | PASS |

Photometric agreement (band-pass NCC, plate-lit): bust FORM3 0.644 (FORM2 0.516), glute FORM3 0.723 (FORM2 0.550); unedited regions of the same model score {'abdomen front': 0.453, 'thighs front': 0.684, 'thighs back': 0.428, 'upper arm L front': 0.428} (mean 0.50) - i.e. the metric tops out around 0.4-0.7 for 'same shape, not pixel-exact'.

## Proof (`proof/`)
`04_plate_vs_form2_vs_form3_3q.png` - `05_bust_closeups_soft.png` / `_clay.png` - `06_glute_closeups_soft.png` / `_clay.png` - `07_mirror_stripe_test.png` - `02_side_profile_overlay.png` - `03_front_back_silhouette_overlay.png` - `01_torso_before_after_soft.png` / `_clay.png` - `08_relief_profiles.png` (brightness profiles through mounds/lobes/cleft, plate vs FORM2 vs FORM3) - `09_merged_preview_torso_limbs_arms_UNOFFICIAL.png` / `10_armpit_seam_check_merged.png` (FORM3 delta merged onto the arms chat candidate; preview only) - `checks.json`. 'Soft' = lighting fitted to the plate, 'clay' = clay-studio matcap, stripes = mirror matcap; panels of one image share cameras and processing.

## Install / merge
See `export/README_MERGE.md`. Default: STAGE ONLY; install only after Adnan's eye PASS. Not done: Unity import / prefab / FBX refresh; no clothes, no hair change, no rig.
