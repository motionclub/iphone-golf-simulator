"""Assemble rebuilt hands into full-body arrays (vertices reuse freed slots; extras appended)."""
import numpy as np
import hand_sdf as H, hand_topo as T, hand_build as HB


def assemble(co, F, sides=(+1, -1), w0=-0.055, build_kwargs=None, smooth_iters=0):
    N = len(co)
    co_new = co.copy()
    results = []
    # choose the number of palm rows so each rebuilt hand has at least as many vertices as slots it frees
    for nrows in (10, 11, 12, 13):
        HB.P['n_rows'] = nrows
        results = [(s, HB.build_hand(co, F, s, w0)) for s in sides]
        ok = True
        for s, r in results:
            used = set(v for f in r['builder'].faces for v in f if v >= N)
            if len(used) < int(r['cut']['Hmask'].sum()):
                ok = False
        if ok:
            break
    else:
        raise AssertionError('could not satisfy vertex budget')
    removed = np.zeros(len(F), bool)
    for s, r in results:
        removed |= r['cut']['removed']
    kept_F = F[~removed]
    extra_pos = []          # appended vertices (global coords)
    new_faces_all = []
    info = []
    base_next = N
    for s, r in results:
        B = r['builder']; cut = r['cut']
        used_faces = B.faces
        used_ids = sorted(set(v for f in used_faces for v in f if v >= N))
        freed = list(np.where(cut['Hmask'])[0])
        mapping = {}
        for k, vid in enumerate(used_ids):
            if k < len(freed):
                mapping[vid] = int(freed[k])
            else:
                mapping[vid] = N + len(extra_pos)
                extra_pos.append(None)
        # positions
        loc = np.array([B.pos[v - N] for v in used_ids])
        G = H.to_global(loc, s)
        for k, vid in enumerate(used_ids):
            m = mapping[vid]
            if m < N:
                co_new[m] = G[k]
            else:
                idx = m - N
                while len(extra_pos) <= idx:
                    extra_pos.append(None)
                extra_pos[idx] = G[k]
        leftover = freed[len(used_ids):]
        mf = [tuple(mapping.get(v, v) for v in f) for f in used_faces]
        oriented, vis = T.orient_consistently(mf, kept_F)
        new_faces_all.extend(oriented)
        info.append(dict(side=s, new_verts=len(used_ids), freed=len(freed), appended=max(0, len(used_ids) - len(freed)),
                         leftover=len(leftover), new_faces=len(mf), tris=sum(1 for f in mf if len(f) == 3)))
        assert not leftover, f'{len(leftover)} freed slots unused'
    verts = np.vstack([co_new] + [np.array(extra_pos)]) if extra_pos else co_new
    # vertices that belong to the rebuilt hands (freed slots + appended) are the only ones allowed to move
    hand_idx = np.zeros(len(verts), bool)
    for s, r in results:
        hand_idx[np.where(r['cut']['Hmask'])[0]] = True
    hand_idx[N:] = True
    if smooth_iters:
        faces_tmp = [tuple(map(int, f)) for f in kept_F] + [tuple(map(int, f)) for f in new_faces_all]
        verts = taubin_new(verts, faces_tmp, hand_idx, smooth_iters)
    faces = [tuple(map(int, f)) for f in kept_F] + [tuple(map(int, f)) for f in new_faces_all]
    return verts, faces, info


def taubin_new(verts, faces, mask, iters, lam=0.45, mu=-0.47):
    E = set()
    for f in faces:
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            E.add((min(a, b), max(a, b)))
    E = np.array(sorted(E))
    deg = np.bincount(E.ravel(), minlength=len(verts)).astype(float)
    w = mask.astype(float)[:, None]
    p = verts.copy()
    def lap(q):
        s = np.zeros_like(q)
        np.add.at(s, E[:, 0], q[E[:, 1]]); np.add.at(s, E[:, 1], q[E[:, 0]])
        return s / np.maximum(deg, 1)[:, None] - q
    for _ in range(iters):
        p += lam * w * lap(p)
        p += mu * w * lap(p)
    return p


def apply_to_blender(verts, faces, name='Body_M'):
    import bpy
    o = bpy.data.objects[name]; me = o.data
    me.clear_geometry()
    me.from_pydata([tuple(v) for v in verts.tolist()], [], faces)
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.update()
    return len(me.vertices), len(me.polygons)
