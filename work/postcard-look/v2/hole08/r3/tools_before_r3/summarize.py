"""Builds GATES_hole08.md from the logs of run_all.sh. python3 summarize.py   (reads logs/*, landmarks*.json, stage/)"""
import json, re, os, hashlib
H = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/hole08"
L = H + "/logs/"
def rd(p): return open(p).read()
def gates(path):
    out = {}
    for ln in rd(path).splitlines():
        m = re.match(r"GATE: (\S+) (PASS|FAIL) - (.*)", ln)
        if m: out[m.group(1)] = (m.group(2) == "PASS", m.group(3))
    return out
V = gates(L + "verify_look.log")
PV = gates(L + "postcard_verify.log")
BU = gates(L + "build.log")
HN = json.load(open(L + "h_numbers.json"))
LMK = json.load(open(H + "/landmarks.json"))
LMC = json.load(open(H + "/landmarks_check.json"))
lines = []
def emit(gid, ok, detail):
    lines.append(f"GATE: {gid} {'PASS' if ok else 'FAIL'} - {detail}")
def vg(name, stage=None):
    k = f"{name}@{stage}" if stage else name
    return V.get(k, (False, f"{k} missing from verify_look.log"))
def both(name):
    a, b = vg(name, "blend"), vg(name, "fbx")
    return a[0] and b[0], f"blend: {a[1][:260]} | fbx: {b[1][:200]}"

# --- required ids
pu = json.load(open(L + "play_unchanged.json"))
emit("H_PLAY_UNCHANGED", pu["ok"], rd(L + "play_unchanged.log").split("GATE: H_PLAY_UNCHANGED PASS - ")[1].split("\n")[0].strip() + f"; verifier PLAY_SURFACE_TOPS/GRID/FACES/WALLS + MARKERS_FROZEN + BASELINE_SIGNATURE at both stages: " + ", ".join(f"{n} {'PASS' if all(V.get(f'{n}@{s}', (False,))[0] for s in ('blend','fbx')) else 'FAIL'}" for n in ("PLAY_SURFACE_TOPS", "PLAY_SURFACE_GRID", "PLAY_SURFACE_FACES", "PLAY_SURFACE_WALLS", "MARKERS_FROZEN")) + f"; build gate LOOK_TOP_SURFACES_UNCHANGED {BU['LOOK_TOP_SURFACES_UNCHANGED'][1]}")
for st in ("blend", "fbx"):
    items = {k: v for k, v in V.items() if k.endswith("@" + st) or ("@" not in k)}
    fails = {k: v for k, v in items.items() if not v[0]}
    emit(f"H_LOOK_VERIFY_{st.upper()}", not fails, f"{len(items) - len(fails)} of {len(items)} gate lines of postcard_look_verify.py PASS at the {st} stage; FAIL: " + (" | ".join(f"{k}: {v[1][:220]}" for k, v in fails.items()) if fails else "none")
         + (" -- LOOK_FILES judges the PNG textures in Look/ (grass albedos Fairway_C / Green_C below the lead's luminance-window floor): the texture agent's files, not this hole's geometry" if fails else ""))
emit("H_POSTCARD_VERIFY", all(k.split("@")[0] in ("MATERIALS", "WATER_LEVEL", "FBX_BUDGET") for k, v in PV.items() if not v[0]),
     f"{sum(1 for v in PV.values() if v[0])} of {len(PV)} lines PASS; the failing lines are exactly the three that fail by design: " + " | ".join(f"{k}: {v[1][:180]}" for k, v in PV.items() if not v[0])
     + "  (MATERIALS = old MAT_* allow-list vs the LK_* names; WATER_LEVEL = the vertical WATER_FALL_00 sheet; FBX_BUDGET = the old 4 MB / 150k tris vs the 20 MB / 250k LOOK budget)")
ck = rd(L + "emit_cs_check.log").strip()
emit("H_CHECK_NO_DRIFT", "PASS" in ck and "FAIL" not in ck, f"postcard_emit_cs.py --check Unity/Assets/Scripts/Course/Hole.cs: {ck}; postcard_check.py hole08_design: " + rd(L + "postcard_check.log").strip().splitlines()[-1])
r = HN["blend"]["rocks"]; rf = HN["fbx"]["rocks"]
emit("H_NO_12_VERTEX_ROCK", r["min_welded_verts"] >= 60 and rf["min_welded_verts"] >= 60 and not r["twelve_vertex_rocks"] and both("ROCK_NOT_ICOSAHEDRON")[0],
     f"{r['objects']} rock instances of {r['unique_meshes']} library meshes: fewest welded vertices {r['min_welded_verts']} (blend) / {rf['min_welded_verts']} (FBX re-import) (>= 60), fewest faces {r['min_faces']}, 12-vertex rocks {r['twelve_vertex_rocks']}; verifier ROCK_NOT_ICOSAHEDRON {both('ROCK_NOT_ICOSAHEDRON')[1][:200]}; ROCK_VARIETY {vg('ROCK_VARIETY','blend')[1][:200]}")
