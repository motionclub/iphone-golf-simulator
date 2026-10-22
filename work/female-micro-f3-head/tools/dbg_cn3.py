import sys, bpy, numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
me = bpy.data.objects['Body_F'].data
n = len(me.vertices); V = np.empty(n * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
vn = np.empty(n * 3); me.vertices.foreach_get('normal', vn); vn = vn.reshape(-1, 3)
nl = len(me.loops); cn = np.empty(nl * 3); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
lv = np.empty(nl, np.int32); me.loops.foreach_get('vertex_index', lv)
ang = np.degrees(np.arccos(np.clip((cn * vn[lv]).sum(1), -1, 1)))
big = np.where(ang > 7.0)[0]
print('loops with shading-normal vs geometry-normal > 7 deg:', len(big))
vs = np.unique(lv[big]); print('verts', len(vs))
for v in vs[np.argsort(-np.array([ang[lv == v].max() for v in vs]))][:14]:
    print(v, 'max %.1f' % ang[lv == v].max(), 'pos mm', np.round(V[v] * 1000, 1))
# spatial histogram by region
reg = {'under-chin y<-0.05,z<1.44': (V[lv[big], 1] < -0.05) & (V[lv[big], 2] < 1.44), 'jaw wall': (V[lv[big], 2] >= 1.44) & (V[lv[big], 2] < 1.50), 'above 1.50': V[lv[big], 2] >= 1.50}
for k, m in reg.items(): print(k, int(m.sum()))
