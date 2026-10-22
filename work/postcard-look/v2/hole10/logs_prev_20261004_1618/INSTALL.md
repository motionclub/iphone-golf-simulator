# Hole 10 Crater: install of the staged look build (NOT installed yet)

Staged 2026-10-04 (round 3, after the second skeptic review; first staging 14:42, round 2 15:29, round 3 16:14 EDT) by `blender/scripts/hole10_build.py -- --out work/postcard-look/v2/hole10/stage`
(it imports `blender/scripts/hole10_look.py`: keep both scripts together; snapshot with sha256 in `scripts_round3/`). Nothing in the repo's `blender/` (except the two hole10 scripts) or
`Unity/Assets/Resources/Course/` was written. The install is a separate step, to be done AFTER the Unity Game-view calibration that is running now
has finished (a changed FBX makes Unity reimport).

## What gets copied (two files, nothing else)

| from (staged) | to (repo) | sha256 of the staged file |
|---|---|---|
| `work/postcard-look/v2/hole10/stage/hole_10.blend` | `blender/hole_10.blend` | `03155939151a3ed04972c17c113db564bcf8860376781a39178f5fc27c97722d` |
| `work/postcard-look/v2/hole10/stage/hole_10.fbx` | `Unity/Assets/Resources/Course/hole_10.fbx` | `f06bc1b2a3d2e89b54c592127be45d8327f49ae336609a06496299ed26e0f12b` (4,020,172 bytes = 3.83 MB) |

Scripts that produced them (sha256): `hole10_build.py` `f818e828b42331a50a45677ca73fa054b08eb96a3c704be83090320e38223cd6`, `hole10_look.py` `5a98769e633520b844981303aaef26d4165e1e21bfe274648520a14405056bc5`,
`hole10_design.py` `97c7507dafca8ef7553620d0a4dcbe8f67b179dc3701f45b549dea3426299959` (unchanged). Geometry hash of the build (vertices, material names, UV0): `17b370a9fcdd9d7d03f5eb50a263a0caa5b9484149f7b45cecd302b59204366a`,
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
#    expected (flat baseline): blend b0c478e6f2a7..., fbx e99475de7175... (the same for the repo files and the baseline copies; verified again 2026-10-04 16:20: the repo hole_10 files are still the baseline)

# 2. install: the .blend and the .fbx ONLY
cp $S/stage/hole_10.blend blender/hole_10.blend
cp $S/stage/hole_10.fbx   Unity/Assets/Resources/Course/hole_10.fbx
# NEVER: cp $S/stage/hole_10.fbx.meta ...   (see above)
shasum -a 256 blender/hole_10.blend Unity/Assets/Resources/Course/hole_10.fbx Unity/Assets/Resources/Course/hole_10.fbx.meta
#    expected: 03155939..., f06bc1b2..., bf25a2be... (the .meta unchanged)

# 3. the same gate tool on the installed files (default paths = the repo files): every line must read as in $S/GATES_hole10.txt (only LOOK_FILES fails)
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
