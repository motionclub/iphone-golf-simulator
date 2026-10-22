# INSTALL - hole 9 "Split" look build, ROUND 4 (rebuild-only on the regenerated textures + changed gate tool; staged 2026-10-04 20:32, NOTHING installed yet)

The staged build is in `work/postcard-look/v2/hole09/stage/`. It was produced by `blender/scripts/hole09_build.py -- --out ...stage` (deterministic, see GATES_hole09.txt H_REPRODUCIBLE)
and exported with `postcard_look_lib.export_look_fbx` (not `postcard_lib.export_fbx`). Install = copy exactly TWO files. Run it only after the Unity
calibration workflow has finished (a reimport of a changed hole_09.fbx would disturb it).

## sha256 of the staged files (verify before copying)

```
70e5b4e8f8b1027775dee190782bdc66ac6cb0dbf82183400014951e933b81fa  work/postcard-look/v2/hole09/stage/hole_09.blend   (2425228 bytes)
455996b9c419dd358c024de8d7b3ce24d0b7ae366984cf70948d67a8a62b6fc6  work/postcard-look/v2/hole09/stage/hole_09.fbx   (4623596 bytes, 4.41 MB, 849 mesh objects, 238,081 triangles)
```
Same list in `work/postcard-look/v2/hole09/final/install_sha256.txt` (that file also holds the sha of the existing `hole_09.fbx.meta`).

## What round 4 changed (rebuild-only; the mesh did not change)

* Nothing in the hole scripts changed since round 3 (`hole09_build.py`, `hole09_look.py`, `hole09_qa.py`, `hole09_design.py` have the same sha256 as in round 3; the three libs are also byte-identical to the round-3 ones). The shared fixers of this round regenerated the Look PNGs
  (Fairway_C/N, Green_C/N, Rough_C/N, Scrub_C/N, Basalt_*, Lava_*: grass hue moved to the stills, mid-frequency grain added) and changed the gate tool (`postcard_look_verify.py`: new GRASS_ALBEDO_HUE, ALBEDO_DISTINCT, SHADERS_STATIC, STILL_FLOOR_SELFCHECK, LOOK_STILLS_TEXTURED gates).
  The hole was re-staged on those final files (`tools/run_final_pipeline.sh`, build 59 s): same geometry (blend geometry hash 33e1e642d35df1ce and FBX re-import hash db1b97ed6058863c are the round-3 values; 238,081 triangles, 849 mesh objects), the blend / FBX bytes differ from round 3 (blend +24 bytes, FBX same size; timestamps and zlib streams: the geometry hashes are identical).
