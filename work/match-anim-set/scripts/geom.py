"""Mesh geometry helpers (pure numpy; runs in Blender's bundled python or any python with numpy).

Cross-sections are taken as *slabs*: all triangles whose centroid lies within +-half/2 of a plane, split into connected loops
(triangles sharing a vertex).  The area-weighted centroid of a slab loop approximates the centre of that limb cross-section."""
import numpy as np


class Mesh:
    def __init__(self, co, tri, ed):
        self.co = np.asarray(co, float)
        self.tri = np.asarray(tri, np.int64)
        self.ed = np.asarray(ed, np.int64)
        n = len(self.co)
        self.n = n
        p0, p1, p2 = self.co[self.tri[:, 0]], self.co[self.tri[:, 1]], self.co[self.tri[:, 2]]
        self.tcent = (p0 + p1 + p2) / 3.0
        cr = np.cross(p1 - p0, p2 - p0)
        self.tarea = 0.5 * np.linalg.norm(cr, axis=1)
        self.tnorm = cr / np.maximum(2 * self.tarea[:, None], 1e-30)
        # CSR adjacency (vertex graph)
        a = np.concatenate([self.ed[:, 0], self.ed[:, 1]])
        b = np.concatenate([self.ed[:, 1], self.ed[:, 0]])
        o = np.argsort(a, kind='stable')
        self.adj_idx = b[o]
        self.adj_ptr = np.zeros(n + 1, np.int64)
        np.add.at(self.adj_ptr, a + 1, 1)
        self.adj_ptr = np.cumsum(self.adj_ptr)
        self.elen = np.linalg.norm(self.co[self.ed[:, 0]] - self.co[self.ed[:, 1]], axis=1)
        # vertex normals (area weighted)
        vn = np.zeros((n, 3))
        for k in range(3):
            np.add.at(vn, self.tri[:, k], self.tnorm * self.tarea[:, None])
        self.vnorm = vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-30)

    def neighbors(self, i):
        return self.adj_idx[self.adj_ptr[i]:self.adj_ptr[i + 1]]


def _uf_components(tri_sel, tri):
    """connected components of the selected triangles (sharing a vertex). returns list of index arrays into tri_sel order."""
    vs = tri[tri_sel]
    uniq, inv = np.unique(vs.ravel(), return_inverse=True)
    inv = inv.reshape(-1, 3)
    parent = np.arange(len(uniq))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b, c in inv:
        ra, rb, rc = find(a), find(b), find(c)
        if ra != rb:
            parent[rb] = ra
        rc = find(c)
        ra = find(a)
        if rc != ra:
            parent[rc] = ra
    root = np.array([find(x) for x in range(len(uniq))])
    tri_root = root[inv[:, 0]]
    out = []
    for r in np.unique(tri_root):
        out.append(np.where(tri_root == r)[0])
    return out


