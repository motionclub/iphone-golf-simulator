import bpy, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft
bpy.ops.wm.open_mainfile(filepath=ft.JAW + '/Female_JawSculpt.blend')
me = bpy.data.objects['Body'].data; co = ft.coords(me)
D = np.load(ft.WORK + '/eval/s4_delta.npy')
me.calc_loop_triangles(); t = np.empty(len(me.loop_triangles) * 3, dtype=np.int64); me.loop_triangles.foreach_get('vertices', t); t = t.reshape(-1, 3)
for q in ((-.070, -.097, 1.505), (-.071, -.088, 1.493), (-.020, -.127, 1.482)):
    d = np.linalg.norm(co - q, axis=1); i = np.argsort(d)[:4]
    print('pt', q, [(int(k), round(float(d[k]) * 1000, 2), np.round(D[k] * 1000, 3).tolist()) for k in i])
    tris = t[np.isin(t, i[:2]).any(1)]
    for tt in tris[:6]:
        P = co[tt]; P2 = P + D[tt]; a = np.linalg.norm(np.cross(P[1] - P[0], P[2] - P[0])) / 2 * 1e6; a2 = np.linalg.norm(np.cross(P2[1] - P2[0], P2[2] - P2[0])) / 2 * 1e6
        print('   tri area mm2', round(a, 3), '->', round(a2, 3))
