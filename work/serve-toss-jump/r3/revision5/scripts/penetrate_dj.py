"""penetrate_dj.py <male|female> [out.json] [action] : the racket (frame + strings, drawn 1.3x about the grip like the game) against the deformed body + face + the dressed kit (polo, shorts, socks, shoes), per frame.
blender -b export/preview/HeroBase_<Hero>_Dressed.blend --python scripts/penetrate_dj.py -- <tag> [out.json] [action]
depth = how far a racket vertex lies behind the nearest obstacle surface (along its normal); 'inside' = depth > 3 mm.  Reports the frames and which obstacle owns the nearest surface."""
import json, sys, os
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
tag = a[0]; outp = a[1] if len(a) > 1 else None; actname = a[2] if len(a) > 2 else 'Serve'
H = dict(male=dict(body='Body_M', face='Face_M'), female=dict(body='Body_F', face='Face_F'))[tag]
OBST = [H['body'], H['face'], 'Kit_Top', 'Kit_Bottom', 'Kit_Sock_L', 'Kit_Sock_R', 'Kit_Shoe_L', 'Kit_Shoe_R']
rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
act = bpy.data.actions[actname]; rig.animation_data.action = act
try: rig.animation_data.action_slot = act.slots[0]
except Exception: pass
sc = bpy.context.scene
racket = bpy.data.objects['Racket_Classic']
racket.scale = (1.3, 1.3, 1.3)
parts = [racket] + [bpy.data.objects[n] for n in ('StringBed',) if n in bpy.data.objects]
res = []
for f in range(int(act.frame_start), int(act.frame_end) + 1):
    sc.frame_set(f); bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    verts, tris, owner, base = [], [], [], 0
    for nm in OBST:
        if nm not in bpy.data.objects: continue
        ev = bpy.data.objects[nm].evaluated_get(dg); me = ev.to_mesh()
        verts += [ev.matrix_world @ v.co for v in me.vertices]
        me.calc_loop_triangles(); tris += [tuple(base + i for i in t.vertices) for t in me.loop_triangles]; owner += [nm] * len(me.loop_triangles)
        base += len(me.vertices); ev.to_mesh_clear()
    bvh = BVHTree.FromPolygons(verts, tris)
    pts = []
    for o in parts:
        ev = o.evaluated_get(dg); me = ev.to_mesh(); pts += [ev.matrix_world @ v.co for v in me.vertices]; ev.to_mesh_clear()
    worst, n_in, who = 0.0, 0, {}
    for p in pts:
        loc, nor, idx, dist = bvh.find_nearest(p)
        if loc is None: continue
        d = (loc - p).dot(nor)
        if d > 0.003:
            n_in += 1; worst = max(worst, d); who[owner[idx]] = who.get(owner[idx], 0) + 1
    res.append(dict(f=f, inside=n_in, depth_mm=worst * 1000, who=who))
if outp: json.dump(res, open(outp, 'w'))
bad = [(r['f'], r['inside'], round(r['depth_mm']), r['who']) for r in res if r['inside']]
print('PEN', actname, 'frames with racket vertices inside body / kit (frame, count, max depth mm, obstacle):')
for b in bad: print('  ', b)
print('PEN_DONE', len(bad), 'bad frames of', len(res))
