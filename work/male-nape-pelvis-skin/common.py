"""Shared mesh helpers (numpy only; run with Blender's python3.13 or any numpy python).
Loads the start-state dump (data/start_*.npz/pkl), neighbours, normals, section extraction."""
import numpy as np, pickle, json
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-nape-pelvis-skin')
V0 = np.load(W / 'data/start_mesh.npz')['co']; F = pickle.load(open(W / 'data/start_faces.pkl', 'rb')); N0 = len(V0)
GROUPS = dict(np.load(W / 'data/start_groups.npz'))
_nb = None
def neighbors():
    global _nb
    if _nb is None:
        s = [set() for _ in range(N0)]
        for f in F:
            for k in range(len(f)):
                a, b = f[k], f[(k + 1) % len(f)]; s[a].add(b); s[b].add(a)
        _nb = [np.array(sorted(x), int) for x in s]
    return _nb
def edges():
    e = set()
    for f in F:
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]; e.add((min(a, b), max(a, b)))
    return np.array(sorted(e), int)
def vnormals(V):
    n = np.zeros_like(V)
    for f in F:
        for k in range(1, len(f) - 1):
            a, b, c = V[f[0]], V[f[k]], V[f[k + 1]]; fn = np.cross(b - a, c - a)
            n[f[0]] += fn; n[f[k]] += fn; n[f[k + 1]] += fn
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12); return n
def section_segments(V, z):
    """polylines (list of segments) of the mesh intersection with the plane Z=z -> array (m,2,2) of (x,y)"""
    segs = []
    for f in F:
        zz = V[list(f), 2]
        if zz.min() > z or zz.max() < z: continue
        pts = []
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]; za, zb = V[a, 2], V[b, 2]
            if (za - z) * (zb - z) < 0:
                t = (z - za) / (zb - za); pts.append(V[a, :2] + t * (V[b, :2] - V[a, :2]))
        if len(pts) == 2: segs.append(pts)
    return np.array(segs)
def rear_profile(V, z, x0=0.0, hw=0.004):
    """max y of surface within |x-x0|<hw at height z (rear-most surface, from section segments)"""
    S = section_segments(V, z)
    if len(S) == 0: return np.nan
    best = -9
    for s in S:
        for p in s:
            if abs(p[0] - x0) < hw: best = max(best, p[1])
    return best

def section_x(V, x):
    """intersection polyline segments of the mesh with plane X=x -> (m,2,2) of (y,z)"""
    segs = []
    for f in F:
        xx = V[list(f), 0]
        if xx.min() > x or xx.max() < x: continue
        pts = []
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]; xa, xb = V[a, 0], V[b, 0]
            if (xa - x) * (xb - x) < 0:
                t = (x - xa) / (xb - xa); p = V[a] + t * (V[b] - V[a]); pts.append((p[1], p[2]))
        if len(pts) == 2: segs.append(pts)
    return np.array(segs)
def rear_curve(V, x, zs):
    """rear-most y (largest y) of the section X=x at each z (interpolated from segment hits); nan if none"""
    S = section_x(V, x); out = np.full(len(zs), np.nan)
    if len(S) == 0: return out
    for i, z in enumerate(zs):
        best = -9.0
        for (p, q) in S:
            if (p[1] - z) * (q[1] - z) <= 0 and p[1] != q[1]:
                t = (z - p[1]) / (q[1] - p[1]); y = p[0] + t * (q[0] - p[0]); best = max(best, y)
        out[i] = best if best > -9 else np.nan
    return out

def front_curve(V, x, zs):
    """front-most y (smallest y) of the section X=x at each z"""
    S = section_x(V, x); out = np.full(len(zs), np.nan)
    if len(S) == 0: return out
    for i, z in enumerate(zs):
        best = 9.0
        for (p, q) in S:
            if (p[1] - z) * (q[1] - z) <= 0 and p[1] != q[1]:
                t = (z - p[1]) / (q[1] - p[1]); y = p[0] + t * (q[0] - p[0]); best = min(best, y)
        out[i] = best if best < 9 else np.nan
    return out
