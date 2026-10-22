# Hole 10 Crater: install of the staged look build (repair round 1 staged 2026-10-04 22:11; the repo still holds the round-4 build installed by the proof phase at 20:43)

Staged 2026-10-04 (round 3, after the second skeptic review; first staging 14:42, round 2 15:29, round 3 16:14 EDT) by `blender/scripts/hole10_build.py -- --out work/postcard-look/v2/hole10/stage`
(it imports `blender/scripts/hole10_look.py`: keep both scripts together; snapshot with sha256 in `scripts_round3/`). Nothing in the repo's `blender/` (except the two hole10 scripts) or
`Unity/Assets/Resources/Course/` was written. The install is a separate step, to be done AFTER the Unity Game-view calibration that is running now
has finished (a changed FBX makes Unity reimport).

## Repair round 1 (2026-10-04 22:11 EDT, staged, NOT installed): rebuilt on the shared fixers' libs / textures + three hole-script fixes

State found: the proof phase had installed the round-4 stage (repo `blender/hole_10.blend` sha `2987bef2...`, `Unity/.../hole_10.fbx` sha `c8a86ecd...`, backup of the flat baseline in `v2/install_backup/`), reviewers failed the Game-view stills, and the shared
fixers then changed `postcard_look_lib.py`, `postcard_props_lib.py`, `postcard_look_verify.py`, `golf_look_textures.py` and 14 Look PNGs (the sha lists before / after: `libs_sha_repair_r1_before.txt` = the file as found,
`libs_sha_repair_r1.txt` = at the gated run; `libs_sha_round4.txt`, the file `v2/proof/install_holes.py` reads, now holds the repair-round-1 list and the old one is `libs_sha_round4_before_repair_r1.txt`).
Rebuild = `work/postcard-look/v2/hole10/run_all.sh` (60 s). What changed in MY files only (`blender/scripts/hole10_build.py`, `hole10_look.py`; `hole10_design.py` byte-identical, `postcard_emit_cs --check` no drift, scoring meshes bit-identical: H_PLAY_UNCHANGED, PLAY_SURFACE_* PASS):

