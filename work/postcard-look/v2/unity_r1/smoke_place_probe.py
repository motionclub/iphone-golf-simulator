# Blender -b --factory-startup --python smoke_place_probe.py -- [blend]
# Where could Crater's smoke cards stand so that the plume is readable in each proof frame (SMOKE_IN_FRAME)? Evaluates flat cards (the library card is a 4x2 grid bowed by <= 0.09 w) with the verifier's own
# camera model, occluders and shader-alpha formula, vectorised over the pixel grid, and prints the best placements per frame plus the best trio. READ-ONLY: nothing is saved; the hole files are not touched.
import sys, os, math, json, importlib.util
import numpy as np
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
import bpy
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
blend = argv[0] if argv else REPO + "/blender/hole_10.blend"
opts = m.parse_args(["10"]); design, dpath = m.load_design(10, None); C = m.Ctx(10, design, dpath, opts)
bpy.ops.wm.open_mainfile(filepath=blend, load_ui=False)
S = m.Snap("blend", C)
YD = m.YD
# existing smoke cards are NOT occluders and are ignored: this probe is about where new / moved cards should stand
occ = [o for n, o in S.meshes.items() if not n.startswith("DRESS_SMOKE") and not (S.used_mats(o) and S.used_mats(o) <= {"LK_SURF", "LK_FALL"})]
obvh = m.bvh_of(S, occ)
spec_rt = m.smoke_runtime_spec()
a_tex = m.look_png(C, "Smoke_C")[..., 3].astype(float)
cams = m.smoke_shot_cameras(S, C)
Wp, Hp = m.SMOKE_VIS["grid"]
cr = C.sc["crater"]; ccx, ccy = cr["cx"] * YD, cr["cd"] * YD; rim = cr["rim_radius"] * YD; wall_in = C.sc["wall_ring"]["r_inner"] * YD
FR = []                      # per camera: origin, dirs (Hp, Wp, 3), occluder distance (Hp, Wp)
for (name, pos, fwd, up, right, fov) in cams:
    th = math.tan(math.radians(fov) / 2.0); aspect = 900.0 / 1600.0
    D = np.zeros((Hp, Wp, 3)); OD = np.full((Hp, Wp), 1e9)
    for j in range(Hp):
        yv = (1.0 - (j + 0.5) / Hp * 2.0) * th
        for i in range(Wp):
            xv = ((i + 0.5) / Wp * 2.0 - 1.0) * th * aspect
            d = (fwd + right * xv + up * yv).normalized()
            D[j, i] = (d.x, d.y, d.z)
            if obvh is not None:
                loc, _n, _idx, dd = obvh.ray_cast(pos, d)
                if loc is not None:
                    OD[j, i] = dd
    FR.append((name, np.array(pos), D, OD))
    print(f"PROBE frame {name}: cam ({pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f}) m, {float((OD > 1e8).mean()) * 100:.1f} % of the pixels see open sky", flush=True)

def card_alpha(frame, cx, cy, cz, w, h, face=(0.0, 0.0)):
    """accumulated alpha grid of one flat card (bottom centre (cx, cy, cz), facing `face`) for one frame"""
    name, pos, D, OD = frame
    n = np.array([face[0] * YD - cx, face[1] * YD - cy, 0.0]); n /= np.linalg.norm(n)
    across = np.array([-n[1], n[0], 0.0])
    p0 = np.array([cx, cy, cz])
    denom = D @ n
    with np.errstate(divide="ignore", invalid="ignore"):
        t = ((p0 - pos) @ n) / denom
    q = pos + D * t[..., None]
    u = ((q - p0) @ across) / w + 0.5
    v = (q[..., 2] - cz) / h
    ok = (t > 0) & (t < OD) & (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1)
    a = np.zeros_like(t)
    if ok.any():
        a[ok] = m.smoke_effective_alpha(np.stack([u[ok], v[ok]], 1), a_tex, spec_rt)
    return a

