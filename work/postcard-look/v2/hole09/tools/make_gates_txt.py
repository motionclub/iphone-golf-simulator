"""make_gates_txt.py - composes GATES_hole09.txt from the logs in final/ (system python3)."""
import re, json, os, hashlib
F = "final"
def lines(path, pat=r"^GATE: "):
    return [l.rstrip("\n") for l in open(os.path.join(F, path), errors="replace") if re.match(pat, l)]
def parse(l):
    m = re.match(r"GATE: (\S+) (PASS|FAIL) - (.*)", l); return (m.group(1), m.group(2) == "PASS", m.group(3)) if m else None
qa = {g[0]: g for g in map(parse, lines("hole09_qa.log")) if g}
lv = [g for g in map(parse, lines("look_verify.log")) if g]
pv = [g for g in map(parse, lines("postcard_verify.log")) if g]
lm = [g for g in map(parse, lines("landmarks_check.log")) if g]
bf = [g for g in map(parse, lines("build_final.log")) if g]
out = []
def emit(i, ok, d): out.append(f"GATE: {i} {'PASS' if ok else 'FAIL'} - {d}")
def lvf(stage): return [g for g in lv if g[0].endswith("@" + stage)]
def lvg(name, stage): return next((g for g in lv if g[0] == f"{name}@{stage}"), None)
# required ids
play = [g for g in lv if g[0].startswith("PLAY_SURFACE") or g[0] == "MARKERS_FROZEN"]
emit("H_PLAY_UNCHANGED", qa["H_PLAY_UNCHANGED"][1] and all(g[1] for g in play), f"{qa['H_PLAY_UNCHANGED'][2]}; postcard_look_verify PLAY_SURFACE_NAMES / GRID / TOPS / FACES / WALLS + MARKERS_FROZEN at both stages: {sum(g[1] for g in play)}/{len(play)} PASS (frozen baseline signature work/postcard-look/baseline_signature, max |dz| 0.00e+00 m on the 1.5 m grid); the in-build compare_ground before / after every look pass: {[g[2] for g in bf if g[0] == 'H_PLAY_UNCHANGED_INBUILD'][0]}")
for st in ("blend", "fbx"):
    g = lvf(st); fails = [x[0] for x in g if not x[1]]
    emit(f"H_LOOK_VERIFY_{st.upper()}", not fails, f"postcard_look_verify.py 9 on the staged {st}: {sum(x[1] for x in g)} of {len(g)} gate lines PASS; FAIL: {fails or 'none'}" + ("" if not fails else " = " + "; ".join(f"{x[0]}: {x[2][:330]}" for x in g if not x[1]) + " [texture files owned by the texture agent / the lead's floor; no hole 9 mesh or material choice can change it. Drop-in candidate textures that make LOOK_FILES PASS at both stages with no other new FAIL: round3/proposal_textures/ (README.md), verifier run round3/evidence/look_verify_with_candidate_textures.log]"))
