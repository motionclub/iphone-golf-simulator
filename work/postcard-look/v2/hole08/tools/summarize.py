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
_expected_pv_fails = {"MATERIALS@blend", "MATERIALS@fbx", "WATER_LEVEL@blend", "WATER_LEVEL@fbx", "FBX_BUDGET@fbx"}
emit("H_POSTCARD_VERIFY", {k for k, v in PV.items() if not v[0]} == _expected_pv_fails,
     f"{sum(1 for v in PV.values() if v[0])} of {len(PV)} lines PASS; the failing lines are exactly the five (three kinds, blend + FBX) that fail by design (the old postcard_verify.py predates the LOOK budget): " + " | ".join(f"{k}: {v[1][:180]}" for k, v in PV.items() if not v[0])
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
oc = p_["outcrop_water_lie"]; ocf = pf["outcrop_water_lie"]
emit("H_NO_PLANT_ON_WATER", not p_["on_water_by_lie"] and not pf["on_water_by_lie"] and not p_["lowest_base_below_5m"] and not pf["lowest_base_below_5m"] and both("NO_PLANT_ON_WATER")[0],
     f"{p_['non_vine']} plants + {p_['vines']} vines. ON THE SEA: 0 (lowest non-vine plant base z {p_['lowest_plant_base_z']:.2f} m blend / {pf['lowest_plant_base_z']:.2f} m FBX, limit >= 5.0 m = 1 m under the pad top; sea level 0.15 m; "
     f"lowest vine vertex {p_['lowest_vine_vertex_z']:.2f} m, every vine is hung on a cliff face, the arch or the outcrop's flank). By the scoring mirror's lie_at (xy only) {oc['count']} plants read Water at their xy: all {oc['count']} stand on the ROCK_OUTCROP top of the arch "
     f"(support top z {oc['support_top_z']}, lowest base z {oc['lowest_base_z']}, kinds {oc['kinds']}), a rock that stands in the sea inside the water ellipse; 0 other plants read Water (FBX: {ocf['count']}). "
     f"The outcrop plants are on rock, not on the sea; the lie-based count is therefore {oc['count']}, not 0. Round 8: {p_['crown_water_lie']['count']} more plants (the crown tufts, lowest base z {p_['crown_water_lie']['lowest_base_z']}) read Water at their xy: each stands on the grass crown of a sea stack / spire (ROCK_SEASTACK_* / ROCK_SPIRE_*, z >= 5 m, the stack's own surface within 25 cm under its base) "
     f"- a rock that stands in the sea (FBX: {pf['crown_water_lie']['count']}). Verifier NO_PLANT_ON_WATER {vg('NO_PLANT_ON_WATER','blend')[1][:200]}")
f_ = HN["blend"]["foam"]
mc = HN["blend"]["marker_clearance_m"]; mcf = HN["fbx"]["marker_clearance_m"]
emit("H_NO_PROP_NEAR_MARKERS", min(v[0] for v in mc.values()) >= 1.5 and min(v[0] for v in mcf.values()) >= 1.5 and min(mc[k][0] for k in ("MARKER_PIN", "HOLE_CUP", "FLAG") if k in mc) >= 3.0,
     "nearest vertex of any plant / rock / masonry object to each gameplay marker (m, blend): " + ", ".join(f"{k} {v[0]}" for k, v in sorted(mc.items())) + f" (limit 1.5 m for pin and tee markers; verifier PROPS_OFF_PLAY: {vg('PROPS_OFF_PLAY','blend')[1][:200]})")
emit("H_NO_FOAM_STRIP", not f_["foam_objects"] and not f_["mat_foam"] and both("NO_FOAM_STRIP")[0] and BU["NO_FOAM_STRIP"][0],
     f"no MAT_FOAM / *FOAM* object ({f_['foam_objects']}, {f_['mat_foam']}); {f_['surf_objects']} sparse WATER_SURF patches; verifier {vg('NO_FOAM_STRIP','blend')[1][:300]}; library audit {BU['NO_FOAM_STRIP'][1][:260]}")
st = rd(L + "build.log")
tris = int(re.search(r"stats: \d+ objects, \d+ meshes, (\d+) triangles", st).group(1)); mb = os.path.getsize(H + "/stage/hole_08.fbx") / 1048576
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
FVn = json.load(open(L + "frame_variation.json"))
emit("H_FEATURE_PATH", both("NEEDLE_PATH")[0] and both("PATH_UNDER_BALL")[0] and tp["visible"] / max(tp["samples"], 1) >= 0.5,
     f"{both('NEEDLE_PATH')[1][:300]}; under the ball: {vg('PATH_UNDER_BALL','blend')[1][:330]}; tee camera (900x1600, 60 deg): {tp['in_frame']} of {tp['samples']} path samples inside the frame, {tp['visible']} unblocked; "
     f"round 3: both paths hug the ball's left side, path covers {FVn['tee']['path_share']:.1%} (tee) / {FVn['approach']['path_share']:.1%} (approach) of the lower 60 % of the frame; paths {HN['blend']['features']['paths']}")
emit("H_PATH_CLEAR_OF_BALL", BU["PATH_CLEAR_OF_BALL"][0], BU["PATH_CLEAR_OF_BALL"][1] + "; the ball is not hidden by the path either way (PATH_UNDER_BALL: ball hidden 0.0 % at <= 1.2 cm)")
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
_nc = rd(L + "negctl.txt").strip().splitlines()[-1]
_m = re.match(r"NEGCTL SUMMARY (\d+)/(\d+) mutations caught", _nc)
emit("H_GATES_CAN_FAIL", bool(_m) and _m.group(1) == _m.group(2) and int(_m.group(2)) >= 33 and "passes every gate: True" in _nc, _nc + " (negctl.py: needle too close / too high / in front of the arch opening / behind the flag, hovering rock, rock on the fairway, boulder on the line of play, hovering block, arch off its outcrop, tee box back on LK_GREEN, tee box UV x3, fairway stripe shift removed, tee path moved onto the tee ball; round 5: tee box back on the 90 degree stripes (now caught by TEE_SEAM_SEEN), tee path bent right at the seam, a ledge face back on dark LK_CLIFF, the lip back on LK_GREEN, the outcrop vines 6 m off the rock; round 6: tee box UV without the hidden-band shift, the path's plate part sunk under the plate, the stones beyond the edge slid 15 cm, the outcrop wall back on bare rock; round 8: the outcrop's rim shading flat again, a fringe tuft on the fairway / in the sea / 1.5 m from the approach ball / 3 m from the pin, a 1.2 m tuft in the ball corridor, the fringe thinned to 100 tufts, the triangle cap at 150k, an island tuft on the rim line, a crown tuft 5 m beside its stack, a cliff vine 0.5 m off the wall)")
emit("H_NO_COLLISION_PREFIX", not HN["blend"]["names"]["collider_named_scenery"] and HN["blend"]["names"]["cart_path"] == [] and both("NEW_OBJECT_PREFIXES")[0] and both("RESERVED_NAMES")[0], f"every new object is ROCK_/PLANT_/DRESS_/WATER_ ({vg('NEW_OBJECT_PREFIXES','blend')[1][:150]}); ground-named meshes {HN['blend']['names']['ground']}; {vg('RESERVED_NAMES','blend')[1][:100]}")
# --- round 2 gates (reviewer findings)
FV = json.load(open(L + "frame_variation.json")); FV0 = json.load(open(H + "/r2/framevar_before.json")); FV2 = json.load(open(H + "/r3/logs_r2/frame_variation.json"))
for _d in (FV0, FV2):                      # older tool versions did not write path_share / grass_only_sd: derive from the material counts
    for _k in _d:
        _d[_k].setdefault("path_share", _d[_k]["materials"].get("LK_PATH", 0) / max(_d[_k]["ground_hits"], 1))
PD = json.load(open(L + "path_dense.json")); PD1 = json.load(open(L + "path_dense_1cm.json"))
def lsd(path, y0=0.4):
    from PIL import Image
    import math
    im = Image.open(path).convert("L"); w, h = im.size
    px = list(im.crop((0, int(h * y0), w, h)).tobytes()); m = sum(px) / len(px)
    return math.sqrt(sum((x - m) ** 2 for x in px) / len(px))
R1 = H + "/r2/r1_previews/"; R2 = H + "/r3/previews_r2/"; P3 = H + "/previews/"
rs = {k: (lsd(R1 + f"hole08_{k}_blender.png"), lsd(R2 + f"hole08_{k}_blender.png"), lsd(P3 + f"hole08_{k}_blender.png")) for k in ("tee", "approach")}
fv_ok = all(FV[k]["lum_sd"] >= 10.0 and FV[k]["path_share"] >= 0.08 for k in ("tee", "approach")) and all(rs[k][2] >= 1.5 * rs[k][0] for k in rs)
emit("H_FRAME_VARIATION", fv_ok,
     "albedo luminance sd (0..255) over the lower 60 % of the phone frames, Fairway_C / Green_C / Path_C PNGs sampled at the real UVs along 120 x 213 rays per frame (camera: ball on the real ground + 0.055 m since round 5), round 1 -> round 2 -> round 5 (this run): "
     + ", ".join(f"{k} {FV0[k]['lum_sd']:.1f} -> {FV2[k]['lum_sd']:.1f} -> {FV[k]['lum_sd']:.1f} (p10..p90 {FV[k]['lum_p10']:.0f}..{FV[k]['lum_p90']:.0f}; need >= 10; grass-only sd {FV[k]['grass_only_sd']:.1f}; stone path share of the frame {FV2[k]['path_share']:.1%} -> {FV[k]['path_share']:.1%}, need >= 8 %)" for k in ("tee", "approach"))
     + "; Blender EEVEE previews, luminance sd of the lower 60 % (round 1 -> 2 -> 5, need round 5 >= 1.5x round 1): " + ", ".join(f"{k} {rs[k][0]:.1f} -> {rs[k][1]:.1f} -> {rs[k][2]:.1f}" for k in rs)
     + f"; materials seen by the tee frame {FV['tee']['materials']}, approach {FV['approach']['materials']}. The thresholds (10, 8 %, 1.5x) are mine, not from the brief; Blender lighting, not the Unity rig: the Game view is unmeasured. Negative control: the round-2 scene gives path share {FV2['tee']['path_share']:.1%} / {FV2['approach']['path_share']:.1%} and fails the 8 % line")
tm = FV["tee"]["mesh_mean_lum"]
tee_d = abs(tm["TEE_BOX"][0] - tm["FAIRWAY"][0]) if "TEE_BOX" in tm and "FAIRWAY" in tm else 0.0
emit("H_TEE_SEAM_SOFT", BU["TEE_SEAM_SEEN"][0] and BU["PATH_STEP_CONTINUOUS"][0] and BU["PATH_SEAM_JUMP"][0] and BU["MOW_PATTERN"][0],
     f"reviewer round 5 (medium, STILL open on the installed round-5 build): 'a hard horizontal seam cuts across the fairway on the tee shot, a strip of grass slices through the stone path and the path shifts sideways at it'. Causes measured on the round-5 build: "
     f"(1) build_path drapes each ribbon vertex on the LOWEST ground of its four cells, so on the tee box side of the 10 cm step the ribbon sank under the plate's edge for 0.2 m and the plate's grass showed through it (a grass strip across the stones); "
     f"(2) the plate is a hovering 10 cm step: the address camera cannot see 0.35 m of the fairway behind its edge, so grass and stones jump by that band although the UVs were continuous in plan. "
     f"Fix (UV + the path ribbon only, no vertex of a scoring mesh moves): {BU['TEE_SEAM_SEEN'][1][:620]} | {BU['PATH_STEP_CONTINUOUS'][1][:520]} | {BU['PATH_SEAM_JUMP'][1][:300]}. "
     f"Round 5's TEE_SEAM_UV (plan-view UV equality across the outline) is RETIRED and replaced by TEE_SEAM_SEEN: it demanded the UVs that cause the seen jump; the replacement measures the seen jump itself, with ray casts, in 52 pixel columns. Not weakened: round 5's H_TEE_SEAM_SOFT lines MOW_PATTERN and PATH_SEAM_JUMP are unchanged and pass. "
     f"Not measurable here: the tee plate's directional-light shadow on the fairway (Unity renders it, the FBX cannot switch it off) and the Game view itself.")
emit("H_ARCH_SLAB", BU["ARCH_SLAB_COVERED"][0] and BU["LEDGES_ARE_TURF"][0], BU["ARCH_SLAB_COVERED"][1] + "; reviewer round 5 (medium, arch shot): 'a flat grey stone slab with hard straight edges still sits on the island next to the grass' = the outcrop's camera-side wall: one library facet of 2 m x 3 m seen from the pad rim at 30 degrees. Fix: the library mesh is cut horizontally, its cut vertices displaced, the wall wears a turf bank over a patchy turf / rock band (the outcrop's grass top ring is unchanged; the shrubs / flowers / tufts and vines on it are scattered again with the same seeds, because the scatter region's faces changed).")
emit("H_LEDGES_TURF", BU["LEDGES_ARE_TURF"][0], BU["LEDGES_ARE_TURF"][1] + "; reviewer (arch shot): 'a black, hard-edged extruded box' = the capping ledge of the strata skin, a horizontal LK_CLIFF face under the grass lip")
emit("H_BUNKER_LIP", BU["BUNKER_LIP_NOT_GREEN"][0], BU["BUNKER_LIP_NOT_GREEN"][1] + "; reviewer (arch shot): 'a bright, saturated, faceted grass ridge with a chevron texture seam'")
emit("H_OUTCROP_VINES", BU["OUTCROP_VINES"][0], BU["OUTCROP_VINES"][1] + "; reviewer (arch shot): 'the island floor is a big flat grey slab': the outcrop's camera-side flank is a sheer wall seen from the pad rim; vines hang over it and a plant fringe runs along its grass rim")
cm = LMC["search"].get("composition", {})
emit("H_ARCH_FRAME", cm.get("lip", 0.0) <= 0.02 and cm.get("skin", 0.0) <= 0.06 and cm.get("flank", 0.0) <= 0.12 and cm.get("top", 0.0) >= 0.10 and LMC["dense_blocked_of"][0] == 0,
     f"arch landmark camera {'PINNED to the rounds 5-7 camera (hole08_look.ARCH_CAM; make_landmarks.py --pin: the new rim shoulder / outcrop clumps change what a re-run of the composition search would pick (it moves to x -13.1, fov 66), and the reviewers measured THIS frame)' if LMC['search'].get('pinned') else 'chosen by a composition-scored search over ' + str(LMC['search'].get('candidates', '?')) + ' candidates'} (30 x 54 rays through the frame, first-hit class shares): bunker lip {cm.get('lip', 0.0):.1%} (<= 2 %), strata skin ledges / walls {cm.get('skin', 0.0):.1%} (<= 6 %), outcrop flank {cm.get('flank', 0.0):.1%} (<= 12 %), "
     f"outcrop grass top {cm.get('top', 0.0):.1%} (>= 10 %), sky {cm.get('sky', 0.0):.1%}, water {cm.get('water', 0.0):.1%}; {LMC['dense_blocked_of'][0]} of {LMC['dense_blocked_of'][1]} arch sample rays blocked; camera {LMC['arch_camera_unity_yards']}; "
     f"round 4 camera (3.4 m above the pad rim) by the same rays on this build: lip {LMC['round4_camera_composition'].get('lip', 0.0):.1%}, skin {LMC['round4_camera_composition'].get('skin', 0.0):.1%}, flank {LMC['round4_camera_composition'].get('flank', 0.0):.1%}, top {LMC['round4_camera_composition'].get('top', 0.0):.1%}")
_rl = gates(L + "verify_look_relocated.log")
emit("H_ABSOLUTE_TEXTURE_PATHS", _rl.get("LK_TEXTURED@blend", (False,))[0] and V.get("LK_TEXTURED@blend", (False,))[0],
     f"proof/PROOF.md (round 4 install): LK_TEXTURED failed on the installed blender/hole_08.blend because the staged blend stored image paths relative to the staging folder. The build now saves with relative_remap=False; the staged blend copied to a deeper folder "
     f"(scratch/relocated/deeper) and verified there: LK_TEXTURED@blend {_rl.get('LK_TEXTURED@blend', (False, 'missing'))[1][:240]}")
tot2 = sum(v["samples"] for v in PD.values()); ov2 = sum(v["over_1p2cm"] for v in PD.values()); tot1 = sum(v["samples"] for v in PD1.values()); ov1 = sum(v["over_1p2cm"] for v in PD1.values())
emit("H_PATH_DENSE", ov2 == 0 and ov1 == 0 and max(v["max_cm"] for v in PD.values()) <= 1.2,
     f"both paths, every sample ray-cast onto the path and the ground colliders: {tot2} samples on a 2 cm grid, {ov2} above 1.2 cm, max {max(v['max_cm'] for v in PD.values()):.2f} cm; {tot1} samples on a 1 cm grid, {ov1} above 1.2 cm, max {max(v['max_cm'] for v in PD1.values()):.2f} cm "
     f"(round 1 on the same tool: 2 samples at 1.81 / 1.86 cm at the old path's left edge; round 3 re-routed both paths along the ball's left side and re-measured); buried share {', '.join(f'{k} {v['buried_share']:.1%}' for k, v in PD.items())}; ball to nearest path vertex: " + ", ".join(f"{k} {v:.2f} m" for k, v in HN["ball_to_path_m"].items()))
emit("H_FEATURE_MOW_PATTERN", BU["MOW_PATTERN"][0] and both("GROUND_MATERIALS")[0] and both("UV_DENSITY")[0], f"{BU['MOW_PATTERN'][1][:520]}; verifier GROUND_MATERIALS {vg('GROUND_MATERIALS','blend')[1][:200]}; UV_DENSITY {vg('UV_DENSITY','blend')[1][:200]}")
tf = HN["tufts"]
tg = HN["tuft_groups"]
cg = tg["carpet"]; fg = tg["fringe"]; og = tg["outcrop_fringe"]; kg = tg["crown"]
ft = HN["fringe_top_above_ground"]
emit("H_TUFT_HEIGHT", cg["max_m"] <= 0.46 and cg["median_m"] <= 0.32 and cg["p95_m"] <= 0.42 and ft["max_m"] <= 0.507,
     f"{tf['count']} PLANT_TUFT_* instances in four groups. (1) the OLD carpet ({cg['count']} tufts, after cheapen_tufts the far ones are the 36-triangle fillers): height median {cg['median_m']:.2f} m, p95 {cg['p95_m']:.2f}, max {cg['max_m']:.2f} m - the round-2 limits are unchanged "
     f"(median <= 0.32, p95 <= 0.42, max <= 0.46: the 0.11 m ball in the rough is not buried); (2) the pad FRINGE ({fg['count']} tufts, scatter_fringe): bbox height median {fg['median_m']:.2f}, p95 {fg['p95_m']:.2f}, max {fg['max_m']:.2f} m (the bbox also counts the 2 cm the base is sunk in and the lean); the EXACT top above the ground under the origin (what the brief caps at 0.55 yd = 0.503 m near the ball corridor, GRASS_BALL_CLEAR) "
     f"median {ft['median_m']:.3f}, p95 {ft['p95_m']:.3f}, max {ft['max_m']:.3f} m (<= 0.507); (3) the island clumps ({og['count']} tufts on the arch outcrop, not a play surface): median {og.get('median_m', 0):.2f}, max {og.get('max_m', 0):.2f} m (GRASS_OUTCROP_FRINGE: <= 1.25); (4) the sea-stack crown tufts ({kg['count']}, 9-17 m up, no ball ever lies there): median {kg.get('median_m', 0):.2f}, max {kg.get('max_m', 0):.2f} m. "
     f"Round 2's single gate over all tufts (max <= 0.46) is split by role: the carpet keeps its numbers, the fringe is held to the brief's 0.55 yd cap instead of 0.46 m (the brief asked for TALLER tufts along the rough edge, 0.6-1.8 x the library tuft, capped at 0.55 yd near the ball corridor)")

# --- round 8: grass liveliness + gentle sway (hole 8 part) ---------------------------------------------------------------------------------------------------------------------------------------------------
for g in ("GRASS_FRINGE_PRESENT", "GRASS_NOT_ON_PLAY_SURFACES", "GRASS_NOT_ON_WATER", "GRASS_BALL_CLEAR"):
    emit(g, BU[g][0], BU[g][1])
fb_mb = os.path.getsize(H + "/stage/hole_08.fbx") / 1048576
fbx_blob = open(H + "/stage/hole_08.fbx", "rb").read()
anim_nodes = fbx_blob.count(b"AnimationStack") + fbx_blob.count(b"AnimationCurve")
tri_before = int(re.search(r"stats: \d+ objects, \d+ meshes, (\d+) triangles", rd(H + "/r8/before_build.log")).group(1))
gt_ = BU["GRASS_TRI_BUDGET"]
emit("GRASS_TRI_BUDGET", gt_[0] and fb_mb <= 20 and anim_nodes == 0 and both("NO_ANIMATION")[0] and both("TRIANGLE_BUDGET")[0],
     f"{gt_[1]}; BEFORE (the round-7 libs, no fringe: r8/before_build.log) {tri_before} triangles -> AFTER {tris} triangles in the export set (cap 250000, margin {250000 - tris}); FBX {fb_mb:.2f} MB (<= 20), animation nodes in the FBX {anim_nodes} (0), "
     f"verifier NO_ANIMATION {vg('NO_ANIMATION','blend')[1][:80]}, TRIANGLE_BUDGET {vg('TRIANGLE_BUDGET','blend')[1][:160]}; the fringe is the pad fringe {BU['GRASS_TRI_BUDGET'][1].split('fringe ')[1].split(' triangles')[0] if 'fringe ' in BU['GRASS_TRI_BUDGET'][1] else '?'} + island clumps + crown tufts (GRASS_OUTCROP_FRINGE, CROWN_TUFTS)")
emit("GRASS_OUTCROP_FRINGE", BU["GRASS_OUTCROP_FRINGE"][0], BU["GRASS_OUTCROP_FRINGE"][1])
emit("CROWN_TUFTS", BU["CROWN_TUFTS"][0] and HN["blend"]["plants"]["crown_water_lie"]["count"] >= 40, BU["CROWN_TUFTS"][1] + f"; verifier NO_PLANT_ON_WATER (a blade-piece-by-piece support test on up-facing rock): {vg('NO_PLANT_ON_WATER','blend')[1][:160]}")
emit("VINE_ROOT_GAP", BU["VINE_ROOT_GAP"][0], BU["VINE_ROOT_GAP"][1])
emit("ARCH_LEFT_STRIP_COVERED", BU["ARCH_LEFT_STRIP_COVERED"][0], BU["ARCH_LEFT_STRIP_COVERED"][1])
FF = json.load(open(L + "fbx_fold.json"))
emit("ARCH_FOLD_SOFT", BU["ARCH_FOLD_SOFT"][0] and FF["max_deg"] <= 30.0 and FF["max_lambert"] <= 0.40,
     BU["ARCH_FOLD_SOFT"][1] + f"; the SAME numbers on the FBX RE-IMPORT (custom normals survive the exporter): max normal step {FF['max_deg']:.1f} deg, p99 {FF['p99_deg']:.1f}, max |N.sun| step {FF['max_lambert']:.3f}, {FF['pairs']} pairs; "
     f"the round-7 FBX measured by the same tool (r8/fbx_fold_before.json): 66.9 deg / 1.08 = the reviewer's fold. Blender shading, not the Unity Game view (that is the integrator's still)")
sw_b, sw_f = vg("PLANT_SWAY_COLORS", "blend"), vg("PLANT_SWAY_COLORS", "fbx")
nplant_meshes = HN["blend"]["plants"]["unique_meshes"]
emit("PLANT_SWAY_COLORS", sw_b[0] and sw_f[0], f"blend: {sw_b[1][:330]} | FBX re-import: {sw_f[1][:330]}; {nplant_meshes} unique PLANT_* library meshes on this hole, {HN['blend']['plants']['objects']} PLANT_* objects (blend) / {HN['fbx']['plants']['objects']} (FBX); the sway attribute rides through postcard_look_lib.export_look_fbx (colors_type LINEAR, raw)")
emit("PLANT_SWAY_CAPS", vg("PLANT_SWAY_CAPS", "blend")[0] and vg("PLANT_SWAY_CAPS", "fbx")[0], f"blend: {vg('PLANT_SWAY_CAPS','blend')[1][:300]} | FBX: {vg('PLANT_SWAY_CAPS','fbx')[1][:200]}")
FC0 = json.load(open(H + "/r8/frame_classes_before_stage.json")); FC1 = json.load(open(L + "frame_classes.json"))
def fcs(d, k): return f"{d[k]['_tuft_share']:.1%}"
emit("GRASS_FRAME_COVERAGE_BLENDER", FC1["arch/all"]["_tuft_share"] > FC0["arch/all"]["_tuft_share"] and FC1["arch/lower60"]["_tuft_share"] > FC0["arch/lower60"]["_tuft_share"],
     f"first-hit class shares of a 56 x 100 ray grid through the three still frames (Blender rays, NOT Game-view pixels; a tuft is a thin blade mesh, so the share of rays is a lower bound of the silhouette share): share of rays ending on a tuft mesh, round 7 build -> this build: "
     f"tee lower 60 % {fcs(FC0,'tee/lower60')} -> {fcs(FC1,'tee/lower60')}, tee frame {fcs(FC0,'tee/all')} -> {fcs(FC1,'tee/all')}; approach lower 60 % {fcs(FC0,'approach/lower60')} -> {fcs(FC1,'approach/lower60')}, approach frame {fcs(FC0,'approach/all')} -> {fcs(FC1,'approach/all')}; "
     f"arch lower 60 % {fcs(FC0,'arch/lower60')} -> {fcs(FC1,'arch/lower60')}, arch frame {fcs(FC0,'arch/all')} -> {fcs(FC1,'arch/all')}. "
     f"WHY THE TEE / APPROACH NEAR GROUND DOES NOT CHANGE: the lower 60 % of the tee frame is {FC1['tee/lower60'].get('TEE_BOX', 0):.1%} tee box + {FC1['tee/lower60'].get('DRESS_PATH', 0):.1%} stone path + {FC1['tee/lower60'].get('BALL_START', 0):.1%} ball + {FC1['tee/lower60'].get('FAIRWAY', 0):.1%} fairway, the approach's {FC1['approach/lower60'].get('FAIRWAY', 0):.1%} fairway + {FC1['approach/lower60'].get('DRESS_PATH', 0):.1%} path: "
     f"100 % play surface, where the brief forbids a tuft (never on Fairway / Green / Bunker / Tee, never within 4 m of a shot ball); the stone paths lie ON the fairway, so the path edge has no rough to stand on (edge samples play / path / lip = {BU['GRASS_FRINGE_PRESENT'][1].split('{')[1].split('}')[0] if '{' in BU['GRASS_FRINGE_PRESENT'][1] else '?'}). "
     f"What the fringe does change: the pad rims (visible at the frame edges / far end of the tee and approach frames), the cliff lips, the sea-stack crowns on the horizon (tee frame) and the arch island's foreground (arch frame). The near ground of the tee / approach frames is the textures' job (mow-band life), not this hole script's.")
open(H + "/GATES_hole08.md", "w").write("# Hole 8 Needle: gate results (staged build, " + "run_all.sh" + ")\n\nBlender previews are NOT Game-view proof.\n\n```\n" + "\n".join(lines) + "\n```\n")
print("\n".join(l[:240] for l in lines))
print(sum(1 for l in lines if " PASS - " in l), "PASS of", len(lines))
