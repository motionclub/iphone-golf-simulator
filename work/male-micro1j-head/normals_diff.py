import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head/pylib')
import numpy as np, bpy
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head'
def grab(p):
    bpy.ops.wm.open_mainfile(filepath=p); me = bpy.data.objects['Body_M'].data
    V = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', V)
    cn = np.empty(len(me.loops) * 3, np.float32); me.corner_normals.foreach_get('vector', cn)
    lv = np.empty(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', lv)
    return V.reshape(-1, 3), cn.reshape(-1, 3), lv
V0, c0, lv = grab(W + '/baseline/HeroBase_Male_Silhouette.blend'); V1, c1, _ = grab(W + '/final/HeroBase_Male_Silhouette_j1.blend')
ang = np.degrees(np.arccos(np.clip((c0 * c1).sum(1), -1, 1)))
moved = np.any(V0 != V1, axis=1)
print('corners changed >0.05deg:', (ang > 0.05).sum(), ' of which on moved verts:', ((ang > 0.05) & moved[lv]).sum())
far = (ang > 0.05) & ~moved[lv]
idx = np.where(far)[0]
vs = np.unique(lv[idx]); print('verts (not moved) with changed normals:', len(vs))
D = np.load(W + '/data/D_j1.npy'); dn = np.linalg.norm(D, axis=1)
for v in vs[:30]: print('  v%d  z=%.4f x=%.4f y=%.4f  ang_max %.3f  |D|float64=%.3g  neighbors moved? ' % (v, V0[v, 2], V0[v, 0], V0[v, 1], ang[lv == v].max(), dn[v]))
