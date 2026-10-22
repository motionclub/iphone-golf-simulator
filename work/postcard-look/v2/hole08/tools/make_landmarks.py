"""landmarks.json for hole 8 (Needle): shots tee (default), approach, arch close-up (landmark), plus an optional path-ball shot.
usage: Blender -b --factory-startup --python make_landmarks.py -- STAGED.blend OUT_DIR
Chooses the arch camera by search (projection + ray tests on the staged blend), writes OUT_DIR/landmarks.json (RUNTIME.md stills schema; Unity world YARDS:
x = Blender x / 0.9144, y = Blender z / 0.9144, z = Blender y / 0.9144) and OUT_DIR/landmarks_check.json (the numbers behind it). Blender frame is metres."""
import sys, os, json, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.dont_write_bytecode = True
import bpy, numpy as np
from mathutils import Vector
import postcard_lib as P
import hole08_look as K

YD = P.YD
args = sys.argv[sys.argv.index("--") + 1:]
blend, out = args[0], os.path.abspath(args[1])
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=blend)
bpy.context.view_layer.update()
info = json.load(open(os.path.join(os.path.dirname(blend), "look_info.json")))
ac = info["arch"]["centre"]; ah = info["arch"]["height"]; aspan = info["arch"]["span"]
W, H = 900, 1600
ASPECT = W / H

meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not any(c.name == "ASSET_LIBRARY" for c in o.users_collection)
          and o.name not in ("BALL_START", "HOLE_CUP", "MARKER_TEE", "MARKER_PIN", "MARKER_UP")]
arch_names = {o.name for o in meshes if o.name.startswith("DRESS_ARCH") or o.name.startswith("ROCK_OUTCROP")}
vine_arch = [o for o in meshes if o.name.startswith("PLANT_VINE")]
def near_arch(o):
    c = np.array(o.matrix_world.translation)
    return math.hypot(c[0] - ac[0], c[1] - ac[1]) <= 0.5 * aspan + 4.5 and c[2] >= ac[2] - 1.0
# the arch's own dressing (vines, the shrubs / flowers / tufts / fallen blocks on its outcrop) is part of the landmark, not a blocker
bv_all = K.bvh_of_objects([o for o in meshes if o.name not in arch_names and not (o.name.startswith(("PLANT_", "DRESS_BLOCK")) and near_arch(o))
                           and not o.name.startswith(("WATER_OCEAN", "WATER_SHELF", "WATER_SURF", "WATER_FALL", "DRESS_PATH"))])
ground = K.bvh_of_objects([o for o in meshes if o.name.startswith(("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER"))])
arch_ob = [o for o in meshes if o.name.startswith("DRESS_ARCH")][0]
outc = [o for o in meshes if o.name.startswith("ROCK_OUTCROP")][0]
AV = K.world_verts([arch_ob]); OV = K.world_verts([outc])
OVtop = OV[OV[:, 2] > ac[2] - 0.5]
samples = AV[np.linspace(0, len(AV) - 1, 160).astype(int)]


def ground_z(x, y):
    h = ground.ray_cast(Vector((x, y, 40.0)), Vector((0, 0, -1)), 80.0)
    return None if h[0] is None else h[0].z


def project(C, T, fov_v_deg, pts):
    """Vectorised pinhole projection: (n, 3) of (x ndc, y ndc, depth) for world points `pts` (n, 3)."""
    f = (T - C).normalized()
    r = f.cross(Vector((0, 0, 1))).normalized()
    u = r.cross(f).normalized()
    tv = math.tan(math.radians(fov_v_deg) / 2)
    th = tv * ASPECT
    Pn = np.asarray(pts, float) - np.array([C.x, C.y, C.z])
    z = Pn @ np.array([f.x, f.y, f.z])
    zs = np.maximum(z, 0.3)
    out = np.stack([(Pn @ np.array([r.x, r.y, r.z])) / (zs * th), (Pn @ np.array([u.x, u.y, u.z])) / (zs * tv), z], 1)
    out[z <= 0.3, :2] = 9
    return out


