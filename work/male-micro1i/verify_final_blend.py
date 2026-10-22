"""verify the authority blend: Body_M coords == data/V_j5.npy (float32 exact), vertex groups, objects, materials.  blender -b --python verify_final_blend.py -- <blend>"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
import bpy
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body_M']; me = body.data
V = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
ref = np.load('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/data/V_j5.npy').astype(np.float32)
print(json.dumps(dict(coords_equal_V_j5=bool(np.array_equal(V, ref)), verts=len(V), objects=sorted(o.name for o in bpy.data.objects if o.type == 'MESH'), empties=sorted(o.name for o in bpy.data.objects if o.type == 'EMPTY'),
                      groups={vg.name: sum(1 for v in me.vertices if any(g.group == vg.index for g in v.groups)) for vg in body.vertex_groups}, face_m_mats=[m.name for m in bpy.data.objects['Face_M'].data.materials])))
