"""Re-create postcard_look_verify.g_crater_wall_cover with our BVH and list which wall targets are exposed."""
import sys, os, runpy, math
sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
import numpy as np, bpy
from mathutils import Vector
import postcard_lib as P
import postcard_look_lib as L
args = sys.argv[sys.argv.index("--") + 1:]
BL = args[0]
OUT = os.path.join(REPO, "work/postcard-look/v2/ground/tools/_scratch_10")
_o = P.start; P.start = lambda name, out_dir=None: _o(name, out_dir=OUT)
sys.argv = [os.path.join(REPO, "work/postcard-look/baseline/scripts", "hole10_build.py")]
try: runpy.run_path(sys.argv[0], run_name="__main__")
except SystemExit: pass
P.start = _o; D = P._ST["D"]
sc = D.SCENERY["crater"]; YD = P.YD
bpy.ops.wm.open_mainfile(filepath=BL)
pz = D.play_z
cx, cy = sc.get("cx", 0.0) * YD, sc.get("cd", 0.0) * YD
rim = sc.get("rim_radius", 150.0) * YD
tee = np.array(bpy.data.objects["MARKER_TEE"].matrix_world.translation)
pin = np.array(bpy.data.objects["MARKER_PIN"].matrix_world.translation)
vps = []
for dx, dy in ((0, 0), (40, 0), (-40, 0), (0, 40), (0, -40)): vps.append(("aerial", np.array((cx+dx, cy+dy, pz+60.0))))
for t in (0.0, .25, .5, .75, 1.0): vps.append(("low", np.array((tee[0]+(pin[0]-tee[0])*t, tee[1]+(pin[1]-tee[1])*t, pz+2.2))))
for k in range(8):
    a = 2*math.pi*k/8; vps.append(("oblique", np.array((cx+0.6*rim*math.cos(a), cy+0.6*rim*math.sin(a), pz+25.0))))
vis = [o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith(("WATER_", "LAVA_", "PLANT_", "DRESS_SMOKE")) and o.name.split(".")[0] not in ("CAM",)]
# only exported geometry: skip cameras/lights (not meshes)
terr = L._terrain_ob(D)
W, ls, lt, lv, mi, pn = L._mesh_arrays(terr)
pol = L._poly_of_loop(ls, lt, len(lv))
cen = np.zeros((len(ls), 3)); np.add.at(cen, pol, W[lv]); cen /= lt[:, None]
sel = (pn[:, 2] <= 0.5) & (cen[:, 2] < pz - 0.02) & (cen[:, 2] > -6.5)
T_pts, T_nrm = cen[sel], pn[sel]
rng = np.random.default_rng(1010); pick = rng.choice(len(T_pts), min(900, len(T_pts)), replace=False)
T_pts, T_nrm = T_pts[pick], T_nrm[pick]
bv_all = L._bvh_of(vis); bv_t = L._bvh_of([terr])
n_vis = n_exp = 0; ex = []
for p, nr in zip(T_pts, T_nrm):
    cands = []
    for kind, vp in vps:
        d = p - vp
        if float(d @ nr) < 0: cands.append((float(np.linalg.norm(d)), kind, vp))
    cands.sort(key=lambda t: t[0])
    for dist, kind, vp in cands[:3]:
        d = (p - vp) / dist
        # first FRONT-facing hit (back faces culled), like postcard_look_verify.TriIndex.first_front
        o_ = Vector(vp); dv_ = Vector(d); trav = 0.0; h = None; hobj = None
        for _ in range(12):
            r = bv_all.ray_cast(o_, dv_, dist + 25.0 - trav)
            if r[0] is None: break
            if r[1].dot(dv_) < 0.0:
                h = (r[0], r[1], r[2], trav + r[3]); break
            o_ = r[0] + dv_ * 1e-4; trav += r[3] + 1e-4
        if h is None: continue
        if h[0].z >= pz - 0.02: continue
        n_vis += 1
        ht = bv_t.ray_cast(Vector(vp), Vector(d), dist + 25.0)
        is_t = ht[0] is not None and (ht[0] - h[0]).length < 1e-3 and h[1].z < 0.5
        if is_t:
            n_exp += 1; ex.append((kind, tuple(np.round(p, 1)), tuple(np.round(h[0], 1)), tuple(np.round(nr, 2))))
print("n_vis", n_vis, "exposed", n_exp)
for e in ex[:25]: print("EXP", e)
import collections
print("by hit z:", collections.Counter(round(e[2][2]) for e in ex).most_common(12))
print("---- ray trace")
skin_bvhs = {o.name: L._bvh_of([o]) for o in L._skin_objs()}
terr_b = bv_t
def trace(vp, tgt):
    d = (tgt - vp); dist = float(np.linalg.norm(d)); d = d / dist
    o = Vector(vp); dv = Vector(d); trav = 0.0; out = []
    for _ in range(10):
        r = bv_all.ray_cast(o, dv, dist + 25.0 - trav)
        if r[0] is None: break
        who = []
        for nm, b in skin_bvhs.items():
            rr = b.ray_cast(o, dv, dist + 25.0 - trav)
            if rr[0] is not None and abs(rr[3] - r[3]) < 1e-5: who.append(nm)
        rt = terr_b.ray_cast(o, dv, dist + 25.0 - trav)
        if rt[0] is not None and abs(rt[3] - r[3]) < 1e-5: who.append("TERRAIN")
        out.append((tuple(round(v, 2) for v in r[0]), who, "front" if r[1].dot(dv) < 0 else "BACK", tuple(round(v, 2) for v in r[1])))
        o = r[0] + dv * 1e-4; trav += r[3] + 1e-4
    return out
for kind, vp in vps:
    if kind == "low" and abs(vp[0] - (tee[0] + (pin[0] - tee[0]) * 0.75)) < 1e-6:
        for tgt in (np.array((206.8, 140.9, 5.5)), np.array((207.2, 154.6, 4.4))):
            print("trace", kind, tuple(np.round(vp, 1)), "->", tuple(tgt))
            for h in trace(vp, tgt)[:6]: print("   ", h)
