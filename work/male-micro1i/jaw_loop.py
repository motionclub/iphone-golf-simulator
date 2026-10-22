"""Continuous jaw->ear edge path: Dijkstra over the mesh graph along the jaw curve (front projection), per side.  python3.13 jaw_loop.py <tag> -> data/jaw_loops_<tag>.pkl"""
import sys, heapq, pickle; sys.path.insert(0, '.')
import numpy as np
from m1i_lib import *

JAW = np.array([(0.014, 1.4575), (0.030, 1.4592), (0.046, 1.4640), (0.060, 1.4720), (0.068, 1.4830), (0.0715, 1.4970), (0.0735, 1.5110), (0.0765, 1.5260)])


def seg_dist_xz(px, pz, pts):
    d = np.full(px.shape, np.inf)
    for (ax_, az_), (bx_, bz_) in zip(pts[:-1], pts[1:]):
        ex, ez = bx_ - ax_, bz_ - az_
        t = np.clip(((px - ax_) * ex + (pz - az_) * ez) / (ex * ex + ez * ez + 1e-18), 0, 1)
        d = np.minimum(d, np.hypot(px - (ax_ + t * ex), pz - (az_ + t * ez)))
    return d


def build(V, F, band=0.0045, lam=2.5):
    n = len(V); adj = [[] for _ in range(n)]
    for a, b in edges_of(F): adj[a].append(b); adj[b].append(a)
    out = {}
    for side, name in ((-1, 'L'), (1, 'R')):
        pts = JAW.copy(); pts[:, 0] *= side
        dist = seg_dist_xz(V[:, 0], V[:, 2], pts)
        cand = (dist < band) & (np.sign(V[:, 0]) == side) & (V[:, 1] > -0.17) & (V[:, 1] < 0.02) & (V[:, 2] > 1.44) & (V[:, 2] < 1.54)
        cset = set(np.where(cand)[0].tolist())
        def nearest(pt):
            idx = np.array(sorted(cset)); d = np.hypot(V[idx, 0] - pt[0], V[idx, 2] - pt[1]) + 0.2 * np.abs(V[idx, 1] + 0.05)
            return int(idx[np.argmin(d)])
        a = nearest(pts[0]); b = nearest(pts[-1])
        pq = [(0.0, a)]; best = {a: 0.0}; prev = {}
        while pq:
            d, u = heapq.heappop(pq)
            if u == b: break
            if d > best.get(u, 1e18): continue
            for v in adj[u]:
                if v not in cset: continue
                w = float(np.linalg.norm(V[u] - V[v])) + lam * dist[v]
                if d + w < best.get(v, 1e18): best[v] = d + w; prev[v] = u; heapq.heappush(pq, (d + w, v))
        if b not in best: raise RuntimeError('no jaw path for side ' + name)
        path = [b]
        while path[-1] != a: path.append(prev[path[-1]])
        out[name] = path[::-1]
    return out


if __name__ == '__main__':
    tag = sys.argv[1]
    V, F, loops = load(tag)
    jl = build(V, F)
    E = set(map(tuple, edges_of(F).tolist()))
    for k, p in jl.items():
        ok = all((min(a, b), max(a, b)) in E for a, b in zip(p[:-1], p[1:]))
        d = np.hypot(V[p, 0] * 1.0 - 0, 0)  # placeholder
        pts = JAW.copy(); pts[:, 0] *= (-1 if k == 'L' else 1)
        dd = seg_dist_xz(V[p, 0], V[p, 2], pts) * 1000
        print(k, 'verts', len(p), 'continuous edge path', ok, 'max dist to jaw curve %.2f mm  mean %.2f' % (dd.max(), dd.mean()), 'path length %.1f mm' % (sum(np.linalg.norm(V[a] - V[b]) for a, b in zip(p[:-1], p[1:])) * 1000))
    pickle.dump(jl, open(f'data/jaw_loops_{tag}.pkl', 'wb'))
