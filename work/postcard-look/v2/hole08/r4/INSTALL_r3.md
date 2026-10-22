# Hole 8 Needle: install (NOT done: staged only) -- round 3 (second reviewer round, 2026-10-04)

Staged build (`run_all.sh`; lib sha256 in `logs/lib_sha_final.txt`, unchanged since the start of round 2 and round 3: `r2/lib_sha_ref.txt`, `r3/sha_at_start.txt`; the Look PNGs too: `logs/look_png_sha_final.txt`). Nothing in the repo was written:
`blender/hole_08.blend`, `Unity/Assets/Resources/Course/hole_08.fbx` and `hole_08.fbx.meta` are still byte-identical to the baseline (sha below).

## sha256 of the staged files (`stage/`, `logs/stage_sha256.txt`)

```
f56e718c976d6aa27454b1a104a8de087e7952deff5ac8bc1ae04ebb397cc50f  stage/hole_08.blend
eecb67c0dcac956e9172fca63e7583922740f516038a13d2f244f72a866b5433  stage/hole_08.fbx          (2.62 MB, 187,146 triangles in the export set, exported with postcard_look_lib.export_look_fbx)
2214b4aa2c08b952fc5b649628e365c29afda93905b332ebde844051b5c02c09  stage/hole_08.fbx.meta     (staging copy of the hole 7 meta with a fresh guid: DO NOT COPY IT)
```
Geometry hash of the build (names + 0.1 mm world vertices of every mesh): `b357d8aab8c03498`, identical in 3 builds (`logs/reproducible.txt`). The .blend / .fbx bytes themselves
carry timestamps, so a rebuild changes their sha but not the geometry hash.

Repo files today: `blender/hole_08.blend` 38c25178..., `hole_08.fbx` d19a46b6..., `hole_08.fbx.meta` 3f7371fe... (the meta holds the GUID and isReadable 1 / tangentImportMode 3: never overwritten).
Baseline backups: `work/postcard-look/baseline/blender/hole_08.blend` 38c25178..., `baseline/fbx/hole_08.fbx` d19a46b6....

## Install (copy the .blend and the .fbx ONLY)

```bash
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
S=work/postcard-look/v2/hole08/stage
shasum -a 256 $S/hole_08.blend $S/hole_08.fbx                                  # must equal the two lines above
cp $S/hole_08.blend blender/hole_08.blend
cp $S/hole_08.fbx   Unity/Assets/Resources/Course/hole_08.fbx
#   do NOT touch Unity/Assets/Resources/Course/hole_08.fbx.meta (and not hole_07.*, not hole_09 / hole_10 files)
```
Unity reimports the FBX on focus (the meta keeps the old GUID, so `Resources.Load("Course/hole_08")` and every reference stay valid).
`blender/previews/hole_08_overview.png` is not part of the install (the staged overview is `stage/hole_08_overview.png`; copy it only if the repo preview should change).

## Rollback

```bash
cp work/postcard-look/baseline/blender/hole_08.blend blender/hole_08.blend
cp work/postcard-look/baseline/fbx/hole_08.fbx       Unity/Assets/Resources/Course/hole_08.fbx
```

## After the copy (Unity side, through work/postcard-look/heavy.sh)

```bash
work/postcard-look/v2/runtime/run_importcheck.sh h8      # GROUND_ALBEDO_AND_NORMAL / NO_FLAT_POSTCARD_GROUND turn PASS for hole 8; ground-height / lie / marker lines stay PASS
work/postcard-look/v2/runtime/run_smoke.sh h8
work/postcard-look/v2/runtime/run_stills.sh h8 ArtDir/screenshots/golf_postcards/look GOLF_STILLS_CFG=$PWD/work/postcard-look/v2/hole08/landmarks.json
#   landmarks.json holds hole 8's shots only (the cfg REPLACES the default list): hole08_tee, hole08_approach, hole08_arch (the landmark), hole08_pathball (optional extra);
#   merge it with the hole 9 / 10 cfgs for one run, or run it alone: the tool takes the shots of one hole together.
```
Rebuild without installing: `Blender -b --factory-startup --python blender/scripts/hole08_build.py -- --out <dir>` (never run it WITHOUT --out until the install is meant to happen: without --out it writes
`blender/hole_08.blend`, `blender/previews/hole_08_overview.png` and `Unity/.../hole_08.fbx`). Everything (build, verifier on blend + FBX re-import, postcard_verify, postcard_check, the baseline comparison,
frame variation, dense path height, landmarks, previews, negative controls, reproducibility, guards): `work/postcard-look/v2/hole08/run_all.sh` (about 12 minutes), summary `GATES_hole08.md`.

