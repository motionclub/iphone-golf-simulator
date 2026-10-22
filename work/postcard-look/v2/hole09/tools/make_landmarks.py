"""make_landmarks.py - choose + verify the hole 9 Game-view cameras on a staged blend and write landmarks.json (RUNTIME.md stills schema).

Blender -b --factory-startup --python make_landmarks.py -- --blend X.blend --out landmarks.json [--check-only]
Unity world yards: x = course x, y = height (play surface 6.56), z = course d (down the hole); Blender metres: x_b = x_yd * 0.9144, y_b = z_yd * 0.9144, z_b = y_yd * 0.9144.
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
BLEND, OUT = opt("--blend"), opt("--out")
bpy.ops.wm.open_mainfile(filepath=BLEND)
HIDDEN = ("FLAG", "FLAG_POLE", "HOLE_CUP", "BALL_START", "MARKER_TEE", "MARKER_PIN", "MARKER_UP")
def mesh_arrays(o):
    me = o.data; mw = o.matrix_world
    V = [tuple(mw @ v.co) for v in me.vertices]
    me.calc_loop_triangles()
    return V, [tuple(t.vertices) for t in me.loop_triangles]
Vs, Fs, owner = [], [], []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name in HIDDEN or o.name.startswith("WATER_"): continue
    if all(c.name == "ASSET_LIBRARY" for c in o.users_collection): continue
    V, F = mesh_arrays(o); b = len(Vs); Vs += V; Fs += [(b + a, b + c, b + d) for a, c, d in F]; owner += [o.name] * len(F)
bvh = BVHTree.FromPolygons(Vs, Fs)
hole = PC.Hole(DES)
def ground(x, y):
    h = bvh.ray_cast((x, y, 60.0), (0, 0, -1), 200.0)
    return h[0].z if h[0] is not None else 0.0
def gz(x, y):  # ground only (terrain / play surfaces)
    best = None
    for h in (bvh.ray_cast((x, y, 60.0), (0, 0, -1), 200.0),):
        if h[0] is not None: best = h[0].z
    return best
def to_u(v): return [round(v[0] / YD, 2), round(v[2] / YD, 2), round(v[1] / YD, 2)]       # blender m -> unity yards (x, y, z)
def from_u(p): return Vector((p[0] * YD, p[2] * YD, p[1] * YD))
def hit_name(h): return owner[h[2]]
def visible_fraction(cam, pts, target_prefix):
    ok = 0; blockers = {}
    for p in pts:
        d = Vector(p) - cam; dist = d.length; d.normalize()
        h = bvh.ray_cast(cam, d, dist + 0.5)
        if h[0] is None: ok += 1; continue
        nm = hit_name(h)
        if nm.startswith(target_prefix) or (h[0] - Vector(p)).length < 0.6: ok += 1
        else: blockers[nm.split(".")[0]] = blockers.get(nm.split(".")[0], 0) + 1
    return ok / len(pts), blockers
def in_frustum(cam, look, fov_v_deg, aspect, pts, margin=0.0):
    f = (look - cam).normalized(); r = f.cross(Vector((0, 0, 1))).normalized(); u = r.cross(f).normalized()
    tv = math.tan(math.radians(fov_v_deg) / 2); th = tv * aspect
    ok = 0
    for p in pts:
        d = Vector(p) - cam; x, y, z = d.dot(r), d.dot(u), d.dot(f)
        if z > 0.3 and abs(x) <= z * th * (1 - margin) and abs(y) <= z * tv * (1 - margin): ok += 1
    return ok / len(pts)
def clearance(cam):
    worst = 99.0
    for az in range(0, 360, 30):
        for el in (-60, -30, 0, 30, 60):
            d = Vector((math.cos(math.radians(el)) * math.cos(math.radians(az)), math.cos(math.radians(el)) * math.sin(math.radians(az)), math.sin(math.radians(el))))
            h = bvh.ray_cast(cam, d, 3.0)
            if h[0] is not None: worst = min(worst, (h[0] - cam).length)
    return worst
# ---- ruin sample points (masonry vertices subsampled + the doorway centre + arch crown)
mas = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(("DRESS_RUIN", "DRESS_ARCH"))]
# REPAIR ROUND 1: the masonry now has a BURIED first course (hole09_masonry): only vertices above the ground (+6 cm) can be seen, so only those are sampled (a buried vertex is blocked by the terrain by construction)
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
P_all = _above_ground(np.vstack([np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]) for o in mas]))
rng = np.random.default_rng(9)
pts = [tuple(p) for p in P_all[rng.choice(len(P_all), 500, replace=False)]]
lo, hi = P_all.min(0), P_all.max(0); ctr = (lo + hi) / 2
corners = [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
print("ruin bbox (yd, unity xyz):", to_u(lo), to_u(hi), "centre", to_u(ctr))
# the landmark core = the broken arch + the doorway wall (the masonry within 6.5 m of the doorway point of the design's tall wall, repair round 1: the walls are no longer one DRESS_RUIN_00 mesh)
import postcard_lib as _P
import hole09_look as _HL
_w = DES.SCENERY["ruin"]["walls"]
_rc = np.array(_P.m(sum(w[k][0] for w in _w for k in ("p0", "p1")) / 8.0, sum(w[k][1] for w in _w for k in ("p0", "p1")) / 8.0))
_big = lambda q: _rc + (np.array(_P.m(*q)) - _rc) * _HL.RUIN_SCALE + np.array(_P.m(*_HL.RUIN_SHIFT_YD))
_door = (_big(_w[2]["p0"]) + _big(_w[2]["p1"])) / 2
P_arch = np.vstack([np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]) for o in mas if o.name.startswith("DRESS_ARCH")])
P_wall = np.vstack([np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices]) for o in mas if o.name.startswith("DRESS_RUIN")])
P_wall = P_wall[np.hypot(P_wall[:, 0] - _door[0], P_wall[:, 1] - _door[1]) < 6.5]
P_core = _above_ground(np.vstack([P_arch, P_wall]))
clo, chi = P_core.min(0), P_core.max(0)
core_corners = [(x, y, z) for x in (clo[0], chi[0]) for y in (clo[1], chi[1]) for z in (clo[2], chi[2])]
look_pt = Vector(((clo[0] + chi[0]) / 2, (clo[1] + chi[1]) / 2, (chi[2] + clo[2]) / 2 + 0.3))
all_pts_in_frame = lambda cam, look: in_frustum(cam, look, 50.0, 900 / 1600, pts, margin=0.0)
cands = []
cx_u, cz_u = look_pt[0] / YD, look_pt[1] / YD
for rr in (22, 26, 30, 34, 40, 46):
    for az in range(60, 200, 10):                         # compass: 90 = east (fairway side), 180 = south; x = cx + r sin(az), z = cz - r cos(az) ... course d grows southwards
        for h in (14, 18, 22, 26):
            pos_u = [cx_u + rr * math.sin(math.radians(az)), h, cz_u - rr * math.cos(math.radians(az))]
            cands.append(pos_u)
rows = []
for pu in cands:
    cam = from_u(pu)
    vis, bl = visible_fraction(cam, pts, ("DRESS_RUIN", "DRESS_ARCH", "DRESS_BLOCK"))
    fr = in_frustum(cam, look_pt, 50.0, 900 / 1600, core_corners, margin=0.02)      # the stills tool renders 900x1600 (portrait): the whole core box must fit with a 4 % margin
    allr = all_pts_in_frame(cam, look_pt)
    cl = clearance(cam)
    dist = (look_pt - cam).length / YD
    rows.append((vis, fr, cl, dist, pu, bl, allr))
rows.sort(key=lambda r: (-(r[0] >= 0.99 and r[1] >= 1.0 and r[2] >= 1.0), -round(r[6], 1), r[3] + (0.0 if r[4][1] >= 24 else 6.0)))      # nearest; the high (26 yd) look-down keeps the ridge in the frame instead of half sky in the 900x1600 portrait
for r in rows[:8]: print("cand", [round(v, 1) for v in r[4]], "visible", round(r[0], 3), "core in frustum", round(r[1], 2), "all pts in frame", round(r[6], 2), "clear", round(r[2], 1), "dist yd", round(r[3], 1), r[5])
best = rows[0]
pos_u = best[4]
look_u = to_u(look_pt)
# ---- approach shot: ball + aim from the design (a drive that rests on the default aim)
ball_a, aim_a = (13.5, 269.0), (6.0, 416.0)
ball_t, aim_t = (0.0, 0.0), (3.0, 60.0)
lie_a, lie_t = str(hole.lie_at(ball_a)), str(hole.lie_at(ball_t))
print("lies: approach ball", lie_a, "tee ball", lie_t)
def address_cam(ball, aim):
    bx, by = ball[0] * YD, ball[1] * YD
    d = Vector((aim[0] * YD - bx, aim[1] * YD - by, 0)).normalized()
    b = Vector((bx, by, ground(bx, by) + 0.06 * YD))
    return b - d * 4.5 * YD + Vector((0, 0, 2.4 * YD)), b + d * 1.5 * YD, b
checks = {}
for nm, ball, aim in (("tee", ball_t, aim_t), ("approach", ball_a, aim_a)):
    cam, look, b = address_cam(ball, aim)
    vis, bl = visible_fraction(cam, [tuple(b + Vector((0, 0, 0.0)))], "TERRAIN")
    # ball visible: ray from the camera to the ball centre meets only ground at the ball (or nothing)
    d = (b - cam); dist = d.length; d.normalize(); h = bvh.ray_cast(cam, d, dist - 0.02)
    bxy = np.array([ball[0] * YD, ball[1] * YD])
    near_props = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.name.startswith(("PLANT_", "ROCK_", "DRESS_")) or o.name.startswith(("ROCK_SKIN",)) or all(c.name == "ASSET_LIBRARY" for c in o.users_collection): continue
        W = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
        if len(W) and np.hypot(W[:, 0] - bxy[0], W[:, 1] - bxy[1]).min() < 1.5: near_props.append(o.name)
    checks[nm] = dict(camera=to_u(cam), look=to_u(look), ball_blocked_by=(owner[h[2]] if h[0] is not None else None), props_within_1_5m=near_props, clearance_m=round(clearance(cam), 2))
print("address checks", json.dumps(checks))
shots = [
    dict(name="hole09_tee", hole=9, kind="address", ball=list(ball_t), aim=list(aim_t), putting=False, label="tee shot: 4.5 yd behind the ball, 2.4 yd up, 60 deg"),
    dict(name="hole09_approach", hole=9, kind="address", ball=list(ball_a), aim=list(aim_a), putting=False, label="second shot over the channel gap from where a default drive rests (13.5, 269)"),
    dict(name="hole09_ruin", hole=9, kind="landmark", pos=[round(v, 2) for v in pos_u], look=[round(v, 2) for v in look_u], fov=50, label="LANDMARK: the ruin ridge (coursed masonry walls with a doorway, broken arch, fallen blocks) seen from 34 yd south of it and 19 yd above the ridge, looking north along the ridge (the whole ruin only fits the 900x1600 portrait frame from here)")]
extra = [dict(name="hole09_aerial", kind="landmark", pos=[70, 130, 430], look=[-35, 5, 255], fov=45, preview_res=[1600, 900], label="oblique aerial like split.jpg (preview only, not a Game-view shot)")]
rep = dict(visible_fraction=round(best[0], 3), core_in_frame_fraction=round(best[1], 3), all_masonry_points_in_frame=round(best[6], 3), camera_clearance_m=round(best[2], 2), distance_yd=round(best[3], 1), blockers=best[5],
           approach_ball_lie=lie_a, tee_ball_lie=lie_t, address=checks)
if OUT:
    json.dump(dict(hole=9, name="Split", units="Unity world yards (x = course x, y = height, play surface 6.56, z = course d); address shots use course yards [x, d]; tee marker = world origin", shots=shots, extra_previews=extra, verification=rep), open(OUT, "w"), indent=1)
    print("wrote", OUT)
print("RESULT", json.dumps(rep))
