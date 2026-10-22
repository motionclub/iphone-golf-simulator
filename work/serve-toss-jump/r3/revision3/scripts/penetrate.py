"""penetrate.py <male|female> [out.json] [action] : racket (and the two hands) against the deformed body mesh, per frame.
blender -b export/HeroBase_<Hero>_MatchAnims.blend --python scripts/penetrate.py -- <tag> [out.json] [action]
depth = how far a racket vertex lies inside Body (+ Face) along the surface normal; 'inside' = depth > 3 mm.  Prints the frames with the racket inside the body."""
import json, sys
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
tag = a[0]; outp = a[1] if len(a) > 1 else None; actname = a[2] if len(a) > 2 else 'Serve'
H = dict(male=dict(body='Body_M', face='Face_M', hair=None), female=dict(body='Body_F', face='Face_F', hair='Hair_F'))[tag]
rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
act = bpy.data.actions[actname]; rig.animation_data.action = act
try: rig.animation_data.action_slot = act.slots[0]
except Exception: pass
sc = bpy.context.scene
racket = bpy.data.objects['Racket_Classic']
res = []
for f in range(int(act.frame_start), int(act.frame_end) + 1):
    sc.frame_set(f); bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    verts, tris, base = [], [], 0
    for nm in (H['body'], H['face']):
        ev = bpy.data.objects[nm].evaluated_get(dg); me = ev.to_mesh()
        verts += [ev.matrix_world @ v.co for v in me.vertices]
        me.calc_loop_triangles(); tris += [tuple(base + i for i in t.vertices) for t in me.loop_triangles]
        base += len(me.vertices); ev.to_mesh_clear()
    bvh = BVHTree.FromPolygons(verts, tris)
    ev = racket.evaluated_get(dg); me = ev.to_mesh(); pts = [ev.matrix_world @ v.co for v in me.vertices]; ev.to_mesh_clear()
    worst, n_in = 0.0, 0
    for p in pts:
        loc, nor, idx, dist = bvh.find_nearest(p)
        if loc is None: continue
        d = (loc - p).dot(nor)                       # > 0: p is behind the surface (inside)
        if d > 0.003:
            n_in += 1; worst = max(worst, d)
    res.append(dict(f=f, inside=n_in, depth_mm=worst * 1000))
if outp: json.dump(res, open(outp, 'w'))
bad = [(r['f'], r['inside'], round(r['depth_mm'])) for r in res if r['inside']]
print('PEN', actname, 'frames with racket vertices inside the body (frame, count, max depth mm):', bad)
