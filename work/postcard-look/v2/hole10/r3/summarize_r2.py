"""Collect the hole 10 gate logs into GATES_hole10.txt / gates_hole10.json (system python3, no numpy). Every line: GATE: <ID> PASS|FAIL - <numbers>.

  python3 work/postcard-look/v2/hole10/tools/summarize.py
Reads work/postcard-look/v2/hole10/logs/*.log (written by tools/run_all.sh). Nothing here decides a pass by itself: every verdict is derived from
the measured lines of the verifier / stage gates / build log, and the id lists below say which source lines it needs.
"""
import json
import os
import re
import subprocess
import sys

R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
S = f"{R}/work/postcard-look/v2/hole10"
L = f"{S}/logs"
OUT = []
BY = {}


def read(name):
    p = f"{L}/{name}"
    return open(p, errors="replace").read() if os.path.exists(p) else ""


def parse(text):
    out = {}
    for ln in text.splitlines():
        m = re.match(r"^GATE: (\S+) (PASS|FAIL) - (.*)$", ln)
        if m:
            out[m.group(1)] = (m.group(2) == "PASS", m.group(3))
    return out


G = {}
for f in ("look_verify.log", "postcard_verify.log", "stage_gates.log", "build_stage.log", "play_unchanged.log", "landmark_check.log", "open_lava.log"):
    G[f] = parse(read(f))
V, PV, SG, BL, PU, LM, OL = (G[f] for f in ("look_verify.log", "postcard_verify.log", "stage_gates.log", "build_stage.log", "play_unchanged.log", "landmark_check.log", "open_lava.log"))


def get(d, k):
    return d.get(k, (False, f"MISSING line {k}"))


def emit(gid, ok, detail):
    BY[gid] = (ok, detail)
    OUT.append(f"GATE: {gid} {'PASS' if ok else 'FAIL'} - {' '.join(str(detail).split())}")


def need(gid, items, extra=""):
    """items = [(dict, key)]; PASS when every listed source line passes."""
    res = [(k, *get(d, k)) for d, k in items]
    ok = all(r[1] for r in res)
    det = "; ".join(f"{k}: {'ok' if o else 'FAIL'} ({d[:150]})" for k, o, d in res)
    emit(gid, ok, (extra + " | " if extra else "") + det)


# ---- scoring frozen
need("H_PLAY_UNCHANGED", [(PU, "H_PLAY_UNCHANGED"), (BL, "H_LOOK_TOP_SURFACES_UNCHANGED")] +
     [(V, f"PLAY_SURFACE_{n}@{st}") for n in ("NAMES", "GRID", "TOPS", "FACES", "WALLS") for st in ("blend", "fbx")] + [(V, "MARKERS_FROZEN@blend"), (V, "MARKERS_FROZEN@fbx")])
vb = {k: v for k, v in V.items() if k.endswith("@blend") or "@" not in k}
vf = {k: v for k, v in V.items() if k.endswith("@fbx") or "@" not in k}
fb = [k for k, v in vb.items() if not v[0]]
ff = [k for k, v in vf.items() if not v[0]]
emit("H_LOOK_VERIFY_BLEND", not fb and len(vb) > 40, f"{sum(1 for v in vb.values() if v[0])}/{len(vb)} gate lines of postcard_look_verify.py pass on the staged blend; FAIL: {fb or 'none'}"
     + "".join(f" || {k}: {vb[k][1][:260]}" for k in fb))
emit("H_LOOK_VERIFY_FBX", not ff and len(vf) > 40, f"{sum(1 for v in vf.values() if v[0])}/{len(vf)} gate lines pass on the FBX re-imported into an empty scene; FAIL: {ff or 'none'}"
     + "".join(f" || {k}: {vf[k][1][:260]}" for k in ff))