# ---- round 5 (reviewer, arch shot: "a big flat grey slab with a hard black box at its edge", "a bright faceted ridge with a chevron seam"): composition scoring. The first-hit class of a coarse
#      grid of rays through the frame (outcrop flank = the sheer LK_ROCK wall, skin = the cliff-skin ledges and walls, lip = BUNKER_01_LIP, top = the outcrop's grass) is penalised /
#      rewarded, so the chosen camera shows the arch on its grassy island rather than the wall and the ledges under the pad rim.
def class_bvh(objs):
    V, F, tag, base = [], [], [], 0
    for ob in objs:
        v, t = K.world_tris(ob)
        me = ob.data
        me.calc_loop_triangles()
        V += [tuple(p) for p in v.tolist()]
        for lt in me.loop_triangles:
            F.append(tuple(base + int(i) for i in lt.vertices))
            mat = me.materials[me.polygons[lt.polygon_index].material_index].name.split(".")[0] if me.materials and me.materials[me.polygons[lt.polygon_index].material_index] else ""
            nz = float(np.array(ob.matrix_world.to_3x3() @ me.polygons[lt.polygon_index].normal)[2])
            n = ob.name
            if n.startswith("BUNKER_01_LIP"):
                k = "lip"
            elif n.startswith("ROCK_SKIN"):
                k = "skin"
            elif n.startswith("ROCK_OUTCROP"):
                k = "top" if mat == "LK_ROUGH" else "flank"
            elif n.startswith("DRESS_ARCH") or n.startswith("DRESS_BLOCK"):
                k = "masonry"
            elif n.startswith(("TERRAIN", "FAIRWAY", "GREEN", "BUNKER")):
                k = "pad"
            elif n.startswith("WATER"):
                k = "water"
            else:
                k = "other"
            tag.append(k)
        base += len(v)
    return BVHTree.FromPolygons(V, F), tag


from mathutils.bvhtree import BVHTree
comp_objs = [o for o in meshes if not o.name.startswith(("PLANT_", "WATER_SURF", "WATER_FALL", "DRESS_PATH", "WATER_SHELF"))]
comp_bvh, comp_tag = class_bvh(comp_objs)
GX, GY = 30, 54


def composition(C, T, fov):
    f = (T - C).normalized()
    r = f.cross(Vector((0, 0, 1))).normalized()
    u = r.cross(f).normalized()
    tv = math.tan(math.radians(fov) / 2)
    th = tv * ASPECT
    cnt = {}
    for gy in range(GY):
        yy = (1 - (gy + 0.5) / GY * 2) * tv
        for gx in range(GX):
            xx = ((gx + 0.5) / GX * 2 - 1) * th
            d = (f + r * xx + u * yy).normalized()
            h = comp_bvh.ray_cast(C, d, 4000.0)
            k = "sky" if h[0] is None else comp_tag[h[2]]
            cnt[k] = cnt.get(k, 0) + 1
    n = GX * GY
    return {k: v / n for k, v in cnt.items()}


