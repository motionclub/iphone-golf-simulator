"""make_install_md.py - writes work/postcard-look/v2/hole09/INSTALL.md for the GRASS + SWAY pass, hole 9 repair round 0 (2026-10-05). System python3; reads final/*.log. Round 3's text lives in r8/before_r8/INSTALL.md."""
import hashlib, os, re, json
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
O = "work/postcard-look/v2/hole09"


def sha(p):
    return hashlib.sha256(open(os.path.join(R, p), 'rb').read()).hexdigest()


def size(p):
    return os.path.getsize(os.path.join(R, p))


def rd(p):
    return open(os.path.join(R, O, p), errors="replace").read()


def rx(log, pat, grp=1, default="?"):
    m = re.search(pat, log)
    return m.group(grp) if m else default


stage_blend, stage_fbx = f"{O}/stage/hole_09.blend", f"{O}/stage/hole_09.fbx"
cur_meta = "Unity/Assets/Resources/Course/hole_09.fbx.meta"
base_blend, base_fbx = "work/postcard-look/baseline/blender/hole_09.blend", "work/postcard-look/baseline/fbx/hole_09.fbx"
r3_blend, r3_fbx = f"{O}/r8/before_r8/stage_r7/hole_09.blend", f"{O}/r8/before_r8/stage_r7/hole_09.fbx"       # the round-3 stage = what the repo holds before this install
scripts = ["blender/scripts/hole09_build.py", "blender/scripts/hole09_look.py", "blender/scripts/hole09_masonry.py", "blender/scripts/hole09_stone.py", "blender/scripts/hole09_qa.py", "blender/scripts/hole09_design.py",
           "blender/scripts/postcard_look_lib.py", "blender/scripts/postcard_props_lib.py", "blender/scripts/postcard_lib.py", "blender/scripts/postcard_look_verify.py", "blender/scripts/golf_look_textures.py",
           f"{O}/tools/ruin_check.py", f"{O}/tools/tee_parallax_check.py", f"{O}/tools/grass_gates.py", f"{O}/tools/tuft_mask.py", f"{O}/tools/run_all_gates.sh", f"{O}/tools/run_final_pipeline.sh",
           f"{O}/tools/make_gates_txt.py", f"{O}/tools/make_install_md.py"]
meta_guid = open(os.path.join(R, cur_meta)).read().splitlines()[1]
bl = rd("final/build_final.log")
mm = re.search(r"HOLE09 stats: (\d+) objects, (\d+) meshes, (\d+) tris", bl)
n_mesh, n_tris = int(mm.group(2)), int(mm.group(3))
lvl = [l for l in rd("final/look_verify.log").splitlines() if l.startswith("GATE:")]
n_all = len(lvl)
gg = rd("final/grass_gates.log")
sway_txt = rx(rd("final/look_verify.log"), r"GATE: PLANT_SWAY_COLORS@fbx \w+ - (all \d+ unique PLANT_\S+ meshes)")
rcl = rd("final/ruin_check_blend.log")
zones = re.findall(r"\[hole09\] grass fringe (\w+): (\d+) tufts, (\d+) tris, (\d+) clumps \+ (\d+) singles, edge covered (\d+)/(\d+)", bl)
zline = "; ".join(f"{z[0]} {z[1]} tufts / {int(z[2]) / 1000:.1f}k tris ({z[3]} clumps + {z[4]} singles)" for z in zones)
chp = re.search(r"cheapen_tufts: \{'swapped': (\d+), 'kept': (\d+), 'tris_saved': (\d+)\}", bl)
fld = rx(bl, r"ruin scrub field: (\d+) tufts in (\d+) clumps", 1), rx(bl, r"ruin scrub field: (\d+) tufts in (\d+) clumps", 2)
wft = rx(bl, r"wall-foot tufts: (\d+) tufts")
skr = rx(bl, r"got a skirt of (\d+) ground-rooted tufts"), rx(bl, r"(\d+) bushes round the ruin")
fr_tot = rx(gg, r"GRASS_FRINGE_PRESENT@blend \w+ - (\d+) fringe tufts"), rx(gg, r"GRASS_TRI_BUDGET@blend \w+ - .*?all (\d+) PLANT_TUFT\* = (\d+) tris", 1), rx(gg, r"GRASS_TRI_BUDGET@blend \w+ - .*?all (\d+) PLANT_TUFT\* = (\d+) tris", 2)
tri_line = rx(gg, r"(GRASS_TRI_BUDGET@blend \w+ - [^\n]*)")
cov_line = rx(gg, r"coverage of the rough-edge strips[^\n]*?plus", 0)
tb = rd("final/tuft_mask_before.log")
ta = rd("final/tuft_mask_after.log")
_lm = json.load(open(os.path.join(R, O, "landmarks.json")))
_ru = [x for x in _lm["shots"] if x["name"] == "hole09_ruin"][0]
lm_pos, lm_look = _ru["pos"], _ru["look"]
tee = rd("final/tee_parallax.log")
mt = re.search(r"max ([\d.]+) m, mean ([\d.]+) m", tee)
planar_worst = rx(rcl, r"worst vertex distance from its own plane ([\d.]+) mm")
split_pairs, split_mism = rx(rcl, r"(\d+) pairs of adjacent polygons within 12 deg"), rx(rcl, r"stones: (\d+) have a UV mismatch")
bury = rx(rcl, r"(\d+) stones stand on the ground, (\d+) \((\d+)%\)", 3)
arch_cov = rx(rcl, r"masonry within 6 cm at (\d+) of 181")
n_stones = rx(rcl, r"RUIN_SUPPORTED PASS - (\d+) masonry stones")
share_low, share_high = rx(rcl, r"lowest LK_MASONRY share (\d+)%"), rx(rcl, r"highest LK_ROCK share (\d+)%")