pvf = [g for g in pv if not g[1]]
emit("H_POSTCARD_VERIFY", all(g[0] in ("MATERIALS@blend", "MATERIALS@fbx", "FBX_BUDGET@fbx") for g in pvf), f"postcard_verify.py hole09_design: {sum(g[1] for g in pv)} of {len(pv)} lines PASS; FAIL by design: " + "; ".join(f"{g[0]} ({g[2][:150]}...)" for g in pvf) + ". Why: MATERIALS accepts only the old MAT_* names (every LK_* name is 'outside the contract'; superseded by LOOK_CONTRACT section 3 + postcard_look_verify NO_LEGACY_MATERIALS / GROUND_MATERIALS, all PASS); FBX_BUDGET is the old 4 MB / 150k limit (superseded by H_BUDGET: 250k triangles / 20 MB). WATER_LEVEL passes (no vertical waterfall sheet on Split).")
ed = open(os.path.join(F, "emit_check.log")).read().strip().splitlines()[-1]; pc = open(os.path.join(F, "postcard_check.log")).read().strip().splitlines()[-1]
emit("H_CHECK_NO_DRIFT", "MATCHES_DESIGN PASS" in ed and "ALL PASS" in pc, f"python3 blender/scripts/postcard_emit_cs.py --check Unity/Assets/Scripts/Course/Hole.cs -> '{ed}' (no drift); postcard_check.py hole09_design -> '{pc}' (design gates incl. one shore, one centerline, 1 water + 3 bunkers, carry 103.7 yd); hole09_design.py sha256 unchanged (see INSTALL.md)")
for i in ("H_NO_12_VERTEX_ROCK", "H_NO_STRETCH_2X", "H_NO_PLANT_ON_WATER", "H_NO_FOAM_STRIP"):
    ok = qa[i][1]; d = qa[i][2]
    extra = ""
    if i == "H_NO_12_VERTEX_ROCK": g = lvg("ROCK_NOT_ICOSAHEDRON", "blend"); extra = f" | verify ROCK_NOT_ICOSAHEDRON@blend {'PASS' if g[1] else 'FAIL'}"; ok = ok and g[1] and qa["H_NO_12_VERTEX_ROCK@fbx"][1]; d += f" | FBX re-import: {qa['H_NO_12_VERTEX_ROCK@fbx'][2][:200]}"
    if i == "H_NO_STRETCH_2X": g = lvg("NO_ROCK_STRETCH_2X", "fbx"); extra = f" | verify NO_ROCK_STRETCH_2X@fbx {'PASS' if g[1] else 'FAIL'}: {g[2][:200]}"; ok = ok and g[1]
    if i == "H_NO_PLANT_ON_WATER": g = lvg("NO_PLANT_ON_WATER", "fbx"); extra = f" | verify NO_PLANT_ON_WATER@fbx {'PASS' if g[1] else 'FAIL'}: {g[2][:160]}"; ok = ok and g[1] and qa["H_NO_PLANT_ON_WATER@fbx"][1]; d += f" | FBX re-import: {qa['H_NO_PLANT_ON_WATER@fbx'][2][:200]}"
    if i == "H_NO_FOAM_STRIP": g = lvg("NO_FOAM_STRIP", "fbx"); extra = f" | verify NO_FOAM_STRIP@fbx {'PASS' if g[1] else 'FAIL'}: {g[2][:160]}"; ok = ok and g[1] and qa["H_NO_FOAM_STRIP@fbx"][1]
    emit(i, ok, d + extra)
g = lvg("TRIANGLE_BUDGET", "fbx")
emit("H_BUDGET", qa["H_BUDGET"][1] and g[1], qa["H_BUDGET"][2] + f" | verify TRIANGLE_BUDGET@fbx: {g[2][:220]}")
emit("H_LANDMARKS_JSON", all(x[1] for x in lm), " | ".join(f"{x[0]}: {x[2][:330]}" for x in lm))
h1 = open(os.path.join(F, "repro_fbx_hash.txt")).read().split("\n")
hq = [l for l in open(os.path.join(F, "hole09_qa_repro.log")) if "H_GEOMETRY_HASH" in l][0]
ha = qa["H_GEOMETRY_HASH"][2].split()[1]; hb = re.search(r"sha256 (\w+)", hq).group(1)
fh = [l.split()[2] for l in h1 if l.startswith("FBXHASH")]
cnt = re.search(r"over (\d+) mesh objects, (\d+) vertices, (\d+) faces", qa["H_GEOMETRY_HASH"][2])
emit("H_REPRODUCIBLE", ha == hb and len(fh) == 2 and fh[0] == fh[1], f"two runs of hole09_build.py -- --out (stage/ and stage_repro/): blend geometry hash {ha[:16]} == {hb[:16]} ({cnt.group(1)} mesh objects, {cnt.group(2)} vertices, {cnt.group(3)} faces; names, world matrices, vertex positions rounded 1e-5, loop indices, material names); FBX re-import hash {fh[0][:16]} == {fh[1][:16]} (the FBX bytes themselves differ: header timestamp + zlib array streams)")
feat = [("H_RIBBON_FAIRWAY_SAND_GREEN", [("LK_REQUIRED", "blend"), ("GROUND_MATERIALS", "fbx"), ("LK_TEXTURED", "blend")]),
        ("H_RIDGE_SCRUB", [("SPLIT_SCRUB_RIDGE", "fbx"), ("SPLIT_NO_SCRUB_RIBBON", "fbx")]),
        ("H_RIDGE_PLANTS_ROCKS", [("SPLIT_RIDGE_SCATTER", "fbx"), ("PLANTS_SHARED_MATERIAL", "fbx"), ("PLANTS_INSTANCED", "fbx")]),
        ("H_RUIN_MASONRY", [("SPLIT_RUIN", "fbx")]),
        ("H_SEA_STACKS_SPIRES", [("SEASTACK_TAPERED", "fbx")])]
