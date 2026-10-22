import sys, numpy as np, bpy
base, new = sys.argv[sys.argv.index('--') + 1:][:2]
def load(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    me = bpy.data.objects['Body_M'].data; me.update()
    n = len(me.vertices)
    V = np.empty(n * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3).astype(np.float32)
    F = [tuple(p.vertices) for p in me.polygons]
    cn = np.empty(len(me.loops) * 3); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
    ls = np.array([p.loop_start for p in me.polygons]); lt = np.array([p.loop_total for p in me.polygons])
    raw = np.zeros(len(me.loops) * 2, np.int32); me.attributes['custom_normal'].data.foreach_get('value', raw)
    return V, F, cn, ls, lt, raw.reshape(-1, 2)
Vb, Fb, cnb, lsb, ltb, rawb = load(base)
Vn, Fn, cnn, lsn, ltn, rawn = load(new)
oldmap = {tuple(f): i for i, f in enumerate(Fb)}
moved = np.any(Vb != Vn[:len(Vb)], axis=1)
rows = []
for k, f in enumerate(Fn):
    i = oldmap.get(f)
    if i is None or any(moved[v] for v in f): continue
    a = cnb[lsb[i]:lsb[i] + ltb[i]]; b = cnn[lsn[k]:lsn[k] + ltn[k]]
    ang = np.degrees(np.arccos(np.clip((a * b).sum(1), -1, 1)))
    for c in range(len(f)):
        rows.append((ang[c], f[c], k, i))
rows.sort(reverse=True)
print('top 12 far-corner differences (deg, vertex, z, x):')
for ang, v, k, i in rows[:12]:
    print(f'  {ang:.3f} v={v} z={Vb[v,2]:.3f} x={Vb[v,0]:.3f} y={Vb[v,1]:.3f}')
A = np.array([r[0] for r in rows]); Z = np.array([Vb[r[1], 2] for r in rows])
for lo, hi in ((0, 0.5), (0.5, 0.77), (0.77, 1.2), (1.2, 1.4), (1.4, 1.8)):
    s = (Z >= lo) & (Z < hi)
    print(f'z[{lo},{hi}): corners {int(s.sum())}, mean diff {A[s].mean() if s.any() else 0:.4f}, max {A[s].max() if s.any() else 0:.4f}')
