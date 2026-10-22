"""Oblique see-through test of the lib's arch. usage: Blender -b --factory-startup --python arch_leak.py -- [LIB.py] [span height broken seed]
Rays from a hemisphere of camera directions to sample points inside the solid masonry; the first hit must be a FRONT face (normal facing the camera).
A first hit on a back face (or no hit) = the ray entered the stone through a crack."""
import sys, os, math, importlib.util
import numpy as np
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.dont_write_bytecode = True
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index("--") + 1:]
libpath = a[0] if a and a[0].endswith(".py") else REPO + "/blender/scripts/postcard_props_lib.py"
rest = [x for x in a if not x.endswith(".py")]
span = float(rest[0]) if rest else 9.144
height = float(rest[1]) if len(rest) > 1 else 12.166
broken = (rest[2] == "1") if len(rest) > 2 else False
seed = int(rest[3]) if len(rest) > 3 else 8
spec = importlib.util.spec_from_file_location("pl_under_test", libpath)
PL = importlib.util.module_from_spec(spec); sys.modules["pl_under_test"] = PL; spec.loader.exec_module(PL)
r = PL.build_masonry_arch(None, (0, 0, 0.0), 0.0, span_m=span, height_m=height, seed=seed, base_rock=False, vines=False, broken=broken, name="DRESS_ARCH_00")
ob = r["arch"]; d = r["dims"]
me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
bvh = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
r_in, r_out, zs, pw = d["r_in"], d["r_out"], d["zs"], d["pw"]
step = 0.06
pts = []
for x in np.arange(-(r_in + pw), r_in + pw, step):
    for z in np.arange(0.42, height - 0.1, step):
        ax = abs(x)
        solid = False
        if z < zs - 0.03 and r_in + 0.04 < ax < r_in + pw - 0.04:
            solid = not (broken and x < 0 and z > zs - 1.9)
        else:
            rr = math.hypot(x, z - zs)
            if z > zs + 0.03 and r_in + 0.04 < rr < r_out - 0.08:
                ang = math.atan2(z - zs, x)
                n_ = int(round(math.pi * (r_in + (r_out - r_in) / 2) / max(0.7, 0.12 * span))); n_ += 1 - n_ % 2
                solid = not (broken and ang > math.pi * (n_ // 2 - 1) / n_ - 0.03)
        if solid:
            pts.append((x, 0.0, z))
cams = []
for az in (-70, -45, -20, 0, 20, 45, 70):
    for el in (-12, 8, 28, 45):
        e, A = math.radians(el), math.radians(az)
        cams.append(Vector((math.sin(A) * math.cos(e), -math.cos(A) * math.cos(e), math.sin(e))) * 25.0)
leaks = {}
nray = 0
for p in pts:
    P0 = Vector(p)
    for ci, c in enumerate(cams):
        o = P0 + c
        dv = -c.normalized()
        h = bvh.ray_cast(o, dv, 25.0 + 0.5)
        nray += 1
        if h[0] is None or h[1].dot(dv) > 0:
            leaks.setdefault(p, []).append(ci)
print("LEAK arch span %.3f height %.3f broken %s faces %d: %d sample points, %d rays, %d leaking rays at %d points (%.3f %% of rays)" % (
    span, height, broken, len(me.polygons), len(pts), nray, sum(len(v) for v in leaks.values()), len(leaks), 100.0 * sum(len(v) for v in leaks.values()) / max(nray, 1)))
if os.environ.get("LEAK_DEBUG"):
    for (xx, zz) in ((5.43, 6.05), (5.43, 6.20), (5.0, 6.05), (5.0, 6.3), (5.8, 6.12), (6.0, 6.3)):
        hh = bvh.ray_cast(Vector((xx, -5.0, zz)), Vector((0, 1, 0)), 12.0)
        print("   +Y ray at x %.2f z %.2f ->" % (xx, zz), None if hh[0] is None else (tuple(round(v, 3) for v in hh[0]), tuple(round(v, 2) for v in hh[1])))
if leaks:
    pp = sorted(leaks.items(), key=lambda kv: -len(kv[1]))[:12]
    for p, cs in pp:
        print("LEAK  at (%.2f, %.2f, %.2f): %d cams %s" % (p[0], p[1], p[2], len(cs), [(round(cams[c].x, 1), round(cams[c].y, 1), round(cams[c].z, 1)) for c in cs]))
        if os.environ.get("LEAK_DEBUG"):
            for c in cs[:1]:
                dv = -cams[c].normalized()
                o_ = Vector(p) + cams[c]
                tt = 0.0
                for _k in range(12):
                    hh = bvh.ray_cast(o_ + dv * tt, dv, 26.0 - tt)
                    if hh[0] is None:
                        print("      ... no more hits"); break
                    print("      hit%d at %s n %s face %d" % (_k, tuple(round(v, 3) for v in hh[0]), tuple(round(v, 2) for v in hh[1]), hh[2]))
                    tt += hh[3] + 1e-4
                h = bvh.ray_cast(Vector(p) + cams[c], dv, 25.5)
                print("      first hit", None if h[0] is None else (tuple(round(v, 3) for v in h[0]), tuple(round(v, 2) for v in h[1]), round(h[3], 3)))