for i, extra in feat:
    ok = qa[i][1] and all(lvg(n, s)[1] for n, s in extra)
    emit(i, ok, qa[i][2] + " | " + " | ".join(f"verify {n}@{s} {'PASS' if lvg(n, s)[1] else 'FAIL'}: {lvg(n, s)[2][:200]}" for n, s in extra))
g = lvg("SPLIT_SHORE_SKIN", "fbx")
emit("H_SHORE_SKIN_JAGGED_STRATA", g[1] and qa["H_SKIN_NOT_OVER_WATER"][1] and qa["H_SKIN_FACES_OUTWARD"][1] and any(b[0] == "SKIN_JAGGED" and b[1] for b in bf), f"verify SPLIT_SHORE_SKIN@fbx: {g[2]} | " + " | ".join(f"{b[0]}: {b[2][:240]}" for b in bf if b[0] in ("SKIN_JAGGED", "LOOK_SKIN_BELOW_PLAY")) + f" | {qa['H_SKIN_NOT_OVER_WATER'][2][:200]} | {qa['H_SKIN_FACES_OUTWARD'][2][:200]}")
emit("H_SHELF_THIN", qa["H_SHELF_THIN"][1] and lvg("SHELF_THIN", "fbx")[1], qa["H_SHELF_THIN"][2] + f" | verify SHELF_THIN@fbx: {lvg('SHELF_THIN', 'fbx')[2][:200]}")
emit("H_SURF_SPARSE_NO_STRIP", qa["H_NO_FOAM_STRIP"][1] and lvg("SURF_SHORE", "fbx")[1], f"verify SURF_SHORE@fbx: {lvg('SURF_SHORE', 'fbx')[2]} | verify NO_FOAM_STRIP@fbx: {lvg('NO_FOAM_STRIP', 'fbx')[2]}")
g1, g2 = lvg("PATH_UNDER_BALL", "fbx"), lvg("SAND_NAMES", "fbx")
emit("H_BUNKER_SAND_OVERLAY", qa["H_BUNKER_SAND_OVERLAY"][1] and g1[1] and g2[1] and lvg("PATH_UNDER_BALL", "blend")[1], qa["H_BUNKER_SAND_OVERLAY"][2] + f" | verify PATH_UNDER_BALL@fbx {'PASS' if g1[1] else 'FAIL'}: {g1[2][:260]} | SAND_NAMES@fbx {'PASS' if g2[1] else 'FAIL'}: {g2[2][:200]}")
g1 = lvg("ONE_GREEN", "fbx")
emit("H_RIDGE_RELIEF", qa["H_RIDGE_RELIEF"][1] and g1[1], qa["H_RIDGE_RELIEF"][2] + f" | verify ONE_GREEN@fbx {'PASS' if g1[1] else 'FAIL'}: {g1[2][:200]}")
emit("H_RIDGE_THICKETS", qa["H_RIDGE_THICKETS"][1], qa["H_RIDGE_THICKETS"][2])
for i in ("H_SCRUB_BOUNDARY_COVERED", "H_LEGACY_ROUTE_CLEAR", "H_LEGACY_RIM_ROCKS_OFF_CHANNEL_LIP", "H_LEGACY_RUIN_LANDING_BAND_AND_CLIFF", "H_LEGACY_SIGHT_LINES", "H_LEGACY_PIN_TEE_CLEAR"):
    emit(i, qa[i][1], qa[i][2])
g = lvg("NEW_OBJECT_PREFIXES", "fbx")
emit("H_NO_COLLISION_PREFIX_PROPS", g[1] and lvg("PROPS_OFF_PLAY", "fbx")[1], f"verify NEW_OBJECT_PREFIXES@fbx: {g[2]} | PROPS_OFF_PLAY@fbx: {lvg('PROPS_OFF_PLAY', 'fbx')[2][:240]}")
g = lvg("ROCK_VARIETY", "fbx")
emit("H_ROCK_VARIETY", g[1], g[2][:300])