rng = np.random.default_rng(7)
best = {fr[0]: [] for fr in FR}
cands = []
for _ in range(900):
    ang = rng.uniform(0, 2 * math.pi); r = rng.uniform(rim + 5.0, wall_in + 120.0)            # beyond the rim (CRATER_CONE_SMOKE), up to behind the wall
    cx, cy = ccx + r * math.cos(ang), ccy + r * math.sin(ang)
    cands.append((cx, cy, rng.uniform(0.0, 60.0), rng.uniform(70.0, 170.0), rng.uniform(90.0, 200.0)))
for c in cands:
    for fr in FR:
        sh = float((card_alpha(fr, *c) >= m.SMOKE_VIS["alpha_readable"]).mean())
        best[fr[0]].append((sh, c))
for name, lst in best.items():
    lst.sort(key=lambda t: -t[0])
    print(f"PROBE best single cards for {name} (need >= {m.SMOKE_VIS['share_min'] * 100:.1f} %):")
    for sh, c in lst[:5]:
        print(f"   {sh * 100:5.2f} %  card bottom centre ({c[0]:.0f}, {c[1]:.0f}, z {c[2]:.0f}) m  w {c[3]:.0f} h {c[4]:.0f}  = {math.hypot(c[0] - ccx, c[1] - ccy) / YD:.0f} yd from the crater centre, wall ring at {wall_in / YD:.0f}")
# one card per frame (the best of each), all three together in every frame
trio = [best[fr[0]][0][1] for fr in FR]
print("PROBE trio (the best single card of each frame, all three standing together):")
for fr in FR:
    tot = np.zeros((Hp, Wp)); tr = np.ones((Hp, Wp))
    for c in trio:
        tr *= 1.0 - card_alpha(fr, *c)
    print(f"   {fr[0]}: {float(((1 - tr) >= m.SMOKE_VIS['alpha_readable']).mean()) * 100:.2f} %")
print("PROBE trio cards:", json.dumps([[round(x, 1) for x in c] for c in trio]))

# ---- confirm with the verifier's own ray-cast gate on real card meshes (bowed 4 x 2 grid like postcard_props_lib.build_smoke_cards), in memory only
distinct = []
for c in trio:
    if not any(np.allclose(c, d) for d in distinct):
        distinct.append(c)
for o in [o for o in bpy.data.objects if o.name.startswith("DRESS_SMOKE")]:
    bpy.data.objects.remove(o)
mat = bpy.data.materials.get("LK_SMOKE") or bpy.data.materials.new("LK_SMOKE")
for k, (cx, cy, cz, w, h) in enumerate(distinct):
    verts, faces, uvs = [], [], []
    cols, rows = 4, 2
    for r_ in range(rows + 1):
        for c_ in range(cols + 1):
            u_, v_ = c_ / cols, r_ / rows
            x_ = u_ - 0.5
            verts.append((x_ * w, -0.18 * (1 - (2 * x_) ** 2) * w * 0.5, v_ * h)); uvs.append((u_, v_))
    for r_ in range(rows):
        for c_ in range(cols):
            a = r_ * (cols + 1) + c_
            faces.append((a, a + 1, a + cols + 2, a + cols + 1))
    me = bpy.data.meshes.new(f"DRESS_SMOKE_P{k}"); me.from_pydata(verts, [], faces); me.update(); me.materials.append(mat)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    ob = bpy.data.objects.new(f"DRESS_SMOKE_P{k}", me); (bpy.data.collections.get("ENVIRONMENT") or bpy.context.scene.collection).objects.link(ob); ob.parent = bpy.data.objects.get("HOLE_10_ROOT")
    yaw = math.atan2(0.0 - cy, 0.0 - cx) - math.pi / 2 + math.pi
    ob.location = (cx, cy, cz); ob.rotation_euler = (0, 0, yaw)
bpy.context.view_layer.update()
S2 = m.Snap("blend", C)
ok, detail = m.g_smoke_frames(S2, C)
print("PROBE verifier on real meshes:", "PASS" if ok else "FAIL", detail)
print("PROBE cards used:", json.dumps([[round(x, 1) for x in c] for c in distinct]))
