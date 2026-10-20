"""Rebuild Face_M with the Micro1i builder on a blend's Body_M and compare with that blend's existing Face_M.  blender -b --python facem_repro.py -- <blend> [out.json]"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head/pylib')
import numpy as np, bpy
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work'
for p in (W + '/male-micro1i', W + '/male-micro1h', W + '/male-micro1e'): sys.path.insert(0, p)
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body_M']; me = body.data; old = bpy.data.objects['Face_M']
oldV = np.array([tuple(v.co) for v in old.data.vertices]); oldF = [tuple(p.vertices) for p in old.data.polygons]; oldS = [p.material_index for p in old.data.polygons]
n = len(me.vertices); P = np.empty(n * 3); me.vertices.foreach_get('co', P); P = P.reshape(-1, 3)
F = [[v for v in p.vertices] for p in me.polygons]
def grp(nm):
    vg = body.vertex_groups[nm]; return [v.index for v in me.vertices if any(g.group == vg.index for g in v.groups)]
import faceparts_i as FPI
o, parts = FPI.build_face_m_i(P, F, margin={-1: grp('LOOP_lid_margin_L'), 1: grp('LOOP_lid_margin_R')}, nostrils={-1: grp('LOOP_nostril_L'), 1: grp('LOOP_nostril_R')})
newV = np.array([tuple(v.co) for v in o.data.vertices]); newF = [tuple(p.vertices) for p in o.data.polygons]
print('old verts', len(oldV), 'faces', len(oldF), '| new verts', len(newV), 'faces', len(newF))
if len(oldV) == len(newV):
    d = np.linalg.norm(oldV.astype(np.float32) - newV.astype(np.float32), axis=1) * 1000
    print('max diff mm', d.max(), ' verts differing >1e-6 mm:', int((d > 1e-6).sum()))
    sl = np.zeros(len(oldV), int) - 1
    for f, s in zip(oldF, oldS):
        for v in f: sl[v] = s
    names = [m.name for m in old.data.materials]
    for k, nm in enumerate(names):
        m = sl == k
        if m.any(): print(f'  slot {nm:14s} verts {int(m.sum()):4d}  max diff {d[m].max():.6f} mm')
    print('faces identical:', oldF == newF)