| finding / need | cause | change | evidence |
|---|---|---|---|
| H_UV_WINDOWS FAIL after the texture agent's v6 (Basalt_C luminance profile deviation 0.0228) | `PROFILE128` (the weights that make the walls come out dark) was baked from the v5 Basalt_C | re-measured on the v6 Basalt_C / Basalt_E (the six glow cores and the five glow-free zones did NOT move: same `GLOW_U` / `ZONES`), `PROFILE128` re-baked | build gate H_UV_WINDOWS PASS (zone glow 0.0000 %, edge glow 9.3 %, profile deviation <= 0.01), stage H_GLOW_JOINTS PASS |
| NEW verifier gate SMOKE_IN_FRAME FAIL (smoke 0.47 / 0.01 / 0.00 % of the tee / approach / lava-rim frames, need 1.5 %) | three single cards behind the wall; Smoke_C peaks at alpha .50 (x AlphaGain 1.35) and only 11 % of a card reaches the gate's effective alpha .30 | `hole10_look.smoke_group`: four stacked plumes of 3 big cards (one per proof camera + one off the volcano's summit), 12 DRESS_SMOKE cards, all beyond the rim circle | verifier SMOKE_IN_FRAME@blend/@fbx PASS: tee **3.03 %**, approach **4.01 %**, lava rim **4.67 %** (limit 1.5 %); `repair_r1/sheet_smoke_frames.png`; CRATER_CONE_SMOKE, SMOKE_SOFT PASS |
| review (medium): hard horizontal seam at the tee pad, hole10_1_tee.png row 590 (mean abs row step 16.4 vs 5.5), no distinct pad | TEE_BOX (z 6.24, 10 cm over the FAIRWAY) was LK_GREEN with planar UVs beside LK_FAIRWAY with centerline UVs: stripes stopped, texture scale / phase jumped; and its far lip hides ~0.4 m of fairway behind it for the address camera | TEE_BOX keeps outline + height and wears LK_FAIRWAY with the FAIRWAY's own centerline UV, offset per vertex by the lip parallax for FrameAddress (dz 0.10 m, eye 2.21 m over the pad: up to 0.50 m): the mow stripes and blades meet across the lip in the tee frame | stage gate H_TEE_CONTINUOUS (UV of every TEE_BOX loop vs the FAIRWAY's UV at p + parallax: 0.0000 tile, negative controls: the round-4 stage 0.49 tile, a constant 0.04 shift 0.046 tile); Blender preview row-step seam gate H_TEE_SEAM_PREVIEW (worst ground row 1.43 x its neighbourhood, limit 1.6; round-4 build 1.98 at row 590, the review's Game-view still 2.90); `repair_r1/sheet_tee_seam.png`. CRATER_TEE_PAD PASS (LK_FAIRWAY is allowed; square fill 0.99, aspect 1.17). The Game-view number needs the Unity re-shoot |
| review (low): dark red-speckled patch at the right of the tee frame (hole10_1_tee.png x 850-900, y 285-310) | identified with ray casts through the tee camera (`repair_r1/pixel_probe.py`): it is NOT a bunker, hazard or lava puddle but the crater-side rim lip at course (36-46, 64-80) yd, 75 yd out, at the right edge of the frame: TERRAIN_CRATER rough, the LK_BASALT lip band and ROCK_SKIN_70 / ROCK_SKIN_71 basalt cladding seen over the shelf edge with the lava glow joints, partly behind PLANT_AGAVE_B.010 / .012 | no geometry change (it is the real cliff drop; bunker 1 at (57.4, 110.3) yd is a 3-px sliver at that distance and angle) | pixel probe table in `repair_r1/` notes (README.md "repair round 1") |
| PROTECTED_FILES (low) | other chats' tennis / emote / multiplayer files | none for this job (this build writes only under `v2/hole10/` and `blender/scripts/hole10_*.py`) | GATES_hole10.txt PROTECTED_FILES line lists the 31 files, none ours |

Gates of the staged run (`GATES_hole10.txt`, `logs/`): `postcard_look_verify` on the blend **50 / 51** and on the FBX re-import **51 / 52** (every line passes except `SMOKE_VISIBLE_STILLS`, which reads `ArtDir/screenshots/golf_postcards/look/stills_stats.json`: that file
was written by the previous stills tool and carries no `smoke` block, so it needs the Unity re-shoot after the install, it is not measurable here), 36 / 36 stage gates (new H_TEE_CONTINUOUS), 21 / 21 build gates, 3 / 3 landmark rays, H_REPRODUCIBLE, guards 7 / 7.
Staged geometry: 697 objects, 153,165 vertices, 113,935 faces, 220,409 triangles (budget 250k), FBX 3,800,460 bytes; geometry hash (vertices, material names, UV0) `3e191bb53f4f004566228a8224da75171d2ca1239dede02ae4ef197874b1c0cc`.
`landmarks.json`: cameras unchanged, ray tests re-run on the new stage (3 / 3 PASS).

Install (same commands as below; the first INSTALL.md line that names a staged file is the table, so `v2/proof/install_holes.py` reads these shas):

| from (staged) | to (repo) | sha256 of the staged file |
|---|---|---|
| `work/postcard-look/v2/hole10/stage/hole_10.blend` | `blender/hole_10.blend` | `ef572f8931856cd6004d8848f171be638a2e9629ec2e1f1c1092968938990609` |
| `work/postcard-look/v2/hole10/stage/hole_10.fbx` | `Unity/Assets/Resources/Course/hole_10.fbx` | `5f3d5bf7c217a1607cf7618cd45997dfcf1a992859a503780d62e564803b929e` (3,800,460 bytes = 3.62 MB) |

Scripts that produced them (sha256, snapshot + the tools in `scripts_repair_r1/sha256.txt`): `hole10_build.py` `39f69d7427f2c57f6442134485edeb55f3d5b9e31b5abe5a7862d42f3598ea1e`, `hole10_look.py` `233691f9860ec17615057bf766a17f54114a71ca1ae135a3dffde4cf6cee59e3`,
`hole10_design.py` `97c7507dafca8ef7553620d0a4dcbe8f67b179dc3701f45b549dea3426299959` (unchanged).
Round-4 rollback target (what the repo holds now): `stage_before_repair_r1/` (blend `2987bef2...`, fbx `c8a86ecd...`); the flat baseline is `work/postcard-look/baseline/`. After the install: Unity re-import, `run_importcheck.sh`, `run_stills.sh` (the three proof shots + the smoke block), then
`postcard_look_verify.py -- 10 --require-stills` must read SMOKE_VISIBLE_STILLS from the fresh stats.

## What follows is the round-4 text (superseded for shas and counts by the section above; the commands are still valid)

## Round 4 (2026-10-04 20:37 EDT): rebuilt on the FINAL textures + the final gate tool (rebuild-only step, no design change)

Between the round-3 staging (16:14) and now the texture agent regenerated 12 Look PNGs (Fairway_C, Green_C, Rough_C/N, Scrub_C/N, Lava_C/E/N, Basalt_C/N/E; TEXTURES.md "v5") and the gate agent changed `postcard_look_verify.py`
(sha `884448e1fc04...`, was `edc96d4d755b...`). `postcard_look_lib.py` / `postcard_props_lib.py` / `postcard_lib.py` did NOT change (same sha as `libs_sha_at_start.txt`). Snapshot of the libs + every Look PNG: `libs_sha_round4.txt`
(= `logs/libs_sha_after.txt`); the round-3 list is in `logs_prev_20261004_1618/libs_sha_after.txt`.

* **What had to change in my scripts (`hole10_look.py`, `hole10_build.py`; `hole10_design.py` is byte-identical, `postcard_emit_cs --check` = no drift)**: the UV windows of round 3 hard-coded the glow-free zones of the OLD Basalt_E. The v5 Basalt_E has the SAME six joint cores
  (u 0.123 / 0.446 / 0.534 / 0.718 / 0.806 / 0.930) but its new fork and T-junction cracks spread glow over +-0.05 of u round every joint: 6 of the 8 round-3 "glow-free" zones now held 0.07-0.6 % glow texels (measured by `r3/zone_stale_v5.py`).
  Rebuilt on the stale constants, `H_GLOW_JOINTS` still passed but with tops 0.22 % (round 3: 0.01 %), sides 1.28 % (limit 1.58 %), 46 % of the side area lit (limit 50 %): glow on the faces' middles and on the tops. Now: `ZONES` re-measured (5 strictly glow-free zones, 2 px margin, `r3/basalt_zones_v5.py`),
  the Basalt_C luminance profile (128 bins) is baked into `hole10_look.PROFILE128` and the window position inside a zone is drawn with weight (0.14 / window luminance)^3 (`pick_u0`; caps of tops too), so the walls still come out darker than the tile mean.
  Result (stage gates, blend and FBX): tops **0.01 %**, sides **0.91 %** (allowed 0.66-1.58 %), **18 %** of the side area carries any glow (10-50 %), median dash 3.2 m, 31 % of the side faces take a window that starts on a glow line.
* **New guard (not a loosened gate)**: the build's `H_UV_WINDOWS` now re-measures the constants from the PNGs on disk (`hole10_look.texture_measure()`): glow share inside every glow-free zone <= 0.02 % (measured 0.0000 %), the narrowest edge window at each of the 6 glow lines >= 4 % glow (measured 7.3 %),
  Basalt_C profile deviation <= 0.01 (0.0005). A later texture change fails the build gate instead of drifting quietly. Everything else of round 3 is unchanged (same walls, crust, stacks, plants, cone, lava lights, scoring meshes).
* **Gate result** (`GATES_hole10.txt`, `run_all.sh` 39 s): `postcard_look_verify` **49/49 on the blend, 50/50 on the FBX re-import, RESULT: ALL PASS** (round 3: LOOK_FILES failed on Fairway_C / Green_C; the new textures and the new gate definition cure it), 34/34 stage gates, 3/3 landmark rays, 21/21 build gates,
  H_REPRODUCIBLE (geometry hash `73b4f872f8909778` twice), guards 7/7. Unchanged FAIL lines: `PROTECTED_FILES` (31 files of tennis / MatchHeroes / Customization / QualitySettings changed by other sessions since the job-start hashes, none written by this build) and the 5 `U_*` lines that only a Unity run can measure.
* Geometry vs round 3: same vertices / faces / objects (158,454 / 117,027 / 689, 227,497 triangles); only UV0 changed, so the geometry hash moved (`17b370a9fcdd9d7d` -> `73b4f872f8909778`). Landmarks, cameras, the three proof shots: unchanged (ray tests pass on the new stage).
* Superseded round-3 stage (stale window constants on the new texture, tops 0.22 %): `logs_stale_constants_20261004_2037/` (previews + the gate table). Round-3 original: `logs_prev_20261004_1618/`.
* Script snapshot: `scripts_round4/` (`*.before_texture_v5` = the round-3 scripts, plus the new ones with `sha256.txt`).


## What gets copied (two files, nothing else)

| from (staged) | to (repo) | sha256 of the staged file |
|---|---|---|
| (round 4, installed 20:43) `stage_before_repair_r1/hole_10.blend` | `blender/hole_10.blend` | `2987bef29470fb8b77093b7965f0e475f809f0cd639f7bfb41366fa64d017686` |
| (round 4, installed 20:43) `stage_before_repair_r1/hole_10.fbx` | `Unity/Assets/Resources/Course/hole_10.fbx` | `c8a86ecd160ea323bc9e4d5d6a28e46a2aa1271a5e23441647cb0bf76977208c` (4,000,300 bytes = 3.81 MB) |

Scripts that produced them (sha256): `hole10_build.py` `ae5eeb2dab7a9253153e986fe6e6747b863b3094517c2535005b356ac8a90e89`, `hole10_look.py` `8fd4b129a77522db71efc44ed781176f6ce7e948bb6cd9578bd1f6ba5141fb94`,
`hole10_design.py` `97c7507dafca8ef7553620d0a4dcbe8f67b179dc3701f45b549dea3426299959` (unchanged). Geometry hash of the build (vertices, material names, UV0): `73b4f872f89097788a7072daffc0468c143e8cefa8898450831eb6a4059c9c1a`,
689 objects, 158,454 vertices, 117,027 faces, 227,497 triangles (a rebuild into any folder gives the same hash; the .blend / .fbx BYTES differ run to run: the FBX header carries the time and the source path).

Files that must NOT be copied or touched:

* `stage/hole_10.fbx.meta` (sha `b4fcf335d3a0...`): it was written by `postcard_lib.export_fbx` with a FRESH random GUID because the staging folder had no .meta.
  The repo's `Unity/Assets/Resources/Course/hole_10.fbx.meta` (sha `bf25a2beedbd...`, GUID of the asset, `isReadable: 1`, `tangentImportMode: 3`, `normalImportMode: 0`,
  `materialName: 0`) stays exactly as it is. Copying the staged one would change the GUID and break every reference to the hole.
