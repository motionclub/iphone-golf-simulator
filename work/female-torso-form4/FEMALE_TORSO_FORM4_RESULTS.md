# FEMALE TORSO FORM4 - bust primary + glute hold (Sonnet 5.5)

**GATE: FEMALE_TORSO_FORM4 PASS**  (group results: {'ZONE_OUTSIDE': 'PASS', 'TOPOLOGY': 'PASS', 'SIDE_SIL': 'PASS', 'FRONT_BACK_TORSO_EDGE': 'PASS', 'SEAM_CLEAN': 'PASS', 'NO_SELF_INTERSECT': 'PASS', 'BUST_LIKENESS': 'PASS', 'GLUTE_HOLD_OR_BETTER': 'PASS', 'BUST_EYE_PASS': 'PASS', 'MIRROR_SOFT': 'PASS'})

## Honest notes - what still differs from the plate / what Adnan's eye should check first

**Verdict basis.** Zone, topology, silhouettes, seams, self-intersection and normals are measured. The bust/glute likeness lines combine (a) measurements against the plate (sub-pixel side contour, plate-lit band-pass NCC, curvature, slope, creases) and (b) **my own reading** of the proofs (`proof/04`, `05`, `05z`, `06`, `07`; flagged *eye check* in `checks.json`). FORM3's agent-measured NCC "soft-passed" a chest Adnan called flat, so **Adnan's eye on `proof/05_bust_closeups_soft.png`, `05z_bust_zoom_soft.png` and `02_side_profile_overlay.png` is the real test and overrides every number here.** I read FORM4 as clearly less flat than FORM3 (two separate soft domes with underbust crescents and a sternal valley, a plate-like side bump and a steeper chest diagonal, no box / cone / shelf), but **still more modest than the plate's soft, bright, broad mounds in the 3/4 views.**

