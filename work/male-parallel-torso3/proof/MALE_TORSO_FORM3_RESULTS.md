GATE: MALE_TORSO_FORM3 PASS

Male torso FORM3 (chest masses + lower-pec shelf, soft mid with oblique planes, in-zone buttock lobes + V-cleft) · 2026-10-02 · follow-up to FORM2 · positions-only (y-only) edit on the existing topology, torso zone only. Silhouette gate <= 5.0 % bald front/back.

| Line | Result | Evidence |
|---|---|---|
| ZONE_OUTSIDE_MOVED=0 | PASS | moved outside zone 0; categories head/neck, legs, feet, hands, arms, arm-gap, outside = [0, 0, 0, 0, 0, 0, 0]; Face_M + LOOP_* groups identical; 5587 verts moved inside the zone (all |x| < 0.20) |
| TOPOLOGY_IDENTICAL | PASS | 30296 verts / 60358 tris, face list identical, boundary/non-manifold edges 92/2 as baseline, height 1.702187 m unchanged, positions-only edit |
| SIL_FRONT_BACK<=5.0% | PASS | front 4.3203 % (before 4.3203), back 4.3854 % (before 4.3854); y-only moves leave the outline unchanged (max |dx|,|dz| = 0.000/0.000 mm) |
| DEPTH_vs_SIDE_hold | PASS | depth deficit vs left/right plate silhouettes z 0.92-1.30: rms 2.69 -> 2.61 mm (limit 3.0), mean +0.73 -> +0.29 mm; front/back extremes per slab z 0.92-1.30 shift <= 1.51 mm |
| PELVIS_SHELF_clean | PASS | pelvis band z 0.77-0.90: edges >55 deg 0 -> 0, max crease 50.0 -> 49.5 deg; whole zone >55 deg 2 -> 2 (armpit); zone-border displacement max 0.015 mm |
| CHEST_DEFINED | PASS | front chest band-pass r +0.450 -> +0.651 (FORM2 +0.450); lower-pec shelf crest-to-crease drop plate-lit 33.7 -> 46.0 lum (plate 38.0, crease z 1.180 vs plate 1.175); Unity-style render drop 14.2 -> 24.1 lum (skin), 13.1 -> 24.1 (clay) |
| MIDSECTION | PASS | front abdomen band-pass r +0.431 -> +0.621 (FORM2 +0.431); front pelvis +0.384 -> +0.690; abdomen fine-ripple ratio 0.92x plate (no carve) |
| GLUTE_FORM | PASS | back glute-upper band-pass r +0.108 -> +0.177 (FORM2 +0.108); twin lobes: centre-to-lobe-crest cleft depth at z 0.84/0.86/0.88 = -0.1->+6.0/-0.7->+3.5/-1.6->-0.6 mm (FORM2 -> FORM3), crests at |x| 38 mm |
| FORM_mean_beats_FORM2 | PASS | mean of 6 torso regions +0.345 -> +0.481 (FORM2 +0.345); every region improved: front chest +0.450->+0.651, front abdomen +0.431->+0.621, front pelvis +0.384->+0.690, back chest +0.413->+0.453, back abdomen +0.285->+0.294, back pelvis +0.108->+0.177; wider band (DoG 2/8) +0.374 -> +0.511 |
| NO_SELF_INTERSECT_FLIPS_NAN | PASS | flipped faces 0, zero-area faces 0, NaN/Inf False; BVH self-intersections (non-adjacent triangle pairs) 3 -> 3 (pre-existing, elsewhere), touching the torso zone 0 -> 0; min face area 5.58 mm2; edge length ratio 0.86..1.32 |
| NO_BANDING_belt_doublepec_rings | PASS | fine-ripple energy FORM3/plate per region: front chest 1.62x, front abdomen 0.92x, front pelvis 1.10x, back upper 0.58x, back lumbar 0.81x, back glute 1.84x (limit 2.0; rejected gain ladder A5/A6 = 2.4x/3.9x chest); longest dark horizontal run belt 0.05 / back 0.00 of the torso width (limit 0.15; plate 0.00); secondary pec minima 0 (<25 % of the main crease) |
| NAPE_STRIP_untouched | PASS | vertices moved at z >= 1.352: 0 (max z moved 1.3499); max |x| moved 0.200 (<0.20, shoulder-ball overlap with the arms chat untouched) |
| FBX_REIMPORT | PASS | FBX re-import: 60358 tris, max vertex error 0.00028 mm, height 1.702187 m |

## Zone (exact mask)