txt = f"""# INSTALL - hole 9 "Split" look build, GRASS + SWAY pass (CONTINUE job phase 3, HOLE 9 REPAIR ROUND 0; staged 2026-10-05, NOTHING installed yet)

The staged build is in `{O}/stage/`. It was produced by `blender/scripts/hole09_build.py -- --out ...stage` (deterministic, see GATES_hole09.txt H_REPRODUCIBLE)
and exported with `postcard_look_lib.export_look_fbx` (not `postcard_lib.export_fbx`; colors_type LINEAR, so the sway vertex colours of every PLANT_ mesh arrive raw in Unity's `mesh.colors`). Install = copy exactly TWO files.
Run it only through the integrator's `run_proof.sh` (a reimport of a changed hole_09.fbx disturbs a running Unity batch).

## sha256 of the staged files (verify before copying)

```
{sha(stage_blend)}  {stage_blend}   ({size(stage_blend)} bytes)
{sha(stage_fbx)}  {stage_fbx}   ({size(stage_fbx)} bytes, {size(stage_fbx) / 1048576:.2f} MB, {n_mesh} mesh objects, {n_tris:,} triangles)
```
Same list in `{O}/final/install_sha256.txt` (that file also holds the sha of the existing `hole_09.fbx.meta`).
The repo holds the ROUND-3 stage before this install (blend `{sha(r3_blend)[:16]}..`, FBX `{sha(r3_fbx)[:16]}..`, kept in `{O}/r8/before_r8/stage_r7/`); the staged files were rebuilt on the libs / textures / verifier the shared fixers changed in this same round
(sha256 of every lib at the start of this round: `lib_sha_r8_start.txt`, at the final build: `final/script_sha256_at_final_build.txt`; the 31 Look PNG sha256 at the final build: `final/look_png_sha256_at_final_build.txt`).
The libs, textures, verifier and Unity files were NOT edited by this agent.

## What this round changed (hole scripts only: hole09_look.py, hole09_build.py docstring, hole09_masonry.py, hole09_stone.py + the tools in {O}/tools/)

Reviewer findings handled: (1) high, GRASS LIVELINESS + SWAY: "the near ground reads as a carpet; add the edge fringe; plants must carry sway data"; (2) medium, the ruin: "still a pile of straight-cut boxes ... the arch crown reads as two floating blocks"; (3) the low protected-files note is not ours.

**1. Sway data.** Every PLANT_* mesh (and every LK_PLANTS mesh without one) carries the sway vertex colours the new props library writes (R weight, G phase, B 0, A 1); the build only has to export with `export_look_fbx` (it does). Verified on the blend AND the FBX re-import by `postcard_look_verify.py 9`
(PLANT_SWAY_COLORS@blend / @fbx and PLANT_SWAY_CAPS@blend / @fbx: {sway_txt} carry them, root <= 0.05, tip > 0.6 for tuft / flower / agave, shrub / tree > 0.25, tuft cap 0.0591 yd <= 0.06 at 20 mph). The new tuft kinds (D, E, F tall, S, T fillers) are in the file; nothing static was added to the water / lava paths.

**2. Edge fringe** (`hole09_look.build_grass`, PL.scatter_fringe in zones). Clumps of 3-7 tall leaning tufts (lean <= 12 deg, 0.6-1.8 x height, +-6 % xy scale) along the rough edge of the fairway / green / tee and the cliff lips, never on a play surface / bunker / water, >= 1.1 m inside the lip (the hole's own gate wants 1.0 m),
>= 4 m (tee ball 1.5 m) from every still ball, >= 6 m from the pin, tops <= 0.503 m (0.55 yd) within 17.2 m of the centerline or 12 m of a ball. Zones (the camera sees the rough edge of the ribbon only from ~35 m ahead of the ball, so the tee zone starts at y 30 m): {zline}.
Green tufts (D / E / S) stand off the scrub polygon, olive / straw tufts (F / T) inside it. `{fr_tot[0]}` fringe tufts in all. Measured by `tools/grass_gates.py` (blend + FBX re-import): GRASS_FRINGE_PRESENT, GRASS_NOT_ON_PLAY_SURFACES, GRASS_NOT_ON_WATER, GRASS_BALL_CLEAR, GRASS_TRI_BUDGET all PASS ({cov_line.replace('plus', '').strip()}).
**Open scrub** (the ground of the ruin landmark frame is open ridge, not a rough edge): {fld[0]} olive tufts in {fld[1]} clumps whose centres are the ground points that project into the landmark camera (landmarks.json hole09_ruin), {wft} tufts at the foot of the ruin walls (>= 0.6 m from any masonry vertex), a skirt of {skr[0]} ground-rooted tufts round the {skr[1]} bushes nearest the ruin.
**Not done, measured:** `PL.tuftify_shrubs` / `tuftify_crowns` (tufts ON a shrub lump / a sea-stack crown): the hole's own H_NO_PLANT_ON_WATER wants every plant rooted on the ground (|origin z - ground| <= 6 cm; a crown tuft has a WATER lie under it) and the verifier's NO_PLANT_ON_WATER wants ground or a rock top within 0.5 m under the lowest blade (a shrub top is 0.7-0.9 m up, a crown blade overhangs the rim): both FAILED them (`r8/g1`, `r8/g2`), the gates stay as they are, the bushes get the ground skirt instead.
**What the stills can show:** the lower 60 % of the tee / approach address frames is the tee box / fairway within ~4 yd of the ball (camera 4.5 yd behind the ball, 2.4 yd up, 60 deg), where no tuft may stand: the fringe is visible on the far rough edges (upper third) there, and clearly on the ruin landmark. Blender-side proxy (NOT the Game-view GRASS_STILL_ALIVE): tuft pixels of the still cameras, round-3 stage -> now: `final/tuft_mask_before.log` / `tuft_mask_after.log`.

**3. Budget** ({tri_line.split(' - ', 1)[1][:260] if ' - ' in tri_line else tri_line}). The fringe was paid for by: `PL.cheapen_tufts(near_m = 25)`: {chp.group(1) if chp else '?'} old 117-triangle tufts -> 36-triangle fillers ({chp.group(3) if chp else '?'} triangles saved, {chp.group(2) if chp else '?'} kept near the balls); ridge shrubs 116 -> 76 (mix C:A 5:1 -> 2:3; the thickets are
18 centres instead of 30 so H_RIDGE_THICKETS still holds), outer shrubs 30 -> 20, ridge stones 56 -> 44. (`SKIN_STEP_M` does nothing: the strata columns follow the TERRAIN outline vertices, closer than 2.4 m apart; a larger step was tried and measured identical, so it is unchanged.) Triangles {n_tris:,} (limit 250,000; before this pass 247,439), FBX {size(stage_fbx) / 1048576:.2f} MB (limit 20), no animation.

**4. The ruin** (`hole09_masonry.py`, `hole09_stone.py`; findings: straight-cut boxes, flat slabs, the two floating arch halves). Stones are 15 % bigger (0.85-1.65 m, bed levels 0.24-0.46 m: {n_stones} masonry stones, was 389), every wall stone has its four VERTICAL edges chamfered 5-12 cm (the tops stop being rectangles) plus 2-6 cm arris bevels and 6-21 cm corner chips
(bottom corners keep the old 5-17 cm), up to 23 faces; wall depth 0.78-1.0 of the wall (more relief). Side planes may not make a near-coplanar (< 14 deg) pair with another side face (`hole09_stone.bad_pairs`: one such pair got two different brick windows in the first try = RUIN_NO_UV_SPLIT, now {split_pairs} near-coplanar pairs, {split_mism} mismatching).
The arch keeps all 11 wedges: the CROWN WEDGE HAS SLIPPED 13 cm toward the opening (a radial slide keeps both side planes in face contact), so there are no two floating halves with a gap; its inner corners are knocked off by the fall; the rubble heap stays under it. Ruin gates (tools/ruin_check.py, blend AND FBX re-import): 13 of 13 PASS (RUIN_BASE_BURIED {bury} %, RUIN_ARCH_SEATED masonry within 6 cm at {arch_cov} of 181 angles, RUIN_PLANAR_FACES worst {planar_worst} mm, LK_MASONRY share >= {share_low} %, LK_ROCK <= {share_high} %).
`landmarks.json` is regenerated (`tools/make_landmarks.py`): the ruin camera is ({lm_pos[0]}, {lm_pos[1]}, {lm_pos[2]}) / look ({lm_look[0]}, {lm_look[1]}, {lm_look[2]}); the tee and approach shots are unchanged. TEE_EDGE_UV_CONTINUOUS (round 3's tee parallax fix) still PASS (max {mt.group(1) if mt else '?'} m).

**5. Gates.** postcard_look_verify.py 9: {n_all} lines at both stages, RESULT ALL PASS; hole09_qa.py: 27 / 27 PASS (blend + FBX re-import); postcard_verify.py: FAIL only MATERIALS@blend / @fbx and FBX_BUDGET@fbx, by design (old MAT_* allow-list, old 4 MB / 150k budget; superseded by LOOK_CONTRACT section 3 / H_BUDGET);
postcard_emit_cs.py --check: no drift; guards.sh 7 / 7; hole09_design.py byte-identical to `hole09_design.py.at_start`. Blender previews (`previews/`, `r8/d*_views/`) are NOT Game-view proof: the Game-view stills must be re-shot with `landmarks.json` by the integrator.

## 0. Preconditions (stop if one is false)

```
cd /Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
S=work/postcard-look/v2/hole09/stage
# the repo hole_09 files are one of known states (this job never writes them):
shasum -a 256 blender/hole_09.blend Unity/Assets/Resources/Course/hole_09.fbx
#   (a) the ROUND-3 STAGE (installed by the integrator; this round replaces it):
#       {sha(r3_blend)}  blender/hole_09.blend        (= {r3_blend})
#       {sha(r3_fbx)}  Unity/Assets/Resources/Course/hole_09.fbx   (= {r3_fbx})
#   (b) or the flat baseline:  {sha(base_blend)}  blender/hole_09.blend  /  {sha(base_fbx)}  hole_09.fbx
# the staged files are the ones that were gated:
echo "{sha(stage_blend)}  $S/hole_09.blend" | shasum -a 256 -c -
echo "{sha(stage_fbx)}  $S/hole_09.fbx" | shasum -a 256 -c -
# the scoring + hole 7 guards (must print 7 PASS):
bash work/postcard-look/guards.sh
```

## 1. Install (copy hole_09.blend and hole_09.fbx ONLY)

```
cp $S/hole_09.blend blender/hole_09.blend
cp $S/hole_09.fbx   Unity/Assets/Resources/Course/hole_09.fbx
```
**NEVER overwrite `Unity/Assets/Resources/Course/hole_09.fbx.meta`.** It holds the GUID ({meta_guid}) and the importer settings
(`isReadable: 1`, `tangentImportMode: 3`, `materialName: 0`, `normalImportMode: 0`); the staged folder also contains a `hole_09.fbx.meta` with a FRESH random GUID: do not copy it. Also not copied: `stage/hole_09.blend1` (Blender's backup),
`stage/hole_09_overview.png` (a preview; copy it to `blender/previews/hole_09_overview.png` only to refresh the overview), `stage_repro/` (the reproducibility twin). The existing `.meta` sha256 must stay `{sha(cur_meta)}`.
The FBX must keep the mesh colours: the `.meta` has no `importVertexColors` switch to flip (Unity imports FBX vertex colours into `mesh.colors` by default); the Unity owner checks `Mesh.colors` of a PLANT_TUFT_D instance after the import (R 0 at the root, 1.0 at the tip).

## 2. Verify after the copy (Blender headless, no Unity needed)

```
B=/Applications/Blender.app/Contents/MacOS/Blender
$B -b --factory-startup --python blender/scripts/postcard_look_verify.py -- 9          # repo blend + FBX; expect RESULT: ALL PASS ({n_all} gate lines; LOOK_STILLS_TEXTURED is SKIPPED until Game-view stills exist, then run with --require-stills)
$B -b blender/hole_09.blend --python blender/scripts/postcard_verify.py -- hole09_design   # FAIL only MATERIALS@blend/@fbx + FBX_BUDGET@fbx, by design
python3 blender/scripts/postcard_emit_cs.py --check Unity/Assets/Scripts/Course/Hole.cs      # HOLE_CS_MATCHES_DESIGN PASS
bash work/postcard-look/guards.sh                                                          # 7 PASS
$B -b --factory-startup --python blender/scripts/hole09_qa.py -- --blend blender/hole_09.blend --fbx Unity/Assets/Resources/Course/hole_09.fbx   # HOLE09_QA: 27 gates, 0 FAIL
$B -b --factory-startup --python {O}/tools/ruin_check.py -- --blend blender/hole_09.blend     # RUIN_CHECK: 0 FAIL of 13
$B -b --factory-startup --python {O}/tools/grass_gates.py -- --blend blender/hole_09.blend --fbx Unity/Assets/Resources/Course/hole_09.fbx   # GRASS_GATES: 8 gates, 0 FAIL
$B -b blender/hole_09.blend --python {O}/tools/tee_parallax_check.py                         # TEE_EDGE_UV_CONTINUOUS PASS
shasum -a 256 blender/hole_09.blend Unity/Assets/Resources/Course/hole_09.fbx              # = the two staged sha256 above
shasum -a 256 Unity/Assets/Resources/Course/hole_09.fbx.meta                               # unchanged
```
Then (Unity owner, through work/postcard-look/heavy.sh): `PostcardImportCheck`, `GolfLookSmoke`, the sway frame pairs, and the stills with `GOLF_STILLS_CFG=work/postcard-look/v2/hole09/landmarks.json` -> `ArtDir/screenshots/golf_postcards/look/`
(shots hole09_tee, hole09_approach, hole09_ruin; the `extra_previews` key is ignored by the tool). Expected: every hole 9 ground / rock / cliff / plant material is an `LK_` name (`LK_PLANTS` = ONE shared material, which GolfLook maps to GolfArcade/GolfPlants);
the ruin / arch meshes have TWO material slots (LK_MASONRY, LK_ROCK; non-colliding); only TERRAIN, FAIRWAY, GREEN, TEE_BOX, BUNKER get colliders (every new object is ROCK_ / PLANT_ / DRESS_ / WATER_).

## 3. Rebuild without staging (same geometry, writes the repo paths = the install)

```
$B -b --factory-startup --python blender/scripts/hole09_build.py            # no --out: blender/hole_09.blend, blender/previews/hole_09_overview.png, Unity/.../hole_09.fbx
```
(`hole_09.fbx.meta` is only created when it does not exist, so the existing one is kept.) The blend and the FBX re-import are geometry-identical to the staged ones (gate H_REPRODUCIBLE); the FBX bytes differ run to run (header timestamp, zlib streams).
Everything the staged build needs is deterministic: `PL.scatter_fringe` / `scatter` / `cheapen_tufts` (crc32 seeds) and the masonry (seeded `random.Random`).

## 4. Rollback

```
cp {r3_blend} blender/hole_09.blend            # the round-3 stage, sha256 {sha(r3_blend)}   (the state the repo is in before this install)
cp {r3_fbx} Unity/Assets/Resources/Course/hole_09.fbx   # sha256 {sha(r3_fbx)}
cp {base_blend} blender/hole_09.blend            # sha256 {sha(base_blend)}   (the flat afternoon baseline)
cp {base_fbx} Unity/Assets/Resources/Course/hole_09.fbx   # sha256 {sha(base_fbx)}
```
The scripts at the start of this round: `{O}/r8/before_r8/*.at_start` (hole09_build / look / masonry / stone / qa / design) and `*.pre_ruin` (masonry / stone before the ruin change); round 3's INSTALL.md / GATES_hole09.txt / landmarks.json: `{O}/r8/before_r8/`.

## Files this job owns / changed (nothing else was touched)

```
{chr(10).join(sha(s) + '  ' + s for s in scripts)}
```
`hole09_design.py` is byte-identical to its start-of-job copy (`{O}/hole09_design.py.at_start`; `postcard_emit_cs.py --check` = no drift), `postcard_lib.py`, both libraries, the textures, the verifier and every Unity file were not edited by this agent
(their sha256 at the start of this round: `{O}/lib_sha_r8_start.txt`; library behaviours worked around in the hole scripts: `{O}/LIB_BUGS.md`).
"""
open(os.path.join(R, O, "INSTALL.md"), "w").write(txt)
print("INSTALL.md written", len(txt))
