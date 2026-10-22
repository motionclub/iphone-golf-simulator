# Hole 8 Needle: install (NOT done: staged only)

Staged build (2026-10-04, `run_all.sh`; lib sha256 in `logs/lib_sha_final.txt`). Nothing in the repo was written: `blender/hole_08.blend`,
`Unity/Assets/Resources/Course/hole_08.fbx` and `hole_08.fbx.meta` are still byte-identical to the baseline (sha below).

## sha256 of the staged files (`stage/`, `logs/stage_sha256.txt`)

```
3895f8fafd04583b703225b2fdeaadb12bb56f648fd714f4c296b1cabdd8bff0  stage/hole_08.blend
9b9fe5ca977b5cfcd14614635ad75ec1b6cdd32d46064606c9db6018034fa33a  stage/hole_08.fbx          (2.58 MB, 186,746 triangles in the export set, exported with postcard_look_lib.export_look_fbx)
2214b4aa2c08b952fc5b649628e365c29afda93905b332ebde844051b5c02c09  stage/hole_08.fbx.meta     (staging copy of the hole 7 meta with a fresh guid: DO NOT COPY IT)
```
Geometry hash of the build (names + 0.1 mm world vertices of every mesh): `767f0333807d8a96`, identical in three builds (`logs/reproducible.txt`). The .blend / .fbx bytes themselves
carry timestamps, so a rebuild changes their sha but not the geometry hash.

Repo files today (the baseline, untouched): `blender/hole_08.blend` 38c25178..., `hole_08.fbx` d19a46b6..., `hole_08.fbx.meta` 3f7371fe... (holds the GUID and isReadable 1 / tangentImportMode 3: never overwritten).

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
landmarks, previews, reproducibility, guards): `work/postcard-look/v2/hole08/run_all.sh` (about 2 minutes), summary `GATES_hole08.md`.

## Runtime facts the integrator needs

* Materials in the FBX are the LK_* contract names (LK_FAIRWAY, LK_GREEN, LK_ROUGH, LK_SAND, LK_CLIFF, LK_CLIFF_DARK, LK_ROCK, LK_ROCK_WET, LK_MASONRY, LK_PATH, LK_PLANTS, LK_WATER, LK_WATER_SHALLOW, LK_SURF,
  LK_FALL) plus MAT_FLAG / POLE / CUP / BALL for the gameplay placeholders; the FBX holds no texture reference (GolfLook loads the PNGs by name).
* Only TERRAIN_NEEDLE, FAIRWAY, FAIRWAY_FIRSTCUT, GREEN, GREEN_APRON, TEE_BOX, BUNKER_01, BUNKER_01_LIP are collision-named (the same 8 meshes, vertex-identical to the baseline). Everything new is ROCK_ / PLANT_ / DRESS_ / WATER_.
* `WATER_FALL_00` (the waterfall sheet, LK_FALL, vertical, UV v runs down) and the 18 `WATER_SURF_nn` patches (vertex colour A = shore closeness) need `GolfArcade/GolfSurf`; `WATER_OCEAN` is one 2 km grid, `WATER_SHELF` the thin shelf.
* 872 mesh objects on 68 mesh datablocks (instanced props: 11 plant meshes, 13 rock meshes); the biggest cost is 627 plants + 120 vines (about 113k of the 187k triangles: 491 tufts 57k, 65 purple flowers 14k, 120 vines 17k, shrubs 17k); drop the 300 far tufts (`PL.scatter` seed 4 in hole08_look) first if the iPhone budget needs it.