**What I could NOT fix inside this zone**
1. **Upper chest / neck-base ring (side profile above z ~1.30).** The pinned ring at z ~1.37 has its front at -0.0695 m (14 cm deep at the neck base); the plate's front there is about -0.040 m. Following the plate's 33-35 deg diagonal right up to the ring forces either an overhang or a stair (tried: try 'a' made a visible ledge and a 6.7 mm neck-seam step; seam budget is <= 1 mm). FORM4 therefore follows the plate within 3 mm up to z 1.28, then eases to a straight line that lands on the original ring: front line vs plate **-3 mm (z 1.28), -10 (1.30), -18 (1.32), -25 (1.34), -29 (1.36)** (FORM3: -10, -16, -22, -27, -30). The chest diagonal is ~25 deg where the plate's is ~33. **Hand-off: neck/head chat slims the neck-base front by >= 25 mm at z 1.34-1.42 (the plate's neck is 3-4 cm shallower); then re-run `torso4.build_final` with `ramp_z1` -> 1.37 and a plate-following `ramp`.** My own stretch target (|FORM4| <= 0.75 |FORM3|) is met at z 1.28 and 1.30 but not at 1.32 (0.82).
2. **Mirror-stripe rings on the domes are polygonal (octagon-like).** At 11 mm vertex spacing the dome apex is only ~3 vertices wide; every profile I tried (p 2.0-3.0) gave the same polygon. FORM3's rings were smoother ovals because its mound was broader and lower. No V-creases or broken stripes; sternum-strip dihedral 15.9 deg (FORM3 8.7), worst bust dihedral 30.0 deg (FORM3 29.5). Not fixable without densifying (not allowed).
3. **Mounds vs plate brightness.** The plate's mound tops are broad bright blobs (~11 cm) above thin crescents; FORM4's domes are 14.8 cm wide x ~2.2 cm high above the (un-flattened) ring and read slightly smaller/darker. The plate is also asymmetric (chest ~2 cm right of the model centre line, viewer-right mound clearer); FORM4 is symmetric by construction.
4. **Glutes are HELD, not improved, except +3 mm of back-apex projection** (the sub-pixel plate contour peaks ~3 mm further back than the old table; FORM3 was -1.7/-2.9/-3.4 mm at z .86/.87/.88, FORM4 +0.6/-0.3/-1.1). A lobe-reshaping 'polish' (taller/narrower lobes) LOWERED the plate-lit NCC from 0.723 to 0.682 and the sheet NCC 0.771 to 0.720, so it was rejected: the glute zone is built from FORM3's own parameters and blended in z with the chest build. The underbutt fold still reads as one horizontal band; the plate's two curved folds + long overhang need the legs chat (thigh backs z .72-.80 are 8-13 mm too deep).
5. **Metric hygiene.** (a) The plate-lit NCC/amplitude numbers are not evidence on their own (FORM3 scored 0.644 and was called flat). (b) The amplitude ratio to the plate depends on the photometric gain: at the raw regression gain 1.0 the bust-core ratio is ~0.59 (FORM3) vs ~0.89 (FORM4); at the calibrated x2.5 it is above 1 for both - so the line in `checks.json` is only 'FORM4 >= FORM3'. (c) The first optimisers I ran produced a peaky bump (apex curvature radius 3.2 cm, dihedral 40.7 deg, polygonal rings) with the *best* NCC; I rejected it by eye. The shipped parameters are a hand-guarded compromise (curvature radius 4.4 cm vs the plate's 5.6, slope 36.7 deg).
6. FORM3's inherited `bm_list[].tilt` was mathematically a no-op (it rotated already-normalised footprint coordinates, leaving rho unchanged). FORM4 implements a real physical-space rotation (-19 deg: lateral end lower, so the lower contour rises toward the sternum like the plate's arcs).
7. The proof matcap gain is 2.2 (compromise of the calibrated front 2.5 / back 2.0); the plate figure is brighter overall than any matcap render, so compare structure, not brightness.
8. Seam budgets: legs 7.60/8 mm (FORM3 7.52), arm 7.04/10 (FORM3 9.34), neck 0.50/1 (FORM3 0.09: FORM3 faded to the original ring, FORM4 follows the plate lower down). Armpit seam on the unofficial merged preview (`proof/10_armpit_seam_check_merged.png`) has no stripe break (smaller jumble than FORM3's).

**What is new vs FORM3 (root causes removed)**
* FORM3 flattened the ring (`fl_k` 0.3, moat, pec fill): the bust became a ~1 cm bump on a plateau (front section at z 1.21 was a trapezoid). FORM4 keeps the ring and puts two real domes (~22 mm above the local wall, valley 9.7 mm) on it; the sternum wall is a near-vertical line (`wl_y`) instead of the plate's apex envelope, which removed the horizontal 'bar' across both mounds.
* FORM3's plate side table was smoothed (35 mm sampling, sigma 9 mm): the real bump is taller/sharper (apex -133 mm at z 1.22 vs -131). FORM4 uses a sub-pixel contour (`tools/plate_side4.py`).
* Two signed domes are summed (`bm_signed`) so the sternal valley has no |x| kink; extra smoothing is confined to the sternum strip.


## Provenance
* Start: `work/female-torso-form3/export/HeroBase_Female_torso_form3_candidate.blend` SHA `a0f69f9d0e8ee4cf...c420dd46` (verified a0f69f9d...; byte copy `START_form3_candidate.blend`). ArtDir `HeroBase_Female.blend` = `200dc3b93e65491a...` (unchanged; 200dc3b9... expected) -> **nothing installed**.
* Staged result: `export/HeroBase_Female_torso_form4_candidate.blend` SHA `aa3e1e443bd46201...3664e383`.
* Drop-in delta relative to the ORIGINAL 200dc3b9 (supersedes FORM3, FORM2 and chat-7 deltas): `export/torso_form4_delta.npz` SHA `3fbbabf65b9bccd2...`, 3,082 vertices. `export/README_MERGE.md`, `export/merge_torso_delta.py`.
* Parameters: `export/form4_params.json` (chest/upper zone, as run) + `export/form4_params_glute.json` (pelvis/glute, FORM3's own + back-apex target), `*_full.json` (incl. defaults of `tools/torso4.py`), `export/form4_wall_corrections.npy`. Reproduce everything: `bash finalize4.sh data/P_final4.json data/P_glute4.json`.

## Method (what was built)
Positions only; topology, UVs, materials, custom-normal raw codes, Hair, plates, lights identical; the 238 zone border vertices bit-identical to the original; 3,082 vertices move (max 40.7 mm vs the original). `tools/torso4.py` (derived from FORM3's `torso3.py`), `build_final(PC, PG)`:
* **chest / upper zone (z > ~1.06)**: FORM3's ring remap on the ORIGINAL ring shape (no flatten band, no moat, no pec fill) + a **plate-following front wall** from the new sub-pixel plate contour (`tools/plate_side4.py`) + a **sternum wall line** `wl_y` (the plate silhouette in the bust band is the dome apex line, not the sternum) + **two signed bell domes** (profile (1-rho^p)^k with separate exponents below/above, physical-space rotation, compact C2 support, `bm_signed`) + an **upper-chest slope ramp** (plate slope eased to a constant slope that lands exactly on the original neck-ring front) + wider geodesic weights (`arm_r` .07, `top_r` .10, `top_f` .07, `ksm` 12: arm step 9.3 -> 7.0 mm, neck 0.5 mm) + sternum-strip smoothing (`cs_k`).
* **pelvis / glute zone (z < ~0.99)**: FORM3's own parameters + a 3 mm back-silhouette target (`bk_amp`); blended with the chest build over z 0.99-1.06 so chest-side parameter changes cannot leak into the glutes.
* Dome parameters were tuned with a bounded evolution strategy (`tools/opt4.py`, objective `tools/score4.py`: plate-lit band-pass NCC at two scales + amplitude + guard rails on silhouette RMS, apex radius, slope, dihedral, seam budgets) and then **chosen by eye** from the candidates (`tools/variants4.py`, `zoom4.py`, `stretch4.py`, `bpmap4.py`, `side4.py`); the pure-NCC optimum was rejected (peaky, polygonal, creased).

## Gate results (`checks.json`; evaluated by `tools/gates4.py`)
| group | line | value | limit | result |
|---|---|---|---|---|
| ZONE_OUTSIDE | moved outside zone vs FORM3 start (a0f69f9d) | 0 | == 0 | PASS |
| ZONE_OUTSIDE | moved outside zone vs ORIGINAL ArtDir 200dc3b9 | 0 | == 0 | PASS |
| ZONE_OUTSIDE | zone border vertices moved (238; neck / arm junction / leg tops) vs ArtDir | 0 | == 0 | PASS |
| ZONE_OUTSIDE | zone border vertices moved vs FORM3 start | 0 | == 0 | PASS |
| TOPOLOGY | poly/loop/edge/material/smooth/UV/custom-normal raw codes/Hair/other objects identical (vs FORM3 start AND vs ArtDir) | True | all True | PASS |
| TOPOLOGY | triangles (budget 35-50k; NO densify) | 44708 | unchanged, <=50k | PASS |
| TOPOLOGY | flipped zone triangles vs original | 0 | == 0 | PASS |
| TOPOLOGY | zone triangles turned >60 deg vs original | 0 | <= 2 | PASS |
| SIDE_SIL | side-profile torso-band XOR vs plate (z .82-1.30) | 0.0232 | <= 0.05 (FORM3 0.0239) | PASS |
| FRONT_BACK_TORSO_EDGE | front torso visible-edge XOR vs bald plate | 0.0342 | <= 0.05 | PASS |
| FRONT_BACK_TORSO_EDGE | back torso visible-edge XOR vs bald plate | 0.0445 | <= 0.05 | PASS |
| SEAM_CLEAN | displacement step at a pinned border edge, legs (mm) | 7.6 | <= 8 (FORM3 7.52) | PASS |
| SEAM_CLEAN | ... arm junction (mm) | 7.04 | <= 10 (FORM3 9.34) | PASS |
| SEAM_CLEAN | ... neck/shoulder top (mm) | 0.5 | <= 1 (FORM3 0.09) | PASS |
| SEAM_CLEAN | zone edges with dihedral >40 deg (count) | 36 | <= original (36) | PASS |
| SEAM_CLEAN | worst zone dihedral (deg) | 80.0 | <= original (80.0) | PASS |
| SEAM_CLEAN | bi-Laplacian roughness mean (mm), zone interior | 0.167 | <= 1.15 x FORM3 (0.219) | PASS |
| SEAM_CLEAN | bi-Laplacian roughness p95 (mm) | 0.752 | <= 1.15 x FORM3 (1.258) | PASS |
| NO_SELF_INTERSECT | no NaN/inf coordinates | 0 | == 0 | PASS |
| NO_SELF_INTERSECT | exact triangle-triangle intersecting pairs touching the torso zone (original / FORM3 / FORM4) | [0, 0, 0] | <= original (0) | PASS |
| NO_SELF_INTERSECT | whole-mesh intersecting pairs unchanged vs original | [4444, 4444] | <= original | PASS |
| NO_SELF_INTERSECT | decoded custom normals still follow the geometry in the zone (median / p95 deg, FORM4 vs original) | [0.62, 3.55, 0.61, 3.52] | within 0.5 / 1.0 deg of the original | PASS |
| BUST_LIKENESS | side-envelope bump band z 1.15-1.27: RMS vs SUB-PIXEL plate contour (mm) | [1.88, 2.05] | <= 3.0 and not worse than FORM3 (value = [FORM4, FORM3]) | PASS |
| BUST_LIKENESS | upper-chest diagonal: front line vs plate at z 1.28/1.30/1.32 (mm, negative = model further forward; FORM3 in 2nd list) | [[-3.2, -10.1, -18.1], [-9.9, -16.0, -22.0]] | |FORM4| < |FORM3| at all three heights | PASS |
| BUST_LIKENESS | mound apex curvature radius of the side envelope (cm): round, not flat (FORM3 8.6) nor pointed; plate 5.6 | [4.4, 8.6] | 4..8 (plate 5.6) | PASS |
| BUST_LIKENESS | dome surface slope (98th pct |dy/dz| angle along the dome column, deg): soft, not conical | [36.7, 27.2] | <= 38 (plate profile max ~39 on the diagonal) | PASS |
| BUST_LIKENESS | no hard shelf / crease: worst dihedral on the front bust region (deg; FORM3 29.5) | 30.0 | <= 31 (11 mm mesh: 31 deg = 2 cm radius, soft; interior edges that were smooth, <=15 deg, in the original) | PASS |
| BUST_LIKENESS | no hard shelf / crease: dihedral increase vs original, bust region (deg) | 20.9 | <= 25 | PASS |
| BUST_LIKENESS | sternal valley without a knife crease: worst dihedral on the sternum strip |x|<2.2 cm, z 1.15-1.30 (deg; FORM3 8.7) | 15.9 | <= 20 (smooth valley: >=2.5 cm radius at 11 mm spacing) | PASS |
| BUST_LIKENESS | relief amplitude in the bust CORE ROI (|x|<.085, z 1.15-1.28; band-pass std ratio model/plate, plate-fit light x2.5): FORM4 not weaker than FORM3 | [2.23, 1.48] | >= FORM3 (value = [FORM4, FORM3]) | PASS |
| BUST_LIKENESS | plate-lit band-pass NCC, bust WIDE ROI (front, |x|<.115, z 1.14-1.30) | [0.696, 0.644] | >= FORM3 - 0.02 (value = [FORM4, FORM3]) | PASS |
| BUST_LIKENESS | plate-lit band-pass NCC, bust CORE ROI | [0.864, 0.879] | >= 0.70 (value = [FORM4, FORM3]) | PASS |
| BUST_LIKENESS | held-out check on the multi-angle SHEET front panel (different render/scale): NCC not worse than FORM3 by > 0.05 | [0.635, 0.592] | form4 >= form3 - 0.05 | PASS |
| BUST_LIKENESS | mound height above the local wall without the domes, at the apex (mm): real mounds, not a flat pancake | 22.0 | >= 12 (FORM3 12.4 incl. the flatten band; FORM4 domes sit on the un-flattened ring) | PASS |
| BUST_LIKENESS | two separate mounds with a sternal valley: front surface at the sternum strip is behind the apex (mm) | 9.7 | >= 3 | PASS |
| GLUTE_HOLD_OR_BETTER | back-envelope apex vs SUB-PIXEL plate contour at z .85/.86/.87/.88 (mm; FORM3 in 2nd list) | [[1.0, 0.6, -0.3, -1.1], [-0.4, -1.7, -2.9, -3.4]] | |FORM4| max <= |FORM3| max | PASS |
| GLUTE_HOLD_OR_BETTER | two distinct round lobes: apex |x| (m) / z (m) | [0.059, 0.869] | |x| .045..095, z .84..90 | PASS |
| GLUTE_HOLD_OR_BETTER | lobe horizontal curvature radius at the apex (cm): round cheeks, not flat pads (FORM3 6.5) | 6.4 | 4..14 | PASS |
| GLUTE_HOLD_OR_BETTER | cleft is a soft V (not a box/pit): width(50% depth)/width(10% depth), worst over z | {"0.86": {"depth_mm": 17.4, "ratio": 0.57}, "0.88": {"depth_mm": 13.4, "ratio": 0.58}, "0.9": {"depth_mm": 8.5, "ratio": 0.58}, "0.92": {"depth_mm": 3.6, "ratio | <= 0.80 (vertical-walled pit ~1.0) | PASS |
| GLUTE_HOLD_OR_BETTER | cleft depth monotone, deepening downward (mm at z .86 .88 .90 .92 .94) | [17.4, 13.4, 8.5, 3.6, 0.8] | monotone, >=12 at z .86, <=12 at z .94 | PASS |
| GLUTE_HOLD_OR_BETTER | no hard rim / flat-top ledge: worst dihedral on the glute region z .80-1.02 (deg; FORM3 24.6) | 24.0 | <= 30 | PASS |
| GLUTE_HOLD_OR_BETTER | no hard rim: dihedral increase vs original, glute region (deg) | 20.8 | <= 25 | PASS |
| GLUTE_HOLD_OR_BETTER | upper shelf rise z1.00->0.94 (mm) vs plate table | 28.8 | plate 32.1 +- 8 | PASS |
| GLUTE_HOLD_OR_BETTER | glute-ROI drift vs FORM3 (mm: max / mean over moved vertices): light polish only | [2.67, 0.34] | max <= 4, mean <= 2 (brief: avg <= 2-4 mm) | PASS |
| GLUTE_HOLD_OR_BETTER | plate-lit band-pass NCC in the glute ROI (back, |x|<.14, z .80-.97): not worse than FORM3 | [0.726, 0.723] | >= FORM3 - 0.03 (value = [FORM4, FORM3]) | PASS |
| GLUTE_HOLD_OR_BETTER | held-out SHEET back panel NCC not worse than FORM3 by > 0.05 | [0.771, 0.771] | form4 >= form3 - 0.05 | PASS |
| BUST_EYE_PASS | VISUAL plate | FORM3 | FORM4 (proof/05 soft + clay + side, proof/04): soft rounded projected mounds, soft matcap still shows volume, no flat wall, no pointy shelves *(eye check)* | PASS | author reading of the proofs | PASS |
| GLUTE_HOLD_OR_BETTER | VISUAL plate | FORM3 | FORM4 (proof/06 soft + clay, proof/04): twin lobes + soft V cleft held, no box/pit/ledge regression *(eye check)* | PASS | author reading of the proofs | PASS |
| MIRROR_SOFT | mirror-stripe test (proof/07): bust/glute rings organic (no square rings / V creases); polygonal innermost bust ring disclosed *(eye check)* | PASS | author reading of proof/07 | PASS |

## Proof (`proof/`)
`04_plate_vs_form3_vs_form4_3q.png` - `05_bust_closeups_soft.png` / `_clay.png` (front, 3/4 L/R, side) - `05z_bust_zoom_soft.png` / `_clay.png` (zoomed) - `06_glute_closeups_soft.png` / `_clay.png` - `02_side_profile_overlay.png` / `12_side_overlay_subpixel_zoom.png` - `03_front_back_silhouette_overlay.png` - `07_mirror_stripe_test.png` - `01_torso_before_after_soft.png` / `_clay.png` - `08_bust_sections_front.png` (horizontal sections: FORM3's trapezoid plateau vs FORM4's domes) - `11_bandpass_maps.png` (2-D shading structure, plate vs FORM3 vs FORM4) - `13_full_torso_soft.png` - `09_merged_preview_torso_limbs_arms_UNOFFICIAL.png` / `10_armpit_seam_check_merged.png` (FORM4 delta merged onto the arms chat candidate; preview only) - `checks.json`. 'Soft' = lighting fitted to the plate (matcap gain 2.2), 'clay' = clay-studio matcap, stripes = mirror matcap; panels of one image share cameras and processing.

## Install / merge
See `export/README_MERGE.md`. Default: STAGE ONLY; install only after Adnan's eye PASS. Not done: Unity import / prefab / FBX refresh; no clothes, no hair change, no rig.