## What round 3 changed (second reviewer round; paths / tools only, no ground vertex moved: H_PLAY_UNCHANGED)

* Both flagstone paths now run along the ball's left side (hole08_look.PATHS): the lower 60 % of the tee and approach frames held only 2 % / 0 % stones (the camera sees 2-3 yd of ground across the lower fifth of the frame, so a path 3 yd away is
  outside it). Now the stones cover 12.9 % (tee) / 16.3 % (approach) of the lower 60 %; the nearest path vertex stays 1.27 m (tee) / 0.61 m (approach) from the ball (new gate PATH_CLEAR_OF_BALL >= 0.5 m; the path may lie under a ball, <= 1.2 cm, but a white ball reads
  best on grass). Albedo luminance sd of the lower 60 %: tee 13.3 -> 16.5, approach 12.7 -> 16.9 (`logs/frame_variation.json`). Optional path-ball shot moved to the tee path control point (0.8, 10).
* The tee box stays cross-mown LK_FAIRWAY (a LK_GREEN tee box was measured and rejected: grass-only albedo sd 7.9 against 13.1); it reads as its own pad by the 90 degree stripe turn, the tone step and the 10 cm step (H_TEE_PAD_DISTINCT).
* Gate honesty: the plant-on-water gate reports both counts (0 on the sea; 45 outcrop plants read Water by the scoring mirror's xy but stand on the arch outcrop rock), and the lowest-plant-base list that was declared but never filled in round 2 is filled now.
* Negative controls 13/13 (a path on the ball is caught).
* STILL FAILING, not a hole file: `LOOK_FILES` (Fairway_C 1 % / Green_C 0 % of 64 px windows reach sd 0.03): texture files and the lead's floor (GATES.md 'LEAD DECISION'). UNVERIFIED: everything in the Game view.

## Runtime facts the integrator needs

* Materials in the FBX are the LK_* contract names (LK_FAIRWAY, LK_GREEN, LK_ROUGH, LK_SAND, LK_CLIFF, LK_CLIFF_DARK, LK_ROCK, LK_ROCK_WET, LK_MASONRY, LK_PATH, LK_PLANTS, LK_WATER, LK_WATER_SHALLOW, LK_SURF,
  LK_FALL) plus MAT_FLAG / POLE / CUP / BALL for the gameplay placeholders; the FBX holds no texture reference (GolfLook loads the PNGs by name). The TEE_BOX now carries LK_FAIRWAY (it was LK_GREEN): its UVs are rotated 90 degrees (stripes across the line of play).
* Only TERRAIN_NEEDLE, FAIRWAY, FAIRWAY_FIRSTCUT, GREEN, GREEN_APRON, TEE_BOX, BUNKER_01, BUNKER_01_LIP are collision-named (the same 8 meshes, vertex-identical to the baseline). Everything new is ROCK_ / PLANT_ / DRESS_ / WATER_.
* `WATER_FALL_00` (the waterfall sheet, LK_FALL, vertical, UV v runs down) and the 18 `WATER_SURF_nn` patches (vertex colour A = shore closeness) need `GolfArcade/GolfSurf`; `WATER_OCEAN` is one 2 km grid, `WATER_SHELF` the thin shelf.
* Unity colours of the water materials come from `GolfLook` by name (LK_WATER_SHALLOW Shallow (27,106,120)); the Blender colours are previews only.
* Mesh objects / datablocks and the triangle split: see `logs/h_numbers.json` (the biggest cost is the plants and vines; drop the 300 far tufts (`PL.scatter` seed 4 in hole08_look) first if the iPhone budget needs it).