* Result: the whole verifier is now ALL PASS on the staged blend and FBX (round 3: LOOK_FILES@blend / @fbx FAILED on the old Fairway_C / Green_C; the regenerated textures pass it: Fairway_C / Green_C / Rough_C window structure 100 %), GRASS_ALBEDO_HUE PASS (Fairway_C h 73.6, Green_C h 72.4, Rough_C h 68.1; est. lit hue 67 / 65 / 61 against the stills' 64-73), `HOLE09_QA` 27 gates 0 FAIL, landmarks check 5 gates 0 FAIL, guards 7 of 7 PASS.
* `LOOK_STILLS_TEXTURED` is SKIPPED (not a PASS in substance): no Game-view still of hole 9 exists yet in `ArtDir/screenshots/golf_postcards/look/`; it must be re-run with `--require-stills` after the Unity stills are shot.
* landmarks.json is byte-identical to round 3 (same cameras; the geometry did not move). Round 3 notes (knolls, shore cliff, bunker overlay at 9 mm, `round3/proposal_textures/` now unnecessary) are in `round4/before/INSTALL.md` (the round-3 INSTALL.md).
* the round-3 stage is kept in `round4/before/` (blend, FBX, INSTALL.md, GATES_hole09.txt, final/ logs) for comparison.

## 0. Preconditions (stop if one is false)

```
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
S=work/postcard-look/v2/hole09/stage
# the repo hole_09 files are still the flat baseline (nothing else installed over them):
shasum -a 256 blender/hole_09.blend Unity/Assets/Resources/Course/hole_09.fbx
#   expect 8846a99f7b5314a7a4bb3f170d57485d2f489b88fd9e64dd509450d8eaee42ad  blender/hole_09.blend
#   expect 88005a32d046181dae84b4b778ca14585dabdf9099f5ba2163d602c737f2b01e  Unity/Assets/Resources/Course/hole_09.fbx
# the staged files are the ones that were gated:
echo "70e5b4e8f8b1027775dee190782bdc66ac6cb0dbf82183400014951e933b81fa  $S/hole_09.blend" | shasum -a 256 -c -
echo "455996b9c419dd358c024de8d7b3ce24d0b7ae366984cf70948d67a8a62b6fc6  $S/hole_09.fbx" | shasum -a 256 -c -
# the scoring + hole 7 guards (must print 7 PASS):
bash work/postcard-look/guards.sh
```

## 1. Install (copy hole_09.blend and hole_09.fbx ONLY)

```
cp $S/hole_09.blend blender/hole_09.blend
cp $S/hole_09.fbx   Unity/Assets/Resources/Course/hole_09.fbx
```
**NEVER overwrite `Unity/Assets/Resources/Course/hole_09.fbx.meta`.** It holds the GUID (guid: a41a7055f5d449c993233b2b3887ba18) and the importer settings
(`isReadable: 1`, `tangentImportMode: 3`, `materialName: 0`, `normalImportMode: 0`); the staged folder also contains a `hole_09.fbx.meta` with a FRESH random GUID
(the exporter writes one when the file is missing): do not copy it. Also not copied: `stage/hole_09.blend1` (Blender's backup), `stage/hole_09_overview.png` (a preview;
copy it to `blender/previews/hole_09_overview.png` only if the overview preview should be refreshed), `stage_repro/` (the reproducibility twin).
The existing `.meta` sha256 must stay `65b4dd392ac3cb1929d9f456d8973b2a1900d80dac0c59d192a7c60d7edeac6c`.

## 2. Verify after the copy (Blender headless, no Unity needed)

```
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- 9          # repo blend + FBX; expect RESULT: ALL PASS (90 gate lines; LOOK_STILLS_TEXTURED is SKIPPED until Game-view stills exist, then run with --require-stills)
$B -b blender/hole_09.blend --python blender/scripts/postcard_verify.py -- hole09_design   # FAIL only MATERIALS@blend/@fbx + FBX_BUDGET@fbx, by design (old MAT_* allow-list, old 4 MB / 150k budget)
python3 blender/scripts/postcard_emit_cs.py --check Unity/Assets/Scripts/Course/Hole.cs      # HOLE_CS_MATCHES_DESIGN PASS
bash work/postcard-look/guards.sh                                                          # 7 PASS
shasum -a 256 blender/hole_09.blend Unity/Assets/Resources/Course/hole_09.fbx              # = the two staged sha256 above
shasum -a 256 Unity/Assets/Resources/Course/hole_09.fbx.meta                               # unchanged
```
Then (Unity owner, through work/postcard-look/heavy.sh): `PostcardImportCheck` (LK_ materials accepted; ground / lie / marker gates unchanged), `GolfLookSmoke`, and the stills
with `GOLF_STILLS_CFG=work/postcard-look/v2/hole09/landmarks.json` -> `ArtDir/screenshots/golf_postcards/look/` (shots hole09_tee, hole09_approach, hole09_ruin; the `extra_previews` key is ignored by the tool).
Expected in the Game view: every hole 9 ground / rock / cliff / plant material is an `LK_` name (GolfLook builds them; `LK_SURF` = GolfSurf, `LK_WATER*` = TennisWater, `LK_PLANTS` one
shared instanced material; `DRESS_SAND_nn` = LK_SAND overlay lobes on the bunker lips, `DRESS_KNOLL_nn` = LK_SCRUB / LK_ROCK hummocks, both non-colliding); only TERRAIN, FAIRWAY, GREEN, TEE_BOX, BUNKER meshes get colliders (every new object is ROCK_ / PLANT_ / DRESS_ / WATER_); there are no LAVA_LIGHT empties on this hole.

## 3. Rebuild without staging (same geometry, writes the repo paths = the install)

```
$B -b --factory-startup --python blender/scripts/hole09_build.py            # no --out: blender/hole_09.blend, blender/previews/hole_09_overview.png, Unity/.../hole_09.fbx
```
(`hole_09.fbx.meta` is only created when it does not exist, so the existing one is kept.) The blend and the FBX re-import are geometry-identical to the staged ones (gate H_REPRODUCIBLE);
the FBX bytes differ run to run because of the header timestamp and zlib streams.

## 4. Rollback

```
cp work/postcard-look/baseline/blender/hole_09.blend blender/hole_09.blend            # sha256 8846a99f7b5314a7a4bb3f170d57485d2f489b88fd9e64dd509450d8eaee42ad
cp work/postcard-look/baseline/fbx/hole_09.fbx Unity/Assets/Resources/Course/hole_09.fbx   # sha256 88005a32d046181dae84b4b778ca14585dabdf9099f5ba2163d602c737f2b01e
```

## Files this job owns / changed (nothing else was touched)

```
d281cea0870ba92aee72dfed6d0d3f9a40e9ed50e0e9f26b543fe632fe3a09eb  blender/scripts/hole09_build.py
a094932bdc0d5ca7a9e3f38f8a8b98a5b9f5c0be70aa902181096852d4af8df7  blender/scripts/hole09_look.py
4833ad5d60ab3d5f8c9f017ba9cb200a0c456db26abfe68411747313b7afaf39  blender/scripts/hole09_qa.py
8264099d82b9f9246a8837c4856d50d3aef151449b5c2cb57a65e12106ed82b0  blender/scripts/hole09_design.py
0f1b29378ae13c383200f377de85e1f405c2f464d666ab42066b006e6ff76e54  blender/scripts/postcard_look_lib.py
e71c1ac2d8348940a53253ddb4725160b5cd142e9f0c95bb0bbdf3830b8070c0  blender/scripts/postcard_props_lib.py
ff3062b6798fafcf021183e2da39461b501ff7dbce45f75dab3111884b94d3f4  blender/scripts/postcard_lib.py
884448e1fc042aa94d3a0d4f55f726e2c77ebff131e6d48e4d792c80564cda8f  blender/scripts/postcard_look_verify.py
6a9501cea499c51be4b3647ccac3048f34c5fdd175d6454e866ff416f3e148f1  blender/scripts/golf_look_textures.py
```
`hole09_design.py` is byte-identical to its start-of-job copy (`work/postcard-look/v2/hole09/hole09_design.py.at_start`), `postcard_lib.py` and both libraries were not edited (this job found library
behaviours that it works around in its own scripts: `work/postcard-look/v2/hole09/LIB_BUGS.md`). Look PNG sha256 list at the final build: `work/postcard-look/v2/hole09/final/look_png_sha256_at_final_build.txt`.
