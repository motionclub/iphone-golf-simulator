# INSTALL - hole 9 "Split" look build, REPAIR ROUND 1 (irregular ruin masonry, tee box on the fairway material; staged 2026-10-04, NOTHING installed yet)

The staged build is in `work/postcard-look/v2/hole09/stage/`. It was produced by `blender/scripts/hole09_build.py -- --out ...stage` (deterministic, see GATES_hole09.txt H_REPRODUCIBLE)
and exported with `postcard_look_lib.export_look_fbx` (not `postcard_lib.export_fbx`). Install = copy exactly TWO files. Run it only after the Unity
calibration workflow has finished (a reimport of a changed hole_09.fbx would disturb it).

## sha256 of the staged files (verify before copying)

```
f6e12d86d6c5c59d8d7701aa34a21320b89f4374c5c1f86fa9bed6456dbaac28  work/postcard-look/v2/hole09/stage/hole_09.blend   (2580308 bytes)
66fc972ff62fb0fd972ca51a3efdda28aa8f50cc73ab714c10bf5993603d6614  work/postcard-look/v2/hole09/stage/hole_09.fbx   (4778428 bytes, 4.56 MB, 832 mesh objects, 241,197 triangles)
```
Same list in `work/postcard-look/v2/hole09/final/install_sha256.txt` (that file also holds the sha of the existing `hole_09.fbx.meta`).

## What repair round 1 changed (hole scripts only; libs, textures, Unity files untouched)

The shared fixers regenerated the libs (`postcard_look_lib.py`, `postcard_props_lib.py`) and the Look PNGs before this round (hashes in `lib_sha_r5_start.txt` / `look_png_sha_r5_start.txt`
against `lib_sha_round4.txt`): the hole was rebuilt on them first (`r5/base/`: 16 in-build gates PASS, 239,251 triangles), then the three reviewer findings that belong to the hole script were fixed.

1. **Ruin (high: "stacked Lego boxes, floating slabs, unsupported lintel")** - `blender/scripts/hole09_masonry.py` (NEW, called from `hole09_look.build_scenery`) replaces `PL.build_ruin` / `PL.build_masonry_arch`:
   * every stone is the convex hull of a tapered / sheared / twisted box with chamfered corners and chips (6 non-parallel planar faces + chips, 0.7-1.5 m long, 0.36-0.58 m courses, 2.5 cm gaps, +-1.4 deg yaw, +-0.9 deg tilt per stone, random depth and +-4 cm out of line);
   * support by construction: a stone exists only if its centre is over the course below AND >= 60 % of its bed is; the first course is buried 0.25-0.45 m; the doorway lintel is ONE 3.5 m stone bearing 0.55 m on each jamb (jamb stones are forced, the profile steps down over 2.4 m beside the door so no lone towers);
     running bond (joints nudged >= 0.2 m off the joints below: 66 of 772 joints within 12 cm), a seeded broken profile (ragged top block cut lower and sloped);
   * the arch is a ring of 11 wedge voussoirs on two rubble piers (left pier 6.2 m, right 3.9 m), the crown wedges 7 and 8 are missing and lie on the ground, a heap of small stones (7 half-buried + 4 resting on them, minus any the clip refused) fills the gap; it faces 172 deg (the ruin landmark camera looks straight through it; the old 110 deg showed it edge-on) and stands 1.5 yd further east so the west pier clears the dry safe route by 6 yd;
   * texture: LK_MASONRY only, but every face has its OWN UV window = a random brick-row INTERIOR of Masonry_C.png (mortar lines skipped), random column offset / flip, 0.6-1.6 x density (UV_DENSITY gate unchanged and PASS): no painted mortar line runs across a stone and the grid cannot read across stones;
   * 219 irregular stones + 13 DRESS_BLOCK fallen blocks (was 99 pieces + 30 blocks), +1.9k triangles net over the rebuilt-on-new-libs baseline (239,251 -> 241,197 total; limit 250,000);
   * independent gates (read the finished mesh only, `tools/ruin_check.py`, run on the blend AND the FBX re-import): RUIN_SUPPORTED, RUIN_LINTEL_BEARING, RUIN_BASE_BURIED, RUIN_NOT_BOXES, RUIN_UV_WINDOWS.
