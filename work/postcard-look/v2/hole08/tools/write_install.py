"""Regenerates INSTALL.md from the logs of the last run_all.sh (hashes, triangle count, geometry hash). python3 write_install.py"""
import re, os, hashlib, json
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
H = R + "/work/postcard-look/v2/hole08"
L = H + "/logs/"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


stage = {ln.split()[1]: ln.split()[0] for ln in open(L + "stage_sha256.txt").read().splitlines() if len(ln.split()) == 2 and len(ln.split()[0]) == 64}
fp = [ln.split() for ln in open(L + "reproducible.txt").read().splitlines() if ln.startswith("FP")]
build = open(L + "build.log").read()
tris = int(re.search(r"stats: \d+ objects, \d+ meshes, (\d+) triangles", build).group(1))
mb = os.path.getsize(H + "/stage/hole_08.fbx") / 1048576
# the staged files on disk must be the ones logged
for nm in ("hole_08.blend", "hole_08.fbx"):
    assert sha(H + "/stage/" + nm) == stage[nm], f"{nm} changed since logs/stage_sha256.txt"
base = {nm: sha(p) for nm, p in dict(blend=R + "/blender/hole_08.blend", fbx=R + "/Unity/Assets/Resources/Course/hole_08.fbx", meta=R + "/Unity/Assets/Resources/Course/hole_08.fbx.meta").items()}
bl = {nm: sha(R + "/work/postcard-look/baseline/" + p) for nm, p in dict(blend="blender/hole_08.blend", fbx="fbx/hole_08.fbx").items()}
repo_is_baseline = base["blend"] == bl["blend"] and base["fbx"] == bl["fbx"]
libs = open(L + "lib_sha_final.txt").read().splitlines()[1:]
r5 = {ln.split()[1]: ln.split()[0] for ln in open(H + "/r7/logs_r6/stage_sha256.txt").read().splitlines() if len(ln.split()) == 2 and len(ln.split()[0]) == 64}   # (name kept) = the round-6 stage
repo_is_r5 = base["blend"] == r5["hole_08.blend"] and base["fbx"] == r5["hole_08.fbx"]
repo_is_new = base["blend"] == stage["hole_08.blend"] and base["fbx"] == stage["hole_08.fbx"]
state = ("byte-identical to the round-6 build (the one the integrator installed at 01:18 on 2026-10-05; r7/stage_r6)" if repo_is_r5 else ("ALREADY the round-7 build (somebody installed it)" if repo_is_new else
         "NEITHER the round-6 build nor this build (somebody changed them: compare before copying)"))
