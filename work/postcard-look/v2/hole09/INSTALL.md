# INSTALL - hole 9 "Split" look build, GRASS + SWAY pass (CONTINUE job phase 3, HOLE 9 REPAIR ROUND 0; staged 2026-10-05, NOTHING installed yet)

The staged build is in `work/postcard-look/v2/hole09/stage/`. It was produced by `blender/scripts/hole09_build.py -- --out ...stage` (deterministic, see GATES_hole09.txt H_REPRODUCIBLE)
and exported with `postcard_look_lib.export_look_fbx` (not `postcard_lib.export_fbx`; colors_type LINEAR, so the sway vertex colours of every PLANT_ mesh arrive raw in Unity's `mesh.colors`). Install = copy exactly TWO files.
Run it only through the integrator's `run_proof.sh` (a reimport of a changed hole_09.fbx disturbs a running Unity batch).

## sha256 of the staged files (verify before copying)

```
b1040710e7b0f10fad51817f2fb0f5165ac1349bfa5c68f2462d06057abd4609  work/postcard-look/v2/hole09/stage/hole_09.blend   (2942677 bytes)
56bf6e371f66e21e981552617a5a86beb790898ba46779a58b9f59e1d7ce3dc2  work/postcard-look/v2/hole09/stage/hole_09.fbx   (5566284 bytes, 5.31 MB, 1417 mesh objects, 247,459 triangles)
```
Same list in `work/postcard-look/v2/hole09/final/install_sha256.txt` (that file also holds the sha of the existing `hole_09.fbx.meta`).
The repo holds the ROUND-3 stage before this install (blend `ceaa6156f6c81fb4..`, FBX `9de2906f53cc2435..`, kept in `work/postcard-look/v2/hole09/r8/before_r8/stage_r7/`); the staged files were rebuilt on the libs / textures / verifier the shared fixers changed in this same round
(sha256 of every lib at the start of this round: `lib_sha_r8_start.txt`, at the final build: `final/script_sha256_at_final_build.txt`; the 31 Look PNG sha256 at the final build: `final/look_png_sha256_at_final_build.txt`).
The libs, textures, verifier and Unity files were NOT edited by this agent.

## What this round changed (hole scripts only: hole09_look.py, hole09_build.py docstring, hole09_masonry.py, hole09_stone.py + the tools in work/postcard-look/v2/hole09/tools/)

Reviewer findings handled: (1) high, GRASS LIVELINESS + SWAY: "the near ground reads as a carpet; add the edge fringe; plants must carry sway data"; (2) medium, the ruin: "still a pile of straight-cut boxes ... the arch crown reads as two floating blocks"; (3) the low protected-files note is not ours.

**1. Sway data.** Every PLANT_* mesh (and every LK_PLANTS mesh without one) carries the sway vertex colours the new props library writes (R weight, G phase, B 0, A 1); the build only has to export with `export_look_fbx` (it does). Verified on the blend AND the FBX re-import by `postcard_look_verify.py 9`
(PLANT_SWAY_COLORS@blend / @fbx and PLANT_SWAY_CAPS@blend / @fbx: all 14 unique PLANT_* meshes carry them, root <= 0.05, tip > 0.6 for tuft / flower / agave, shrub / tree > 0.25, tuft cap 0.0591 yd <= 0.06 at 20 mph). The new tuft kinds (D, E, F tall, S, T fillers) are in the file; nothing static was added to the water / lava paths.

**2. Edge fringe** (`hole09_look.build_grass`, PL.scatter_fringe in zones). Clumps of 3-7 tall leaning tufts (lean <= 12 deg, 0.6-1.8 x height, +-6 % xy scale) along the rough edge of the fairway / green / tee and the cliff lips, never on a play surface / bunker / water, >= 1.1 m inside the lip (the hole's own gate wants 1.0 m),
>= 4 m (tee ball 1.5 m) from every still ball, >= 6 m from the pin, tops <= 0.503 m (0.55 yd) within 17.2 m of the centerline or 12 m of a ball. Zones (the camera sees the rough edge of the ribbon only from ~35 m ahead of the ball, so the tee zone starts at y 30 m): tee_view 142 tufts / 8.5k tris (27 clumps + 7 singles); ribbon_mid 68 tufts / 4.0k tris (11 clumps + 7 singles); green_end 113 tufts / 7.0k tris (23 clumps + 7 singles); ruin 45 tufts / 2.5k tris (11 clumps + 3 singles); far_green 36 tufts / 2.0k tris (7 clumps + 5 singles); far_olive 19 tufts / 1.0k tris (5 clumps + 2 singles).
Green tufts (D / E / S) stand off the scrub polygon, olive / straw tufts (F / T) inside it. `423` fringe tufts in all. Measured by `tools/grass_gates.py` (blend + FBX re-import): GRASS_FRINGE_PRESENT, GRASS_NOT_ON_PLAY_SURFACES, GRASS_NOT_ON_WATER, GRASS_BALL_CLEAR, GRASS_TRI_BUDGET all PASS (coverage of the rough-edge strips (a fringe tuft within 2.2 m of a 2 m grid point 0.35-2.5 m outside a play surface / 0.9-2.5 m inside the lip): tee view 67/166 = 40% (>= 30 %), green end 54/238 = 23% (>= 20 %), ribbon middle 56/363 = 15%;).
**Open scrub** (the ground of the ruin landmark frame is open ridge, not a rough edge): 130 olive tufts in 32 clumps whose centres are the ground points that project into the landmark camera (landmarks.json hole09_ruin), 60 tufts at the foot of the ruin walls (>= 0.6 m from any masonry vertex), a skirt of 48 ground-rooted tufts round the 12 bushes nearest the ruin.
**Not done, measured:** `PL.tuftify_shrubs` / `tuftify_crowns` (tufts ON a shrub lump / a sea-stack crown): the hole's own H_NO_PLANT_ON_WATER wants every plant rooted on the ground (|origin z - ground| <= 6 cm; a crown tuft has a WATER lie under it) and the verifier's NO_PLANT_ON_WATER wants ground or a rock top within 0.5 m under the lowest blade (a shrub top is 0.7-0.9 m up, a crown blade overhangs the rim): both FAILED them (`r8/g1`, `r8/g2`), the gates stay as they are, the bushes get the ground skirt instead.
**What the stills can show:** the lower 60 % of the tee / approach address frames is the tee box / fairway within ~4 yd of the ball (camera 4.5 yd behind the ball, 2.4 yd up, 60 deg), where no tuft may stand: the fringe is visible on the far rough edges (upper third) there, and clearly on the ruin landmark. Blender-side proxy (NOT the Game-view GRASS_STILL_ALIVE): tuft pixels of the still cameras, round-3 stage -> now: `final/tuft_mask_before.log` / `tuft_mask_after.log`.

**3. Budget** (247459 triangles over 1417 mesh objects (<= 250000; before the grass pass 247439: +20); all 841 PLANT_TUFT* = 48024 tris, fringe 423 tufts = 24894 tris (59 per tuft); FBX 5.31 MB (<= 20); animation actions 0). The fringe was paid for by: `PL.cheapen_tufts(near_m = 25)`: 162 old 117-triangle tufts -> 36-triangle fillers (13122 triangles saved, 18 kept near the balls); ridge shrubs 116 -> 76 (mix C:A 5:1 -> 2:3; the thickets are
18 centres instead of 30 so H_RIDGE_THICKETS still holds), outer shrubs 30 -> 20, ridge stones 56 -> 44. (`SKIN_STEP_M` does nothing: the strata columns follow the TERRAIN outline vertices, closer than 2.4 m apart; a larger step was tried and measured identical, so it is unchanged.) Triangles 247,459 (limit 250,000; before this pass 247,439), FBX 5.31 MB (limit 20), no animation.

**4. The ruin** (`hole09_masonry.py`, `hole09_stone.py`; findings: straight-cut boxes, flat slabs, the two floating arch halves). Stones are 15 % bigger (0.85-1.65 m, bed levels 0.24-0.46 m: 360 masonry stones, was 389), every wall stone has its four VERTICAL edges chamfered 5-12 cm (the tops stop being rectangles) plus 2-6 cm arris bevels and 6-21 cm corner chips
(bottom corners keep the old 5-17 cm), up to 23 faces; wall depth 0.78-1.0 of the wall (more relief). Side planes may not make a near-coplanar (< 14 deg) pair with another side face (`hole09_stone.bad_pairs`: one such pair got two different brick windows in the first try = RUIN_NO_UV_SPLIT, now 18 near-coplanar pairs, 0 mismatching).
The arch keeps all 11 wedges: the CROWN WEDGE HAS SLIPPED 13 cm toward the opening (a radial slide keeps both side planes in face contact), so there are no two floating halves with a gap; its inner corners are knocked off by the fall; the rubble heap stays under it. Ruin gates (tools/ruin_check.py, blend AND FBX re-import): 13 of 13 PASS (RUIN_BASE_BURIED 86 %, RUIN_ARCH_SEATED masonry within 6 cm at 167 of 181 angles, RUIN_PLANAR_FACES worst 0.017 mm, LK_MASONRY share >= 65 %, LK_ROCK <= 35 %).
`landmarks.json` is regenerated (`tools/make_landmarks.py`): the ruin camera is (-64.33, 26, 145.96) / look (-64.33, 10.17, 115.96); the tee and approach shots are unchanged. TEE_EDGE_UV_CONTINUOUS (round 3's tee parallax fix) still PASS (max 0.002 m).

**5. Gates.** postcard_look_verify.py 9: 96 lines at both stages, RESULT ALL PASS; hole09_qa.py: 27 / 27 PASS (blend + FBX re-import); postcard_verify.py: FAIL only MATERIALS@blend / @fbx and FBX_BUDGET@fbx, by design (old MAT_* allow-list, old 4 MB / 150k budget; superseded by LOOK_CONTRACT section 3 / H_BUDGET);
postcard_emit_cs.py --check: no drift; guards.sh 7 / 7; hole09_design.py byte-identical to `hole09_design.py.at_start`. Blender previews (`previews/`, `r8/d*_views/`) are NOT Game-view proof: the Game-view stills must be re-shot with `landmarks.json` by the integrator.

## 0. Preconditions (stop if one is false)

```
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
S=work/postcard-look/v2/hole09/stage
# the repo hole_09 files are one of known states (this job never writes them):
shasum -a 256 blender/hole_09.blend Unity/Assets/Resources/Course/hole_09.fbx
#   (a) the ROUND-3 STAGE (installed by the integrator; this round replaces it):
#       ceaa6156f6c81fb42f01f0772da67a6a46ff73c55a9cd4741d3ac3bbfe183d39  blender/hole_09.blend        (= work/postcard-look/v2/hole09/r8/before_r8/stage_r7/hole_09.blend)
#       9de2906f53cc243501a5e78965eef00956c29b4db7f9c6c44d5c76b30a03c67c  Unity/Assets/Resources/Course/hole_09.fbx   (= work/postcard-look/v2/hole09/r8/before_r8/stage_r7/hole_09.fbx)
#   (b) or the flat baseline:  8846a99f7b5314a7a4bb3f170d57485d2f489b88fd9e64dd509450d8eaee42ad  blender/hole_09.blend  /  88005a32d046181dae84b4b778ca14585dabdf9099f5ba2163d602c737f2b01e  hole_09.fbx
# the staged files are the ones that were gated:
echo "b1040710e7b0f10fad51817f2fb0f5165ac1349bfa5c68f2462d06057abd4609  $S/hole_09.blend" | shasum -a 256 -c -
echo "56bf6e371f66e21e981552617a5a86beb790898ba46779a58b9f59e1d7ce3dc2  $S/hole_09.fbx" | shasum -a 256 -c -
# the scoring + hole 7 guards (must print 7 PASS):
bash work/postcard-look/guards.sh
```

## 1. Install (copy hole_09.blend and hole_09.fbx ONLY)

```
cp $S/hole_09.blend blender/hole_09.blend
cp $S/hole_09.fbx   Unity/Assets/Resources/Course/hole_09.fbx
```
**NEVER overwrite `Unity/Assets/Resources/Course/hole_09.fbx.meta`.** It holds the GUID (guid: a41a7055f5d449c993233b2b3887ba18) and the importer settings
(`isReadable: 1`, `tangentImportMode: 3`, `materialName: 0`, `normalImportMode: 0`); the staged folder also contains a `hole_09.fbx.meta` with a FRESH random GUID: do not copy it. Also not copied: `stage/hole_09.blend1` (Blender's backup),
`stage/hole_09_overview.png` (a preview; copy it to `blender/previews/hole_09_overview.png` only to refresh the overview), `stage_repro/` (the reproducibility twin). The existing `.meta` sha256 must stay `65b4dd392ac3cb1929d9f456d8973b2a1900d80dac0c59d192a7c60d7edeac6c`.
The FBX must keep the mesh colours: the `.meta` has no `importVertexColors` switch to flip (Unity imports FBX vertex colours into `mesh.colors` by default); the Unity owner checks `Mesh.colors` of a PLANT_TUFT_D instance after the import (R 0 at the root, 1.0 at the tip).

## 2. Verify after the copy (Blender headless, no Unity needed)

```
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- 9          # repo blend + FBX; expect RESULT: ALL PASS (96 gate lines; LOOK_STILLS_TEXTURED is SKIPPED until Game-view stills exist, then run with --require-stills)
$B -b blender/hole_09.blend --python blender/scripts/postcard_verify.py -- hole09_design   # FAIL only MATERIALS@blend/@fbx + FBX_BUDGET@fbx, by design
python3 blender/scripts/postcard_emit_cs.py --check Unity/Assets/Scripts/Course/Hole.cs      # HOLE_CS_MATCHES_DESIGN PASS
bash work/postcard-look/guards.sh                                                          # 7 PASS
$B -b --factory-startup --python blender/scripts/hole09_qa.py -- --blend blender/hole_09.blend --fbx Unity/Assets/Resources/Course/hole_09.fbx   # HOLE09_QA: 27 gates, 0 FAIL
$B -b --factory-startup --python work/postcard-look/v2/hole09/tools/ruin_check.py -- --blend blender/hole_09.blend     # RUIN_CHECK: 0 FAIL of 13
$B -b --factory-startup --python work/postcard-look/v2/hole09/tools/grass_gates.py -- --blend blender/hole_09.blend --fbx Unity/Assets/Resources/Course/hole_09.fbx   # GRASS_GATES: 8 gates, 0 FAIL
$B -b blender/hole_09.blend --python work/postcard-look/v2/hole09/tools/tee_parallax_check.py                         # TEE_EDGE_UV_CONTINUOUS PASS
shasum -a 256 blender/hole_09.blend Unity/Assets/Resources/Course/hole_09.fbx              # = the two staged sha256 above
shasum -a 256 Unity/Assets/Resources/Course/hole_09.fbx.meta                               # unchanged
```
Then (Unity owner, through work/postcard-look/heavy.sh): `PostcardImportCheck`, `GolfLookSmoke`, the sway frame pairs, and the stills with `GOLF_STILLS_CFG=work/postcard-look/v2/hole09/landmarks.json` -> `ArtDir/screenshots/golf_postcards/look/`
(shots hole09_tee, hole09_approach, hole09_ruin; the `extra_previews` key is ignored by the tool). Expected: every hole 9 ground / rock / cliff / plant material is an `LK_` name (`LK_PLANTS` = ONE shared material, which GolfLook maps to GolfArcade/GolfPlants);
the ruin / arch meshes have TWO material slots (LK_MASONRY, LK_ROCK; non-colliding); only TERRAIN, FAIRWAY, GREEN, TEE_BOX, BUNKER get colliders (every new object is ROCK_ / PLANT_ / DRESS_ / WATER_).

## 3. Rebuild without staging (same geometry, writes the repo paths = the install)

```
$B -b --factory-startup --python blender/scripts/hole09_build.py            # no --out: blender/hole_09.blend, blender/previews/hole_09_overview.png, Unity/.../hole_09.fbx
```
(`hole_09.fbx.meta` is only created when it does not exist, so the existing one is kept.) The blend and the FBX re-import are geometry-identical to the staged ones (gate H_REPRODUCIBLE); the FBX bytes differ run to run (header timestamp, zlib streams).
Everything the staged build needs is deterministic: `PL.scatter_fringe` / `scatter` / `cheapen_tufts` (crc32 seeds) and the masonry (seeded `random.Random`).

## 4. Rollback

```
cp work/postcard-look/v2/hole09/r8/before_r8/stage_r7/hole_09.blend blender/hole_09.blend            # the round-3 stage, sha256 ceaa6156f6c81fb42f01f0772da67a6a46ff73c55a9cd4741d3ac3bbfe183d39   (the state the repo is in before this install)
cp work/postcard-look/v2/hole09/r8/before_r8/stage_r7/hole_09.fbx Unity/Assets/Resources/Course/hole_09.fbx   # sha256 9de2906f53cc243501a5e78965eef00956c29b4db7f9c6c44d5c76b30a03c67c
cp work/postcard-look/baseline/blender/hole_09.blend blender/hole_09.blend            # sha256 8846a99f7b5314a7a4bb3f170d57485d2f489b88fd9e64dd509450d8eaee42ad   (the flat afternoon baseline)
cp work/postcard-look/baseline/fbx/hole_09.fbx Unity/Assets/Resources/Course/hole_09.fbx   # sha256 88005a32d046181dae84b4b778ca14585dabdf9099f5ba2163d602c737f2b01e
```
The scripts at the start of this round: `work/postcard-look/v2/hole09/r8/before_r8/*.at_start` (hole09_build / look / masonry / stone / qa / design) and `*.pre_ruin` (masonry / stone before the ruin change); round 3's INSTALL.md / GATES_hole09.txt / landmarks.json: `work/postcard-look/v2/hole09/r8/before_r8/`.

## Files this job owns / changed (nothing else was touched)

```
5ca039948d4b32c94fa9a8a622e081d82c364452eb933149d71ed2bcd98bfb46  blender/scripts/hole09_build.py
9067512e72894b81ddc2118d876a1b111e31bfc3ed5b46ddbbd54ad7d38fbca9  blender/scripts/hole09_look.py
9197e7a762ceb5e877af69db2ced1cf81cc86559c4c96be19520f857cef022a5  blender/scripts/hole09_masonry.py
fb272e9d606d24378462f2516a66a017f087213a00319984471083d67a4ebf62  blender/scripts/hole09_stone.py
3069418688b3f2b7b2e73bc63fe0b4cbebb30a1252e0a09795139fb0c126f84d  blender/scripts/hole09_qa.py
8264099d82b9f9246a8837c4856d50d3aef151449b5c2cb57a65e12106ed82b0  blender/scripts/hole09_design.py
02bee4eb29f053ba701c03d3b27b7a659005f587f8da7f241c235c9c67bacc33  blender/scripts/postcard_look_lib.py
42e2bf2bda31b23e534012a8b5dae9bdab2985dd6c8f364ba8a7e5401ceb1157  blender/scripts/postcard_props_lib.py
ff3062b6798fafcf021183e2da39461b501ff7dbce45f75dab3111884b94d3f4  blender/scripts/postcard_lib.py
a78560f62ee12cb38df6c8515e4530ce458dc19bc97634d0a56dd5d268b02ef4  blender/scripts/postcard_look_verify.py
0395e94d0fdf1e82d4c0979c9b173f2033bc6b5968162875846afcf357ecd27f  blender/scripts/golf_look_textures.py
4b1b4cd3fbdfc407308195730f44f67c29c397b49e574213840d324cc454daa4  work/postcard-look/v2/hole09/tools/ruin_check.py
1b427a78cc035bf31627352a5fd23eca2d2b4b302223dea011292fb8e49ea760  work/postcard-look/v2/hole09/tools/tee_parallax_check.py
93cb4859fabd6d884d9d06f65825c492c2e9ffee5c14d69d28d5be3da967971e  work/postcard-look/v2/hole09/tools/grass_gates.py
80b892661f64b7d01b538119088492d7b009a5269b5a00e3b63a775151faff84  work/postcard-look/v2/hole09/tools/tuft_mask.py
38ca395fed06607d910c1fb7cf268031008656cb038125b9875cdf618f1bd55d  work/postcard-look/v2/hole09/tools/run_all_gates.sh
bd4ac8c004622addd6e8c4792bee22160acc1854470433d24c9ac8f666a1763d  work/postcard-look/v2/hole09/tools/run_final_pipeline.sh
ab206b4b131f3ec773b467c7a424d4bed0432ab2cb4d2c33f149ba5668ba2f09  work/postcard-look/v2/hole09/tools/make_gates_txt.py
ad640a487cf9754136a2863769d7553e9ea8268e577b3765c0152cb028b662e1  work/postcard-look/v2/hole09/tools/make_install_md.py
```
`hole09_design.py` is byte-identical to its start-of-job copy (`work/postcard-look/v2/hole09/hole09_design.py.at_start`; `postcard_emit_cs.py --check` = no drift), `postcard_lib.py`, both libraries, the textures, the verifier and every Unity file were not edited by this agent
(their sha256 at the start of this round: `work/postcard-look/v2/hole09/lib_sha_r8_start.txt`; library behaviours worked around in the hole scripts: `work/postcard-look/v2/hole09/LIB_BUGS.md`).
