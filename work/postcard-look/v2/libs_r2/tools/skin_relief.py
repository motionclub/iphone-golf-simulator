"""Relief of the basalt skin on hole 10's pillar: how far the first skin surface stands in FRONT of the TERRAIN wall, and how strongly the wall reads as courses.
usage: Blender -b --factory-startup --python skin_relief.py -- BLEND [BLEND ...]    (prints GATE-style lines; scratch measurement, not Game-view proof)
Rays from 40 m out, every 2 degrees round the pillar axis (the GREEN centre), at z 0.5 .. 5.5: relief = distance(first TERRAIN hit) - distance(first ROCK_SKIN hit)."""
import sys, math
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
for path in sys.argv[sys.argv.index("--") + 1:]:
    bpy.ops.wm.open_mainfile(filepath=path)
    g = bpy.data.objects["GREEN"]
    ws = [g.matrix_world @ Vector(c) for c in g.bound_box]
    cx = sum(w.x for w in ws) / 8; cy = sum(w.y for w in ws) / 8
    dg = bpy.context.evaluated_depsgraph_get()

    def bvh_of(prefix):
        V, F, off = [], [], 0
        for ob in bpy.data.objects:
            if ob.type == 'MESH' and ob.name.startswith(prefix):
                me = ob.data
                mw = ob.matrix_world
                V += [tuple(mw @ v.co) for v in me.vertices]
                for p in me.polygons:
                    F.append([off + i for i in p.vertices])
                off += len(me.vertices)
        return BVHTree.FromPolygons(V, F)
    bt, bs = bvh_of("TERRAIN"), bvh_of("ROCK_SKIN")
    rel = []
    miss = 0
    for az in range(0, 360, 2):
        d = Vector((math.cos(math.radians(az)), math.sin(math.radians(az)), 0.0))
        for z in (0.5, 1.5, 2.5, 3.5, 4.5, 5.5):
            o = Vector((cx, cy, z)) + d * 40.0
            ht = bt.ray_cast(o, -d, 80.0)
            hs = bs.ray_cast(o, -d, 80.0)
            if ht[0] is None or hs[0] is None:
                miss += 1
                continue
            rel.append(ht[3] - hs[3])
    rel = np.array(rel)
    # the pillar is the nearest solid: only rays that hit the pillar wall (within 30 m of the axis)
    print("SKINRELIEF %s: %d rays (%d without a hit), relief p10 %.3f  median %.3f  p90 %.3f m, share >= 0.10 m %.1f %%, share >= 0.20 m %.1f %%" % (
        path.split("/")[-3] + "/" + path.split("/")[-1], len(rel), miss, np.percentile(rel, 10), np.median(rel), np.percentile(rel, 90), 100 * float((rel >= 0.10).mean()), 100 * float((rel >= 0.20).mean())))
