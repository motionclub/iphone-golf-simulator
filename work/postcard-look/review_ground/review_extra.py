"""Reviewer extras: surf edge alpha, exposed lip band above the skin, TERRAIN lip material, extra preview renders.
Blender -b --factory-startup --python review_extra.py -- --hole 08 [--no-render]"""
import sys, os, math, runpy
sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import postcard_lib as P

args = sys.argv[sys.argv.index("--") + 1:]
H = args[args.index("--hole") + 1].zfill(2)
RG = os.path.join(REPO, "work", "postcard-look", "review_ground")
OUT = os.path.join(RG, f"check_hole{H}")
_o = P.start
P.start = lambda name, out_dir=None: _o(name, out_dir=os.path.join(OUT, "D_build2"))
sys.argv = [os.path.join(REPO, "work/postcard-look/baseline/scripts", f"hole{H}_build.py")]
try:
    runpy.run_path(sys.argv[0], run_name="__main__")
except SystemExit:
    pass
D = P._ST["D"]
PZ = D.play_z
bpy.ops.wm.open_mainfile(filepath=os.path.join(RG, f"smoke_hole{H}", f"smoke_hole{H}.blend"))


def W_of(o):
    mw = np.array(o.matrix_world)
    co = np.array([v.co[:] for v in o.data.vertices])
    return co @ mw[:3, :3].T + mw[:3, 3]


def tree(obs, up_only=False):
    V, F = [], []
    for o in obs:
        W = W_of(o)
        b = len(V)
        V += [tuple(p) for p in W.tolist()]
        for p in o.data.polygons:
            F.append([b + v for v in p.vertices])
    return BVHTree.FromPolygons(V, F)


# ---------------- (a) surf: alpha at the visible open edges
surfs = [o for o in bpy.data.objects if o.name.startswith("WATER_SURF")]
if surfs:
    hard, tot, amax_open = 0, 0, 0.0
    for o in surfs:
        me = o.data
        W = W_of(o)
        A = np.array([c.color[3] for c in me.color_attributes["Col"].data])
        cnt = {}
        for e in me.edges:
            cnt[e.key] = 0
        for p in me.polygons:
            for k in p.edge_keys:
                cnt[k] += 1
        bverts = sorted({v for k, c in cnt.items() if c == 1 for v in k})
        bverts = np.array(bverts)
        sd = P.signed_dist_m(D, W[bverts, 0], W[bverts, 1])
        vis = sd > 0.5                                 # boundary vertex in open water, not under the skin
        tot += int(vis.sum())
        hard += int((A[bverts][vis] > 0.15).sum())
        if vis.any():
            amax_open = max(amax_open, float(A[bverts][vis].max()))
    print(f"GATE: R_SURF_SOFT_OPEN_EDGES {'PASS' if hard <= 0.02 * max(tot, 1) else 'FAIL'} - {tot} surf boundary vertices in open water "
          f"(> 0.5 m outside the scoring shore): {hard} carry vertex alpha > 0.15 ({100 * hard / max(tot, 1):.1f}%), max {amax_open:.2f} "
          f"(an alpha-blended piece whose border is not at A 0 shows a hard cut edge)")

# ---------------- (b) lip band: gap between the local skin top just outside the shore and PLAY_Z; TERRAIN material there
skins = [o for o in bpy.data.objects if o.name.startswith("ROCK_SKIN")]
st = tree(skins)
ter = [o for o in bpy.data.objects if o.name.startswith("TERRAIN")][0]
tt = tree([ter])
gaps = []
lipmat = {}
loops = [np.array(L_) for L_ in D.loops]
for L_ in loops:
    seg = np.roll(L_, -1, 0) - L_
    sl = np.linalg.norm(seg, axis=1)
    cs = np.concatenate([[0], np.cumsum(sl)])
    for s in np.arange(0.25, cs[-1], 1.0):
        i = int(np.searchsorted(cs, s, side="right") - 1)
        p = L_[i] + seg[i] * (s - cs[i]) / max(sl[i], 1e-9)
        tg = seg[i] / max(sl[i], 1e-9)
        n = np.array([tg[1], -tg[0]])
        if P.signed_dist_m(D, np.array([p[0] + 2 * n[0]]), np.array([p[1] + 2 * n[1]]))[0] < 0:
            n = -n
        # highest skin surface within 0..1.2 m outside the edge (looking down), = what a viewer sees just below the grass
        top = -1e9
        for dd in (0.05, 0.3, 0.6, 0.9, 1.2):
            h = st.ray_cast(Vector((p[0] + n[0] * dd, p[1] + n[1] * dd, PZ + 1)), Vector((0, 0, -1)), 20)
            if h[0] is not None:
                top = max(top, h[0].z)
        gaps.append(PZ - top if top > -1e8 else 99.0)
        # material of the TERRAIN wall face 0.3 m below play, hit horizontally from outside
        h = tt.ray_cast(Vector((p[0] + n[0] * 3, p[1] + n[1] * 3, PZ - 0.3)), Vector((-n[0], -n[1], 0)), 6)
        if h[0] is not None:
            m = ter.data.materials[ter.data.polygons[h[2]].material_index].name
            lipmat[m] = lipmat.get(m, 0) + 1
