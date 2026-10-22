# INSTALL - hole 9 "Split" look build, REPAIR ROUND 3 (planar-faced ruin stones, haunch-seated arch, tee-edge UV parallax; staged 2026-10-05, NOTHING installed yet)

The staged build is in `work/postcard-look/v2/hole09/stage/`. It was produced by `blender/scripts/hole09_build.py -- --out ...stage` (deterministic, see GATES_hole09.txt H_REPRODUCIBLE)
and exported with `postcard_look_lib.export_look_fbx` (not `postcard_lib.export_fbx`). Install = copy exactly TWO files. Run it only after the Unity
calibration workflow has finished (a reimport of a changed hole_09.fbx would disturb it).

## sha256 of the staged files (verify before copying)

```
dbc43946e77286f9cf201d90e6bfeef9adf8746e1912fc3352b38b367d7cd42c  work/postcard-look/v2/hole09/stage/hole_09.blend   (2800202 bytes)
ce92141ce61c9521fcd06f4341875d896219f4e156c75f1bc84b1413adeb2b61  work/postcard-look/v2/hole09/stage/hole_09.fbx   (5036748 bytes, 4.80 MB, 817 mesh objects, 246,239 triangles)
```
Same list in `work/postcard-look/v2/hole09/final/install_sha256.txt` (that file also holds the sha of the existing `hole_09.fbx.meta`).

## What repair round 3 changed (hole scripts only; the libs, the verifier, the texture generator, the design file and every Unity file are untouched: the first 8 lines of `lib_sha_r7_start.txt` == `lib_sha_r7_final.txt`; the 31 Look PNGs byte-identical: `look_png_sha_r7_start.txt` == `look_png_sha_r7_final.txt`)

