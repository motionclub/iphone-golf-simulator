"""landmarks_check.py - H_LANDMARKS_JSON: re-derives the Game-view cameras from landmarks.json (independent of make_landmarks.py) and checks them on a blend.

Blender -b --factory-startup --python landmarks_check.py -- --blend stage/hole_09.blend --json landmarks.json [--previews DIR]
"""
import bpy, sys, json, math, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts"
sys.path.insert(0, HERE)
import postcard_check as PC
import hole09_design as DES
YD = 0.9144
A = sys.argv[sys.argv.index("--") + 1:]
def opt(n, d=None): return A[A.index(n) + 1] if n in A else d
BLEND, JS, PREV = opt("--blend"), opt("--json"), opt("--previews")
RES = []
def gate(i, ok, d):
    RES.append((i, ok)); print(f"GATE: {i} {'PASS' if ok else 'FAIL'} - {d}", flush=True)
bpy.ops.wm.open_mainfile(filepath=BLEND)
cfg = json.load(open(JS))
hole = PC.Hole(DES)
HIDDEN = ("FLAG", "FLAG_POLE", "HOLE_CUP", "BALL_START", "MARKER_TEE", "MARKER_PIN", "MARKER_UP")
Vs, Fs, owner = [], [], []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name in HIDDEN or o.name.startswith("WATER_") or all(c.name == "ASSET_LIBRARY" for c in o.users_collection): continue
    me = o.data; me.calc_loop_triangles(); mw = o.matrix_world; b = len(Vs)
    Vs += [tuple(mw @ v.co) for v in me.vertices]; Fs += [tuple(b + i for i in t.vertices) for t in me.loop_triangles]; owner += [o.name] * len(me.loop_triangles)
bvh = BVHTree.FromPolygons(Vs, Fs)
tee_m = bpy.data.objects["MARKER_TEE"]; pin_m = bpy.data.objects["MARKER_PIN"]
def ground(x, y):
    h = bvh.ray_cast((x, y, 60.0), (0, 0, -1), 200.0); return h[0].z if h[0] is not None else None
# 1. schema
shots = {s["name"]: s for s in cfg["shots"]}
need = {"hole09_tee": ("address", ("ball", "aim")), "hole09_approach": ("address", ("ball", "aim")), "hole09_ruin": ("landmark", ("pos", "look", "fov"))}
bad = []
for n, (kind, keys) in need.items():
    s = shots.get(n)
    if s is None: bad.append(f"{n} missing"); continue
    if s.get("kind") != kind or s.get("hole") != 9: bad.append(f"{n} kind/hole")
    for k in keys:
        v = s.get(k)
        if v is None or (isinstance(v, list) and not all(isinstance(x, (int, float)) and math.isfinite(x) for x in v)): bad.append(f"{n}.{k}")
    for k in ("ball", "aim"):
        if k in s and len(s[k]) != 2: bad.append(f"{n}.{k} length")
    for k in ("pos", "look"):
        if k in s and len(s[k]) != 3: bad.append(f"{n}.{k} length")
gate("H_LANDMARKS_JSON_SCHEMA", not bad and list(shots)[:3] == ["hole09_tee", "hole09_approach", "hole09_ruin"], f"3 shots {list(shots)} (tee = default address, approach = address with ball + aim in course yards, ruin = landmark pos / look in Unity world yards + fov), problems {bad or 'none'}; schema = RUNTIME.md v2.8 (name, hole, kind, ball, aim, pos, look, fov)")
# 2. mapping check: tee marker lands at the world origin, pin at the design pin
tm = np.array(tee_m.matrix_world.translation); pm = np.array(pin_m.matrix_world.translation)
pin_u = (pm[0] / YD, pm[1] / YD)
gate("H_LANDMARKS_MAPPING", abs(tm[0]) < 1e-6 and abs(tm[1]) < 1e-6 and math.hypot(pin_u[0] - DES.CENTERLINE[-1][0], pin_u[1] - DES.CENTERLINE[-1][1]) < 0.05,
     f"MARKER_TEE at Blender ({tm[0]:.3f}, {tm[1]:.3f}) = world origin; MARKER_PIN {pin_u[0]:.2f}, {pin_u[1]:.2f} yd vs design pin {DES.CENTERLINE[-1]}: Unity world yards = (x_b / 0.9144, z_b / 0.9144 (height), y_b / 0.9144 (down the hole)); HoleView.BuildFromModel maps tee -> tee, pin -> pin with uniform scale 1.0936 and zero yaw (course axes = model axes), tee marker height {tm[2] / YD:.2f} yd")