`Body_M` vertices with start position **z in [0.77, 1.40)** and **|x| <= xlim(z)**, xlim = 0.205 for z < 1.20, rising linearly to 0.28 at z = 1.24, 0.28 above (shoulder ball) = **7617 of 30296** vertices (same mask as the torso PASS / FORM2). 5587 of them moved, **all with |x| < 0.20 and 0.775 <= z <= 1.349**; **0 moved outside**: head/neck (z >= 1.40; nothing at z >= 1.352, so the Micro1k nape strip is untouched), arms (|x| > 0.28), the shoulder-ball overlap with the arms chat (|x| >= 0.20), arm-gap side, hands/forearms, legs (z < 0.77), feet = 0 each (Float32 bit-identical, audit `proof/male-torso-form3-audit.json`); Face_M, `LOOP_*` groups, cameras, materials, topology bit-identical. Border displacement max 0.015 mm.

## Why FORM2 looked under-defined, and what changed

* **The game-style rig hides relief.** The same FORM2 shelf reads at only ~26 % of its plate-lit contrast in the Unity-style render (normalised crest-to-crease contrast 0.081 skin vs the plate's 0.30 under its own near-frontal light). FORM2's depth guard also shifted whole height slabs (20 mm smoothing), which flattened the pec crest.
* **There was depth headroom.** At z 1.20-1.22 the *sternum* was the front-most point (-180.6 mm) and the pec crests sat 8-9 mm behind it, so the side plates never required a flat chest. FORM3 lifts the pecs to the existing front-most line and carves the sternum / creases behind it: the front/back extremes per slab (z 0.92-1.30) move <= 1.51 mm, so silhouettes and side-plate depth are held.
* **Stage 1 - plate-lit photometric refit with relief gain** (frozen asset `data/RBF_FORM3_asset.npz`, 874 mirror-symmetric Gaussian-RBF y-fields, start = the installed FORM2 mesh): plate target high-pass x region gain (front chest 3.5, abdomen 2.6, pelvis 2.2; back upper 2.2, lumbar 2.0, glute 3.5), lighting fitted on the untouched limbs only (as FORM2), joint Levenberg-Marquardt with per-vertex bounds |dy| <= 14 mm **and the silhouette extremes of the FORM2 mesh** (inequality inside the solve), 14 iterations. Displacements stay small (max 5 mm) but the gate correlation is very sensitive to ~1-5 mm of relief. Raising the gain further (5x / 7x) produced parallel creases and ripple energy 2.4x / 3.9x the plate - rejected.
* **Stage 2 - structure that the plate supports or the brief asks for** (`struct3.py`, all y-only, tapered to 0 at |x| = 0.20, z = 0.775 and z = 1.35): pec lift A = 8 mm (crest up to the extreme), soft sternum valley A = 4 mm (pec crest 3.1 / 4.5 mm in front of the sternum at z 1.20 / 1.22; FORM2 -0.3 / 0.1), broad oblique planes A = 3 mm at |x| = 0.108 (sigma 0.028, z 0.955-1.13; position fitted to the plate: plate-lit abdomen r also rises, 0.775 -> 0.781), buttock lobes (A = 9.6 mm, |x| = 0.056, sigma 0.08 x 0.039, centre z 0.825) and a V-cleft that deepens toward the zone floor (peak 10 mm at z 0.82, 0 above z 0.93). The buttock lobes may use <= 8 mm of back allowance at z 0.805-0.855 because the side plates are 6-12 mm deeper than the mesh there (5.8 mm/px); the depth gate band z 0.92-1.30 is unaffected.
* **Stage 3 - hard clamp + deficit guard**: zone vertices (|x| < 0.20) are clamped to the FORM2 slab extremes (+0.4 mm, plus the glute allowance); receded extremes are lifted back with a smoothed slab shift (3 passes, sigma 8 mm).
* Displacement: max 10.3 mm (buttock lobes), mean of moved 1.01 mm, volume +0.23 L. Surface stays clean: zone dihedral p99 19.7 -> 21.5 deg; creases > 55 deg in the zone 2 -> 2 (the natural armpit crease), pelvis band 0 -> 0 (max 50.0 -> 49.5 deg); edge-length ratio 0.86..1.32; vertex-normal change mean 1.5 deg.

## Numbers

| Region (Unity-style clay render vs plate, band-passed shading r) | FORM2 | FORM3 | delta |
|---|---:|---:|---:|
| front chest (z 1.15-1.32) | +0.450 | +0.651 | +0.201 |
| front abdomen (0.90-1.15) | +0.431 | +0.621 | +0.190 |
| front pelvis (0.80-0.90) | +0.384 | +0.690 | +0.306 |
| back upper (1.15-1.32) | +0.413 | +0.453 | +0.039 |
| back lower/waist (0.90-1.15) | +0.285 | +0.294 | +0.009 |
| back glute-upper (0.80-0.90) | +0.108 | +0.177 | +0.069 |
| **mean of 6** | **+0.345** | **+0.481** | **+0.136** |

* Wider band (DoG 2/8): mean +0.374 -> +0.511. Under the **plate's own lighting** (mesh shaded with the limb-fitted SH model): mean +0.634 -> +0.718 (front chest +0.912 -> +0.907, abdomen +0.775 -> +0.781, pelvis +0.633 -> +0.897, back upper +0.426 -> +0.568, lumbar +0.773 -> +0.766, glute +0.285 -> +0.391; regions marginally lower under plate light: front chest -0.005, back lumbar -0.007).
* **Lower-pec shelf** (crest-to-crease luminance drop down the pec, |x| 0.07-0.13): plate-lit plate 38.0 lum (crease z 1.175), FORM2 33.7 (z 1.175), **FORM3 46.0** (z 1.180); Unity-style render FORM2 14.2 -> **FORM3 24.1 lum** (skin; clay 13.1 -> 24.1; normalised 0.081 -> 0.140).
* **Buttock split** (back-most surface across x, centre vs lobe crest at |x| ~ 38 mm): cleft depth z 0.82 / 0.84 / 0.86 = +1.1 / -0.1 / -0.7 mm (FORM2: one block, centre proud) -> **+10.3 / +6.0 / +3.5 mm**; back-most extent vs the side plates at z 0.82 / 0.84 / 0.86 (mm from centre, 5.8 mm/px): plate 153 / 148 / 142, FORM2 142 / 142 / 142, FORM3 145 / 148 / 145.
* Silhouette bald front/back 4.3203 / 4.3854 % (FORM2 4.3203 / 4.3854; unchanged by construction; left/right masks 8.98/9.87 vs 9.01/9.76). On the **installed** ArtDir blend (whole figure incl. the newer hands/legs of the other chats): front 4.1407 / back 4.7340 % - identical to the pre-install values (4.1407 / 4.7340). Depth vs left/right plate silhouettes z 0.92-1.30: rms 2.69 -> 2.61 mm, mean +0.73 -> +0.29 mm.
* **No banding**: fine-scale (2.9-7 mm) shading energy per region, FORM3 / plate: front chest 1.62x, front abdomen 0.92x, front pelvis 1.10x, back upper 0.58x, back lumbar 0.81x, back glute 1.84x (FORM2: 0.65x, 0.64x, 0.88x, 0.55x, 0.75x, 1.19x); longest dark horizontal run 0.05 (front) / 0.00 (back) of the torso width; one pec crease (secondary minima < 25 % of it).
* **Custom normals follow the geometry** (the mesh carries a custom-normal attribute): corner normals vs freshly computed smooth normals of the new shape, torso zone: median 0.000 deg, p99 0.024 deg, in the installed blend and in the re-imported FBX - the relief will shade in Unity.

## Honest limits and what Adnan should know

* **Held-out check is slightly WORSE.** The two back 3/4 panels of the sheet (validation only, never fitted; the AI plates are not fully 3D-consistent) correlate less with FORM3: left 0.616 -> 0.588, right 0.482 -> 0.466; glute band 0.86/0.82 -> 0.79/0.76, lumbar 0.69/0.68 -> 0.63/0.64, upper back 0.59/0.59 -> 0.56/0.55. The frozen photometric fit alone moves the panels 0.616 -> 0.595 (left) and 0.482 -> 0.489 (right); the requested buttock lobes + cleft take them on to 0.588 / 0.466 (glute band 0.83/0.86 -> 0.79/0.76, lumbar even improves 0.61/0.61 -> 0.63/0.64) and the glute-band loss trades almost linearly against cleft depth (6 / 10 / 15 mm cleft: left glute band 0.82 / 0.79 / 0.72). The primary front/back plates improve in all six regions; the brief names the 3/4 panels as validation only, so this is disclosed rather than gated.
* **The gate metric is lighting-capped and hypersensitive.** It compares a Unity-style render with a plate lit almost head-on; the same mesh Unity-lit vs plate-lit correlates only ~0.68, and ~1-5 mm of relief moves the band-passed r by 0.1-0.2 (the pec/abdomen/glute gains are real and visible, but absolute r is not 'fidelity'). The joint solver's path matters: running front and back as independent solves stalls on the back (stuck at a worse minimum), so the validated joint solution is frozen as an asset.
* **Not fixed (belongs to other zones or resolution-limited).** The plate's gluteal fold arcs, thigh overhang and the squared crotch slot (z < 0.77, legs zone) - the cleft ends in a closing ramp at the zone floor; the plate's pecs are rounder and bigger in 3/4 than the silhouette-bound mesh allows; the shelf fades at the sternum (the plate's own centre dip is only ~4 lum); vertex spacing is ~11.5 mm with no vertex on the midline, so creases cannot get sharper than 2 vertices; the Unity-style shelf contrast (24 lum) is still below the plate's own normalised contrast because the rig is flatter.
* **Unity not refreshed.** The Unity project keeps its own FBX copy (`Unity/Assets/Characters/HeroBase/Models/`); other chats were still installing, so only the ArtDir blend + FBX were updated (`HeroBaseMaleFormProof.cs` `ExpectedTriangles` must be 66158 when it is refreshed).

## Files, hashes, install

* Install: SHA-guarded **vertex-index patch** onto the then-current ArtDir blend `2e8f973b…` (the brief's start SHA `1fe4d53b…` had moved three times: hands FORM2 `4287ba52…`, hands FORM3 `b51cbb05…`, legs/feet `2e8f973b…`); guard: all 5587 delta vertices at their FORM2 positions (0 foreign); post-merge verifier: 5587 vertices differ from the pre-install blend, all inside the delta set, topology/Face_M/groups/materials/cameras identical (`proof/male-torso-form3-install-verify.json`). Lock dir taken/released; backup before copy; last-moment SHA recheck; atomic move.
* Blend (installed): `ArtDir/hero/base_lock/blender/HeroBase_Male_Silhouette.blend` SHA-256 `548a83f4bf3f8624e452955bfef84e3f5bf84a3088f8cd9ae5325dc20d426495`
* FBX (installed; Body_M only, same flags, re-export of the merged blend): `ArtDir/hero/base_lock/unity_import/HeroBase_Male_Body.fbx` SHA-256 `2e0740d7127556fc2176e4d35d7f8d916180e856187de3de71b46ef16f5e5bfc` (66,158 tris, re-import max error 0.00028 mm)
* Staged (start-blend based, pre-merge) copies: `work/male-parallel-torso3/export/HeroBase_Male_Silhouette_form3.blend` `ee827d3a94a6…`, `HeroBase_Male_Body_form3.fbx` `c691a7d85161…` (60,358 tris, re-import max error 0.00028 mm); merged copies `export/merged_2e8f973b.*`.
* **Rollback**: `work/male-parallel-torso3/baseline/pre_install_form3_2e8f973b.blend` / `work/male-parallel-torso3/baseline/pre_install_form3_d40e9b55.fbx`. **Re-apply on a newer blend**: `blender -b --factory-startup --python work/male-parallel-torso3/apply_form3.py -- <current.blend> <out.blend>` (5,587 vertices in `export/form3_zone_delta.npz`; aborts on any foreign torso vertex).
* Machine checks: `proof/male-torso-form3-checks.json` (zone categories, topology, integrity, silhouettes, depth, form r, shelf contrast, held-out, banding, glute split, self-intersection, FBX, install), `proof/male-torso-form3-audit.json`, `proof/normals_form3*.json`, `proof/selfisect_*.json`, `proof/installed_silhouette.json`.

## Proof

* `proof/03_form3_proof_m.png` - front/back: plate | FORM2 | FORM3, real render and local-contrast relief, with the gate numbers.
* `proof/03_form3_proof_q3_m.png` - four 3/4 views: plate | FORM2 | FORM3.
* `proof/03_form3_proof_side_m.png` - left/right silhouettes vs the plate masks, FORM2 vs FORM3.
* `proof/03_form3_closeup_chest_m.png`, `03_form3_closeup_mid_m.png`, `03_form3_closeup_glute_m.png` - mandatory close-ups: plate (raw + relief) | FORM2 (skin + relief) | FORM3 (skin + relief).
* `proof/03_form3_proof_detail_m.png` - chest / waist / upper back / glute under the plate's own lighting.
* `proof/03_form3_proof_pelvis_m.png` - pelvis shelf and buttock under raking light (shelf stays clean).
* `proof/03_form3_zone_m.png` - displacement heat map (grey = bit-identical).

## Reproduce

`work/male-parallel-torso3/`: `./run_form3.sh FORM3` (build -> stage blend + FBX -> audit -> self-intersection -> renders -> gates), recipe `base_FORM3.json` (+ frozen asset `data/RBF_FORM3_asset.npz`, produced by `path3.py both PJ '{"iters":14,"gF":[3.5,2.6,2.2],"gB":[2.2,2.0,3.5]}'`, iterate 12), `fast3.py` / `form3.py` (stages), `pmo3.py` (solver with extreme bounds, relief gain, deficit guard), `struct3.py` (structure fields), `finalize_form3.py` (gates), `compose_form3.py` + `zonemap.py` (proof), `banding3.py`, `selfisect3.py`, `normals3.py`, `install_form3.sh` / `apply_form3.py` / `verify_merge3.py` (install). Exploration scripts: `parfit3.py` (parametric feature fit), `sweep_*`, `rsearch*.py`, `abl3.py`.