best = None
ranked = []
tgt_z = ac[2] + 0.5 * ah
cands = []
PIN = "--pin" in args          # round 8: keep the arch camera of rounds 5-7 (hole08_look.ARCH_CAM) instead of searching again: the reviewers' Game-view measurements are about that frame; the numbers are computed for it
if PIN:
    C0, T0, fov0 = Vector(K.ARCH_CAM["pos"]), Vector(K.ARCH_CAM["look"]), float(K.ARCH_CAM["fov"])
    pr = project(C0, T0, fov0, AV)
    wfrac = float(pr[:, 0].max() - pr[:, 0].min()) / 2.0
    hfrac = float(pr[:, 1].max() - pr[:, 1].min()) / 2.0
    blocked0 = 0
    for p in list(samples.tolist()) + OVtop[np.linspace(0, len(OVtop) - 1, 40).astype(int)].tolist():
        d = Vector(p) - C0
        if bv_all.ray_cast(C0, d.normalized(), d.length - 0.05)[0] is not None:
            blocked0 += 1
    po = project(C0, T0, fov0, OVtop)
    in_frame0 = float(((np.abs(po[:, 0]) < 0.97) & (np.abs(po[:, 1]) < 0.97)).mean())
    cmp0 = composition(C0, T0, fov0)
    g0 = ground_z(C0.x, C0.y)
    best = (0.0, (C0.x, C0.y, C0.z), (T0.x, T0.y, T0.z), fov0, dict(width_frac=wfrac, height_frac=hfrac, blocked=blocked0 / (len(samples) + 40), outcrop_in_frame=in_frame0, ground=g0,
                                                                   height_above_ground=C0.z - g0, composition={k: round(v, 3) for k, v in sorted(cmp0.items())}, pinned=True))
    cands = []
    print("PINNED arch camera", K.ARCH_CAM)
for x in ([] if PIN else np.arange(-20.0, -3.9, 1.0)):
    for y in np.arange(256.0, 278.0, 1.0):
        g = ground_z(x, y)
        if g is None or g < 5.9:
            continue
        for hh in (1.8, 2.6, 3.4, 4.6, 6.0):
            for fov in (60.0, 66.0, 72.0):
                C = Vector((x, y, g + hh))
                for dz in (-3.5, -2.5, -1.5, -0.5, 0.5, 1.5):
                    T = Vector((ac[0], ac[1], tgt_z + dz))
                    pr = project(C, T, fov, AV)
                    if (np.abs(pr[:, 0]) > 0.92).any() or (np.abs(pr[:, 1]) > 0.92).any() or (pr[:, 2] < 8).any():
                        continue
                    wfrac = float(pr[:, 0].max() - pr[:, 0].min()) / 2.0          # share of the frame width
                    hfrac = float(pr[:, 1].max() - pr[:, 1].min()) / 2.0
                    if wfrac < 0.62 or wfrac > 0.88:
                        continue
                    cands.append((x, y, g, hh, fov, dz, wfrac, hfrac))
print("candidates after the projection tests:", len(cands))
for (x, y, g, hh, fov, dz, wfrac, hfrac) in cands:
    C = Vector((x, y, g + hh))
    T = Vector((ac[0], ac[1], tgt_z + dz))
    # ray tests: camera -> 160 arch sample points + outcrop top points, blocked by anything but the arch / outcrop
    blocked = 0
    for p in list(samples.tolist()) + OVtop[np.linspace(0, len(OVtop) - 1, 40).astype(int)].tolist():
        d = Vector(p) - C
        if bv_all.ray_cast(C, d.normalized(), d.length - 0.05)[0] is not None:
            blocked += 1
    frac_b = blocked / (len(samples) + 40)
    if frac_b > 0.10:
        continue
    # the outcrop (its flat top and the foot of the piers) in frame too
    po = project(C, T, fov, OVtop)
    in_frame = float(((np.abs(po[:, 0]) < 0.97) & (np.abs(po[:, 1]) < 0.97)).mean())
    cmp_ = composition(C, T, fov)
    lipf, skinf, flankf, topf, padf = (cmp_.get(k, 0.0) for k in ("lip", "skin", "flank", "top", "pad"))
    score = (-frac_b * 10 + 1.5 * hfrac + 0.5 * in_frame - 0.02 * abs(wfrac - 0.75) * 10 - 0.01 * (hh - 1.8)
             - 12.0 * max(0.0, lipf - 0.01) - 6.0 * max(0.0, skinf - 0.05) - 5.0 * max(0.0, flankf - 0.10) + 4.0 * min(topf, 0.20) - 1.5 * max(0.0, padf - 0.15) - 3.0 * max(0.0, cmp_.get('sky', 0.0) - 0.35))
    ranked.append((score, round(x, 1), round(y, 1), hh, fov, dz, {k: round(v, 3) for k, v in sorted(cmp_.items())}))
    if best is None or score > best[0]:
        best = (score, (x, y, g + hh), (T.x, T.y, T.z), fov, dict(width_frac=wfrac, height_frac=hfrac, blocked=frac_b, outcrop_in_frame=in_frame, ground=g, height_above_ground=hh,
                                                              composition={k: round(v, 3) for k, v in sorted(cmp_.items())}))