2. **Straight seam across the tee frame (medium)** - `TEE_BOX` is now `LK_FAIRWAY` (was `LK_GREEN`: planar UVs, no mow stripes, next to the striped ribbon). postcard_look_verify allows {LK_GREEN, LK_FAIRWAY} on TEE_BOX; centerline UVs make the stripes run on under the tee ball;
   the rim shading is sharp at 30 deg (shading only; vertices, faces and heights are untouched, H_PLAY_UNCHANGED PASS). `hole09_qa.py` H_RIBBON_FAIRWAY_SAND_GREEN now expects `TEE_BOX: LK_FAIRWAY` (and `FAIRWAY_FIRSTCUT: LK_ROUGH`, item 3; the only QA edits besides the message text: same strictness, a named material per surface).
   Measured on the Blender preview only (NOT Game view): the row-mean step across the tee far edge fell from 4.94 to 3.29 levels; the remainder is the 10 cm tee plateau itself (lowering TEE_BOX 10 cm in a scratch render removes it; scoring heights are frozen).
3. **Island does not read as Split at tee / approach (medium: "flat wide strip", no darker fringe)** - `FAIRWAY_FIRSTCUT` is now `LK_ROUGH` (was LK_FAIRWAY, i.e. the same stripes as the fairway). Why this is the honest colour: the first-cut mesh covers the fairway lie too, but that part is UNDER the FAIRWAY mesh (6 cm higher);
   its VISIBLE part is the 3 yd collar of ROUGH LIE round the ribbon (measured: 1947 of 1947 visible sample points are lie Rough, `tools/collar_lie_check.py`, gate H_COLLAR_IS_ROUGH_LIE): the mown ribbon is now bounded by darker rough exactly where the lie changes (like split.jpg), and the fairway no longer looks 6 m wider than it plays.
   The material is swapped AFTER `assign_uvs`: the collar keeps its CENTERLINE UVs (its n-gons are up to 108 m2: planar+warp UVs of LK_ROUGH streak across them, seen in a first try) at the 10 m fairway tile (1.2 x the rough contract density; UV_DENSITY allows 1/3..3 x). Vertices / faces / heights are untouched.
   `hole09_qa.py` H_RIBBON_FAIRWAY_SAND_GREEN now expects `FAIRWAY_FIRSTCUT: LK_ROUGH` (verify allows {LK_FAIRWAY, LK_ROUGH}). Also: the tee box stripes now run on under the ball (item 2) and the regenerated Look PNGs (shared fixers) carry the mid-frequency grain.
   Still open (not in a hole script's reach): the 900x1600 address cameras look 36 deg across, so the fairway fills the lower 60 % of both frames; the lip of the first ribbon section is a play surface (nothing may stand on it: PROPS_OFF_PLAY). Re-shoot the Game-view stills and re-judge.
4. Landmark tools (`tools/make_landmarks.py`, `tools/landmarks_check.py`, work-folder tools): the ruin visibility gate now samples only masonry vertices above the ground (+6 cm; the buried first course cannot be seen by definition) and the landmark core is the doorway wall (masonry within 6.5 m of the design doorway) + the arch.
   The 97 % threshold is unchanged: 800 of 800 samples reach the new camera (-64.37, 26, 146.75).
   The camera moved (the arch now faces it): `landmarks.json` is regenerated, shots hole09_tee / hole09_approach are byte-identical in meaning.

* `LOOK_STILLS_TEXTURED` is SKIPPED (not a PASS in substance): no Game-view still of hole 9 exists from this build; re-run `postcard_look_verify.py 9 --require-stills` after the Unity stills are shot.
* the round-4 stage is kept in `r5/before_round4/` (blend, FBX, INSTALL.md, GATES_hole09.txt, landmarks.json, final/ logs) for comparison; it is also what the integrator already installed in the repo (see section 0); older rounds in `round4/before/`.

## 0. Preconditions (stop if one is false)

```
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
S=work/postcard-look/v2/hole09/stage
# the repo hole_09 files are one of two known states (this job never writes them):
shasum -a 256 blender/hole_09.blend Unity/Assets/Resources/Course/hole_09.fbx
#   (a) the ROUND-4 STAGE the integrator installed at 20:43 (backup of the flat baseline in work/postcard-look/v2/install_backup/):
#       70e5b4e8f8b1027775dee190782bdc66ac6cb0dbf82183400014951e933b81fa  blender/hole_09.blend        (= work/postcard-look/v2/hole09/r5/before_round4/hole_09.blend)
#       455996b9c419dd358c024de8d7b3ce24d0b7ae366984cf70948d67a8a62b6fc6  Unity/Assets/Resources/Course/hole_09.fbx   (= work/postcard-look/v2/hole09/r5/before_round4/hole_09.fbx)
#   (b) or the flat baseline:  8846a99f7b5314a7a4bb3f170d57485d2f489b88fd9e64dd509450d8eaee42ad  blender/hole_09.blend  /  88005a32d046181dae84b4b778ca14585dabdf9099f5ba2163d602c737f2b01e  hole_09.fbx
# the staged files are the ones that were gated:
echo "f6e12d86d6c5c59d8d7701aa34a21320b89f4374c5c1f86fa9bed6456dbaac28  $S/hole_09.blend" | shasum -a 256 -c -
echo "66fc972ff62fb0fd972ca51a3efdda28aa8f50cc73ab714c10bf5993603d6614  $S/hole_09.fbx" | shasum -a 256 -c -
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
cp work/postcard-look/baseline/blender/hole_09.blend blender/hole_09.blend            # sha256 8846a99f7b5314a7a4bb3f170d57485d2f489b88fd9e64dd509450d8eaee42ad   (the flat afternoon baseline)
cp work/postcard-look/baseline/fbx/hole_09.fbx Unity/Assets/Resources/Course/hole_09.fbx   # sha256 88005a32d046181dae84b4b778ca14585dabdf9099f5ba2163d602c737f2b01e
# or back to the round-4 stage (the state the repo is in now): cp work/postcard-look/v2/hole09/r5/before_round4/hole_09.blend blender/hole_09.blend; cp work/postcard-look/v2/hole09/r5/before_round4/hole_09.fbx Unity/Assets/Resources/Course/hole_09.fbx
```

## Files this job owns / changed (nothing else was touched)

```
fdcaea8dfc8595daa76e2f01e8187846dc96699ecd848d2dcd51f07273298f8b  blender/scripts/hole09_build.py
6291a89c93155c656b210f9a4e2fc5a71600db4de723a948173e243353afd9c3  blender/scripts/hole09_look.py
4e5a9f109ac2829a8a8a7be09853ad116832e4a1b192fd1f9d24b97ebb0ab6f0  blender/scripts/hole09_masonry.py
8f0b9b7370e5f479b7a7be7cf2519bf1e913d7f865fd09f7be9b0df6c434b25d  blender/scripts/hole09_qa.py
8264099d82b9f9246a8837c4856d50d3aef151449b5c2cb57a65e12106ed82b0  blender/scripts/hole09_design.py
e6a7f70e132a13592c2696c2064c2ae041e8d87bf0d64a7bdbe0b396e2413501  blender/scripts/postcard_look_lib.py
23072cc1fded10d179ffbbc385628f70a30dd9aa8f27f87435f4e1e474bb43eb  blender/scripts/postcard_props_lib.py
ff3062b6798fafcf021183e2da39461b501ff7dbce45f75dab3111884b94d3f4  blender/scripts/postcard_lib.py
3fe3083eec7d7765beed6bc8a19b27763bb24dc6dc82d8d80f2a780d74f464a4  blender/scripts/postcard_look_verify.py
68920a89d2b4f495ae7cccf7cde4b26a9a3116bf17476b3f440ea5b76807ed11  blender/scripts/golf_look_textures.py
```
`hole09_design.py` is byte-identical to its start-of-job copy (`work/postcard-look/v2/hole09/hole09_design.py.at_start`; `postcard_emit_cs.py --check` = no drift), `postcard_lib.py`, both libraries, the textures and every Unity file were not edited by this job
(library behaviours worked around in the hole scripts: `work/postcard-look/v2/hole09/LIB_BUGS.md`; `hole09_masonry.py` only CALLS the props lib's private `_hull`). Look PNG sha256 list at the final build: `work/postcard-look/v2/hole09/final/look_png_sha256_at_final_build.txt`.
