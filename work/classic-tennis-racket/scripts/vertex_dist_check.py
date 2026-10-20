"""Blender-side counterpart of the Unity socket check: min vertex-to-vertex distance racket<->body in the A-pose blends."""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
from mathutils.kdtree import KDTree
out = {}
for tag, name in (('male', 'Male'), ('female', 'Female')):
    bpy.ops.wm.open_mainfile(filepath=str(WORK / 'export' / f'RacketOnHero_{name}_APose.blend'))
    body = [o for o in bpy.data.objects if o.name.startswith('Body_')][0]
    bv = mesh_co(body, world=True)
    kd = KDTree(len(bv))
    for i, v in enumerate(bv):
        kd.insert(v, i)
    kd.balance()
    best = (1e9, None, None)
    nr = 0
    for n in ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap'):
        rv = mesh_co(bpy.data.objects[n], world=True)
        nr += len(rv)
        for v in rv:
            co, idx, d = kd.find(v)
            if d < best[0]:
                best = (d, v.copy(), bv[idx].copy())
    out[tag] = dict(min_vertex_distance_mm=best[0] * 1000, racket_vert=best[1].tolist(), body_vert=best[2].tolist(), body_verts=len(bv), racket_verts=nr)
    C = np.array([[-1.0, 0, 0], [0, 0, 1.0], [0, -1.0, 0]])
    out[tag]['racket_vert_unity'] = (C @ best[1]).tolist()
    out[tag]['body_vert_unity'] = (C @ best[2]).tolist()
print('VDIST', json.dumps(out))
(WORK / 'data' / 'vertex_dist_blender.json').write_text(json.dumps(out, indent=1))