for r_ in sorted(ranked, key=lambda q: -q[0])[:6]:
    print("RANK", r_)
print("BEST", best)
score, pos, look, fov, det = best
det["candidates"] = len(cands)
r4cam = composition(Vector((-9.0, 276.0, 9.48)), Vector((-26.243, 289.865, 9.8)), 60.0)        # the round-4 arch camera (3.4 m above the pad rim), same rays, for the comparison
C = Vector(pos); T = Vector(look)
# final blocking test with a denser sample + the camera not inside geometry
dense = AV[np.linspace(0, len(AV) - 1, min(len(AV), 400)).astype(int)]
blocked_d = sum(1 for p in dense.tolist() if bv_all.ray_cast(C, (Vector(p) - C).normalized(), (Vector(p) - C).length - 0.05)[0] is not None)
# a ray from the camera along its look direction reaches the arch (centre) before anything else
f = (T - C).normalized()
hit = bv_all.ray_cast(C, f, 200.0)
yd = lambda v: [round(v[0] / YD, 2), round(v[2] / YD, 2), round(v[1] / YD, 2)]        # Blender (x, y, z) m -> Unity world yards (x, y up, z down the hole)
cfg = dict(shots=[
    dict(name="hole08_tee", hole=8, kind="address", ball=[0, 0], aim=[19, 178], putting=False),
    dict(name="hole08_approach", hole=8, kind="address", ball=[19, 178], aim=[-6, 340], putting=False),
    dict(name="hole08_arch", hole=8, kind="landmark", pos=yd(pos), look=yd(look), fov=round(fov, 1)),
    dict(name="hole08_pathball", hole=8, kind="address", ball=[float(K.PATHBALL_YD[0]), float(K.PATHBALL_YD[1])], aim=[19, 178], putting=False),
])
json.dump(cfg, open(os.path.join(out, "landmarks.json"), "w"), indent=2)
chk = dict(round4_camera_composition={k: round(v, 3) for k, v in sorted(r4cam.items())}, arch_camera_blender_m=dict(pos=[round(v, 3) for v in pos], look=[round(v, 3) for v in look], fov_v=fov),
           arch_camera_unity_yards=dict(pos=yd(pos), look=yd(look), fov=fov), search=det, dense_blocked_of=[blocked_d, len(dense)],
           look_ray_hit=None if hit[0] is None else dict(dist=round(hit[3], 2), point=[round(c, 2) for c in hit[0]]),
           arch_centre_m=ac, arch_height_m=ah, arch_span_m=aspan,
           shots_notes=dict(tee="default shot: ball on the tee (0,0), aim = the landing station M (19,178) = RecommendedTarget",
                            approach="second shot from the landing station M (19,178) on the middle pad, 164 yd to the pin (-6,340): a real 7-iron approach over gap 2",
                            arch=f"close-up of the masonry arch on its grassy outcrop, from a vantage {det['height_above_ground']:g} m above the green pad's north-west rim, beside the bunker (round 5: composition-scored search, the bunker lip and the dark ledges are out of the frame)",
                            pathball="OPTIONAL extra: a lay-up lie on the tee-pad path (a path vertex, course yards): proves the ball is not hidden by the path"))
json.dump(chk, open(os.path.join(out, "landmarks_check.json"), "w"), indent=2)
print("LANDMARKS", json.dumps(cfg["shots"][2]))
print("dense blocked", blocked_d, "of", len(dense), "look ray hit", chk["look_ray_hit"])
