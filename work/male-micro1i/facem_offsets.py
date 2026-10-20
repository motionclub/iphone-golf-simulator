"""distance of every Face_M vertex to the Body_M skin, per material slot (NO_STICKER_VOLUME evidence).  blender -b --python facem_offsets.py -- <blend> <out.json>"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
import bpy
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body_M']; face = bpy.data.objects['Face_M']
verts = [tuple(v.co) for v in body.data.vertices]; tris = []
for p in body.data.polygons:
    vs = list(p.vertices)
    tris.append((vs[0], vs[1], vs[2]))
    if len(vs) > 3: tris.append((vs[0], vs[2], vs[3]))
bvh = BVHTree.FromPolygons(verts, tris)
slots = [m.name for m in face.data.materials]
out = {}
for si, name in enumerate(slots):
    idx = sorted({v for p in face.data.polygons if p.material_index == si for v in p.vertices})
    if not idx: out[name] = dict(verts=0); continue
    d = []
    for i in idx:
        co = face.data.vertices[i].co
        loc, nrm, fi, dist = bvh.find_nearest(co)
        d.append(dist)
    d = np.array(d) * 1000
    out[name] = dict(verts=len(idx), max_mm=round(float(d.max()), 3), mean_mm=round(float(d.mean()), 3))
json.dump(out, open(argv[1], 'w'), indent=1)
print(json.dumps(out))
