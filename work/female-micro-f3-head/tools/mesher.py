"""Graded refinement of the direction-space cage (bmesh) + evaluation of Phi.  Runs inside Blender (bmesh)."""
import numpy as np
import bmesh


def refine(cg, H, level_fn, max_level=3, verbose=True):
    pinned_set = set(int(k) for k in cg['pinned'])
    bm = bmesh.new()
    vs = [bm.verts.new(tuple(float(c) for c in u)) for u in cg['u']]
    for f, k in zip(cg['faces'], cg['kind']):
        fc = bm.faces.new([vs[i] for i in f]); fc.material_index = 0 if k in (0, 2) else 99
    n_orig = len(vs)
    for lev in range(1, max_level + 1):
        bm.faces.ensure_lookup_table()
        faces = list(bm.faces)
        quad = np.array([len(f.verts) == 4 and f.material_index < 99 for f in faces])
        depth = np.array([f.material_index for f in faces])
        cd = np.array([np.mean([v.co[:] for v in f.verts], axis=0) for f in faces])
        cd /= np.linalg.norm(cd, axis=1, keepdims=True)
        cen = H.phi(cd)
        want = level_fn(cen)
        has_pin = np.array([any(v.index in pinned_set for v in f.verts) for f in faces])
        sel = [faces[i] for i in range(len(faces)) if quad[i] and depth[i] == lev - 1 and want[i] >= lev and not has_pin[i]]
        selset = set(sel)
        extra = set()
        for f in selset:
            for e in f.edges:
                for g in e.link_faces:
                    if g not in selset and g.material_index < lev - 1 and len(g.verts) == 4 and not any(v.index in pinned_set for v in g.verts):
                        extra.add(g)
        edges = set()
        for f in selset | extra:
            for e in f.edges:
                if not e.is_boundary: edges.add(e)
        if not edges: continue
        for f in selset: f.material_index = lev
        for g in extra: g.material_index = g.material_index + 1
        bmesh.ops.subdivide_edges(bm, edges=list(edges), cuts=1, use_grid_fill=True)
        for v in bm.verts:
            c = v.co; n = c.length
            if n > 0: v.co = c / n
        if verbose: print(f'level {lev}: refined {len(selset)}+{len(extra)} faces -> {len(bm.faces)} faces, {len(bm.verts)} verts')
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    U = np.array([v.co[:] for v in bm.verts], float)
    # original vertices keep their indices (bmesh preserves order for existing verts)
    F = [[v.index for v in f.verts] for f in bm.faces]
    depth = [f.material_index for f in bm.faces]
    bm.free()
    return U, F, depth, n_orig