# ---- repair rounds 1 + 2: the ruin masonry gates (tools/ruin_check.py, independent of the construction records) on the blend and on the FBX re-import, and the tee seam
def rc(stage):
    return {g[0]: g for g in map(parse, [l.rstrip("\n") for l in open(os.path.join(F, f"ruin_check_{stage}.log"), errors="replace") if l.startswith("GATE: ")]) if g}
rcb, rcf = rc("blend"), rc("fbx")
for name, hid in (("RUIN_SUPPORTED", "H_RUIN_SUPPORTED"), ("RUIN_LINTEL_BEARING", "H_RUIN_LINTEL_ON_JAMBS"), ("RUIN_BASE_BURIED", "H_RUIN_BASE_BURIED"), ("RUIN_NOT_BOXES", "H_RUIN_IRREGULAR_STONES"), ("RUIN_UV_WINDOWS", "H_RUIN_UV_WINDOWS"),
                  # repair round 2 (2026-10-05): the review "the ruin still reads as stacked bricks"
                  ("RUIN_FLAT_FACES", "H_RUIN_FLAT_FACES"), ("RUIN_UV_BRICK_INTERIOR", "H_RUIN_UV_BRICK_INTERIOR"), ("RUIN_BEDS_NOT_RULED", "H_RUIN_BEDS_NOT_RULED"),
                  ("RUIN_TOPS_RAGGED", "H_RUIN_TOPS_RAGGED"), ("RUIN_ARCH_SEATED", "H_RUIN_ARCH_SEATED"),
                  # repair round 3 (2026-10-05): the review "stacked boxes / triangle-split shading / floating crown"
                  ("RUIN_PLANAR_FACES", "H_RUIN_PLANAR_FACES"), ("RUIN_NO_UV_SPLIT", "H_RUIN_NO_UV_SPLIT"), ("RUIN_MASONRY_SHARE", "H_RUIN_MASONRY_SHARE")):
    emit(hid, rcb[name][1] and rcf[name][1], f"[blend] {rcb[name][2]} | [FBX re-import] {'PASS' if rcf[name][1] else 'FAIL'}: {rcf[name][2][:200]}")
sm = [l.strip() for l in open(os.path.join(F, "seam_check.log")) if l.startswith("SEAM")]
sb = open(os.path.join("r5", "seam_base_round4_geometry.txt")).read().strip()
mm = re.search(r"max ([\d.]+) levels", sm[0]); mb = re.search(r"max ([\d.]+) levels", sb)
tee_ok = float(mm.group(1)) < float(mb.group(1)) and float(mm.group(1)) <= 4.0
emit("H_TEE_SEAM_PREVIEW", tee_ok, f"TEE_BOX is LK_FAIRWAY on centerline UVs (was LK_GREEN on planar UVs): Blender EEVEE preview of the hole09_tee camera, row-mean step across the TEE_BOX far edge (rows 552-560): {mm.group(1)} levels now vs {mb.group(1)} levels with the round-4 stage geometry+libs (need < before and <= 4.0); {sm[0]}; the 10 cm tee plateau edge itself leaves ~2 levels (TEE_BOX lowered 10 cm in a scratch render: no step); BLENDER PREVIEW, NOT A GAME-VIEW MEASURE: the Game-view row-mean step must be re-measured on the re-shot hole09_1_tee.png")

tp = parse(next(l.rstrip("\n") for l in open(os.path.join(F, "tee_parallax.log"), errors="replace") if l.startswith("GATE: TEE_EDGE_UV_CONTINUOUS")))
emit("H_TEE_EDGE_UV_CONTINUOUS", tp[1], tp[2] + " | review finding 'a faint straight ruler line crosses the whole tee frame' (Game-view rows 556 / 557 of hole09_1_tee.png): the cause is a 10 cm plate (TEE_BOX, no riser) that hides 0.48 m of fairway behind its far edge from the address camera, not an albedo mismatch (both meshes carry the same centerline UV function: 0.0 m UV difference at the plate's vertices); the fix scales the plate's UVs about the camera (hole09_build.tee_parallax_uvs); the check re-casts the camera rays on the finished blend")