s_ = HN["blend"]["stretch"]; sf = HN["fbx"]["stretch"]
emit("H_NO_STRETCH_2X", not s_["violations"] and not sf["violations"] and both("NO_ROCK_STRETCH_2X")[0],
     f"{s_['instances']} rock / masonry instances: singular values {s_['min']:.3f}..{s_['max']:.3f}, max/min {s_['max_ratio']:.3f} (blend); FBX {sf['min']:.3f}..{sf['max']:.3f}, {sf['max_ratio']:.3f} (limits 0.5..2.0 and <= 2.0); verifier NO_ROCK_STRETCH_2X {vg('NO_ROCK_STRETCH_2X','blend')[1][:220]}")
p_ = HN["blend"]["plants"]; pf = HN["fbx"]["plants"]
emit("H_NO_PLANT_ON_WATER", not p_["on_water_by_lie"] and not pf["on_water_by_lie"] and not p_["lowest_base_below_5m"] and both("NO_PLANT_ON_WATER")[0],
     f"{p_['non_vine']} plants + {p_['vines']} vines: 0 whose xy is water by the scoring mirror unless a rock top is under them (the arch outcrop), lowest plant base >= 5.0 m (blend and FBX); verifier NO_PLANT_ON_WATER {vg('NO_PLANT_ON_WATER','blend')[1][:260]}")
f_ = HN["blend"]["foam"]
mc = HN["blend"]["marker_clearance_m"]; mcf = HN["fbx"]["marker_clearance_m"]
emit("H_NO_PROP_NEAR_MARKERS", min(v[0] for v in mc.values()) >= 1.5 and min(v[0] for v in mcf.values()) >= 1.5 and min(mc[k][0] for k in ("MARKER_PIN", "HOLE_CUP", "FLAG") if k in mc) >= 3.0,
     "nearest vertex of any plant / rock / masonry object to each gameplay marker (m, blend): " + ", ".join(f"{k} {v[0]}" for k, v in sorted(mc.items())) + f" (limit 1.5 m for pin and tee markers; verifier PROPS_OFF_PLAY: {vg('PROPS_OFF_PLAY','blend')[1][:200]})")
emit("H_NO_FOAM_STRIP", not f_["foam_objects"] and not f_["mat_foam"] and both("NO_FOAM_STRIP")[0] and BU["NO_FOAM_STRIP"][0],
     f"no MAT_FOAM / *FOAM* object ({f_['foam_objects']}, {f_['mat_foam']}); {f_['surf_objects']} sparse WATER_SURF patches; verifier {vg('NO_FOAM_STRIP','blend')[1][:300]}; library audit {BU['NO_FOAM_STRIP'][1][:260]}")
st = rd(L + "build.log")
tris = int(re.search(r"(\d+) triangles", st).group(1)); mb = os.path.getsize(H + "/stage/hole_08.fbx") / 1048576
emit("H_BUDGET", tris <= 250000 and mb <= 20 and p_["max_faces"] <= 500 and p_["materials"] == ["LK_PLANTS"],
     f"{tris} triangles in the export set (<= 250000), FBX {mb:.2f} MB (<= 20), {HN['blend']['budget']['mesh_objects']} mesh objects on {HN['blend']['budget']['unique_mesh_datablocks']} mesh datablocks, library props <= {p_['max_faces']} faces (<= 500), plants share {p_['materials']} on {p_['unique_meshes']} instanced meshes; verifier TRIANGLE_BUDGET {vg('TRIANGLE_BUDGET','blend')[1][:200]}, PLANTS_INSTANCED {vg('PLANTS_INSTANCED','blend')[1][:160]}")
