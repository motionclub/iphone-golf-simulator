# Hole 8 Needle: install (NOT done: staged only) -- round 2 (reviewer findings fixed, 2026-10-04)

Staged build (`run_all.sh`; lib sha256 in `logs/lib_sha_final.txt`, unchanged since the start of round 2: `r2/lib_sha_ref.txt`). Nothing in the repo was written:
`blender/hole_08.blend`, `Unity/Assets/Resources/Course/hole_08.fbx` and `hole_08.fbx.meta` are still byte-identical to the baseline (sha below).

## sha256 of the staged files (`stage/`, `logs/stage_sha256.txt`)

```
ea5ad189677b4c0207229eb82709c7ce2494c43aa26589f097bec5bdb356f578  stage/hole_08.blend
95573bc38843445b853db3dd10824085da49b25e3b8fd52168c486a3376f7d72  stage/hole_08.fbx          (2.60 MB, 188,395 triangles in the export set, exported with postcard_look_lib.export_look_fbx)
2214b4aa2c08b952fc5b649628e365c29afda93905b332ebde844051b5c02c09  stage/hole_08.fbx.meta     (staging copy of the hole 7 meta with a fresh guid: DO NOT COPY IT)
```
Geometry hash of the build (names + 0.1 mm world vertices of every mesh): `a09d4a2036f5a087`, identical in 3 builds (`logs/reproducible.txt`). The .blend / .fbx bytes themselves
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

## What round 2 changed (reviewer findings; all UV / material / path / plant level, no ground vertex moved: H_PLAY_UNCHANGED)

* Mow pattern (`hole08_look.mow_pattern`): `Fairway_C` has its light mow band centred on u = 0, so the whole 4 m wide near field of both phone cameras sat in one band. LK_FAIRWAY u + 0.2 (a band edge 0.5 m right of the line), the TEE_BOX is cross-mown LK_FAIRWAY
  (was LK_GREEN, Green_C is nearly flat) with an edge 0.5 m behind the ball. Albedo luminance sd over the lower 60 % of the frames: tee 7.2 -> 13.3, approach 6.4 -> 12.7 (`logs/frame_variation.json`).
* Paths re-routed into the frames (tee path from 3 yd past the ball, middle path across the fairway to the pad end): 0 samples above 1.2 cm on a 2 cm and a 1 cm grid (the old middle path had 2 samples at 1.8 cm at its left border).
* Tufts at scale 0.55-0.85 (were 0.8-1.25).
* Blender preview colour of the shelf = the Unity colour (preview only).
* STILL FAILING: `LOOK_FILES` of `postcard_look_verify.py` (the textures `Fairway_C` / `Green_C`, the lead's luminance-window floor): not a hole file, see `LIB_BUGS.md` 10 and the report.

## Runtime facts the integrator needs

* Materials in the FBX are the LK_* contract names (LK_FAIRWAY, LK_GREEN, LK_ROUGH, LK_SAND, LK_CLIFF, LK_CLIFF_DARK, LK_ROCK, LK_ROCK_WET, LK_MASONRY, LK_PATH, LK_PLANTS, LK_WATER, LK_WATER_SHALLOW, LK_SURF,
  LK_FALL) plus MAT_FLAG / POLE / CUP / BALL for the gameplay placeholders; the FBX holds no texture reference (GolfLook loads the PNGs by name). The TEE_BOX now carries LK_FAIRWAY (it was LK_GREEN): its UVs are rotated 90 degrees (stripes across the line of play).
* Only TERRAIN_NEEDLE, FAIRWAY, FAIRWAY_FIRSTCUT, GREEN, GREEN_APRON, TEE_BOX, BUNKER_01, BUNKER_01_LIP are collision-named (the same 8 meshes, vertex-identical to the baseline). Everything new is ROCK_ / PLANT_ / DRESS_ / WATER_.
* `WATER_FALL_00` (the waterfall sheet, LK_FALL, vertical, UV v runs down) and the 18 `WATER_SURF_nn` patches (vertex colour A = shore closeness) need `GolfArcade/GolfSurf`; `WATER_OCEAN` is one 2 km grid, `WATER_SHELF` the thin shelf.
* Unity colours of the water materials come from `GolfLook` by name (LK_WATER_SHALLOW Shallow (27,106,120)); the Blender colours are previews only.
* Mesh objects / datablocks and the triangle split: see `logs/h_numbers.json` (the biggest cost is the plants and vines; drop the 300 far tufts (`PL.scatter` seed 4 in hole08_look) first if the iPhone budget needs it).