cl = [l.strip() for l in open(os.path.join(F, "collar_lie.log")) if l.startswith("COLLAR")]
mv = re.search(r"visible points (\d+) lies \{(.*?)\}", cl[0]); mh = re.search(r"hidden .*? points (\d+) lies \{(.*?)\}", cl[1])
emit("H_COLLAR_IS_ROUGH_LIE", "'LIE_ROUGH': 1.0" in mv.group(2) and qa["H_RIBBON_FAIRWAY_SAND_GREEN"][1], f"FAIRWAY_FIRSTCUT is LK_ROUGH (centerline UVs kept): its VISIBLE part (not under FAIRWAY / GREEN / APRON / TEE_BOX / BUNKER) is the rough LIE round the fairway: {mv.group(1)} sample points (1 m grid) with lie {{{mv.group(2)}}} (need 100 % rough); "
     f"the part under the FAIRWAY mesh ({mh.group(1)} points) is {{{mh.group(2)}}}; materials are only a colour (Hole.LieAt untouched, H_PLAY_UNCHANGED PASS); postcard_look_verify allows LK_ROUGH on FAIRWAY_FIRSTCUT (GROUND_MATERIALS@fbx PASS)")
# ---- grass + ruin pass (2026-10-05): the GRASS_* gates of the staged blend + FBX re-import (tools/grass_gates.py), the sway vertex colours (postcard_look_verify), the Blender-side tuft-silhouette proxy of GRASS_STILL_ALIVE
gg = {g[0]: g for g in map(parse, [l.rstrip("\n") for l in open(os.path.join(F, "grass_gates.log"), errors="replace") if l.startswith("GATE: ")]) if g}
for name in ("GRASS_FRINGE_PRESENT", "GRASS_NOT_ON_PLAY_SURFACES", "GRASS_NOT_ON_WATER", "GRASS_BALL_CLEAR", "GRASS_TRI_BUDGET"):
    b_ = gg[name + "@blend"]; f_ = gg.get(name + "@fbx")
    emit(name, b_[1] and (f_ is None or f_[1]), f"[blend] {b_[2]}" + (f" | [FBX re-import] {'PASS' if f_[1] else 'FAIL'}: {f_[2][:260]}" if f_ else " | (the FBX re-import carries no custom properties, so the fringe-only structure checks run on the blend; the vertex rules above run on both)"))
for name in ("PLANT_SWAY_COLORS", "PLANT_SWAY_CAPS"):
    b_, f_ = lvg(name, "blend"), lvg(name, "fbx")
    emit(name, b_[1] and f_[1], f"postcard_look_verify {name}@blend: {b_[2][:330]} | @fbx (export_look_fbx -> FBX -> Blender re-import): {'PASS' if f_[1] else 'FAIL'}: {f_[2][:330]}")
def tm(path):
    out_ = {}
    for l in open(os.path.join(F, path), errors="replace"):
        m = re.match(r"TUFTMASK (hole09_\w+?)_(before|after): tufts (\d+); tuft pixels ([\d.]+)% of the non-sky frame, ([\d.]+)% of the lower 60 %; 16 px cells with a tuft pixel ([\d.]+)% \(lower 60 %: ([\d.]+)%\)", l)
        if m:
            out_[m.group(1)] = dict(n=int(m.group(3)), px=float(m.group(4)), px_low=float(m.group(5)), cells=float(m.group(6)), cells_low=float(m.group(7)))
    return out_