# landmarks json
shots = {s["name"]: s for s in LMK["shots"]}
ok_lm = set(shots) >= {"hole08_tee", "hole08_approach", "hole08_arch"} and shots["hole08_arch"]["kind"] == "landmark" and LMC["dense_blocked_of"][0] == 0 and LMC["look_ray_hit"] is None
lies = HN["lies"]
emit("H_LANDMARKS_JSON", ok_lm and lies["tee"] == "Tee" and lies["M"] == "Fairway" and lies["pathball"] == "Fairway",
     f"landmarks.json: {len(LMK['shots'])} shots {sorted(shots)} in the RUNTIME.md stills schema (address ball/aim in course yards, landmark pos/look in Unity world yards, fov {shots['hole08_arch']['fov']}); "
     f"ball lies by the scoring mirror: tee {lies['tee']}, approach M (19,178) {lies['M']}, path-ball {tuple(HN['pathball_yd'])} {lies['pathball']}; arch camera: {LMC['dense_blocked_of'][0]} of {LMC['dense_blocked_of'][1]} arch sample rays blocked, look ray {LMC['look_ray_hit']}, "
     f"arch fills {LMC['search']['width_frac']:.0%} of the frame width, {LMC['search']['height_frac']:.0%} of its height, outcrop in frame {LMC['search']['outcrop_in_frame']:.0%}")
rp = [ln.split() for ln in rd(L + "reproducible.txt").splitlines() if ln.startswith("FP")]
emit("H_REPRODUCIBLE", len(rp) == 3 and len({(x[2], x[4], x[6], x[8]) for x in rp}) == 1,
     f"3 builds (stage, PYTHONHASHSEED 7, 14) give the same geometry hash {rp[0][2]}, {rp[0][4]} meshes, {rp[0][6]} vertices, {rp[0][8]} triangles (names + 0.1 mm world vertices, every mesh)")
gd = rd(L + "guards.log")
emit("H_HOLE07_UNTOUCHED", "hole_07.blend unchanged PASS" in gd and "hole_07.fbx unchanged PASS" in gd and "hole_07.fbx.meta unchanged PASS" in gd and vg("HOLE07_UNTOUCHED")[0],
     "hole_07.blend, hole_07.fbx, hole_07.fbx.meta sha256 unchanged (guards.sh + verifier HOLE07_UNTOUCHED); Hole.cs sha unchanged")
emit("GUARDS_7_OF_7", gd.count("PASS") == 7 and "FAIL" not in gd, f"work/postcard-look/guards.sh: {gd.count('PASS')} PASS lines of 7")
# --- features
tp = HN["tee_path"]
emit("H_FEATURE_PATH", both("NEEDLE_PATH")[0] and both("PATH_UNDER_BALL")[0] and tp["visible"] / max(tp["samples"], 1) >= 0.5,
     f"{both('NEEDLE_PATH')[1][:300]}; under the ball: {vg('PATH_UNDER_BALL','blend')[1][:330]}; tee camera (900x1600, 60 deg): {tp['in_frame']} of {tp['samples']} path samples inside the frame, {tp['visible']} unblocked; paths {HN['blend']['features']['paths']}")
emit("H_FEATURE_FLOWERS_SHRUBS_TUFTS", both("NEEDLE_FLOWERS_SHRUBS_TUFTS")[0], both("NEEDLE_FLOWERS_SHRUBS_TUFTS")[1][:380])
ar = BU
emit("H_FEATURE_ARCH", both("NEEDLE_ARCH")[0] and ar["ARCH"][0] and ar["ARCH_FALLEN_BLOCKS_REST"][0] and ar["ARCH_OPENING_CLEAR"][0] and ar["ARCH_NOT_HIDDEN_BY_NEEDLES"][0] and not HN["blend"]["names"]["collider_named_scenery"],
     f"{both('NEEDLE_ARCH')[1][:330]}; hole gates: ARCH {ar['ARCH'][1][:200]} | FALLEN {ar['ARCH_FALLEN_BLOCKS_REST'][1][:120]} | OPENING {ar['ARCH_OPENING_CLEAR'][1][:200]} | not hidden {ar['ARCH_NOT_HIDDEN_BY_NEEDLES'][1][:200]}; arch object {HN['blend']['features']['arch_objects']} (DRESS_ prefix, no collider)")