Reviewer findings handled here (hole script / geometry / placement / scenery): (1) medium, `hole09_3_ruin.png`: "The ruin still reads as stacked boxes, not broken masonry. Straight-cut block courses, triangle-split shading on the faces, and a floating arch crown";
(2) low, `hole09_1_tee.png` row 556 / 557: "A faint straight ruler line still crosses the whole tee frame where the grass shade steps" (the reviewer's guess: a FAIRWAY / GREEN albedo boundary); (3) from the proof pass (PROOF.md, hole script): `LK_TEXTURED@blend`
failed on the installed `blender/hole_09.blend` (relative image paths). The third finding in the list (protected files) is a note for other chats, not mine.
Before this round the hole was rebuilt on the libs / textures of the shared fixers (the props library's new shrub meshes cost +3.9k triangles: 244,825 -> 248,693; `r7/base/`, 16 in-build gates PASS, every gate as before).

**1. The 'triangle-split shading' - measured cause and fix.** NOT the flat shading (round 2 fixed that) and NOT a UV shear. The round-2 stones were convex HULLS of jittered corner points (`postcard_props_lib._hull`): the hull face of a twisted / tapered / sheared quad is not planar, so the hull
split it into two triangles with normals 1-7 deg apart, and every triangle took its OWN random brick window. Measured on the round-2 stage (`r7/face_split_stats.py`): of 4,477 masonry faces 2,467 were triangles, 1,411 pairs of adjacent faces were near-coplanar (< 20 deg, median 1.6 deg) and 1,092 of those pairs (77 %)
had a different UV along the shared edge: two bricks meeting on a diagonal. New `blender/scripts/hole09_stone.py`: a stone is the intersection of half-spaces {x : n.x <= d} (the six best-fit planes of a tapered / sheared / twisted / tilted hexahedron + 4-17 cm corner chips + 1.2-3.5 cm arris bevels + fracture planes
on the broken tops + quarry-split folds of 15-23 deg), so every face is ONE exactly planar n-gon with ONE UV mapping (9-17 faces, ~40 triangles per stone). Gates: RUIN_PLANAR_FACES (worst vertex 0.018 mm off its plane, 0 over 1 mm), RUIN_NO_UV_SPLIT (24 near-coplanar pairs, 0 with a UV mismatch; round 2: 1,092 of 1,411).

**2. Flat-colour cap slabs, pale uniform stones.** The tops were one magnified brick window per face (a moss brick drawn at random = a flat green slab) and the stones rendered about twice as bright as split.jpg's ruin (mean 190 against 95). Now: every stone TOP and about one stone in four is `LK_ROCK` (Rock_C.png, darker, blotchy moss like
split.jpg's lichen) with ONE continuous world-axis box projection per stone (a darker-leaning window of 7 random candidates), the other faces keep the brick-interior windows of Masonry_C.png but the bricks are drawn with dark / moss-free weights (z-score weights over the 8-row table). LK_ROCK is kept below 36 % of the area of every DRESS_RUIN / DRESS_ARCH mesh
(the verifier calls a mesh with >= 50 % LK_ROCK a ROCK and holds it to the rock-shape gates; PROP_MATERIALS needs >= 50 % LK_MASONRY): RUIN_MASONRY_SHARE, lowest masonry share 65 %, highest rock share 35 %. `hole09_qa.py` H_RUIN_MASONRY used to require materials == {LK_MASONRY}: it now requires {LK_MASONRY, LK_ROCK} with those two shares (a disclosed change of the gate's premise, the share rule is stricter than before).
The UV-window gates (RUIN_UV_WINDOWS, RUIN_UV_BRICK_INTERIOR) judge the LK_MASONRY polygons only (the LK_ROCK polygons have no brick to be inside of); their thresholds are unchanged and they still PASS (100 % / 99.5 %).

**3. The arch crown.** The round-2 arch cantilevered wedge 7 over the opening from wedges embedded in a pier 0.5 m lower (the 'floating crown'), and the left pier ended in a thin 6.2 m spike over the ring. Now: the ring keeps its 11 wedges with ONE missing (the same <= 1 m gap, the fallen wedge + rubble heap under it), the wedges bear on each other by face contact
(corners on a joint chipped <= 3.5 cm, the two sides that face the gap up to 12 cm), and an OUTER COURSE of irregular haunch stones (4-6 on the left haunch, 3-5 on the right one, 0.45-0.8 m thick, joints not in line with the ring's) fills the angle between the ring and the piers on both sides, so no ring stone hangs over a hole; left pier 5.8 m (was 6.2), right pier 4.9 m (was 4.4); the piers get TWIN stones (two half-depth stones side by side
across the thickness in 38 % of the courses: seen end-on a pier is no longer a stack of full-depth slabs). RUIN_ARCH_SEATED PASS (longest uncovered arc 14 deg = 0.49 m, springers covered); every ring stone is supported (RUIN_SUPPORTED: 0 floating, 2 wedges rest by face contact on a supported neighbour).
Also: wall stone depth 0.82-1.0 of the wall (was 0.86); the skyline is retuned for a more rubble-like wall (bed levels 0.20-0.42 m apart, was 0.27-0.44; a stone spans 1 / 2 / 3 levels in 60 / 32 / 8 % of the cases, was 72 / 24 / 4; 31 % short stones, was 24; 11 % long, was 16: 356 masonry stones instead of 341); ragged tops (the fracture planes make steeply cut tops: RUIN_TOPS_RAGGED 90 % tilted, median step 46.0 cm), the fallen DRESS_BLOCK variants (98 vertices, 192 triangles) have ONE continuous projection per axis region inside one brick (the round-2 per-triangle windows were the same split artifact at small scale).

**4. The tee ruler line - measured cause and fix.** NOT an albedo mismatch: the TEE_BOX and the FAIRWAY carry the same centerline UV function (0.0 m difference at every tee vertex, `r7/tee_uv_check.py`; the sampled textures at the same world point are equal). The cause is geometry: the tee box is a flat plate 10 cm over the fairway with NO riser (scoring: heights are frozen),
so the address camera (11.9 deg down at the far edge) cannot see the 0.48 m of fairway just behind the edge: the picture jumps from the plate's texture at the edge to the fairway's texture 0.48 m further on, a texture phase jump across the whole frame width (the stretched crop of rows 500-620 of the still shows the mottle blobs cut off by the line). `tools/tee_parallax_check.py` re-casts the camera rays on the finished
blend: texture jump between the last plate hit and the first fairway hit max 0.505 m, mean 0.487 m on 15 of 15 rays (round-2 stage and `r7/d3`). Fix (`hole09_build.tee_parallax_uvs`, UV data only: vertices, faces, heights and outline of the TEE_BOX are untouched): the plate's UVs are the fairway's centerline UV of the point p + k (p - c), i.e. the plate texture scaled by k = 0.1 m / 2.25 m = 4.4 % about the address camera c,
which is exactly the ground the plate hides from c. Result: gate TEE_EDGE_UV_CONTINUOUS max 0.002 m, mean 0.002 m (limit 0.10 m); Blender preview of the hole09_tee camera: row step across the edge 1.67 levels, ratio to the other rows 0.86 (round-2 geometry: 3.29 levels, ratio 1.79). Not a Game-view number: re-measure rows 556 / 557 of the re-shot `hole09_1_tee.png`.
Limits, disclosed: the compensation is exact for the default tee address camera (the one of the proof still); from other viewpoints the plate texture is offset by up to 0.5 m against the fairway at the plate's edges (the 10 cm lip is visible there anyway).

**5. `LK_TEXTURED@blend` on the installed blend.** `hole09_build.py` now saves with `relative_remap=False` (like hole08_build / hole10_build): the LK_* image paths stay absolute, so the blend finds its textures after the copy to `blender/hole_09.blend` (checked on a copy in another folder: `postcard_look_verify.py 9 --blend <copy>` LK_TEXTURED@blend PASS).

**6. Triangle budget.** Masonry grew 8.2k -> 13.2k triangles (356 stones of ~37 triangles, was 341 of ~24); to stay under the 250,000 limit `N_SHRUB_RIDGE` 132 -> 116 and `N_TUFT_OUT` 64 -> 56 (the thickets are the same clusters, 14 fewer shrubs / 8 fewer tufts). Triangles 246,239 (limit 250,000), FBX 4.80 MB (limit 20).

Numbers: 356 masonry stones in 16 DRESS_RUIN_ / DRESS_ARCH_ meshes (209 + 41 wall stones incl. the 38 % twin stones of the arch piers, 24 wall-foot rubble stones, 3 refused by the shore / route clip), 13 DRESS_BLOCK instances. Look PNG sha256 list at the final build: `work/postcard-look/v2/hole09/final/look_png_sha256_at_final_build.txt`.
Gates (`tools/ruin_check.py`, run on the blend AND the FBX re-import): the ten of rounds 1 / 2 + RUIN_PLANAR_FACES, RUIN_NO_UV_SPLIT, RUIN_MASONRY_SHARE (3 new) = 13 of 13 PASS on both. Changes to the measuring code, none relaxes a threshold: the two UV-window gates skip LK_ROCK polygons (reported as the share gate's rock share). Measured on THIS stage with the round-1 support definition (3 cm cross, no inside test; `RUIN_OLD_SUPPORT=1`,
`final/ruin_check_old_support.log`): 1 of 356 stones is called floating (a bed whose centre sample lies over a joint between two stones below, its other samples rest); the 8 cm cross of round 2 counts the stones it rests on at both sides of the joint.
`landmarks.json` is regenerated (`tools/make_landmarks.py`): shots hole09_tee and hole09_approach are identical; the ruin camera is (-64.34, 26, 146.18) / look (-64.34, 10.21, 116.18) (was (-64.33, 26, 146.17) / (-64.33, 10.01, 116.17): the ruin bounds moved by 1 cm): 100% of the masonry ray samples reach it unblocked.
The Game-view stills must be re-shot with this file (the Unity owner, through `work/postcard-look/heavy.sh`): the Blender previews in `previews/`, the before / after sheet `r7/ruin_before_after.jpg` and the dev views in `r7/d*_views/` are NOT Game-view proof. Previous stages are kept: round 2 in `r7/before_r7/` (blend, FBX, INSTALL.md, GATES_hole09.txt, landmarks.json, final/ logs, the scripts at start `r7/*.at_start`),
round 1 in `r6/before_r6/`, round 4 in `r5/before_round4/`.

## 0. Preconditions (stop if one is false)

```
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
S=work/postcard-look/v2/hole09/stage
# the repo hole_09 files are one of known states (this job never writes them):
shasum -a 256 blender/hole_09.blend Unity/Assets/Resources/Course/hole_09.fbx
#   (a) the ROUND-2 REPAIR STAGE (installed by the integrator; this round replaces it):
#       a00670d2521f729810fbdc4c9fd76bf6c3a54757ecc9b41300d1909d2d466f96  blender/hole_09.blend        (= work/postcard-look/v2/hole09/r7/before_r7/stage/hole_09.blend)
#       4007673dc17043789ed6c7cf72f7ab53abc8b3708e27da2573b38fc3e67f68ed  Unity/Assets/Resources/Course/hole_09.fbx   (= work/postcard-look/v2/hole09/r7/before_r7/stage/hole_09.fbx)
#   (b) or the round-1 stage f6e12d86d6c5.. / 66fc972ff62f.. (= work/postcard-look/v2/hole09/r6/before_r6/stage/), or the round-4 stage 70e5b4e8f8b1.. / 455996b9c419.. (= work/postcard-look/v2/hole09/r5/before_round4/), or (c) the flat baseline:  8846a99f7b5314a7a4bb3f170d57485d2f489b88fd9e64dd509450d8eaee42ad  blender/hole_09.blend  /  88005a32d046181dae84b4b778ca14585dabdf9099f5ba2163d602c737f2b01e  hole_09.fbx
# the staged files are the ones that were gated:
echo "dbc43946e77286f9cf201d90e6bfeef9adf8746e1912fc3352b38b367d7cd42c  $S/hole_09.blend" | shasum -a 256 -c -
echo "ce92141ce61c9521fcd06f4341875d896219f4e156c75f1bc84b1413adeb2b61  $S/hole_09.fbx" | shasum -a 256 -c -
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
$B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- 9          # repo blend + FBX; expect RESULT: ALL PASS (92 gate lines incl. LK_TEXTURED@blend from blender/; LOOK_STILLS_TEXTURED is SKIPPED until Game-view stills exist, then run with --require-stills)
$B -b blender/hole_09.blend --python blender/scripts/postcard_verify.py -- hole09_design   # FAIL only MATERIALS@blend/@fbx + FBX_BUDGET@fbx, by design (old MAT_* allow-list, old 4 MB / 150k budget)
python3 blender/scripts/postcard_emit_cs.py --check Unity/Assets/Scripts/Course/Hole.cs      # HOLE_CS_MATCHES_DESIGN PASS
bash work/postcard-look/guards.sh                                                          # 7 PASS
$B -b --factory-startup --python work/postcard-look/v2/hole09/tools/ruin_check.py -- --blend blender/hole_09.blend     # RUIN_CHECK: 0 FAIL of 13
$B -b blender/hole_09.blend --python work/postcard-look/v2/hole09/tools/tee_parallax_check.py                         # TEE_EDGE_UV_CONTINUOUS PASS
shasum -a 256 blender/hole_09.blend Unity/Assets/Resources/Course/hole_09.fbx              # = the two staged sha256 above
shasum -a 256 Unity/Assets/Resources/Course/hole_09.fbx.meta                               # unchanged
```
Then (Unity owner, through work/postcard-look/heavy.sh): `PostcardImportCheck` (LK_ materials accepted; ground / lie / marker gates unchanged), `GolfLookSmoke`, and the stills
with `GOLF_STILLS_CFG=work/postcard-look/v2/hole09/landmarks.json` -> `ArtDir/screenshots/golf_postcards/look/` (shots hole09_tee, hole09_approach, hole09_ruin; the `extra_previews` key is ignored by the tool).
Expected in the Game view: every hole 9 ground / rock / cliff / plant material is an `LK_` name (GolfLook builds them; `LK_SURF` = GolfSurf, `LK_WATER*` = TennisWater, `LK_PLANTS` one
shared instanced material; `DRESS_SAND_nn` = LK_SAND overlay lobes on the bunker lips, `DRESS_KNOLL_nn` = LK_SCRUB / LK_ROCK hummocks, both non-colliding); the ruin / arch meshes (DRESS_RUIN_nn_pp / DRESS_ARCH_nn_pp) have TWO material slots (LK_MASONRY, LK_ROCK; non-colliding);
only TERRAIN, FAIRWAY, GREEN, TEE_BOX, BUNKER meshes get colliders (every new object is ROCK_ / PLANT_ / DRESS_ / WATER_); there are no LAVA_LIGHT empties on this hole.
Re-measure in the new stills: hole09_1_tee rows 556 / 557 (the review's row-mean step, R 143.6 -> 148.8, +5.2) and the 2x crops of hole09_3_ruin (100,860,700,1280) / (190,420,750,860).

## 3. Rebuild without staging (same geometry, writes the repo paths = the install)

```
$B -b --factory-startup --python blender/scripts/hole09_build.py            # no --out: blender/hole_09.blend, blender/previews/hole_09_overview.png, Unity/.../hole_09.fbx
```
(`hole_09.fbx.meta` is only created when it does not exist, so the existing one is kept.) The blend and the FBX re-import are geometry-identical to the staged ones (gate H_REPRODUCIBLE);
the FBX bytes differ run to run because of the header timestamp and zlib streams.

## 4. Rollback

```
cp work/postcard-look/v2/hole09/r7/before_r7/stage/hole_09.blend blender/hole_09.blend            # the round-2 stage, sha256 a00670d2521f729810fbdc4c9fd76bf6c3a54757ecc9b41300d1909d2d466f96   (the state the repo is in before this install)
cp work/postcard-look/v2/hole09/r7/before_r7/stage/hole_09.fbx Unity/Assets/Resources/Course/hole_09.fbx   # sha256 4007673dc17043789ed6c7cf72f7ab53abc8b3708e27da2573b38fc3e67f68ed
cp work/postcard-look/baseline/blender/hole_09.blend blender/hole_09.blend            # sha256 8846a99f7b5314a7a4bb3f170d57485d2f489b88fd9e64dd509450d8eaee42ad   (the flat afternoon baseline)
cp work/postcard-look/baseline/fbx/hole_09.fbx Unity/Assets/Resources/Course/hole_09.fbx   # sha256 88005a32d046181dae84b4b778ca14585dabdf9099f5ba2163d602c737f2b01e
# or the round-1 stage: cp work/postcard-look/v2/hole09/r6/before_r6/stage/hole_09.blend blender/hole_09.blend; cp work/postcard-look/v2/hole09/r6/before_r6/stage/hole_09.fbx Unity/Assets/Resources/Course/hole_09.fbx   (sha256 f6e12d86d6c5c59d8d7701aa34a21320b89f4374c5c1f86fa9bed6456dbaac28 / 66fc972ff62fb0fd972ca51a3efdda28aa8f50cc73ab714c10bf5993603d6614)
# or the round-4 stage: cp work/postcard-look/v2/hole09/r5/before_round4/hole_09.blend blender/hole_09.blend; cp work/postcard-look/v2/hole09/r5/before_round4/hole_09.fbx Unity/Assets/Resources/Course/hole_09.fbx
```

## Files this job owns / changed (nothing else was touched)

```
bbd5e473659757df53451f42ff368153b620015b9e324abb97536de9b33cd89f  blender/scripts/hole09_build.py
bbfecf236d9ff65b379344e38658bcbca3165a631a3e7b6aba437c91bf12ac47  blender/scripts/hole09_look.py
1f75d28f9ddac31bc91c02175975eb214d7d96e0c57206ec3f4225a84b42969e  blender/scripts/hole09_masonry.py
afe9e368639c2b6d4e462f9de2d0d17d997ce5f72c981e90f36dc0b201009e37  blender/scripts/hole09_stone.py
3069418688b3f2b7b2e73bc63fe0b4cbebb30a1252e0a09795139fb0c126f84d  blender/scripts/hole09_qa.py
8264099d82b9f9246a8837c4856d50d3aef151449b5c2cb57a65e12106ed82b0  blender/scripts/hole09_design.py
19e01c57a313349280f13b52e49464d957409e06f99dfe4ca87f959dc82fb2b3  blender/scripts/postcard_look_lib.py
6cdc5c6df49d08b5de8fa209a09368e092d27339ebbe0e3069a1abb80b50f2f4  blender/scripts/postcard_props_lib.py
ff3062b6798fafcf021183e2da39461b501ff7dbce45f75dab3111884b94d3f4  blender/scripts/postcard_lib.py
9b3a3ec1a5f34536a5921b3d601e03aa9b7835ad60872e08ba11398170beb4de  blender/scripts/postcard_look_verify.py
28c5d092ead86a0cdc8884540ecac2c321dbc089d027ecc443994e78072fb783  blender/scripts/golf_look_textures.py
4b1b4cd3fbdfc407308195730f44f67c29c397b49e574213840d324cc454daa4  work/postcard-look/v2/hole09/tools/ruin_check.py
1b427a78cc035bf31627352a5fd23eca2d2b4b302223dea011292fb8e49ea760  work/postcard-look/v2/hole09/tools/tee_parallax_check.py
2df924fcd2a75ad96c17326828bfa598e72ebf977b1ad0c077e97e1d489a4be5  work/postcard-look/v2/hole09/tools/run_all_gates.sh
051f219d9800a0db46ed5a1a3374d3c4ec2e3b5c6762629612a5d0eb9e2b35a9  work/postcard-look/v2/hole09/tools/make_gates_txt.py
c0a21e1310aaf23a573960a870721daf99e52563f1f533d7ec152b8063823a13  work/postcard-look/v2/hole09/tools/make_install_md.py
```
`hole09_design.py` is byte-identical to its start-of-job copy (`work/postcard-look/v2/hole09/hole09_design.py.at_start`; `postcard_emit_cs.py --check` = no drift), `postcard_lib.py`, both libraries, the textures and every Unity file were not edited by this job
(library behaviours worked around in the hole scripts: `work/postcard-look/v2/hole09/LIB_BUGS.md`; `hole09_masonry.py` no longer calls the props lib's private `_hull`: the stones come from `hole09_stone.py`). Start-of-round copies of the changed scripts: `work/postcard-look/v2/hole09/r7/*.at_start`.