# 3. address shots: ball lies, aim lies, clear ground
rows = []
for n in ("hole09_tee", "hole09_approach"):
    s = shots[n]; b = tuple(s["ball"]); a = tuple(s["aim"])
    lie_b, lie_a = hole.lie_at(b), hole.lie_at(a)
    bx, by = b[0] * YD, b[1] * YD
    gz = ground(bx, by)
    d = Vector((a[0] * YD - bx, a[1] * YD - by, 0)).normalized()
    ball = Vector((bx, by, gz + 0.06 * YD))
    cam = ball - d * 4.5 * YD + Vector((0, 0, 2.4 * YD)); look = ball + d * 1.5 * YD
    dd = (ball - cam); L_ = dd.length; dd.normalize(); h = bvh.ray_cast(cam, dd, L_ - 0.03)
    cam_ground = ground(cam.x, cam.y)
    # nearest prop to the ball (vertices)
    near = 99.0
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith(("PLANT_", "ROCK_", "DRESS_")) and not o.name.startswith("ROCK_SKIN") and not all(c.name == "ASSET_LIBRARY" for c in o.users_collection):
            W = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
            if len(W): near = min(near, float(np.hypot(W[:, 0] - bx, W[:, 1] - by).min()))
    ok = str(lie_b) in ("Tee", "Fairway") and str(lie_a) in ("Fairway", "Green") and h[0] is None and (cam_ground is None or cam.z - cam_ground > 1.0) and near >= 1.5
    rows.append((n, ok, f"{n}: ball {b} lie {lie_b}, aim {a} lie {lie_a}; the camera (CameraRig.FrameAddress: 4.5 yd back, 2.4 yd up) at Unity ({cam.x / YD:.1f}, {cam.z / YD:.2f}, {cam.y / YD:.1f}) looks at ({look.x / YD:.1f}, {look.z / YD:.2f}, {look.y / YD:.1f}); "
                  f"nothing between camera and ball (first hit {owner[h[2]] if h[0] is not None else 'none'}), camera {(cam.z - (cam_ground or 0)) / YD:.1f} yd over the ground, nearest prop vertex {near:.1f} m from the ball"))
gate("H_LANDMARKS_ADDRESS", all(r[1] for r in rows), " | ".join(r[2] for r in rows))
# 4. landmark: visibility, framing, clearance
s = shots["hole09_ruin"]
cam = Vector((s["pos"][0] * YD, s["pos"][2] * YD, s["pos"][1] * YD)); look = Vector((s["look"][0] * YD, s["look"][2] * YD, s["look"][1] * YD)); fov = float(s["fov"])
mas = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(("DRESS_RUIN", "DRESS_ARCH"))]
_GV, _GF = [], []
for _o in bpy.data.objects:                                            # ground-only BVH (the play surfaces + terrain: the masonry itself must not count as ground)
    if _o.type == 'MESH' and _o.name.startswith(("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER")):
        _o.data.calc_loop_triangles()
        _b = len(_GV)
        _GV += [tuple(_o.matrix_world @ v.co) for v in _o.data.vertices]
        _GF += [tuple(_b + i for i in t.vertices) for t in _o.data.loop_triangles if t.normal.z > 0.3]
_gbvh = BVHTree.FromPolygons(_GV, _GF)
def _gz(x, y):
    h = _gbvh.ray_cast(Vector((x, y, 80.0)), Vector((0, 0, -1)), 200.0)
    return h[0].z if h[0] is not None else None
def _above_ground(P3):
    keep = [i for i, q in enumerate(P3) if (_gz(q[0], q[1]) is None) or q[2] >= _gz(q[0], q[1]) + 0.06]
    return P3[keep]
Pm = _above_ground(np.vstack([np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]) for o in mas]))     # repair round 1: only vertices above the ground can be seen (the first course is buried)
rng = np.random.default_rng(1234)
pts = [tuple(p) for p in Pm[rng.choice(len(Pm), min(800, len(Pm)), replace=False)]]
ok_n, blockers = 0, {}
for p in pts:
    d = Vector(p) - cam; dist = d.length; d.normalize(); h = bvh.ray_cast(cam, d, dist + 0.5)
    if h[0] is None or owner[h[2]].startswith(("DRESS_RUIN", "DRESS_ARCH", "DRESS_BLOCK")) or (h[0] - Vector(p)).length < 0.6: ok_n += 1
    else: blockers[owner[h[2]].split(".")[0]] = blockers.get(owner[h[2]].split(".")[0], 0) + 1
