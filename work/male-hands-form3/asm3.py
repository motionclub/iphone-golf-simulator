"""Assemble a candidate Body_M mesh: current mesh (72fc6465) with both hand shells replaced by hand3 hands.

usage (Blender's python):  py asm3.py <tag> '<json params>'
writes data/cand_<tag>.npz (V, corner_verts, loop_start, loop_total, meta) and prints a short report.
Existing vertex indices never change: the freed hand-shell slots (873 per side) are reused, extra vertices are appended.
"""
import sys, json, time
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parent
sys.path.insert(0, str(W))
from hlib import *
import hand4 as hand3, arms3

import os
BASE_MESH = os.environ.get('BASE_MESH', 'data/mesh_cur.npz')
M0 = Mesh.from_npz(W / BASE_MESH)
V0 = M0.V.astype(np.float64); POLYS0 = M0.polys; N0 = len(V0)


def side_data(side):
    return (np.load(W / f'data/ring_{side}.npy'), np.load(W / f'data/shellv_{side}.npy'), np.load(W / f'data/removed_{side}.npy'))


def local_graph(B, info, ring_ids, ring_L):
    """compact graph of the new hand shell for smoothing: returns (ids, pos(local), E, fixed mask)"""
    N = B.N
    ids_new = np.arange(N, N + len(B.pos))
    pos = np.vstack([np.array(B.pos), ring_L])
    ids = np.r_[ids_new, np.array(ring_ids)]
    lut = {int(v): i for i, v in enumerate(ids)}
    E = set()
    for f in B.faces:
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            E.add((min(lut[a], lut[b]), max(lut[a], lut[b])))
    E = np.array(sorted(E))
    fixed = np.zeros(len(ids), bool); fixed[len(ids_new):] = True
    return ids, pos, E, fixed, lut


def assemble(params=None, post=None, verbose=True, arm=None):
    t0 = time.time()
    Vb = V0.copy()
    if arm is not None:
        Vb, _ = arms3.arm_edit(V0, POLYS0, arm if isinstance(arm, dict) else None)
    V = Vb.copy(); polys_new = []; extra = []; removed_all = np.zeros(len(POLYS0), bool)
    sides_info = {}
    base_next = N0
    for side in (+1, -1):
        ring, shellv, removed = side_data(side)
        L = to_local(Vb, side)
        B, info = hand3.build_hand(ring.tolist(), L[ring], N0, params)
        if post is not None:
            post(B, info, ring, L[ring], side)
        used = sorted(set(v for f in B.faces for v in f if v >= N0))
        # vertices strictly inside the thumb hole are unused and simply not mapped
        slots = list(shellv)                               # ascending indices
        mapping = {}
        for k, vid in enumerate(used):
            if k < len(slots): mapping[vid] = int(slots[k])
            else:
                mapping[vid] = N0 + len(extra); extra.append(None)
        # (extra entries are filled below)
        loc = np.array([B.pos[v - N0] for v in used]); G = to_global(loc, side)
        for k, vid in enumerate(used):
            m = mapping[vid]
            if m < N0: V[m] = G[k]
            else: extra[m - N0] = G[k]
        assert len(used) >= len(slots), f'new hand has {len(used)} verts < {len(slots)} slots'
        mf = [tuple(mapping.get(v, v) for v in f) for f in B.faces]
        sides_info[side] = dict(B=B, info=info, mapping=mapping, faces=mf, n_new=len(used), n_slots=len(slots), used=used)
        removed_all |= np.zeros(len(POLYS0), bool); removed_all[removed] = True
        polys_new.append(mf)
    Vn = np.vstack([V, np.array(extra)]) if extra else V
    kept = [POLYS0[i] for i in range(len(POLYS0)) if not removed_all[i]]
    ring_all = set()
    for side in (+1, -1): ring_all |= set(int(i) for i in np.load(W / f'data/ring_{side}.npy'))
    fixed = [p for p in kept if any(v in ring_all for v in p)]
    allnew = [f for mf in polys_new for f in mf]
    oriented, vis = orient_consistently(allnew, fixed)
    assert all(vis[len(fixed):]) , 'unreached new faces during orientation'
    polys = kept + oriented
    if verbose:
        print('assembled: verts %d (+%d appended) polys %d (kept %d + new %d) in %.1fs' % (len(Vn), len(extra), len(polys), len(kept), len(oriented), time.time() - t0))
    return Vn, polys, sides_info


def save(path, Vn, polys, meta=None):
    M = Mesh(Vn.astype(np.float32), polys)
    cv, ls, lt = M.arrays()
    np.savez(path, V=M.V, corner_verts=cv, loop_start=ls, loop_total=lt, **(meta or {}))


if __name__ == '__main__':
    tag = sys.argv[1]; params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    Vn, polys, si = assemble(params)
    mani = check_manifold(polys); mani0 = check_manifold(POLYS0)
    print('manifold new', mani, 'orig', mani0)
    for s in (+1, -1):
        print('side', s, 'new verts', si[s]['n_new'], 'slots', si[s]['n_slots'])
    save(W / f'data/cand_{tag}.npz', Vn, polys)
    print('saved', tag)