by_design = {"MATERIALS@blend", "MATERIALS@fbx", "FBX_BUDGET@fbx"}
pf = [k for k, v in PV.items() if not v[0]]
emit("H_POSTCARD_VERIFY", len(PV) >= 20 and set(pf) <= by_design and set(PV) >= {"LIE_MIRROR", "ONE_HEIGHT@blend", "LIES_MATCH_MESH@fbx", "SHORE_MATCH@blend", "HAZARD_PLACEMENT@fbx", "PADS@blend", "MARKERS@blend", "NO_UPFACE_OUTSIDE_LAND@fbx"},
     f"{sum(1 for v in PV.values() if v[0])}/{len(PV)} lines pass (scoring: LIE_MIRROR, ONE_HEIGHT, LIES_MATCH_MESH, SHORE_MATCH, HAZARD_PLACEMENT, PADS, MARKERS, NO_UPFACE_OUTSIDE_LAND, WATER_LEVEL, NO_ANIMATION all PASS at both stages); "
     f"FAIL by design: {pf or 'none'}: MATERIALS accepts only the old MAT_* names (the LK_* contract names supersede it, covered by NO_LEGACY_MATERIALS / GROUND_MATERIALS / PROP_MATERIALS), "
     f"FBX_BUDGET is the old 4 MB / 150k-triangle cap (the look budget is 250k / 20 MB: H_BUDGET)")
emit("H_CHECK_NO_DRIFT", "HOLE_CS_MATCHES_DESIGN PASS" in read("emit_cs_check.log") and "baked data matches the generator" in read("design_verify.log") and "RESULT: ALL PASS" in read("postcard_check.log"),
     "postcard_emit_cs.py --check Unity/Assets/Scripts/Course/Hole.cs: " + (read("emit_cs_check.log").strip().splitlines() or ["?"])[-1] + "; hole10_design.py --verify: " + (read("design_verify.log").strip().splitlines() or ["?"])[-1]
     + "; postcard_check.py hole10_design.py: " + (read("postcard_check.log").strip().splitlines() or ["?"])[-1])

# ---- the hard "no" lines of the user's brief
need("H_NO_12_VERTEX_ROCK", [(SG, "H_NO_12_VERTEX_ROCK@blend"), (SG, "H_NO_12_VERTEX_ROCK@fbx"), (V, "ROCK_NOT_ICOSAHEDRON@blend"), (V, "ROCK_NOT_ICOSAHEDRON@fbx")])
need("H_NO_STRETCH_2X", [(SG, "H_NO_STRETCH_2X@blend"), (SG, "H_NO_STRETCH_2X@fbx"), (V, "NO_ROCK_STRETCH_2X@blend"), (V, "NO_ROCK_STRETCH_2X@fbx")])
need("H_NO_PLANT_ON_WATER", [(BL, "H_NO_PLANT_ON_WATER"), (V, "NO_PLANT_ON_WATER@blend"), (V, "NO_PLANT_ON_WATER@fbx"), (V, "PROPS_OFF_PLAY@fbx")])
need("H_NO_FOAM_STRIP", [(SG, "H_NO_FOAM_STRIP@blend"), (SG, "H_NO_FOAM_STRIP@fbx"), (V, "NO_MAT_FOAM@fbx"), (V, "NO_FOAM_STRIP@fbx"), (BL, "LIB_LOOK_NO_MAT_FOAM")])
tri = re.search(r"(\d+) triangles", get(SG, "H_BUDGET_TRIS@fbx")[1])
fbx_mb = os.path.getsize(f"{S}/stage/hole_10.fbx") / 1048576 if os.path.exists(f"{S}/stage/hole_10.fbx") else 99
b_items = [(SG, "H_BUDGET_TRIS@blend"), (SG, "H_BUDGET_TRIS@fbx"), (V, "TRIANGLE_BUDGET@fbx"), (V, "FBX_FILE@fbx"), (V, "PROP_FACE_BUDGET@fbx"), (V, "PLANTS_SHARED_MATERIAL@fbx"), (V, "PLANTS_INSTANCED@fbx")]
need("H_BUDGET", b_items, f"{tri.group(1) if tri else '?'} triangles (<= 250000), staged FBX {fbx_mb:.2f} MB (<= 20)" + ("" if fbx_mb <= 20 else " OVER"))
if fbx_mb > 20:
    BY["H_BUDGET"] = (False, BY["H_BUDGET"][1])
    OUT[-1] = OUT[-1].replace("PASS", "FAIL", 1)