f = (look - cam).normalized(); r = f.cross(Vector((0, 0, 1))).normalized(); u = r.cross(f).normalized()
tv = math.tan(math.radians(fov) / 2); th = tv * 900 / 1600
def frac_in(points, margin=0.0):
    c = 0
    for p in points:
        v = Vector(p) - cam; x, y, z = v.dot(r), v.dot(u), v.dot(f)
        if z > 0.3 and abs(x) <= z * th * (1 - margin) and abs(y) <= z * tv * (1 - margin): c += 1
    return c / len(points)
import postcard_lib as _P
import hole09_look as _HL
_w = DES.SCENERY["ruin"]["walls"]
_rc = np.array(_P.m(sum(w[k][0] for w in _w for k in ("p0", "p1")) / 8.0, sum(w[k][1] for w in _w for k in ("p0", "p1")) / 8.0))
_big = lambda q: _rc + (np.array(_P.m(*q)) - _rc) * _HL.RUIN_SCALE + np.array(_P.m(*_HL.RUIN_SHIFT_YD))
_door = (_big(_w[2]["p0"]) + _big(_w[2]["p1"])) / 2
P_arch = np.vstack([np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]) for o in mas if o.name.startswith("DRESS_ARCH")])
P_wall = np.vstack([np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]) for o in mas if o.name.startswith("DRESS_RUIN")])
P_wall = P_wall[np.hypot(P_wall[:, 0] - _door[0], P_wall[:, 1] - _door[1]) < 6.5]       # the doorway wall = the masonry within 6.5 m of the design's tall-wall doorway point
Pc = _above_ground(np.vstack([P_arch, P_wall]))
corners = [(x, y, z) for x in (Pc[:, 0].min(), Pc[:, 0].max()) for y in (Pc[:, 1].min(), Pc[:, 1].max()) for z in (Pc[:, 2].min(), Pc[:, 2].max())]
worst = 99.0
for az in range(0, 360, 20):
    for el in (-70, -40, -15, 0, 20, 50):
        dv = Vector((math.cos(math.radians(el)) * math.cos(math.radians(az)), math.cos(math.radians(el)) * math.sin(math.radians(az)), math.sin(math.radians(el))))
        hh = bvh.ray_cast(cam, dv, 3.0)
        if hh[0] is not None: worst = min(worst, (hh[0] - cam).length)
cg = ground(cam.x, cam.y)
ok = ok_n / len(pts) >= 0.97 and frac_in(corners, 0.0) == 1.0 and worst >= 1.0 and (cg is None or cam.z - cg > 1.0)
gate("H_LANDMARKS_RUIN_VISIBLE", ok, f"landmark camera Unity pos {s['pos']} look {s['look']} fov {fov:g} (900x1600): {ok_n}/{len(pts)} ray samples on the masonry (walls + doorway + arch) reach the camera unblocked ({ok_n / len(pts):.1%}, need >= 97 %), blockers {blockers or 'none'}; "
     f"the core box (tall doorway wall + broken arch) is inside the frame: {frac_in(corners, 0.0):.0%} of its 8 corners ({frac_in(corners, 0.05):.0%} with a 5 % margin), all masonry {frac_in(pts):.0%}; nothing within {worst:.1f} m of the camera (need >= 1.0), camera {(cam.z - (cg or 0)) / YD:.1f} yd over the ground; distance to the ruin {(look - cam).length / YD:.0f} yd")
# 5. previews exist
if PREV:
    names = ["hole09_tee", "hole09_approach", "hole09_ruin", "hole09_aerial"]
    miss = [n for n in names if not os.path.exists(os.path.join(PREV, n + ".png"))]
    gate("H_LANDMARKS_PREVIEWS", not miss, f"Blender EEVEE previews from these cameras in {PREV}: missing {miss or 'none'} (previews are NOT Game-view proof)")
fails = [i for i, ok in RES if not ok]
print("LANDMARKS_CHECK", len(RES), "gates", len(fails), "FAIL", fails)
sys.exit(1 if fails else 0)
