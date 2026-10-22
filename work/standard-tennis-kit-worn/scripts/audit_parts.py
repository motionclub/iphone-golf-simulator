"""Topology audit of garment npz parts after a position weld (1e-6): closed? non-manifold? islands? where are the open boundaries?
blender -b --factory-startup --python audit_parts.py -- <data dir> <name> [<name> ...]"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from collections import defaultdict


def weld(V, F, eps=1e-6):
    key = np.round(V / eps).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inv = inv.reshape(-1)
    Vw = V[first]
    Fw = inv[F]
    ok = (Fw[:, 0] != Fw[:, 1]) & (Fw[:, 1] != Fw[:, 2]) & (Fw[:, 0] != Fw[:, 2])
    return Vw, Fw[ok], int((~ok).sum())


def topo(F, nv):
    E = np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], 0)
    Es = np.sort(E, axis=1)
    u, inv, cnt = np.unique(Es, axis=0, return_inverse=True, return_counts=True)
    inv = inv.reshape(-1)
    boundary = u[cnt == 1]
    nonman = u[cnt > 2]
    # directed-edge consistency (each interior edge must appear once in each direction)
    d = np.unique(E, axis=0, return_counts=True)
    dupdir = int((d[1] > 1).sum())
    # islands via union-find
    par = np.arange(nv)
    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for a, b in u.tolist():
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb
    used = np.unique(F)
    roots = np.array([find(a) for a in used.tolist()])
    isl = {}
    for a, r in zip(used.tolist(), roots.tolist()):
        isl.setdefault(r, []).append(a)
    return boundary, nonman, dupdir, list(isl.values())


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:]
    d = args[0]
    for nm in args[1:]:
        z = np.load(f'{d}/{nm}.npz')
        V, F = z['V'], z['F']
        Vw, Fw, ndeg = weld(V, F)
        b, nm_e, dupdir, isl = topo(Fw, len(Vw))
        # boundary edge clusters (islands of open edges)
        bb = ''
        if len(b):
            pts = Vw[np.unique(b)]
            bb = f'boundary bbox {pts.min(0).round(3).tolist()} .. {pts.max(0).round(3).tolist()}'
        sizes = sorted([len(i) for i in isl], reverse=True)
        print(f'{nm:22s} tris {len(F):6d} -> welded verts {len(Vw):6d} tris {len(Fw):6d} (degenerate {ndeg}) boundary {len(b):5d} nonmanifold {len(nm_e):4d} dup-directed {dupdir:4d} islands {len(isl):3d} (largest {sizes[:4]}) {bb}')