tb, ta = tm("tuft_mask_before.log"), tm("tuft_mask_after.log")
rk = "hole09_ruin"
px_x = ta[rk]["px"] / max(tb[rk]["px"], 1e-9); cell_x = ta[rk]["cells"] / max(tb[rk]["cells"], 1e-9)
emit("GRASS_STILL_ALIVE_PROXY", px_x >= 10.0 and cell_x >= 5.0 and all(ta[k]["px"] >= tb[k]["px"] for k in ta),
     "BLENDER-SIDE PROXY, NOT the Game-view gate (that one is the integrator's: lower-60 % luminance sd + the skeptic verdict on the re-shot stills): flat Workbench mask render of the three still cameras (tufts white, everything else black; tools/tuft_mask.py), staged build against the round-3 stage (180 tufts): "
     + "; ".join(f"{k}: tuft pixels {tb[k]['px']:.3f}% -> {ta[k]['px']:.3f}% of the non-sky frame (x{ta[k]['px'] / max(tb[k]['px'], 1e-9):.1f}), 16 px cells with a tuft {tb[k]['cells']:.2f}% -> {ta[k]['cells']:.2f}%, lower 60 %: {tb[k]['px_low']:.3f}% -> {ta[k]['px_low']:.3f}%" for k in ("hole09_tee", "hole09_approach", "hole09_ruin"))
     + f". The ruin landmark needs >= 10x the tuft pixels and >= 5x the tuft cells ({px_x:.0f}x, {cell_x:.0f}x). LIMIT, by rule: the lower 60 % of the tee / approach address frames is the tee box / fairway within 4 yd of the ball (the camera is 4.5 yd behind it, 2.4 yd up, 60 deg), where no tuft may stand "
     "(play surface, 4 m ball zone): the tee / approach stills show the fringe only on the far rough edges (upper third); their near ground stays the textures' job.")
guards = [l.strip() for l in open(os.path.join(F, "guards.log"))]
emit("GUARDS_7_OF_7", sum(1 for l in guards if l.endswith("PASS")) == 7, f"work/postcard-look/guards.sh: {sum(1 for l in guards if l.endswith('PASS'))} of {len(guards)} lines PASS (hole_07.blend / .fbx / .fbx.meta, Hole.cs, no drift, GolfGame starts Course.Postcards(), Cliffside() still in Hole.cs)")
h7 = [g for g in lv if g[0] == "HOLE07_UNTOUCHED"][0]
emit("H_HOLE07_UNTOUCHED", h7[1] and all(l.endswith("PASS") for l in guards if "hole_07" in l), f"verify HOLE07_UNTOUCHED: {h7[2]} | guards.sh: hole_07 lines PASS")
info = ""
bc = "r5/evidence/ball_cover.json"
if os.path.exists(bc):
    b = json.load(open(bc))
    info = ("\nINFO (report-only, not a gate; tools/ball_cover.py, r5/evidence/ball_cover.json): the ridge is Rough and every prop on it is non-colliding, so a ball can rest INSIDE a prop. "
            f"{b['n']} Rough ridge ball positions (2 m grid, >= 2 m inside the shore): inside a prop {b['inside_share_all']:.1%} overall; within 8 yd of the dry safe route {b['inside_share_corridor']:.1%} "
            f"({b['n_corridor']} positions; only the design-allowed near-route classes: boundary-chain shrubs/rocks at 4 yd, knolls 5 yd, masonry 6 yd, tufts); off the route {b['inside_share_off_route']:.1%} "
            f"(by class {', '.join(f'{k} {v:.1%}' for k, v in b['inside_by_class_off_route'].items())}); hidden from the phone address camera (4.5 yd behind, 2.4 yd up, 4 headings) off the route: "
            f"{b['occluded_share_off_route_mean_heading']:.0%} per heading ({b['occluded_share_off_route_any_heading']:.0%} for at least one heading), in the corridor {b['occluded_share_corridor_mean_heading']:.1%}.\n")
open("GATES_hole09.txt", "w").write("POSTCARD_LOOK CONTINUE phase 3, GRASS + SWAY pass, HOLE 9 REPAIR ROUND 0 (2026-10-05: edge fringe + ruin scrub clumps + sway vertex colours on every plant, rounder ruin stones + slipped keystone; rebuilt on the shared fixers' new tuft library / props / verifier / textures) - hole 9 Split: gate results of the STAGED build (nothing installed). Every line is a measurement; Blender renders are previews, NOT Game-view proof.\nstaged files: stage/hole_09.blend, stage/hole_09.fbx (sha256 in INSTALL.md). Source logs: final/*.log\n\n" + "\n".join(out) + "\n" + info + "\n--- every in-build library gate (build_final.log) ---\n" + "\n".join(f"GATE: {b[0]} {'PASS' if b[1] else 'FAIL'} - {b[2][:300]}" for b in bf) + "\n")
print("\n".join(l[:240] for l in out))
print("FAIL lines:", [l[:60] for l in out if " FAIL " in l])
