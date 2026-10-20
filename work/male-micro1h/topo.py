"""Stage 2 topology: graded quad subdivision of the cage head region (weld ring untouched).
Zones are nested so every transition is one level: L0 9.5 mm -> L1 4.7 mm -> L2 2.4 mm (-> L3 1.2 mm).
"""
import pickle
import numpy as np
import bmesh
import h1lib as H

ZRING = 1.43            # cage faces with all verts above this form the head region (weld ring = boundary of this set)


def region_faces(V, F, zring=ZRING):
    """indices of cage faces in the head region: every vertex z > zring and |x| < 0.16 (above the neck)"""
    sel = []
    for i, f in enumerate(F):
        if all(V[j, 2] > zring and abs(V[j, 0]) < 0.16 for j in f):
            sel.append(i)
    return sel


ZONES = dict(
    eyes=dict(x=(0.014, 0.062), z=(1.563, 1.607)),
    nose=dict(x=(0.0, 0.030), z=(1.524, 1.604)),
    mouth=dict(x=(0.0, 0.046), z=(1.474, 1.526)),
    ears=dict(x=(0.062, 0.118), y=(-0.042, 0.018), z=(1.518, 1.606)),
)


def zone_level(c, cfg=None):
    """target subdivision level at face centres c (N,3): 2 = features (2.4 mm), 1 = face/sides (4.7 mm), 0 = rest"""
    x = np.abs(c[:, 0]); y = c[:, 1]; z = c[:, 2]
    lvl = np.zeros(len(c), int)
    l1 = (z > 1.450) & (z < 1.650) & (y < -0.005) & (x < 0.094)
    lvl[l1] = 1
    l2 = np.zeros(len(c), bool)
    for k, zn in (cfg or ZONES).items():
        m = (x >= zn['x'][0]) & (x <= zn['x'][1]) & (z >= zn['z'][0]) & (z <= zn['z'][1])
        if 'y' in zn:
            m &= (y >= zn['y'][0]) & (y <= zn['y'][1])
        else:
            m &= (y < -0.020)                                   # front only
        l2 |= m
    lvl[l2] = 2
    return lvl


def build_graded(V, F, fidx, level_fn=zone_level, max_level=2, verbose=True):
    """returns (Vn, Fn, info): refined region mesh. Vertices of the original cage region keep their positions; boundary ring is unchanged."""
    used = sorted({int(v) for i in fidx for v in F[i]})
    rem = {v: k for k, v in enumerate(used)}
    bm = bmesh.new()
    verts = [bm.verts.new(tuple(V[v])) for v in used]
    bm.verts.ensure_lookup_table()
    for i in fidx:
        bm.faces.new([verts[rem[int(v)]] for v in F[i]])
    bm.faces.ensure_lookup_table()
    boundary_before = [e for e in bm.edges if e.is_boundary]
    ring_pos = {tuple(np.round(np.array(v.co[:]), 9)) for e in boundary_before for v in e.verts}
    for lev in range(1, max_level + 1):
        faces = [f for f in bm.faces]
        c = np.array([f.calc_center_median()[:] for f in faces])
        cur_levels = np.array([f.index for f in faces])      # placeholder
        want = level_fn(c)
        # a face of current depth d needs subdividing when want > d ; track depth via edge length class: store in face material_index
        depth = np.array([f.material_index for f in faces])
        todo = [f for f, w, d in zip(faces, want, depth) if w >= lev and d < lev]
        edges = set()
        for f in todo:
            for e in f.edges:
                if not e.is_boundary:
                    edges.add(e)
        if not edges:
            continue
        ret = bmesh.ops.subdivide_edges(bm, edges=list(edges), cuts=1, use_grid_fill=True)
        # faces created by the op: mark depth
        for g in ret['geom_inner'] + ret['geom_split'] + ret['geom']:
            if isinstance(g, bmesh.types.BMFace) and g.material_index < lev:
                g.material_index = lev
        if verbose:
            print(f'level {lev}: subdivided {len(todo)} faces ({len(edges)} edges) -> faces {len(bm.faces)}')
    ng = [f for f in bm.faces if len(f.verts) > 4]
    if ng:
        bmesh.ops.triangulate(bm, faces=ng, quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table(); bm.edges.ensure_lookup_table()
    Vn = np.array([v.co[:] for v in bm.verts], float)
    Fn = [[v.index for v in f.verts] for f in bm.faces]
    bnd = {tuple(np.round(Vn[v.index], 9)) for e in bm.edges if e.is_boundary for v in e.verts}
    info = dict(n_verts=len(Vn), n_faces=len(Fn), tris=int(sum(len(f) - 2 for f in Fn)),
                n_tri_faces=int(sum(1 for f in Fn if len(f) == 3)), n_quad_faces=int(sum(1 for f in Fn if len(f) == 4)),
                n_ngon=int(sum(1 for f in Fn if len(f) > 4)), boundary_ring_unchanged=bnd == ring_pos, used=used)
    bm.free()
    return Vn, Fn, info