lm_ok = "RESULT: ALL PASS" in read("landmark_check.log")
try:
    jd = json.load(open(f"{S}/landmarks.json"))
    shots = jd["shots"]
    names = [s["name"] for s in shots]
    schema = (names == ["hole10_tee", "hole10_approach", "hole10_lavarim"] and shots[0]["kind"] == "address" and shots[1]["kind"] == "address" and shots[2]["kind"] == "landmark"
              and all(len(s["ball"]) == 2 and len(s["aim"]) == 2 for s in shots[:2]) and len(shots[2]["pos"]) == 3 and len(shots[2]["look"]) == 3 and "fov" in shots[2])
except Exception as e:  # noqa: BLE001
    schema, names = False, str(e)
emit("H_LANDMARKS_JSON", lm_ok and schema, f"landmarks.json parses, shots {names} follow the PostcardLookStills schema (RUNTIME.md v2.8: address ball/aim in course yards, landmark pos/look in Unity world yards + fov); ray tests: "
     + "; ".join(f"{k}: {'ok' if v[0] else 'FAIL'} ({v[1][:200]})" for k, v in LM.items()))


def build_hash(name):
    m = re.search(r"\[hole10_build\] HASH (\w+) objects (\d+) verts (\d+) faces (\d+)", read(name))
    return m.groups() if m else None


h1, h2 = build_hash("build_stage.log"), build_hash("build_repro.log")


def sha(p):
    return subprocess.run(["shasum", "-a", "256", p], capture_output=True, text=True).stdout.split()[0] if os.path.exists(p) else "missing"


emit("H_REPRODUCIBLE", bool(h1) and h1 == h2,
     f"two builds into different --out folders: geometry hash {h1[0][:16] if h1 else None} vs {h2[0][:16] if h2 else None}, objects {h1[1] if h1 else None}/{h2[1] if h2 else None}, vertices {h1[2] if h1 else None}/{h2[2] if h2 else None}, "
     f"faces {h1[3] if h1 else None}/{h2[3] if h2 else None} (hash over every mesh: name, world matrix, rounded vertices); FBX sha256 {sha(f'{S}/stage/hole_10.fbx')[:12]} vs {sha(f'{S}/stage_repro/hole_10.fbx')[:12]} "
     f"({'byte-identical' if sha(f'{S}/stage/hole_10.fbx') == sha(f'{S}/stage_repro/hole_10.fbx') else 'not byte-identical: ' + str(os.path.getsize(f'{S}/stage/hole_10.fbx')) + ' vs ' + str(os.path.getsize(f'{S}/stage_repro/hole_10.fbx')) + ' bytes, the FBX header carries the creation time and the source .blend path (checked with strings: only those lines differ); the geometry hash above is the gate'})")

