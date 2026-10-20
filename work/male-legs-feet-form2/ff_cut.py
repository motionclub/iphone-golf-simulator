"""Cut the old forefoot off the body mesh at f >= f_cut (foot frame) and return the clean boundary loop."""
import numpy as np
from collections import defaultdict
from ff_common import *


def _boundary(F, kept):
    ec = defaultdict(list)
    for fi in np.where(kept)[0]:
        f = F[fi]
        for k in range(len(f)):
            a, b = int(f[k]), int(f[(k + 1) % len(f)])
            ec[(min(a, b), max(a, b))].append(fi)
    bedges = [e for e, v in ec.items() if len(v) == 1]
    verts = set(v for e in bedges for v in e)
    cnt = defaultdict(int)
    for fi in np.where(kept)[0]:
        for v in F[fi]:
            if int(v) in verts:
                cnt[int(v)] += 1
    adj = defaultdict(list)
    for a, b in bedges:
        adj[a].append(b); adj[b].append(a)
    return bedges, verts, cnt, adj


def extract_cut(V, F, side, f_cut, frame=None, peel=10, region=None):
    """Remove every face that has a vertex in the foot region with local f >= f_cut.  Peel corner faces (vertices with a single kept face)
    until the boundary is a simple loop.  Returns dict(Lc (local coords of all verts), region mask, removed faces mask, kept mask, ring (ordered ids), free (vertex ids used only by removed faces))."""
    frame = frame or foot_frame(side)
    Lc = to_local(V, side, frame)
    if region is None:
        region = (side * V[:, 0] > 0.10) & (V[:, 2] < 0.20)
    Fl = [tuple(f) for f in F]
    cen_f = np.array([Lc[list(f), 0].mean() for f in Fl])
    in_any = np.array([region[list(f)].all() for f in Fl])          # whole face inside the foot region
    rem = in_any & (cen_f >= f_cut)
    kept = ~rem
    # peel only corner faces close to the cut plane (a vertex with a single kept face makes a pinched, non-simple loop)
    for it in range(peel):
        bedges, verts, cnt, adj = _boundary(Fl, kept)
        corners = set(v for v in verts if cnt[v] == 1)
        bad = set(v for v in verts if len(adj[v]) != 2)
        if not corners and not bad:
            break
        trial = kept.copy()
        for fi in np.where(kept)[0]:
            if cen_f[fi] > f_cut - 0.012 and any((int(v) in corners or int(v) in bad) for v in Fl[fi]):
                trial[fi] = False
        if (trial == kept).all():
            break
        kept = trial
    bedges, verts, cnt, adj = _boundary(Fl, kept)
    # the boundary of the kept faces may also include pre-existing open edges of the mesh (92 in the whole body); restrict to the foot region
    bverts = [v for v in verts if region[v] and Lc[v, 0] > f_cut - 0.04]
    loops = []
    seen = set()
    for v0 in sorted(bverts):
        if v0 in seen: continue
        ring = [v0]; seen.add(v0); prev = None; cur = v0
        while True:
            nbrs = [u for u in adj[cur] if u != prev]
            if prev is None: nxt = adj[cur][0]
            else:
                if len(nbrs) != 1: raise AssertionError(f'boundary vertex {cur} has {len(adj[cur])} boundary neighbours')
                nxt = nbrs[0]
            if nxt == v0: break
            ring.append(nxt); seen.add(nxt); prev, cur = cur, nxt
        loops.append(ring)
    assert len(loops) == 1, f'expected a single cut loop, got {len(loops)}: {[len(l) for l in loops]}'
    ring = loops[0]
    used = np.zeros(len(V), bool)
    for fi in np.where(kept)[0]:
        used[list(Fl[fi])] = True
    free = (~used) & region                      # vertices that belonged only to removed faces (reusable slots)
    # every removed face must have all its vertices either free or on the ring
    ringset = set(ring)
    return dict(Lc=Lc, region=region, removed=~kept, kept=kept, ring=ring, free=free, frame=frame, nloop=len(ring))


def order_ring_lz(ring, Lc):
    """Order the loop S_lat -> dorsal -> S_med -> plantar (counter-clockwise in (l, z) seen with l to the right and z up).
    Returns ring list (starting at the vertex nearest the lateral equator), polar angle array."""
    P = Lc[ring]
    lc = 0.5 * (P[:, 1].max() + P[:, 1].min()); zc = 0.5 * (P[:, 2].max() + P[:, 2].min())
    A = 0.5 * (P[:, 1].max() - P[:, 1].min()); B = 0.5 * (P[:, 2].max() - P[:, 2].min())
    ang = np.arctan2((P[:, 2] - zc) / B, (P[:, 1] - lc) / A)
    d = np.diff(np.r_[ang, ang[0]]); d = (d + np.pi) % (2 * np.pi) - np.pi
    ring = list(ring)
    if d.sum() < 0:                       # clockwise -> reverse
        ring = ring[::-1]; ang = ang[::-1]
    t = ang % (2 * np.pi)
    k0 = int(np.argmin(np.minimum(t, 2 * np.pi - t)))   # nearest to angle 0 (lateral side)
    ring = ring[k0:] + ring[:k0]; ang = np.r_[ang[k0:], ang[:k0]]
    return ring, (ang % (2 * np.pi), (lc, zc, A, B))


if __name__ == '__main__':
    import sys
    V, F = load_base()
    for side in (+1, -1):
        for yc in (-0.095,):
            fr = foot_frame(side)
            fcut = float(to_local(np.array([[side * 0.2207, yc, 0.0]]), side, fr)[0, 0])
            c = extract_cut(V, F, side, fcut)
            ring, (th, geo) = order_ring_lz(c['ring'], c['Lc'])
            P = c['Lc'][ring]
            print(f'side {side:+d} y_cut {yc} f_cut {fcut:+.4f}: loop {len(ring)} verts, removed faces {int(c["removed"].sum())}, free verts {int(c["free"].sum())}')
            print('  ring f range', P[:, 0].min().round(4), P[:, 0].max().round(4), ' l range', P[:, 1].min().round(4), P[:, 1].max().round(4), ' z range', P[:, 2].min().round(4), P[:, 2].max().round(4))
            for i in range(len(ring)):
                print(f'   {i:2d} id={ring[i]:6d} f={P[i,0]*1000:7.1f} l={P[i,1]*1000:7.1f} z={P[i,2]*1000:6.1f} th={np.degrees(th[i]):6.1f}')
            break