def slab_loops(m, point, direction, half=0.004, mask=None, min_tris=6):
    """cross-section loops of mesh m by the plane through `point` with normal `direction` (slab +-half).
    mask: optional boolean array over TRIANGLES to restrict to.  returns list of dicts sorted by size (desc):
    centroid (area weighted), area, n, verts (vertex ids), bounds along u,v (the two in-plane axes), mean radius."""
    d = np.asarray(direction, float)
    d = d / np.linalg.norm(d)
    s = (m.tcent - np.asarray(point)) @ d
    sel = np.where(np.abs(s) <= half)[0]
    if mask is not None:
        sel = sel[mask[sel]]
    if len(sel) < min_tris:
        return []
    comps = _uf_components(sel, m.tri)
    out = []
    # in-plane basis
    ref = np.array([0.0, 0.0, 1.0]) if abs(d[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(d, ref)
    u /= np.linalg.norm(u)
    v = np.cross(d, u)
    for c in comps:
        t = sel[c]
        if len(t) < min_tris:
            continue
        a = m.tarea[t]
        cen = (m.tcent[t] * a[:, None]).sum(0) / a.sum()
        verts = np.unique(m.tri[t].ravel())
        P = m.co[verts] - cen
        pu, pv = P @ u, P @ v
        out.append(dict(centroid=cen, area=float(a.sum()), n=len(t), verts=verts, tris=t,
                        ubounds=(float(pu.min()), float(pu.max())), vbounds=(float(pv.min()), float(pv.max())),
                        radius=float(np.sqrt(pu ** 2 + pv ** 2).mean()), u=u, v=v))
    out.sort(key=lambda r: -r['n'])
    return out


def components_vertex(m, vmask):
    """connected components (vertex graph) of the vertices selected by vmask; returns list of vertex-index arrays (largest first)."""
    seen = np.zeros(m.n, bool)
    comps = []
    for s in np.where(vmask)[0]:
        if seen[s]:
            continue
        st = [int(s)]
        seen[s] = True
        comp = [int(s)]
        while st:
            u_ = st.pop()
            for w in m.neighbors(u_):
                if vmask[w] and not seen[w]:
                    seen[w] = True
                    st.append(int(w))
                    comp.append(int(w))
        comps.append(np.array(comp))
    comps.sort(key=lambda c: -len(c))
    return comps


def dijkstra(m, sources, vmask=None):
    """geodesic (edge-graph) distance from `sources` (vertex ids) over the mesh edges; vmask restricts the vertices that may be used."""
    import heapq
    INF = 1e30
    dist = np.full(m.n, INF)
    heap = []
    for s in np.atleast_1d(sources):
        dist[s] = 0.0
        heap.append((0.0, int(s)))
    heapq.heapify(heap)
    ptr, idx = m.adj_ptr, m.adj_idx
    co = m.co
    while heap:
        d0, u_ = heapq.heappop(heap)
        if d0 > dist[u_]:
            continue
        for k in range(ptr[u_], ptr[u_ + 1]):
            w = idx[k]
            if vmask is not None and not vmask[w]:
                continue
            nd = d0 + float(np.linalg.norm(co[u_] - co[w]))
            if nd < dist[w]:
                dist[w] = nd
                heapq.heappush(heap, (nd, int(w)))
    return dist


def point_in_mesh(m, pts, rays=((0.3, 0.5, 0.8), (-0.6, 0.2, 0.4), (0.1, -0.9, 0.3))):
    """ray-parity inside test (Moller-Trumbore, brute force over all triangles per point; use for a handful of points)."""
    p0 = m.co[m.tri[:, 0]]
    e1 = m.co[m.tri[:, 1]] - p0
    e2 = m.co[m.tri[:, 2]] - p0
    res = np.zeros(len(pts), int)
    for r in rays:
        dvec = np.asarray(r, float)
        dvec /= np.linalg.norm(dvec)
        pv = np.cross(dvec, e2)
        det = (e1 * pv).sum(1)
        ok = np.abs(det) > 1e-14
        inv = np.zeros_like(det)
        inv[ok] = 1.0 / det[ok]
        for k, o in enumerate(np.asarray(pts, float)):
            tv = o - p0
            u = (tv * pv).sum(1) * inv
            qv = np.cross(tv, e1)
            v = (dvec * qv).sum(1) * inv
            t = (e2 * qv).sum(1) * inv
            hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-9)
            res[k] += int(hit.sum() % 2)
    return res >= (len(rays) // 2 + 1)


def track_centerline(m, p0, d0, step=0.01, nsteps=80, half=0.004, max_jump=0.03, ring_cap=0.45, smooth=3, mask=None):
    """follow a limb: slab loop nearest to the running point, centroid -> next point along the (smoothed) direction.
    returns list of dict(point, centroid, dir, radius, ext, n) ; stops when the loop jumps (limb merges into the trunk) or vanishes."""
    out = []
    p = np.asarray(p0, float)
    d = np.asarray(d0, float) / np.linalg.norm(d0)
    cents = []
    for k in range(nsteps):
        loops = slab_loops(m, p, d, half=half, mask=mask, min_tris=5)
        if not loops:
            break
        best = min(loops, key=lambda L: np.linalg.norm(L['centroid'] - p))
        c = best['centroid']
        if np.linalg.norm(c - p) > max_jump * 3 and k > 0:
            break
        u, v = best['u'], best['v']
        ext = (best['ubounds'][1] - best['ubounds'][0], best['vbounds'][1] - best['vbounds'][0])
        if max(ext) > ring_cap:
            out.append(dict(point=p.copy(), centroid=c, dir=d.copy(), radius=best['radius'], ext=ext, n=best['n'], merged=True))
            break
        out.append(dict(point=p.copy(), centroid=c, dir=d.copy(), radius=best['radius'], ext=ext, n=best['n'], merged=False))
        cents.append(c)
        if len(cents) > smooth:
            dd = c - cents[-1 - smooth]
            if np.linalg.norm(dd) > 1e-6:
                dn = dd / np.linalg.norm(dd)
                if dn @ d0 < 0:
                    dn = -dn
                d = 0.5 * d + 0.5 * dn
                d /= np.linalg.norm(d)
        p = c + d * step
    return out


def section_loops(m, point, normal, tri_mask=None):
    """exact plane section: closed loops of the mesh surface cut by the plane (point, normal).
    returns list of dict(poly (k,3), centroid (area centroid of the polygon, 3d), area, perim, req (equivalent radius), ext (u,v extents), u, v, center_of_bbox)
    sorted by |area| desc.  Open chains are closed implicitly."""
    n = np.asarray(normal, float)
    n = n / np.linalg.norm(n)
    p0 = np.asarray(point, float)
    s = (m.co - p0) @ n
    sg = s[m.tri]
    pos = sg > 0
    cut = pos.any(1) & (~pos.all(1))
    if tri_mask is not None:
        cut &= tri_mask
    ti = np.where(cut)[0]
    if len(ti) == 0:
        return []
    segs = []   # (edge_key_a, edge_key_b, pa, pb)
    for t in ti:
        a, b, c = m.tri[t]
        pts = []
        keys = []
        for (u_, v_) in ((a, b), (b, c), (c, a)):
            su, sv = s[u_], s[v_]
            if (su > 0) != (sv > 0):
                f = su / (su - sv)
                pts.append(m.co[u_] + f * (m.co[v_] - m.co[u_]))
                keys.append((min(u_, v_), max(u_, v_)))
        if len(pts) == 2:
            segs.append((keys[0], keys[1], pts[0], pts[1]))
    if not segs:
        return []
    # chain
    from collections import defaultdict
    link = defaultdict(list)
    for i, (ka, kb, pa, pb) in enumerate(segs):
        link[ka].append(i)
        link[kb].append(i)
    used = [False] * len(segs)
    loops = []
    for i0 in range(len(segs)):
        if used[i0]:
            continue
        ka, kb, pa, pb = segs[i0]
        used[i0] = True
        chain = [pa, pb]
        cur_key = kb
        while True:
            nxt = None
            for j in link[cur_key]:
                if not used[j]:
                    nxt = j
                    break
            if nxt is None:
                break
            used[nxt] = True
            kA, kB, pA, pB = segs[nxt]
            if kA == cur_key:
                chain.append(pB)
                cur_key = kB
            else:
                chain.append(pA)
                cur_key = kA
        loops.append(np.array(chain))
    ref = np.array([0.0, 0.0, 1.0]) if abs(n[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = np.cross(n, ref)
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    out = []
    for poly in loops:
        if len(poly) < 4:
            continue
        pu, pv = (poly - p0) @ u, (poly - p0) @ v
        x1, y1 = pu, pv
        x2, y2 = np.roll(pu, -1), np.roll(pv, -1)
        cr = x1 * y2 - x2 * y1
        A = 0.5 * cr.sum()
        perim = float(np.linalg.norm(np.diff(np.vstack([poly, poly[:1]]), axis=0), axis=1).sum())
        if abs(A) > 1e-9:
            cx = ((x1 + x2) * cr).sum() / (6 * A)
            cy = ((y1 + y2) * cr).sum() / (6 * A)
        else:
            cx, cy = pu.mean(), pv.mean()
        cen = p0 + cx * u + cy * v
        out.append(dict(poly=poly, centroid=cen, area=abs(A), perim=perim, req=float(np.sqrt(abs(A) / np.pi)),
                        ext=(float(pu.max() - pu.min()), float(pv.max() - pv.min())), u=u, v=v,
                        bbox_center=p0 + 0.5 * (pu.max() + pu.min()) * u + 0.5 * (pv.max() + pv.min()) * v, n=len(poly)))
    out.sort(key=lambda L: -L['area'])
    return out


def track_limb(m, p0, d0, step=0.01, nsteps=80, max_jump=0.03, area_cap=0.06, smooth=3, tri_mask=None, min_area=1e-5, jump_ratio=1.8):
    """follow a limb with exact section loops; stops when the loop area suddenly grows (limb merges into the trunk) or vanishes."""
    out = []
    p = np.asarray(p0, float)
    d = np.asarray(d0, float) / np.linalg.norm(d0)
    d_ref = d.copy()
    cents = []
    prev_area = None
    for k in range(nsteps):
        loops = section_loops(m, p, d, tri_mask=tri_mask)
        loops = [L for L in loops if L['area'] > min_area]
        if not loops:
            break
        best = min(loops, key=lambda L: np.linalg.norm(L['centroid'] - p))
        if k > 0 and np.linalg.norm(best['centroid'] - p) > max_jump * 2:
            break
        merged = (prev_area is not None and best['area'] > jump_ratio * prev_area) or best['area'] > area_cap
        out.append(dict(point=p.copy(), centroid=best['centroid'], dir=d.copy(), area=best['area'], req=best['req'], ext=best['ext'], merged=merged, perim=best['perim']))
        if merged:
            break
        prev_area = best['area']
        cents.append(best['centroid'])
        if len(cents) > smooth:
            dd = best['centroid'] - cents[-1 - smooth]
            if np.linalg.norm(dd) > 1e-6:
                dn = dd / np.linalg.norm(dd)
                if dn @ d_ref < 0:
                    dn = -dn
                d = 0.5 * d + 0.5 * dn
                d /= np.linalg.norm(d)
        p = best['centroid'] + d * step
    return out