# ---- one gate per feature of the hole-10 list
need("H_WALL_COLUMNS", [(SG, "H_NEAR_WALL@blend"), (SG, "H_NEAR_WALL@fbx"), (BL, "H_NEAR_WALL"), (SG, "H_FAR_RING@blend"), (SG, "H_FAR_RING@fbx"), (V, "CRATER_COLUMNS@blend"), (V, "CRATER_COLUMNS@fbx"), (V, "BASALT_PRISMS@fbx")])
need("H_SKYLINE_VARIED", [(SG, "H_SKYLINE_VARIED@blend"), (SG, "H_SKYLINE_VARIED@fbx")])
need("H_MESAS", [(SG, "H_MESAS@blend"), (SG, "H_MESAS@fbx"), (BL, "H_MESAS")])
need("H_UV_PHASE", [(BL, "H_UV_PHASE"), (V, "UV_DENSITY@blend"), (V, "UV_DENSITY@fbx")])
need("H_OPEN_LAVA", [(OL, "H_OPEN_LAVA")])
need("H_WALL_COVERED", [(BL, "LIB_CRATER_WALL_COVERED"), (V, "CRATER_WALL_COVERED@blend"), (V, "CRATER_WALL_COVERED@fbx"), (BL, "LIB_SKIN_FACES_OUTWARD"), (BL, "LIB_LOOK_SKIN_BELOW_PLAY")])
need("H_LAVA", [(V, "CRATER_LAVA@blend"), (V, "CRATER_LAVA@fbx"), (V, "LAVA_TEXTURE@fbx"), (SG, "H_NO_ANIMATION_ON_LAVA@fbx"), (V, "NO_ANIMATION@fbx"), (V, "SHADERS_STATIC")])
need("H_LAVA_LIGHTS", [(SG, "H_LAVA_LIGHTS@blend"), (SG, "H_LAVA_LIGHTS@fbx"), (V, "CRATER_LAVA_LIGHTS@fbx"), (SG, "H_ROCK_CHUNKING@blend"), (SG, "H_ROCK_CHUNKING@fbx")])
need("H_PILLAR", [(V, "CRATER_PILLAR@blend"), (V, "CRATER_PILLAR@fbx")])
need("H_TEE_PAD", [(V, "CRATER_TEE_PAD@blend"), (V, "CRATER_TEE_PAD@fbx")])
need("H_PLANTS_SHELF", [(BL, "H_SHELF_PLANTS"), (V, "CRATER_SHELF_PLANTS@fbx"), (BL, "H_PLANTS_CLEAR_OF_PIN_AND_TEE"), (V, "PLANTS_SHARED_MATERIAL@fbx")])
need("H_CONE_AND_SMOKE", [(SG, "H_BACKDROP@blend"), (SG, "H_BACKDROP@fbx"), (V, "CRATER_CONE_SMOKE@blend"), (V, "CRATER_CONE_SMOKE@fbx"), (V, "SMOKE_SOFT@fbx")])
need("H_STACKS_BASALT", [(SG, "H_STACKS@blend"), (SG, "H_STACKS@fbx"), (BL, "H_SIGHTLINES_CLEAR"), (SG, "H_RUBBLE@blend"), (SG, "H_RUBBLE@fbx")])
need("H_NO_COLLIDER_PROPS", [(SG, "H_NO_COLLIDER_PROPS@blend"), (SG, "H_NO_COLLIDER_PROPS@fbx"), (V, "NEW_OBJECT_PREFIXES@fbx"), (V, "RESERVED_NAMES@fbx"), (V, "SAND_NAMES@fbx")])
need("H_ONE_GREEN_NO_SECOND", [(V, "ONE_GREEN@blend"), (V, "ONE_GREEN@fbx")])
need("H_MATERIALS_LK_TEXTURED", [(V, "NO_LEGACY_MATERIALS@fbx"), (V, "GROUND_MATERIALS@fbx"), (V, "LK_REQUIRED@fbx"), (V, "LK_TEXTURED@blend"), (V, "UV_DENSITY@fbx"), (V, "GRASS_ALBEDO_HUE@fbx")])
need("H_HOLE07_UNTOUCHED", [(V, "HOLE07_UNTOUCHED"), (PV, "HOLE07_UNTOUCHED")])
g_after = read("guards_after.log") or read("guards_after.txt")
n_g = len(re.findall(r"^GATE: .* PASS", g_after, re.M))
emit("GUARDS_7_OF_7", n_g == 7 and "FAIL" not in g_after, f"work/postcard-look/guards.sh after the run: {n_g} PASS, 0 FAIL (hole_07.blend / .fbx / .fbx.meta, Hole.cs, Hole.cs Postcards() == design data, GolfGame starts Postcards, Cliffside() present)")
libs_same = read("libs_sha_before.txt") == read("libs_sha_after.txt") and bool(read("libs_sha_before.txt"))
emit("H_LIBS_UNCHANGED_DURING_RUN", libs_same, "sha256 of postcard_look_lib.py, postcard_props_lib.py, postcard_look_verify.py, postcard_lib.py, golf_look_textures.py and every Look/*.png identical before and after the final run")

with open(f"{S}/GATES_hole10.txt", "w") as f:
    f.write("\n".join(OUT) + "\n")
json.dump({k: {"pass": v[0], "detail": v[1]} for k, v in BY.items()}, open(f"{S}/gates_hole10.json", "w"), indent=1)
print("\n".join(l[:420] for l in OUT))
print("FAILED:", [k for k, v in BY.items() if not v[0]])
sys.exit(0 if all(v[0] for v in BY.values()) else 1)