txt = f"""# Hole 8 Needle: install (NOT done: staged only) -- round 7 (repair round 3, 2026-10-05)

Staged build (`run_all.sh`; sha256 of the libs / verifier / texture generator in `logs/lib_sha_final.txt`, the Look PNGs in `logs/look_png_sha_final.txt`; the start-of-round-7 state: `r7/lib_sha_at_start.txt`, `r7/look_png_sha_at_start.txt`;
the libs / textures of the round-6 build (= what is installed): `r7/lib_sha_r6.txt`, `r7/look_png_sha_r6.txt`).
Nothing in the repo was written by this round: `blender/hole_08.blend`, `Unity/Assets/Resources/Course/hole_08.fbx` and `hole_08.fbx.meta` are {state} (sha below).

## sha256 of the staged files (`stage/`, `logs/stage_sha256.txt`)

```
{stage['hole_08.blend']}  stage/hole_08.blend
{stage['hole_08.fbx']}  stage/hole_08.fbx          ({mb:.2f} MB, {tris:,} triangles in the export set, exported with postcard_look_lib.export_look_fbx)
{stage['hole_08.fbx.meta']}  stage/hole_08.fbx.meta     (staging copy of the hole 7 meta with a fresh guid: DO NOT COPY IT)
```
Geometry hash of the build (names + 0.1 mm world vertices of every mesh): `{fp[0][2]}`, identical in {len(fp)} builds (`logs/reproducible.txt`). The .blend / .fbx bytes themselves
carry timestamps, so a rebuild changes their sha but not the geometry hash.

Repo files today: `blender/hole_08.blend` {base['blend'][:8]}..., `hole_08.fbx` {base['fbx'][:8]}..., `hole_08.fbx.meta` {base['meta'][:8]}... (the meta holds the GUID and isReadable 1 / tangentImportMode 3: never overwritten).
Round-6 build (what is installed now): `r7/stage_r6/hole_08.blend` {r5['hole_08.blend'][:8]}..., `hole_08.fbx` {r5['hole_08.fbx'][:8]}.... Baseline (flat afternoon mesh): `work/postcard-look/baseline/blender/hole_08.blend` {bl['blend'][:8]}..., `baseline/fbx/hole_08.fbx` {bl['fbx'][:8]}....

## Install (copy the .blend and the .fbx ONLY)

```bash
cd {R}
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
cp work/postcard-look/v2/hole08/r7/stage_r6/hole_08.blend blender/hole_08.blend      # back to the round-6 build
cp work/postcard-look/v2/hole08/r7/stage_r6/hole_08.fbx   Unity/Assets/Resources/Course/hole_08.fbx
# or all the way to the flat baseline:
cp work/postcard-look/baseline/blender/hole_08.blend blender/hole_08.blend
cp work/postcard-look/baseline/fbx/hole_08.fbx       Unity/Assets/Resources/Course/hole_08.fbx
```

## After the copy (Unity side, through work/postcard-look/heavy.sh)

```bash
work/postcard-look/v2/runtime/run_importcheck.sh h8      # GROUND_ALBEDO_AND_NORMAL / NO_FLAT_POSTCARD_GROUND stay PASS for hole 8; ground-height / lie / marker lines stay PASS
work/postcard-look/v2/runtime/run_smoke.sh h8
work/postcard-look/v2/runtime/run_stills.sh h8 ArtDir/screenshots/golf_postcards/look GOLF_STILLS_CFG=$PWD/work/postcard-look/v2/hole08/landmarks.json
#   landmarks.json holds hole 8's shots only (the cfg REPLACES the default list): hole08_tee, hole08_approach, hole08_arch (the landmark: 6 m above the green pad's rim, UNCHANGED camera since round 5 (landmarks.json byte-equal in content to the round-6 file)), hole08_pathball (optional extra: ball position (-1, 11) on the straightened path);
#   merge it with the hole 9 / 10 cfgs for one run, or run it alone: the tool takes the shots of one hole together.
```
Rebuild without installing: `Blender -b --factory-startup --python blender/scripts/hole08_build.py -- --out <dir>` (never run it WITHOUT --out until the install is meant to happen: without --out it writes
`blender/hole_08.blend`, `blender/previews/hole_08_overview.png` and `Unity/.../hole_08.fbx`). The build itself takes 13 s. Everything (build, verifier on blend + FBX re-import, relocated-copy texture check, postcard_verify, postcard_check, the baseline comparison,
frame variation, dense path height, landmarks, previews, negative controls, reproducibility, guards): `work/postcard-look/v2/hole08/run_all.sh` (about 10 minutes), summary `GATES_hole08.md`.

## What round 7 changed (repair round 3, 2026-10-05): a rebuild on the shared fixers' libs, NO hole-script change

The only reviewer finding assigned to this hole script in round 3 was a NOTE ("PROTECTED_FILES: 32 differing files, all other chats'"; fix_hint: none for this job; `guards.sh` 7 PASS, hole 7 / Hole.cs byte-identical): nothing to repair in `hole08_build.py` / `hole08_look.py` / the `SCENERY` dict (sha256 of the three hole scripts unchanged vs `r7/hole08_*.py.at_start_r7`; `postcard_emit_cs.py --check` no drift).
What moved is under the hole: the shared fixers' round-3 changes to `postcard_props_lib.py` (arch haunch recess 0.12 -> 0.02 m = no brown strand across the right pier; sea stacks with a smooth waist / swell and bigger shelves; olive shrubs, no lime), `postcard_look_verify.py`, `golf_look_textures.py` and the Look PNGs Fairway_C / Fairway_N / Green_C / Green_N / Lava_* / Smoke_C (`r7/lib_sha_r6.txt` vs `logs/lib_sha_final.txt`, `r7/look_png_sha_r6.txt` vs `logs/look_png_sha_final.txt`).
Rebuilt with `run_all.sh` on them: **40 of 40 hole gates PASS** (`GATES_hole08.md`), build 37 / 37, `postcard_look_verify` 96 / 96 on the blend + the FBX re-import (the same 96 gate names as round 6), relocated-copy texture check 96 / 96, 22 / 22 negative controls caught, geometry hash `{fp[0][2]}` identical in 3 builds, guards 7 / 7.
Per-object diff against the INSTALLED round-6 blend (`tools/diff_builds.py`, `logs/diff_r6_r7.json`): 962 meshes in both; **63 changed, 0 added, 0 removed, 0 re-materialled**: 46 shrubs (PLANT_SHRUB_A 27 / B 14 / C 5), 16 sea stack parts (ROCK_SPIRE_A 9, ROCK_SEASTACK_A 5, ROCK_SEASTACK_D 2) and the arch (DRESS_ARCH_00). **No collision-named mesh changed** (TERRAIN_NEEDLE, FAIRWAY, FAIRWAY_FIRSTCUT, GREEN, GREEN_APRON, TEE_BOX, BUNKER_01, BUNKER_01_LIP are vertex-identical to the baseline: H_PLAY_UNCHANGED max |delta| 0.00 m).
Triangles in the export set 199,304 -> {tris:,} (the shrubs are lighter). The four cameras (`landmarks.json`: tee, approach, arch, pathball) are unchanged: the arch camera search lands on the same camera (Blender m (-10.0, 277.0, 12.08)); content-identical to the round-6 file, `landmarks_check.json` has the new composition shares.
The round-6 fixes still pass on the new libs (TEE_SEAM_SEEN dU 0.0001 / dV 0.0002 tile units, PATH_STEP_CONTINUOUS 0 rows without stones, ARCH_SLAB_COVERED 1.6 % of the lower 40 % / 0.6 % of the frame, PATH_UNDER_BALL max 1.15 cm, PATH_DENSE 0 samples above 1.2 cm on 2 cm and 1 cm grids).
Blender previews (NOT Game view): `previews/sheet_round7_full.jpg` (round 6 vs round 7 from the tee / approach / arch cameras), `previews/sheet_round7_aerial.jpg`.
Not mine / open: the Unity Game view of this build (no Unity run by this agent: the integrator's `run_stills.sh` is the proof); the tee plate's directional shadow beyond its edge (Unity casts it; the FBX cannot switch it off); the sky-fold hairline at x 586-589 of `hole08_3_arch.png` (TennisSky mirror fold + `GolfAtmosphere` heading, Unity side, libs round-3 notes); the grass hue / saturation under the golf key light (textures + runtime, not the mesh).

## What round 6 changed (the two reviewer findings of the installed round-5 build that are the hole's; no vertex of a scoring mesh moved: H_PLAY_UNCHANGED)

Libs / textures under the hole changed first (the shared fixers, same round, BEFORE this agent): `postcard_look_lib.py`, `postcard_props_lib.py`, `postcard_look_verify.py`, `golf_look_textures.py` and the Look PNGs Basalt / Lava / Smoke (`lib_sha_r5.txt` vs `logs/lib_sha_final.txt`).
Rebuilt on them, then the hole's own fixes (`hole08_look.py`; `hole08_build.py`: docstring only; `hole08_design.py` untouched, `postcard_emit_cs.py --check` no drift):

* **Tee seam (reviewer, medium: "a hard horizontal seam still cuts across the fairway on the tee shot, a strip of grass slices through the stone path and the path shifts sideways at it"; the round-5 fix did not cure it)**. Two causes, both reproduced in Blender
  with the same camera (the seam row is 671 in the Game view and in the ray casts): (1) `L.build_path` drapes each ribbon vertex on the LOWEST ground of its four cells, so on the plate side of the 10 cm step the ribbon sank under the plate's edge (z 6.15 under the 6.24 plate) for ~0.2 m
  and the plate's grass showed through the stones = the grass strip; (2) the plate hovers 10 cm over the fairway with no riser, so from the address camera it hides a 0.35 m band of fairway behind its edge: grass and stones jump by 0.35 m at the edge although the UVs were continuous in plan.
  Fix: `hole08_look.step_path_over_plate` cuts the ribbon along the plate outline (bmesh bisect on every outline edge, split along the seam), lifts the plate part onto the plate (+1.15 cm), leaves the rest on the fairway (+1.15 cm), joins them with a vertical riser (faces away from the camera; the plate part stops 2 mm inside the outline so a top-down ray meets the plate:
  the path stays <= 1.2 cm over the collider, gates PATH_UNDER_BALL / H_PATH_DENSE); the plate part's UVs and the TEE_BOX UVs are shifted by the hidden band (UV_tee(p) = UV_fairway(C + k (p - C)), k = (camera z - fairway z) / (camera z - plate z) = 1.0445). New gates (ray casts through the 900 x 1600 tee frame):
  TEE_SEAM_SEEN (grass texture jump across the edge <= 4 cm in 52 columns; round 5 build, same rays: 33 cm in V) and PATH_STEP_CONTINUOUS (0 rows without stones across the edge in 43 columns, round 5 build: 7-14 rows in every one; stone texture jump <= 4 cm). Round 5's TEE_SEAM_UV (plan-view UV equality) is retired: it demanded the UVs that cause the seen jump.
* **Arch shot (reviewer, medium: "a flat grey stone slab with hard straight edges still sits on the island next to the grass")**. The slab is the outcrop's camera-side wall: the library mesh ROCK_OUTCROP_A is a hull of 163 planar facets, one of them 2 m x 3 m (normal (0.68, -0.68, 0.27)), seen from the pad rim at 30 degrees; a camera search cannot lose it (every candidate sees >= 9 % of the frame as wall).
  Fix: `hole08_look.dress_outcrop` cuts the placed mesh horizontally at 0.75 / 1.5 / 2.3 / 3.2 m under its grass top, displaces the 87 cut vertices by a smooth noise field (-0.12 .. +0.34 m), puts turf (LK_ROUGH) on the upper 1.5 m, patchy turf / rock down to 3.2 m, rock below, and rewrites the box UVs with the props library's rule.
  Gate ARCH_SLAB_COVERED: the outcrop's bare rock in the lower 40 % of the arch frame <= 2 % (round 5 build, same rays: 22.7 %; now 1.6 %), whole frame <= 4 % (9.1 % -> 0.6 %). The arch camera and the outcrop's top ring (z, outline) are unchanged; the shrubs / flowers / tufts and vines on the outcrop are scattered again with the same seeds (the scatter region's faces changed), all plant / vine gates pass.
* Not mine / not cured (open): the tee plate's directional-light shadow on the fairway just beyond its edge (Unity casts it from the TEE_BOX mesh; the FBX cannot switch it off), the Game view itself (no Unity run by this agent), the blotchy Rough_C grass of the arch shot's foreground (texture, shared fixers), anything in the libs.

## Runtime facts the integrator needs

* Materials in the FBX are the LK_* contract names (LK_FAIRWAY, LK_GREEN, LK_ROUGH, LK_SAND, LK_CLIFF, LK_CLIFF_DARK, LK_ROCK, LK_ROCK_WET, LK_MASONRY, LK_PATH, LK_PLANTS, LK_WATER, LK_WATER_SHALLOW, LK_SURF,
  LK_FALL) plus MAT_FLAG / POLE / CUP / BALL for the gameplay placeholders; the FBX holds no texture reference (GolfLook loads the PNGs by name). The TEE_BOX carries LK_FAIRWAY with its own UVs (the fairway's, shifted by the hidden band); BUNKER_01_LIP carries LK_ROUGH; the capping ledges of the cliff skin carry LK_ROUGH; the outcrop wall carries LK_ROUGH + LK_ROCK.
* Only TERRAIN_NEEDLE, FAIRWAY, FAIRWAY_FIRSTCUT, GREEN, GREEN_APRON, TEE_BOX, BUNKER_01, BUNKER_01_LIP are collision-named (the same 8 meshes, vertex-identical to the baseline). Everything new is ROCK_ / PLANT_ / DRESS_ / WATER_.
* `DRESS_PATH_01` now has a vertical riser quad at the tee plate's front and rear edges (no collider: DRESS_ prefix).
* `WATER_FALL_00` (the waterfall sheet, LK_FALL, vertical, UV v runs down) and the 18 `WATER_SURF_nn` patches (vertex colour A = shore closeness) need `GolfArcade/GolfSurf`; `WATER_OCEAN` is one 2 km grid, `WATER_SHELF` the thin shelf.
* Unity colours of the water materials come from `GolfLook` by name (LK_WATER_SHALLOW Shallow (27,106,120)); the Blender colours are previews only.
* Mesh objects / datablocks and the triangle split: see `logs/h_numbers.json` (the biggest cost is the plants and vines; drop the 300 far tufts (`PL.scatter` seed 4 in hole08_look) first if the iPhone budget needs it).
"""
open(H + "/INSTALL.md", "w").write(txt)
print("INSTALL.md written; repo state:", state, "tris", tris, "fbx MB %.2f" % mb, "geometry hash", fp[0][2])
