"""Regenerates INSTALL.md (round 8) from the logs of the last run_all.sh (hashes, triangle counts, gate counts, geometry hash). python3 write_install_r8.py"""
import re, os, hashlib, json
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
H = R + "/work/postcard-look/v2/hole08"
L = H + "/logs/"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def rd(p):
    return open(p).read()


stage = {ln.split()[1]: ln.split()[0] for ln in rd(L + "stage_sha256.txt").splitlines() if len(ln.split()) == 2 and len(ln.split()[0]) == 64}
fp = [ln.split() for ln in rd(L + "reproducible.txt").splitlines() if ln.startswith("FP")]
build = rd(L + "build.log")
tris = int(re.search(r"stats: \d+ objects, \d+ meshes, (\d+) triangles", build).group(1))
tris_before = int(re.search(r"stats: \d+ objects, \d+ meshes, (\d+) triangles", rd(H + "/r8/before_build.log")).group(1))
mb = os.path.getsize(H + "/stage/hole_08.fbx") / 1048576
for nm in ("hole_08.blend", "hole_08.fbx"):
    assert sha(H + "/stage/" + nm) == stage[nm], f"{nm} changed since logs/stage_sha256.txt"
base = {nm: sha(p) for nm, p in dict(blend=R + "/blender/hole_08.blend", fbx=R + "/Unity/Assets/Resources/Course/hole_08.fbx", meta=R + "/Unity/Assets/Resources/Course/hole_08.fbx.meta").items()}
bl = {nm: sha(R + "/work/postcard-look/baseline/" + p) for nm, p in dict(blend="blender/hole_08.blend", fbx="fbx/hole_08.fbx").items()}
r7 = {"blend": sha(H + "/r8/stage_r7/hole_08.blend"), "fbx": sha(H + "/r8/stage_r7/hole_08.fbx")}
state = ("byte-identical to the round-7 build (r8/stage_r7: the one installed at 04:19 on 2026-10-05)" if base["blend"] == r7["blend"] and base["fbx"] == r7["fbx"] else
         ("ALREADY this round-8 build (somebody installed it)" if base["blend"] == stage["hole_08.blend"] and base["fbx"] == stage["hole_08.fbx"] else
          "NEITHER the round-7 build nor this build (somebody changed them: compare before copying)"))