gaps = np.array(gaps)
print(f"INFO: exposed TERRAIN lip above the skin (PLAY_Z - highest skin surface within 1.2 m outside the edge), {len(gaps)} samples at 1 m: "
      f"median {np.median(gaps[gaps < 50]):.2f} m, p90 {np.percentile(gaps[gaps < 50], 90):.2f} m, max {gaps[gaps < 50].max():.2f} m, "
      f"> 0.8 m at {100 * (gaps > 0.8).mean():.0f}%, no skin within 1.2 m at {100 * (gaps > 50).mean():.0f}%; TERRAIN wall material 0.3 m "
      f"under play: {lipmat}")
# lip band material vs top material on the Split ridge (scrub top over a rough lip?)
if H == "09":
    me = ter.data
    W = W_of(ter)
    names = [m.name for m in me.materials]
    top_scrub, lip_rough_under_scrub = 0, 0
    cen = np.array([W[list(p.vertices)].mean(0) for p in me.polygons])
    nz = np.array([p.normal.z for p in me.polygons])
    scrub_top = [(i, cen[i]) for i, p in enumerate(me.polygons) if names[p.material_index] == "LK_SCRUB"]
    from mathutils.kdtree import KDTree
    kd = KDTree(len(scrub_top))
    for k, (i, c) in enumerate(scrub_top):
        kd.insert((c[0], c[1], 0), k)
    kd.balance()
    lips = [i for i, p in enumerate(me.polygons) if abs(nz[i]) < 0.5 and cen[i, 2] > PZ - 1.0]
    near_scrub = [i for i in lips if kd.find((cen[i, 0], cen[i, 1], 0))[2] < 8.0]
    mats_ns = {}
    for i in near_scrub:
        m = names[me.polygons[i].material_index]
        mats_ns[m] = mats_ns.get(m, 0) + 1
    print(f"INFO: Split TERRAIN lip-band wall faces (top 1 m) within 8 m of an LK_SCRUB top face: {len(near_scrub)}, materials {mats_ns}")

if "--no-render" in args:
    sys.exit(0)

# ---------------- (c) extra renders
sc = bpy.context.scene
try:
    sc.view_settings.view_transform = 'AgX'
except Exception:
    pass
bg = sc.world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = P.rgb(150, 196, 240)
for nm in ("BALL_START", "HOLE_CUP", "MARKER_TEE", "MARKER_PIN", "MARKER_UP"):
    if bpy.data.objects.get(nm) is not None:
        bpy.data.objects[nm].hide_render = True


def cam(name, loc, target, fov_v=60.0):
    c = bpy.data.cameras.new(name)
    ob = bpy.data.objects.new(name, c)
    sc.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    c.clip_start = 0.27
    c.clip_end = 6000
    c.sensor_fit = 'VERTICAL'
    c.angle_y = math.radians(fov_v)
    return ob


shots = []
pin = Vector((*P.m(*D.hole.pin), PZ))
cl = [Vector((*P.m(*p), PZ)) for p in D.hole.center]
if H == "10":
    # phone-height view from the fairway end toward the pillar green: lava meets basalt
    a = cl[-2]
    d = (pin - a); d.z = 0; d.normalize()
    shots.append(("pillar_phone", a + d * 20 + Vector((0, 0, 2.2)), pin + Vector((0, 0, -2.0)), 60, (900, 1600)))
    shots.append(("pillar_close", pin - d * 32 + Vector((8, 0, 5.0)), pin + Vector((0, 0, 1.0)) - d * 10, 45, (1400, 900)))
else:
    # aerial oblique like the stills, and a phone view across a water hazard
    bx0, by0, bx1, by1 = P._shore_bbox_m(D)
    c = Vector(((bx0 + bx1) / 2, (by0 + by1) / 2, 0))
    shots.append(("aerial", c + Vector((-(bx1 - bx0) * 0.9, -(by1 - by0) * 0.55, (by1 - by0) * 0.45)), c, 45, (1400, 900)))
    hz = [h for h in D.hole.hazards if h[0] == "water"]
    if hz:
        k, hx, hd, w, l, tag = hz[0]
        e = Vector((*P.m(hx, hd), 0))
        d = (e - cl[0]); d.z = 0; d.normalize()
        start = e - d * (l / 2 * P.YD + 12)
        shots.append(("hazard_phone", start + Vector((0, 0, PZ + 2.2)), e + d * 25 + Vector((0, 0, PZ - 3)), 60, (900, 1600)))
for nm, loc, tgt, fov, res in shots:
    ob = cam(f"CAM_R_{nm}", loc, tgt, fov)
    P.render_camera(ob.name, os.path.join(OUT, f"r_{nm}.png"), res, 24)
    print("render", nm)