* `stage/hole_10_overview.png` is optional (Blender preview). If wanted: `cp stage/hole_10_overview.png blender/previews/hole_10_overview.png`.
* `hole_07.*`, `Hole.cs`, any tennis / hero / locker / Serve file, `QualitySettings.asset`.

The staged .blend keeps ABSOLUTE image paths (`/Users/adnanyonathan/.../Unity/Assets/Resources/Course/Look/*.png`; saved with `relative_remap=False`), so it opens with
its textures from `blender/` as well as from the staging folder.

## Commands (run from the repo root, with Unity closed or idle; use bash)

```bash
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
S=work/postcard-look/v2/hole10

# 0. the staged files are the ones that were gated (the hashes above), the libs / textures / scripts did not move since
shasum -a 256 $S/stage/hole_10.blend $S/stage/hole_10.fbx blender/scripts/hole10_build.py blender/scripts/hole10_look.py
diff <(cat $S/logs/libs_sha_after.txt) <(shasum -a 256 blender/scripts/postcard_look_lib.py blender/scripts/postcard_props_lib.py blender/scripts/postcard_look_verify.py blender/scripts/postcard_lib.py blender/scripts/golf_look_textures.py Unity/Assets/Resources/Course/Look/*.png) \
  && echo "libs + textures identical to the gated run" || echo "LIBS OR TEXTURES CHANGED SINCE THE GATED RUN: rerun $S/tools/run_all.sh first (it rebuilds into stage/ and re-gates; then refresh the hashes above from stage_sha256.txt)"

# 1. back up the flat baseline (already in work/postcard-look/baseline/blender/hole_10.blend and baseline/fbx/hole_10.fbx; this just proves it)
shasum -a 256 work/postcard-look/baseline/blender/hole_10.blend work/postcard-look/baseline/fbx/hole_10.fbx blender/hole_10.blend Unity/Assets/Resources/Course/hole_10.fbx
#    expected: the baseline copies b0c478e6f2a7... / e99475de7175...; the repo files are the round-4 build 2987bef2... / c8a86ecd... until the repair-round-1 stage is installed (v2/proof/install_holes.py keeps the first backup and saves a prev_<sha8> copy)

# 2. install: the .blend and the .fbx ONLY
cp $S/stage/hole_10.blend blender/hole_10.blend
cp $S/stage/hole_10.fbx   Unity/Assets/Resources/Course/hole_10.fbx
# NEVER: cp $S/stage/hole_10.fbx.meta ...   (see above)
shasum -a 256 blender/hole_10.blend Unity/Assets/Resources/Course/hole_10.fbx Unity/Assets/Resources/Course/hole_10.fbx.meta
#    expected: ef572f89..., 5f3d5bf7..., bf25a2be... (the .meta unchanged)

# 3. the same gate tool on the installed files (default paths = the repo files): every line must read as in $S/GATES_hole10.txt (repair round 1: 50/51 on the blend, 51/52 on the FBX re-import; the only line that fails is SMOKE_VISIBLE_STILLS until the stills are re-shot, then ALL PASS)
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python blender/scripts/postcard_look_verify.py -- 10 --json /tmp/h10_installed_verify.json | grep -E "^GATE|^RESULT"
bash work/postcard-look/guards.sh                                   # 7 PASS
python3 blender/scripts/postcard_emit_cs.py --check Unity/Assets/Scripts/Course/Hole.cs   # HOLE_CS_MATCHES_DESIGN PASS

# 4. Unity (through heavy.sh, never two Unity runs at once): reimport + PostcardImportCheck + the proof shots
work/postcard-look/v2/runtime/run_importcheck.sh hole10_installed          # GROUND_ALBEDO_AND_NORMAL, NO_FLAT_POSTCARD_GROUND, LAVA_LIGHTS_PLACED, ROCK_NEAR_LAVA_CHUNKED must read PASS for hole 10
work/postcard-look/v2/runtime/run_stills.sh hole10_proof ArtDir/screenshots/golf_postcards/look GOLF_STILLS_CFG=$PWD/$S/landmarks.json GOLF_STILLS_HOLES=10
#    -> hole10_tee.png, hole10_approach.png, hole10_lavarim.png (900x1600 Game view) + stills_stats.json
#    (hole 8 / 9 shots come from their own landmarks.json: run them in one cfg if the three holes are installed together)
```

