"""Dense proxy of the head: Catmull-Clark limit surface of the cage patch (Micro1f cage), via a temp Blender mesh + Subsurf.
build_proxy(level) -> (V, F) numpy (quads), only the region z > ZCUT.  Cached in data/proxy_L{level}.npz
"""
import pickle
import numpy as np
import h1lib as H

ZPATCH = 1.34      # cage patch bottom (buffer under the weld)
ZCUT = 1.405       # proxy keeps faces above this


def build_proxy(level=3, V=None, cache=True):
    import bpy
    fn = H.W / f'data/proxy_L{level}.npz'
    if cache and V is None and fn.exists():
        d = np.load(fn, allow_pickle=True)
        return d['V'], [f for f in d['F']] if d['F'].dtype == object else d['F']
    if V is None:
        V = np.load(H.W / 'data/V_micro1f.npy')
    F = pickle.load(open(H.W / 'data/F.pkl', 'rb'))
    keep = [f for f in F if all(V[i, 2] > ZPATCH and abs(V[i, 0]) < 0.30 for i in f)]
    used = sorted({i for f in keep for i in f}); rem = {v: k for k, v in enumerate(used)}
    Vp = V[used]; Fp = [[rem[i] for i in f] for f in keep]
    o = H.make_mesh_object('cc_patch', Vp, Fp)
    m = o.modifiers.new('ss', 'SUBSURF')
    m.levels = level; m.render_levels = level; m.subdivision_type = 'CATMULL_CLARK'
    try:
        m.boundary_smooth = 'PRESERVE_CORNERS'
    except Exception:
        pass
    try:
        m.use_limit_surface = True
    except Exception:
        pass
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg); me = ev.to_mesh()
    Vd, Fd = H.mesh_arrays(me)
    ev.to_mesh_clear()
    bpy.data.objects.remove(o, do_unlink=True)
    # region cut
    zf = np.array([Vd[f, 2].min() for f in Fd])
    sel = [f for f, zz in zip(Fd, zf) if zz > ZCUT]
    used = sorted({int(i) for f in sel for i in f}); rem = {v: k for k, v in enumerate(used)}
    Vo = Vd[used]; Fo = np.array([[rem[int(i)] for i in f] for f in sel], np.int64)
    if cache:
        np.savez(fn, V=Vo, F=Fo)
    return Vo, Fo


def vertex_normals(V, F):
    """area-weighted vertex normals; F may be an (N,4)/(N,3) array or a list of mixed tri/quad index lists"""
    V = np.asarray(V)
    n = np.zeros_like(V)
    if isinstance(F, np.ndarray) and F.ndim == 2:
        groups = [F]
    else:
        tri = [f for f in F if len(f) == 3]; quad = [f for f in F if len(f) == 4]
        groups = [np.array(g, dtype=np.int64) for g in (tri, quad) if len(g)]
    for G in groups:
        if G.shape[1] == 4:
            a, b, c, d = (V[G[:, k]] for k in range(4))
            fn = np.cross(c - a, d - b)
        else:
            a, b, c = (V[G[:, k]] for k in range(3))
            fn = np.cross(b - a, c - a)
        for k in range(G.shape[1]):
            np.add.at(n, G[:, k], fn)
    l = np.linalg.norm(n, axis=1, keepdims=True)
    return n / np.maximum(l, 1e-12)
