"""H_PATH_DENSE: how high the flagstone paths stand over the collider, on a DENSE grid (the reviewer's check: 2 cm grid over both paths, every sample ray-cast onto the
path mesh and onto the ground colliders).  Reports samples, the count and area above 1.2 cm, the max, and where the worst ones are.
usage: Blender -b --factory-startup --python path_dense.py -- STAGED.blend OUT.json [--step 0.02]"""
import sys, os, json, math
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts")
sys.dont_write_bytecode = True
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

YD = 0.9144
GROUND = ("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER", "CART_PATH")


def world(o):
    M = np.array(o.matrix_world)
    V = np.array([v.co[:] for v in o.data.vertices]).reshape(-1, 3)
    return V @ M[:3, :3].T + M[:3, 3]


def bvh_of(objs, up_only=False):
    vs, fs, off = [], [], 0
    for o in objs:
        V = world(o)
        vs += V.tolist()
        for p in o.data.polygons:
            if up_only and (np.array(o.matrix_world)[:3, :3] @ np.array(p.normal))[2] <= 0.5:
                continue
            fs.append([i + off for i in p.vertices])
        off += len(V)
    return BVHTree.FromPolygons(vs, fs)


def run(blend, step):
    bpy.ops.wm.open_mainfile(filepath=blend)
    bpy.context.view_layer.update()
    gr = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith(GROUND)]
    gb = bvh_of(gr, up_only=True)
    out = {}
    down = Vector((0, 0, -1))
    for o in sorted((o for o in bpy.data.objects if o.name.startswith("DRESS_PATH")), key=lambda o: o.name):
        pb = bvh_of([o])
        V = world(o)
        lo, hi = V[:, :2].min(0), V[:, :2].max(0)
        xs = np.arange(lo[0], hi[0], step)
        ys = np.arange(lo[1], hi[1], step)
        tot, over, buried, mx, mn = 0, [], 0, -9.0, 9.0
        for y in ys:
            for x in xs:
                r = pb.ray_cast(Vector((x, y, 40.0)), down)
                if r[0] is None:
                    continue
                g = gb.ray_cast(Vector((x, y, 40.0)), down)
                if g[0] is None:
                    continue
                tot += 1
                dz = r[0].z - g[0].z
                mx, mn = max(mx, dz), min(mn, dz)
                if dz > 0.012:
                    over.append((x / YD, y / YD, dz))
                if dz < 0.0:
                    buried += 1
        a = np.array(over) if over else np.zeros((0, 3))
        out[o.name] = dict(samples=tot, over_1p2cm=len(over), area_m2=len(over) * step * step, max_cm=round(100 * mx, 3), min_cm=round(100 * mn, 3),
                           buried_share=round(buried / max(tot, 1), 4), worst=[[round(float(x), 2), round(float(y), 2), round(100 * float(z), 2)] for x, y, z in sorted(over, key=lambda t: -t[2])[:6]])
        print(f"PATHDENSE {o.name}: {tot} samples at {step * 100:g} cm, {len(over)} over 1.2 cm ({len(over) * step * step:.4f} m2), max {100 * mx:.2f} cm, min {100 * mn:.2f} cm, buried {buried / max(tot, 1):.1%}, worst (x yd, d yd, cm) {out[o.name]['worst']}", flush=True)
    return out


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:]
    step = float(args[args.index("--step") + 1]) if "--step" in args else 0.02
    res = run(args[0], step)
    json.dump(res, open(args[1], "w"), indent=1)