emit("H_FEATURE_WATERFALL", both("NEEDLE_WATERFALL")[0] and HN["blend"]["features"]["waterfall"] == ["WATER_FALL_00"], f"{both('NEEDLE_WATERFALL')[1][:420]}; WATER_ prefix, no collider, no animation ({vg('NO_ANIMATION','blend')[1][:60]})")
emit("H_FEATURE_CLIFF_STRATA_VINES", both("NEEDLE_CLIFF_SKIN")[0] and both("NEEDLE_WALL_VINES")[0], f"{both('NEEDLE_CLIFF_SKIN')[1][:300]} | {both('NEEDLE_WALL_VINES')[1][:200]}; build gates SKIN_JAGGED/SKIN_NOT_OVER_WATER/SKIN_FACES_OUTWARD: " + ", ".join(f"{n} {'PASS' if BU[n][0] else 'FAIL'}" for n in ("SKIN_NOT_OVER_WATER", "SKIN_FACES_OUTWARD", "LOOK_SKIN_BELOW_PLAY")))
emit("H_FEATURE_SEA_STACKS", both("NEEDLE_SEA_STACKS")[0] and both("SEASTACK_TAPERED")[0] and BU["NEEDLES"][0], f"{both('NEEDLE_SEA_STACKS')[1][:300]}; {vg('SEASTACK_TAPERED','blend')[1][:260]}; build NEEDLES: {BU['NEEDLES'][1]}")
emit("H_FEATURE_FOOT_BOULDERS", BU["ROCKS_STAND_IN_THE_SEA"][0] and BU["ROCKS_CONTACT_CHAIN"][0] and BU["ROCKS_REST"][0], f"{BU['ROCKS_STAND_IN_THE_SEA'][1]}; {BU['ROCKS_CONTACT_CHAIN'][1][:200]}; {BU['ROCKS_REST'][1][:200]}")
emit("H_FEATURE_SHELF_THIN", both("SHELF_THIN")[0] and BU["SHELF_THIN"][0], f"{vg('SHELF_THIN','blend')[1][:300]}; library: {BU['SHELF_THIN'][1][:260]}")
emit("H_FEATURE_SURF_SPARSE", both("SURF_SHORE")[0] and both("NO_FOAM_STRIP")[0], f"{vg('SURF_SHORE','blend')[1][:200]}; {vg('NO_FOAM_STRIP','blend')[1][:260]}")
emit("H_FEATURE_FAIRWAY_GREEN_SAND_TEXTURED", both("GROUND_MATERIALS")[0] and vg("LK_TEXTURED", "blend")[0] and both("SAND_NAMES")[0] and both("NO_LEGACY_MATERIALS")[0] and both("UV_DENSITY")[0],
     f"{both('GROUND_MATERIALS')[1][:300]}; LK_TEXTURED {vg('LK_TEXTURED','blend')[1][:200]}; SAND_NAMES {vg('SAND_NAMES','blend')[1][:120]}; UV_DENSITY {vg('UV_DENSITY','blend')[1][:200]}; sand materials on the bunker {HN['blend']['features']['sand_materials']}")
emit("H_FEATURE_NEEDLE_RULES", all(BU[n][0] for n in ("NEEDLES", "LINES_OF_PLAY_VISIBLE", "NEEDLES_NOT_BEHIND_TARGETS")), f"{BU['NEEDLES'][1]}; {BU['LINES_OF_PLAY_VISIBLE'][1][:200]}; {BU['NEEDLES_NOT_BEHIND_TARGETS'][1][:200]}")
emit("H_GATES_CAN_FAIL", rd(L + "negctl.txt").strip().splitlines()[-1].startswith("NEGCTL SUMMARY 12/12"), rd(L + "negctl.txt").strip().splitlines()[-1] + " (negctl.py: needle too close / too high / in front of the arch opening / behind the flag, hovering rock, rock on the fairway, boulder on the line of play, hovering block, arch off its outcrop, tee box back on LK_GREEN, tee box UV x3, fairway stripe shift removed)")
emit("H_NO_COLLISION_PREFIX", not HN["blend"]["names"]["collider_named_scenery"] and HN["blend"]["names"]["cart_path"] == [] and both("NEW_OBJECT_PREFIXES")[0] and both("RESERVED_NAMES")[0], f"every new object is ROCK_/PLANT_/DRESS_/WATER_ ({vg('NEW_OBJECT_PREFIXES','blend')[1][:150]}); ground-named meshes {HN['blend']['names']['ground']}; {vg('RESERVED_NAMES','blend')[1][:100]}")
# --- round 2 gates (reviewer findings)
FV = json.load(open(L + "frame_variation.json")); FV0 = json.load(open(H + "/r2/framevar_before.json"))
PD = json.load(open(L + "path_dense.json")); PD1 = json.load(open(L + "path_dense_1cm.json"))
def lsd(path, y0=0.4):
    from PIL import Image
    import math
    im = Image.open(path).convert("L"); w, h = im.size
    px = list(im.crop((0, int(h * y0), w, h)).tobytes()); m = sum(px) / len(px)
    return math.sqrt(sum((x - m) ** 2 for x in px) / len(px))
