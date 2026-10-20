"""Micro1j edit library: topology-preserving, position-only edits of the male HeroBase head/neck (zone z >= 1.40), pure numpy.
Run with Blender's python3.13 and PYTHONPATH=pylib.  Every edit returns a new V; `ZONE` is enforced centrally (verts with start z < 1.40 never move)."""
import sys, math, heapq, pickle, json
from pathlib import Path
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1k-head')
from j_lib import *
sys.path.insert(0, str(I1))
from edlib import Mesh, vertex_normals, sstep

ZONE_Z = 1.40
mm = 1e-3


class Ctx:
    """start geometry + adjacency + helpers shared by all edits"""
    def __init__(self):
        self.V0, self.F, self.loops = load_start()
        self.n = len(self.V0)
        self.M = Mesh(self.V0, self.F)
        self.E = self.M.E
        self.N0 = vertex_normals(self.V0, self.F)
        self.zone = self.V0[:, 2] >= ZONE_Z
        adj = [[] for _ in range(self.n)]
        for a, b in self.E: adj[a].append(b); adj[b].append(a)
        self.adj = adj
        self.jaw = pickle.load(open(W / 'data/jaw_loops_start.pkl', 'rb'))
        self.stored_vn = np.load(W / 'data/vn_stored.npy')

    def geodesic(self, V, src, maxd=0.06):
        """multi-source Dijkstra over mesh edges (edge length weights); returns dist array (inf beyond maxd) and nearest-source index"""
        dist = np.full(self.n, np.inf); who = np.full(self.n, -1)
        pq = []
        for s in src:
            dist[s] = 0.0; who[s] = s; pq.append((0.0, int(s)))
        heapq.heapify(pq)
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u] or d > maxd: continue
            for v in self.adj[u]:
                w = d + float(np.linalg.norm(V[u] - V[v]))
                if w < dist[v]: dist[v] = w; who[v] = who[u]; heapq.heappush(pq, (w, v))
        return dist, who

    def enforce_zone(self, V):
        V = V.copy(); V[~self.zone] = self.V0[~self.zone]; return V


def gauss(x, c, s): return np.exp(-0.5 * ((np.asarray(x, float) - c) / s) ** 2)


def interp_profile(zs, ys, z):
    """monotone-cubic (PCHIP-like, numpy only) interpolation of y(z) through nodes (zs ascending)"""
    zs = np.asarray(zs, float); ys = np.asarray(ys, float); z = np.asarray(z, float)
    h = np.diff(zs); d = np.diff(ys) / h
    m = np.zeros_like(ys)
    for i in range(1, len(zs) - 1):
        if d[i - 1] * d[i] > 0:
            w1 = 2 * h[i] + h[i - 1]; w2 = h[i] + 2 * h[i - 1]; m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    m[0] = d[0]; m[-1] = d[-1]
    i = np.clip(np.searchsorted(zs, z) - 1, 0, len(zs) - 2)
    t = (z - zs[i]) / h[i]
    h00 = 2 * t**3 - 3 * t**2 + 1; h10 = t**3 - 2 * t**2 + t; h01 = -2 * t**3 + 3 * t**2; h11 = t**3 - t**2
    out = h00 * ys[i] + h10 * h[i] * m[i] + h01 * ys[i + 1] + h11 * h[i] * m[i + 1]
    return np.where((z < zs[0]) | (z > zs[-1]), np.interp(z, zs, ys), out)


# ------------------------------------------------------------------------------------------------------------
# normals: keep the stored (shipped) custom normals; rotate them by the change of the geometric vertex normal
# ------------------------------------------------------------------------------------------------------------
def rotate_normals(stored, G0, G1):
    """per-vertex rotation taking G0 -> G1 applied to `stored` (Rodrigues); identity where G0 == G1"""
    out = stored.copy()
    c = np.clip((G0 * G1).sum(1), -1, 1)
    ang = np.arccos(c); ax = np.cross(G0, G1); an = np.linalg.norm(ax, axis=1)
    sel = np.where((an > 1e-9) & (ang > 1e-9))[0]
    if len(sel):
        k = ax[sel] / an[sel, None]; v = stored[sel]; a = ang[sel, None]
        out[sel] = v * np.cos(a) + np.cross(k, v) * np.sin(a) + k * (k * v).sum(1, keepdims=True) * (1 - np.cos(a))
    out /= np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-12)
    return out


def updated_normals(ctx, V1, extra_smooth=None, smooth_iters=0):
    """normals for the edited mesh: stored normals, rotated by the geometric change.  extra_smooth: per-vertex weight 0..1 for additional
    umbrella smoothing of the *result* (shading-only fairing, geometry untouched)"""
    G0 = ctx.N0; G1 = vertex_normals(V1, ctx.F)
    out = rotate_normals(ctx.stored_vn, G0, G1)
    if extra_smooth is not None and smooth_iters:
        w = np.asarray(extra_smooth, float)[:, None]
        for _ in range(smooth_iters):
            t = 0.5 * out + 0.5 * ctx.M.nbr_mean(out); t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-12)
            out = out * (1 - w) + t * w; out /= np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-12)
    return out


def moved_report(ctx, V1):
    d = np.linalg.norm(V1 - ctx.V0, axis=1)
    mv = d > 0
    return dict(moved=int(mv.sum()), max_mm=float(d.max() * 1000), min_z_moved=float(ctx.V0[mv, 2].min()) if mv.any() else None,
                outside_zone=int((mv & ~ctx.zone).sum()))