## Rollback (if the Game view or any gate is worse)

```bash
cp work/postcard-look/baseline/blender/hole_10.blend blender/hole_10.blend
cp work/postcard-look/baseline/fbx/hole_10.fbx Unity/Assets/Resources/Course/hole_10.fbx     # the .meta is untouched either way
```
The round-2 staged build (not recommended: it failed review) is in `round2/hole_10_round2.blend` / `.fbx`.

## Rebuild instead of copy (e.g. a lib or texture changed after the staged run)

Needs `blender/scripts/hole10_build.py` AND `blender/scripts/hole10_look.py` (wall / crust / cone / UV-window helpers) in the repo.

```bash
S=work/postcard-look/v2/hole10; $S/tools/run_all.sh | tee $S/logs/run_all_output.txt; python3 $S/tools/summarize.py
```
`run_all.sh` (about 50 s) rebuilds into `stage/` (and a second time into `stage_repro/` for the reproducibility gate), re-runs every gate and refreshes the sha256 above in
`stage_sha256.txt`. The build itself is `blender/scripts/hole10_build.py -- --out DIR` (add `--no-render` to skip the EEVEE overview). Without `--out` the
script writes the repo paths directly: that is what an install-by-rebuild would do, and it is the reason this folder uses `--out` for everything.

## What Unity should show after the install (the checks that only the Game view can make)

* `hole10_tee.png`: textured fairway (mow stripes), the near terraced wall and the far ring as dark columnar basalt with sparse long orange cracks and a low window to the right where the volcano shows, the volcano with its lava flows, no flat colour.
* `hole10_approach.png`: the pillar with basalt sides dropping into orange lava (GolfLava), a flag on a grass top at play height, the tall dark wall behind it with sparse cracks (not a field of dashes).
* `hole10_lavarim.png`: the raised rim camera: the basalt columns of the rim with glowing joints meeting the lava, the grass shelf with agave, the pillar, the wall.
* Round 3 additions to judge in the Game view: the glow on the wall faces should read as a few long cracks along column edges (3 m dashes, a third of the old density), the walls darker (dark UV slices), the crust as black plates with lava rivers (not dark stains), the volcano glowing along its flanks.
* Unity-side lines of the brief that nothing here measured: lava orange without bloom, basalt dark with joints only, smoke wisps soft, grass hue 64-73, albedo + normal on the real meshes (`GATES.md` "Unity-side companions"). The staged `DRESS_CONE` carries LK_LAVA faces (the Blender verifier allows it): confirm PostcardImportCheck accepts that.