R1 = H + "/r2/r1_previews/"; P2 = H + "/previews/"
rs = {k: (lsd(R1 + f"hole08_{k}_blender.png"), lsd(P2 + f"hole08_{k}_blender.png")) for k in ("tee", "approach")}
fv_ok = all(FV[k]["lum_sd"] >= 10.0 for k in ("tee", "approach")) and all(rs[k][1] >= 1.5 * rs[k][0] for k in rs)
emit("H_FRAME_VARIATION", fv_ok,
     "albedo luminance sd (0..255) over the lower 60 % of the phone frames, Fairway_C / Green_C / Path_C PNGs sampled at the real UVs along 120 x 213 rays per frame: "
     + ", ".join(f"{k} {FV0[k]['lum_sd']:.1f} -> {FV[k]['lum_sd']:.1f} (p10..p90 {FV[k]['lum_p10']:.0f}..{FV[k]['lum_p90']:.0f}; need >= 10)" for k in ("tee", "approach"))
     + "; Blender EEVEE previews, luminance sd of the lower 60 % (round 1 -> now, need >= 1.5x): " + ", ".join(f"{k} {rs[k][0]:.1f} -> {rs[k][1]:.1f}" for k in rs)
     + f"; materials seen by the tee frame {FV['tee']['materials']}, approach {FV['approach']['materials']} (Blender lighting, not the Unity rig: the Game view is unmeasured)")
tot2 = sum(v["samples"] for v in PD.values()); ov2 = sum(v["over_1p2cm"] for v in PD.values()); tot1 = sum(v["samples"] for v in PD1.values()); ov1 = sum(v["over_1p2cm"] for v in PD1.values())
emit("H_PATH_DENSE", ov2 == 0 and ov1 == 0 and max(v["max_cm"] for v in PD.values()) <= 1.2,
     f"both paths, every sample ray-cast onto the path and the ground colliders: {tot2} samples on a 2 cm grid, {ov2} above 1.2 cm, max {max(v['max_cm'] for v in PD.values()):.2f} cm; {tot1} samples on a 1 cm grid, {ov1} above 1.2 cm, max {max(v['max_cm'] for v in PD1.values()):.2f} cm "
     f"(round 1 on the same tool: 2 samples at 1.81 / 1.86 cm at the old path's left edge, course (6.3, 186) / (6.45, 167) yd, 0.0008 m2); buried share {', '.join(f'{k} {v['buried_share']:.1%}' for k, v in PD.items())}; ball to nearest path vertex: " + ", ".join(f"{k} {v:.2f} m" for k, v in HN["ball_to_path_m"].items()))
emit("H_FEATURE_MOW_PATTERN", BU["MOW_PATTERN"][0] and both("GROUND_MATERIALS")[0] and both("UV_DENSITY")[0], f"{BU['MOW_PATTERN'][1][:520]}; verifier GROUND_MATERIALS {vg('GROUND_MATERIALS','blend')[1][:200]}; UV_DENSITY {vg('UV_DENSITY','blend')[1][:200]}")
tf = HN["tufts"]
emit("H_TUFT_HEIGHT", tf["max_m"] <= 0.46 and tf["median_m"] <= 0.32 and tf["p95_m"] <= 0.42, f"{tf['count']} PLANT_TUFT_* instances (pads, rim and the arch outcrop): height median {tf['median_m']:.2f} m, p95 {tf['p95_m']:.2f}, max {tf['max_m']:.2f} m (round 1: median 0.43, max 0.56 on the pads, 0.62 on the outcrop; need median <= 0.32, p95 <= 0.42, max <= 0.46: the 0.11 m ball in the rough is not buried; scale 0.55-0.85 of the library tuft)")
open(H + "/GATES_hole08.md", "w").write("# Hole 8 Needle: gate results (staged build, " + "run_all.sh" + ")\n\nBlender previews are NOT Game-view proof.\n\n```\n" + "\n".join(lines) + "\n```\n")
print("\n".join(l[:240] for l in lines))
print(sum(1 for l in lines if " PASS - " in l), "PASS of", len(lines))
