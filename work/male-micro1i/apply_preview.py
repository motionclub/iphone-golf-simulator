"""Apply a vertex array to the baseline blend (Body_M only, normals recomputed like run_final.py), optionally rebuild Face_M, save blend.
blender -b --factory-startup --python apply_preview.py -- <V.npy> <out.blend> [facem=0|1]"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np, pickle
import bpy
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i'
H1 = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h'
for p in (W, H1, H1.replace('micro1h', 'micro1e')):
    sys.path.insert(0, p)
argv = sys.argv[sys.argv.index('--') + 1:]
V = np.load(argv[0]); out = argv[1]; facem = len(argv) > 2 and argv[2] == '1'
NSMOOTH = int(argv[3]) if len(argv) > 3 else 3
bpy.ops.wm.open_mainfile(filepath=W + '/baseline/HeroBase_Male_Silhouette.blend')
body = bpy.data.objects['Body_M']; me = body.data
assert len(me.vertices) == len(V)
me.vertices.foreach_set('co', V.astype(np.float32).ravel()); me.update()
# smoothed shading normals in the head region (same recipe as run_final.py)
n = len(V)
nrm = np.empty(n * 3); me.vertex_normals.foreach_get('vector', nrm); nrm = nrm.reshape(-1, 3)
F = [[v for v in p.vertices] for p in me.polygons]
adj = [set() for _ in range(n)]
for f in F:
    m = len(f)
    for i in range(m):
        a, b = f[i], f[(i + 1) % m]; adj[a].add(b); adj[b].add(a)
base = np.load(W + '/data/V_h0.npy')
ring = set(int(i) for i in np.where((np.abs(base[:, 2] - 1.43) < 0.0015) & (np.abs(base[:, 0]) < 0.14))[0])
hv = np.where((V[:, 2] > 1.43) & (np.abs(V[:, 0]) < 0.14))[0]
for it in range(NSMOOTH):
    new = nrm.copy()
    for v in hv:
        if v in ring: continue
        nb = list(adj[v]); m_ = nrm[nb].mean(axis=0); t = 0.5 * nrm[v] + 0.5 * m_
        new[v] = t / (np.linalg.norm(t) + 1e-12)
    nrm = new
me.normals_split_custom_set_from_vertices([tuple(x) for x in nrm]); me.update()
if facem:
    import importlib, h1lib as H, sculpt as S, finalize as FZ, faceparts as FP
    old = bpy.data.objects.get('Face_M')
    if old: bpy.data.objects.remove(old, do_unlink=True)
    for m_ in list(bpy.data.materials):
        if m_.name.startswith('Face_') or m_.name.startswith('eye_mat') or m_.name.startswith('brow_mat'): bpy.data.materials.remove(m_)
    def grp(nm):
        vg = body.vertex_groups[nm]; return [v.index for v in me.vertices if any(g.group == vg.index for g in v.groups)]
    import faceparts_i as FPI
    face_o, parts = FPI.build_face_m_i(V, F, margin={-1: grp('LOOP_lid_margin_L'), 1: grp('LOOP_lid_margin_R')}, nostrils={-1: grp('LOOP_nostril_L'), 1: grp('LOOP_nostril_R')})
    face_o.parent = None
bpy.ops.wm.save_as_mainfile(filepath=out)
print('saved', out)