gates_md = rd(H + "/GATES_hole08.md")
n_gate = len(re.findall(r"^GATE: ", gates_md, re.M))
n_pass = len(re.findall(r"^GATE: \S+ PASS", gates_md, re.M))
bl_log = rd(L + "build.log")
n_build = len(re.findall(r"^GATE: \S+ PASS", bl_log, re.M))
n_build_all = len(re.findall(r"^GATE: ", bl_log, re.M))
vl = rd(L + "verify_look.log")
n_v = len(re.findall(r"^GATE: \S+ PASS", vl, re.M))
n_v_all = len(re.findall(r"^GATE: ", vl, re.M))
neg = rd(L + "negctl.txt").strip().splitlines()[-1]
HN = json.load(open(L + "h_numbers.json"))
tg = HN["tuft_groups"]
FF = json.load(open(L + "fbx_fold.json"))
FF0 = json.load(open(H + "/r8/fbx_fold_before.json"))
libs = rd(L + "lib_sha_final.txt").splitlines()[1:]
txt = f"""# Hole 8 Needle: install (NOT done: staged only) -- round 8 (repair round 0 of the GRASS LIVELINESS + GENTLE SWAY add-on, 2026-10-05)

Staged build (`run_all.sh`; sha256 of the libs / verifier / texture generator in `logs/lib_sha_final.txt`, the Look PNGs in `logs/look_png_sha_final.txt`; the start-of-round-8 state: `r8/lib_sha_at_start.txt`, `r8/look_png_sha_at_start.txt`).
Nothing in the repo was written by this round: `blender/hole_08.blend`, `Unity/Assets/Resources/Course/hole_08.fbx` and `hole_08.fbx.meta` are {state} (sha below).

## sha256 of the staged files (`stage/`, `logs/stage_sha256.txt`)

```
{stage['hole_08.blend']}  stage/hole_08.blend
{stage['hole_08.fbx']}  stage/hole_08.fbx          ({mb:.2f} MB, {tris:,} triangles in the export set, exported with postcard_look_lib.export_look_fbx)
{stage['hole_08.fbx.meta']}  stage/hole_08.fbx.meta     (staging copy of the hole 7 meta with a fresh guid: DO NOT COPY IT)
```
Geometry hash of the build (names + 0.1 mm world vertices of every mesh): `{fp[0][2]}`, identical in {len(fp)} builds (`logs/reproducible.txt`). The .blend / .fbx bytes themselves carry timestamps, so a rebuild changes their sha but not the geometry hash.

Repo files today: `blender/hole_08.blend` {base['blend'][:8]}..., `hole_08.fbx` {base['fbx'][:8]}..., `hole_08.fbx.meta` {base['meta'][:8]}... (the meta holds the GUID and isReadable 1 / tangentImportMode 3: never overwritten).
Round-7 build (what is installed now): `r8/stage_r7/hole_08.blend` {r7['blend'][:8]}..., `hole_08.fbx` {r7['fbx'][:8]}.... Baseline (flat afternoon mesh): `work/postcard-look/baseline/blender/hole_08.blend` {bl['blend'][:8]}..., `baseline/fbx/hole_08.fbx` {bl['fbx'][:8]}....

## Install (copy the .blend and the .fbx ONLY)

```bash
cd {R}
S=work/postcard-look/v2/hole08/stage
shasum -a 256 $S/hole_08.blend $S/hole_08.fbx                                  # must equal the two lines above
cp $S/hole_08.blend blender/hole_08.blend
cp $S/hole_08.fbx   Unity/Assets/Resources/Course/hole_08.fbx
#   do NOT touch Unity/Assets/Resources/Course/hole_08.fbx.meta (and not hole_07.*, not hole_09 / hole_10 files)
```
Unity reimports the FBX on focus (the meta keeps the old GUID, so `Resources.Load("Course/hole_08")` and every reference stay valid). `blender/previews/hole_08_overview.png` is not part of the install (the staged overview is `stage/hole_08_overview.png`).

## Rollback

```bash
cp work/postcard-look/v2/hole08/r8/stage_r7/hole_08.blend blender/hole_08.blend      # back to the round-7 build (no fringe)
cp work/postcard-look/v2/hole08/r8/stage_r7/hole_08.fbx   Unity/Assets/Resources/Course/hole_08.fbx
# or all the way to the flat baseline:
cp work/postcard-look/baseline/blender/hole_08.blend blender/hole_08.blend
cp work/postcard-look/baseline/fbx/hole_08.fbx       Unity/Assets/Resources/Course/hole_08.fbx
```

## After the copy (Unity side, through work/postcard-look/heavy.sh)

```bash
work/postcard-look/v2/runtime/run_importcheck.sh h8      # GROUND_ALBEDO_AND_NORMAL / NO_FLAT_POSTCARD_GROUND stay PASS for hole 8; ground-height / lie / marker lines stay PASS
work/postcard-look/v2/runtime/run_smoke.sh h8
work/postcard-look/v2/runtime/run_stills.sh h8 ArtDir/screenshots/golf_postcards/look GOLF_STILLS_CFG=$PWD/work/postcard-look/v2/hole08/landmarks.json
#   landmarks.json holds hole 8's shots only (the cfg REPLACES the default list): hole08_tee, hole08_approach, hole08_arch (the landmark; the camera is PINNED to the rounds 5-7 camera: landmarks.json is byte-equal in content to the round-7 file, r8/landmarks_r7.json),
#   hole08_pathball (optional extra: ball position (-1, 11) on the straightened path). Merge it with the hole 9 / 10 cfgs for one run, or run it alone.
#   The sway stills (SWAY_FRAME_PAIR / SWAY_STILLS_DETERMINISTIC) and GRASS_STILL_ALIVE are the integrator's Game-view runs (work/postcard-look/v2/sway/run_swaystills.sh).
```
Rebuild without installing: `Blender -b --factory-startup --python blender/scripts/hole08_build.py -- --out <dir>` (never run it WITHOUT --out until the install is meant to happen: without --out it writes `blender/hole_08.blend`, `blender/previews/hole_08_overview.png` and `Unity/.../hole_08.fbx`).
The build itself takes about 35 s. Everything (build, verifier on blend + FBX re-import, relocated-copy texture check, postcard_verify, postcard_check, the baseline comparison, frame variation, dense path height, landmarks, FBX fold, frame classes, previews, negative controls, reproducibility, guards): `work/postcard-look/v2/hole08/run_all.sh` (about 15 minutes), summary `GATES_hole08.md`.

## What round 8 changed (the reviewer findings of the add-on that are the hole's; no vertex of a scoring mesh moved: H_PLAY_UNCHANGED)

Libs / textures under the hole changed first (the shared fixers, BEFORE this agent: sway colours on every PLANT_* mesh, the tuft library D / E / F / S / T, `scatter_fringe`, `cheapen_tufts`, `attach_vines`, `tuftify_*`, `export_look_fbx` keeping the colours; `r8/lib_sha_at_start.txt` vs `r7/lib_sha_r6.txt`). Rebuilt on them, then the hole's own changes (`hole08_look.py`; `hole08_build.py`: docstring only; `hole08_design.py` untouched, `postcard_emit_cs.py --check` no drift):

* **Edge fringe (reviewer, high: "the near ground reads as a carpet; add the edge fringe; plants must carry sway data")**. `PL.scatter_fringe(D, kinds tall D / E + fill S, tri_budget 52,000, seed 11)` after every other scatter: {HN['tuft_groups']['fringe']['count']} tufts in clumps of 3-7 along the rough edge of the pads and the cliff lips (lean <= 12 degrees, 0.6-1.8 x the library tuft, tops <= 0.55 yd = 0.503 m near the ball corridor, which on these 30 yd pads is the whole pad), never on a play surface / the sea / within 4 m of a shot ball (1.5 m at the tee ball) / within 6 m of the pin.
  The old 117-triangle carpet pays for it: `PL.cheapen_tufts(D, near_m=14)` swaps every old A / B tuft farther than 14 m from a shot ball for the 36-triangle filler S / T (the library default of 60 m would swap nothing here: all three pads are within 60 m of a shot ball). Triangles in the export set **{tris_before:,} (this build's libs, no fringe) -> {tris:,}** (cap 250,000; the installed round-7 build had 195,500).
  Island clumps `hole08_look.outcrop_fringe` (the arch island is not a play surface: 20+ clumps of the same tufts on its grass top, rim band + pier / block bases) and the tufts on the sea-stack crowns (`hole08_look.crown_tufts`: PL.tuftify_crowns candidates pruned by the verifier's own support rule, see LIB_BUGS.md). Gates GRASS_FRINGE_PRESENT / _NOT_ON_PLAY_SURFACES / _NOT_ON_WATER / _BALL_CLEAR / _TRI_BUDGET, GRASS_OUTCROP_FRINGE, CROWN_TUFTS (hole08_look.look_gates, run in the build; independent checks in the verifier: NO_PLANT_ON_WATER, PLANT_SWAY_COLORS, PLANT_SWAY_CAPS on the blend AND the FBX re-import).
  **What the fringe cannot do** (measured, GRASS_FRAME_COVERAGE_BLENDER): the lower 60 % of the tee and approach frames is 100 % tee box / fairway / stone path / ball. The brief forbids a tuft there (never on Fairway / Green / Bunker / Tee, never within 4 m of a shot ball), and the stone paths lie ON the fairway, so the path edge has no rough to stand on (edge samples play / path / lip = 106 / 0 / 51, every sample covered). The fringe shows at the pad rims (frame edges and far end of the tee / approach frames), on the sea-stack crowns on the horizon and in the arch frame. The near ground of the tee / approach frames stays the textures' job.
* **Arch island fold (reviewer, medium: "a hard polygonal fold in the lower third of the arch shot, a 30-35 % step with no AO feather")**. Cause: the flat grass top meets the steep turf bank in a flat-shaded 60-75 degree crease (the library hull's facets, `set_sharp_from_angle(13)`), one pixel row wide. Fix in `dress_outcrop`: the rim edges are bevelled ({'0.5 m, 4 segments'}) into a rounded shoulder and every LK_ROUGH face below the flat top gets smooth custom normals (angle-weighted over the turf faces; the flat top keeps its exact up normal). Gate ARCH_FOLD_SOFT (ray casts over the reviewer's region, shading normals as Unity will light them, FBX re-import too): largest normal step between rows 4 px apart **{FF0['max_deg']:.1f} deg -> {FF['max_deg']:.1f} deg** (round-7 FBX / this FBX), largest |N.sun| step **{FF0['max_lambert']:.2f} -> {FF['max_lambert']:.2f}**. The custom normals survive the exporter (the FBX re-import measures the same numbers); Unity imports normals from the file (`normalImportMode 0` in the meta). The left strip (a grey slab): bare rock 31 % -> 0 % (ARCH_LEFT_STRIP_COVERED).
* **Vines touch the wall (libs hand-off)**. `PL.attach_vines(D)` after the last vine (cliff-skin and arch vines); the outcrop vines are hung with the root ON the wall at its own height and tilted about the root to follow the wall's slope (plumb vines either hung up to 0.9 m off the rock at the root or sank into the bulge). Gate VINE_ROOT_GAP: every root within 5 cm of a surface.
* **Arch camera pinned**. A re-run of `make_landmarks.py`'s composition search now picks another camera (x -13.1, fov 66) because the rim shoulder and the clumps changed the frame; the reviewers measured the old one, so `make_landmarks.py --pin` keeps `hole08_look.ARCH_CAM` (landmarks.json unchanged in content) and computes the composition numbers for it (lip 0 %, skin 4.1 %, flank 0.6 %, top 22.8 %).
* Reviewer low ("the tee and approach foreground island is bare grass and path with no shrubs, flowers or ruins"): the foreground is the fairway; the brief keeps plants off it. Not changed beyond the pad fringe (see above): shrubs / flowers on the rough band were already placed by the earlier rounds.

Numbers: **{n_pass} of {n_gate} hole gate lines PASS** (`GATES_hole08.md`), build {n_build} / {n_build_all}, `postcard_look_verify` {n_v} / {n_v_all} on the blend + the FBX re-import, {neg.split('mutations caught')[0].replace('NEGCTL SUMMARY ', '')} negative controls caught, geometry hash `{fp[0][2]}` identical in {len(fp)} builds, guards 7 / 7.
Tufts by group (blend, bbox height m): old carpet {tg['carpet']['count']} (median {tg['carpet']['median_m']:.2f}, max {tg['carpet']['max_m']:.2f}), pad fringe {tg['fringe']['count']} (median {tg['fringe']['median_m']:.2f}, max {tg['fringe']['max_m']:.2f}), island clumps {tg['outcrop_fringe']['count']} (max {tg['outcrop_fringe'].get('max_m', 0):.2f}), crown tufts {tg['crown']['count']} (max {tg['crown'].get('max_m', 0):.2f}).
Blender previews (NOT Game view): `previews/sheet_round8_full.jpg` (round 7 vs round 8 from the tee / approach / arch cameras), `sheet_round8_arch_fold.jpg`, `sheet_round8_aerial.jpg`, `sheet_round8_fringe.jpg`, `previews/fringe/top_overlay.png` (the fringe positions on a top view).
Not mine / open: the Unity Game view of this build (no Unity run by this agent: the integrator's stills are the proof, including GRASS_STILL_ALIVE and the SWAY_* frame pairs); the tee plate's directional shadow beyond its edge; the sky-fold hairline of the arch still; the grass hue under the golf key light (textures + runtime).

## Runtime facts the integrator needs

* Materials in the FBX are the LK_* contract names (LK_FAIRWAY, LK_GREEN, LK_ROUGH, LK_SAND, LK_CLIFF, LK_CLIFF_DARK, LK_ROCK, LK_ROCK_WET, LK_MASONRY, LK_PATH, LK_PLANTS, LK_WATER, LK_WATER_SHALLOW, LK_SURF, LK_FALL) plus MAT_FLAG / POLE / CUP / BALL; the FBX holds no texture reference (GolfLook loads the PNGs by name).
* Every PLANT_* object (tufts D / E / S / A / B, shrubs, flowers, vines, the new tufts on the crowns and the island) shares ONE `LK_PLANTS` material and carries the colour attribute `Col` (R sway weight, G phase, B 0, A 1; raw, LINEAR export) that `GolfArcade/GolfPlants` reads from `mesh.colors`. Meshes WITHOUT sway data are static (B = 1 in Unity's default colour). The sea-stack crowns (LK_PLANTS faces of the ROCK_ meshes) are static (R 0).
* Only TERRAIN_NEEDLE, FAIRWAY, FAIRWAY_FIRSTCUT, GREEN, GREEN_APRON, TEE_BOX, BUNKER_01, BUNKER_01_LIP are collision-named (the same 8 meshes, vertex-identical to the baseline). Everything new is ROCK_ / PLANT_ / DRESS_ / WATER_.
* The outcrop mesh (`ROCK_OUTCROP_A`) carries custom split normals (Unity: `normalImportMode 0` keeps them; the hole FBX meta is never overwritten).
* `DRESS_PATH_01` has a vertical riser quad at the tee plate's front and rear edges (no collider: DRESS_ prefix). `WATER_FALL_00` and the 18 `WATER_SURF_nn` patches need `GolfArcade/GolfSurf`.
* Mesh objects / datablocks and the triangle split: see `logs/h_numbers.json`; if the iPhone budget needs triangles back, drop the island clumps (`OUTCROP_FRINGE_CLUMPS`) or the crown tufts (`CROWN_TUFTS_ON`) first, then lower `FRINGE_TRI_BUDGET`.
"""
open(H + "/INSTALL.md", "w").write(txt)
print("INSTALL.md written; repo state:", state, "tris", tris, "fbx MB %.2f" % mb, "geometry hash", fp[0][2], "gates", n_pass, "/", n_gate)
