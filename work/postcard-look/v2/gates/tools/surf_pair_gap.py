import bpy, numpy as np, sys
f = sys.argv[sys.argv.index("--")+1]
bpy.ops.wm.open_mainfile(filepath=f, load_ui=False)
def verts(o):
    mw = np.array(o.matrix_world); V = np.array([v.co[:] for v in o.data.vertices]); W = V @ mw[:3,:3].T + mw[:3,3]
    T = np.array([p.vertices[:] for p in o.data.polygons if len(p.vertices)==3]) if all(len(p.vertices)==3 for p in o.data.polygons) else None
    return W[:, :2], o
def pt_seg(P, A, B):
    AB = B-A; l2 = (AB**2).sum(1); out = np.full(len(P), 1e9)
    for a, ab, l in zip(A, AB, l2):
        k = np.clip(((P-a)@ab)/max(l,1e-12), 0, 1); d = np.linalg.norm(P-(a+ab*k[:,None]), axis=1); out = np.minimum(out, d)
    return out.min()
def edges(o, W):
    E = set()
    for p in o.data.polygons:
        vs = list(p.vertices)
        for i in range(len(vs)): E.add(tuple(sorted((vs[i], vs[(i+1)%len(vs)]))))
    E = np.array(sorted(E)); return W[E[:,0]], W[E[:,1]]
surf = sorted([o for o in bpy.data.objects if o.name.startswith("WATER_SURF") and o.type=="MESH"], key=lambda o: o.name)
Ws = {o.name: verts(o)[0] for o in surf}; Es = {o.name: edges(o, Ws[o.name]) for o in surf}
YD = 0.9144
res = []
for i, a in enumerate(surf):
    for b in surf[i+1:]:
        A, B = Ws[a.name], Ws[b.name]
        # aabb gap
        lo1, hi1, lo2, hi2 = A.min(0), A.max(0), B.min(0), B.max(0)
        g = np.hypot(max(0, max(lo1[0]-hi2[0], lo2[0]-hi1[0])), max(0, max(lo1[1]-hi2[1], lo2[1]-hi1[1])))
        if g/YD < 7.0:
            d = min(pt_seg(A, *Es[b.name]), pt_seg(B, *Es[a.name]))
            res.append((a.name, b.name, g/YD, d/YD))
print("SURFGAP pairs with AABB gap < 7 yd:", len(res))
for r in res: print("SURFGAP", r[0], r[1], f"bounds {r[2]:.2f} yd, real plan distance {r[3]:.2f} yd")
