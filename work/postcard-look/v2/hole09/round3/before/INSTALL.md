# INSTALL - hole 9 "Split" look build, ROUND 2 (after the skeptic review; staged 2026-10-04, NOTHING installed yet)

The staged build is in `work/postcard-look/v2/hole09/stage/`. It was produced by `blender/scripts/hole09_build.py -- --out ...stage` (deterministic, see GATES_hole09.txt H_REPRODUCIBLE)
and exported with `postcard_look_lib.export_look_fbx` (not `postcard_lib.export_fbx`). Install = copy exactly TWO files. Run it only after the Unity
calibration workflow has finished (a reimport of a changed hole_09.fbx would disturb it).

## sha256 of the staged files (verify before copying)

```
64a552e36618d81df2fd4729a5fb37322ea5053fefb9b3eff78627cd69c2784e  work/postcard-look/v2/hole09/stage/hole_09.blend   (2392558 bytes)
c888f3681ecb66d1df16556c90810bda00ecf32436ddb116ed34d2985da9604f  work/postcard-look/v2/hole09/stage/hole_09.fbx   (4580412 bytes, 4.37 MB, 851 mesh objects, 236,375 triangles)
```
Same list in `work/postcard-look/v2/hole09/final/install_sha256.txt` (that file also holds the sha of the existing `hole_09.fbx.meta`).

## What round 2 changed (reviewer findings; round 1 is kept in `work/postcard-look/v2/hole09/round2/`: stage_round1/, final_round1/, *.before_round2 scripts)

* bunkers: `DRESS_SAND_01..03` scalloped sand lobes on the lip rings (<= 0.9 cm over the collider, PATH_UNDER_BALL pass), scoring BUNKER_nn untouched
* ridge: 30 `DRESS_KNOLL_nn` hummocks (rock caps, scrub flanks), crag groups, shrub thickets; shrub + rock chain over the scrub / rough colour step (bare only on the route axis)
* masonry: the 30 fallen `DRESS_BLOCK` instances use a chipped mesh with 70 welded vertices (was 24)
* cliff: skin displacement 0.3-1.7 m / jag 2.6 m (plan tortuosity 1.165 -> 1.213); vegetation re-balanced (tufts down, thickets up) to stay under 250k triangles
* NOT changed here (not mine): `LOOK_FILES` (Fairway_C / Green_C texture flatness) still FAILS at both stages; the textures and the lead's 0.03 / 90 % floor belong to the texture owner / lead

## 0. Preconditions (stop if one is false)

```
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
S=work/postcard-look/v2/hole09/stage
# the repo hole_09 files are still the flat baseline (nothing else installed over them):
shasum -a 256 blender/hole_09.blend Unity/Assets/Resources/Course/hole_09.fbx
#   expect 8846a99f7b5314a7a4bb3f170d57485d2f489b88fd9e64dd509450d8eaee42ad  blender/hole_09.blend
#   expect 88005a32d046181dae84b4b778ca14585dabdf9099f5ba2163d602c737f2b01e  Unity/Assets/Resources/Course/hole_09.fbx
# the staged files are the ones that were gated:
echo "64a552e36618d81df2fd4729a5fb37322ea5053fefb9b3eff78627cd69c2784e  $S/hole_09.blend" | shasum -a 256 -c -
echo "c888f3681ecb66d1df16556c90810bda00ecf32436ddb116ed34d2985da9604f  $S/hole_09.fbx" | shasum -a 256 -c -
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
$B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- 9          # repo blend + FBX; expect 86 of 88 lines PASS, FAIL only LOOK_FILES@blend/@fbx (texture files, see GATES_hole09.txt)
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
545a373490cdfecef8c2b33ce60d43266d095e12b18e2b834c0211b7953d6b31  blender/scripts/hole09_build.py
c934ac3a078be74e2320a7067a919a0402b1918bc2ce259209a7cd74777bf057  blender/scripts/hole09_look.py
882da513294fc3773e931685d759b0c893795730c7ed510eda86d55bd3556b19  blender/scripts/hole09_qa.py
8264099d82b9f9246a8837c4856d50d3aef151449b5c2cb57a65e12106ed82b0  blender/scripts/hole09_design.py
0f1b29378ae13c383200f377de85e1f405c2f464d666ab42066b006e6ff76e54  blender/scripts/postcard_look_lib.py
e71c1ac2d8348940a53253ddb4725160b5cd142e9f0c95bb0bbdf3830b8070c0  blender/scripts/postcard_props_lib.py
ff3062b6798fafcf021183e2da39461b501ff7dbce45f75dab3111884b94d3f4  blender/scripts/postcard_lib.py
edc96d4d755bb248439603be3bf97a783dbfd930cd654b2189b10fa7eac420fd  blender/scripts/postcard_look_verify.py
2bd12ba1f60e3150db4c4b803e0717e8940a28e6093baf3fbcd745575c3476ee  blender/scripts/golf_look_textures.py
```
`hole09_design.py` is byte-identical to its start-of-job copy (`work/postcard-look/v2/hole09/hole09_design.py.at_start`), `postcard_lib.py` and both libraries were not edited (this job found library
behaviours that it works around in its own scripts: `work/postcard-look/v2/hole09/LIB_BUGS.md`). Look PNG sha256 list at the final build: `work/postcard-look/v2/hole09/final/look_png_sha256_at_final_build.txt`.
