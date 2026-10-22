"""Head cage in direction space: spherified cube (top + 4 sides, N cells per edge -> 4N columns) + extension rows to the 30-vertex collar ring.
Vertices are unit direction vectors about C; the collar ring vertices are pinned to their real positions.
build_cage(ring_pos, C) -> dict(u (n,3), faces list, kind list, pinned {vidx: pos}, B list, rows)"""
import numpy as np


def spherify(p):
    x, y, z = p[..., 0], p[..., 1], p[..., 2]
    x2, y2, z2 = x * x, y * y, z * z
    return np.stack([x * np.sqrt(1 - y2 / 2 - z2 / 2 + y2 * z2 / 3), y * np.sqrt(1 - z2 / 2 - x2 / 2 + z2 * x2 / 3), z * np.sqrt(1 - x2 / 2 - y2 / 2 + x2 * y2 / 3)], axis=-1)


def slerp(a, b, t):
    a = a / np.linalg.norm(a, axis=-1, keepdims=True); b = b / np.linalg.norm(b, axis=-1, keepdims=True)
    d = np.clip((a * b).sum(-1, keepdims=True), -1, 1); om = np.arccos(d)
    so = np.sin(om)
    w0 = np.where(so < 1e-6, 1 - t, np.sin((1 - t) * om) / np.where(so < 1e-6, 1, so)); w1 = np.where(so < 1e-6, t, np.sin(t * om) / np.where(so < 1e-6, 1, so))
    r = w0 * a + w1 * b
    return r / np.linalg.norm(r, axis=-1, keepdims=True)


def stretch_down(U, dphi_deg=16.0):
    """push the lower rows of the side faces further down (more polar angle) on the FRONT so that the chin / lower lip stay inside the refinable cube-sphere region"""
    th = np.arctan2(U[:, 1], U[:, 0]); ph = np.arccos(np.clip(U[:, 2], -1, 1))
    def ss(a, b, x):
        t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
    w = ss(0.35, -0.85, np.sin(th))                                   # 1 on the front (sin(theta) = -1), 0 on the back
    ph2 = ph + np.radians(dphi_deg) * w * ss(np.radians(70.0), np.radians(135.0), ph)
    return np.stack([np.sin(ph2) * np.cos(th), np.sin(ph2) * np.sin(th), np.cos(ph2)], axis=1)


def cube_faces(N):
    """vertex array (unit dirs) + quads for the 5 upper faces of the spherified cube (the bottom face is omitted)"""
    g = np.linspace(-1.0, 1.0, N + 1)
    A, Bg = np.meshgrid(g, g, indexing='ij')
    faces_xyz = {
        'top': np.stack([A, Bg, np.ones_like(A)], -1),
        'px': np.stack([np.ones_like(A), A, Bg], -1),
        'nx': np.stack([-np.ones_like(A), A, Bg], -1),
        'py': np.stack([A, np.ones_like(A), Bg], -1),
        'ny': np.stack([A, -np.ones_like(A), Bg], -1),
    }
    # side faces: Bg is the vertical coordinate (z) running from -1 (bottom) .. +1 (top)
    verts = []; key = {}; quads = []
    def vid(p):
        k = tuple(np.round(p, 9))
        if k not in key:
            key[k] = len(verts); verts.append(p)
        return key[k]
    for name, P in faces_xyz.items():
        U = spherify(P)
        idx = np.zeros((N + 1, N + 1), int)
        for i in range(N + 1):
            for j in range(N + 1): idx[i, j] = vid(U[i, j])
        for i in range(N):
            for j in range(N):
                q = [idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]]
                quads.append(q)
    verts = stretch_down(np.array(verts))
    # orient outward (counter-clockwise seen from outside)
    out = []
    for q in quads:
        p = verts[q]; c = p.mean(0)
        n = np.cross(p[1] - p[0], p[3] - p[0])
        out.append(q if np.dot(n, c) > 0 else q[::-1])
    return verts, out


def boundary_loop(faces):
    cnt = {}
    for f in faces:
        n = len(f)
        for i in range(n):
            a, b = int(f[i]), int(f[(i + 1) % n]); k = (min(a, b), max(a, b)); cnt[k] = cnt.get(k, 0) + 1
    be = [k for k, c in cnt.items() if c == 1]
    nxt = {}
    for a, b in be: nxt.setdefault(a, []).append(b); nxt.setdefault(b, []).append(a)
    start = be[0][0]; loop = [start]; prev = None; cur = start
    while True:
        cand = [v for v in nxt[cur] if v != prev]
        nx = cand[0]
        if nx == start: break
        loop.append(nx); prev, cur = cur, nx
    return loop


def wrap(a): return (a + np.pi) % (2 * np.pi) - np.pi


def make_consistent(faces):
    """flip faces so that every shared edge is traversed in opposite directions (BFS from face 0)"""
    edge_faces = {}
    for fi, f in enumerate(faces):
        n = len(f)
        for i in range(n):
            a, b = f[i], f[(i + 1) % n]; edge_faces.setdefault((min(a, b), max(a, b)), []).append(fi)
    faces = [list(f) for f in faces]; seen = {0}; stack = [0]
    def dir_of(f, a, b):
        n = len(f)
        for i in range(n):
            if f[i] == a and f[(i + 1) % n] == b: return 1
            if f[i] == b and f[(i + 1) % n] == a: return -1
        return 0
    while stack:
        fi = stack.pop(); f = faces[fi]; n = len(f)
        for i in range(n):
            a, b = f[i], f[(i + 1) % n]
            for gj in edge_faces[(min(a, b), max(a, b))]:
                if gj == fi or gj in seen: continue
                if dir_of(faces[gj], a, b) == 1: faces[gj] = faces[gj][::-1]      # same direction as f -> flip
                seen.add(gj); stack.append(gj)
    return faces


def build_cage(ring_pos, C, N=15, n_ext=9, t_first=0.10, H=None, z_collar_top=1.4125):
    U, quads = cube_faces(N)
    nU = len(U)
    B = boundary_loop(quads)
    assert len(B) == 4 * N, len(B)
    thB = np.arctan2(U[B, 1], U[B, 0])
    # make the loop run in increasing azimuth
    if np.sum(wrap(np.diff(np.concatenate([thB, thB[:1]]))) < 0) > len(B) / 2:
        B = B[::-1]; thB = thB[::-1]
    # collar ring: directions from C, ordered by azimuth about C's axis
    d = ring_pos - C[None, :]; uK = d / np.linalg.norm(d, axis=1, keepdims=True)
    thK = np.arctan2(uK[:, 1], uK[:, 0]); oK = np.argsort(thK); uK = uK[oK]; thK = thK[oK]
    nK = len(ring_pos); assert 2 * nK == len(B)
    best = None
    for s in range(len(B)):
        res = sum(wrap(thK[k] - thB[(2 * k + s) % len(B)]) ** 2 for k in range(nK))
        if best is None or res < best[0]: best = (res, s)
    s = best[1]
    nB = len(B)
    uBc = np.array([U[B[(c + s) % nB]] for c in range(nB)])                      # boundary directions per column (60)
    # collar target per column: even columns = collar vertices, odd columns = between two collar vertices
    ring_sorted = ring_pos[oK]
    Rc = np.array([ring_sorted[c // 2] if c % 2 == 0 else 0.5 * (ring_sorted[c // 2] + ring_sorted[(c // 2 + 1) % nK]) for c in range(nB)])
    uKc = np.array([uK[c // 2] if c % 2 == 0 else slerp(uK[c // 2][None, :], uK[(c // 2 + 1) % nK][None, :], 0.5)[0] for c in range(nB)])
    nrow = n_ext                                                                     # 60-column rows R_0 .. R_{n_ext-1}; then the 30-vertex collar row
    rows_dirs = [np.zeros((nB, 3)) for _ in range(nrow)]
    wall_pos = {}
    ts_grid = np.linspace(0.0, 1.0, 201)
    for c in range(nB):
        R = Rc[c]
        if H is None:
            for j in range(nrow):
                tj = (j + 1) / (nrow + 1); rows_dirs[j][c] = slerp(uBc[c][None, :], uKc[c][None, :], tj)[0]
            continue
        zs = np.linspace(max(R[2] + 0.001, 1.426), 1.53, 400)
        pw = H.neck_wall_point(R, zs); dw = pw - C[None, :]; rw = np.linalg.norm(dw, axis=1); uw = dw / rw[:, None]
        inside_head = (H.r_base(uw) - rw) > 0.0008                   # wall point lies inside the (union) surface -> above the junction
        iz = int(np.argmax(inside_head)) if inside_head.any() else len(zs) - 1
        zJ = zs[iz]; pJ = H.phi(uw[iz][None, :])[0]; uJ = uw[iz]
        dirsA = slerp(np.repeat(uBc[c][None, :], len(ts_grid), 0), np.repeat(uJ[None, :], len(ts_grid), 0), ts_grid[:, None])
        PA = H.phi(dirsA); PA[-1] = pJ
        segA = np.linalg.norm(np.diff(PA, axis=0), axis=1); cumA = np.concatenate([[0], np.cumsum(segA)]); LA = cumA[-1]
        LW = zJ - R[2]; Ltot = LA + LW
        gap = 0.0065
        sA = max(LA - gap, 0.004); sW = min(LA + gap, Ltot - 0.004)
        nb_ = nrow - 2
        nA = int(np.clip(round(nb_ * sA / max(sA + (Ltot - sW), 1e-6)), 1, nb_ - 1)); nW = nb_ - nA
        rowsA = (np.arange(nA) + 1.0) / (nA + 1.0) * sA
        rowsW = sW + (np.arange(nW) + 1.0) / (nW + 1.0) * (Ltot - sW)
        fr = np.concatenate([rowsA, [sA, sW], rowsW]); fr = np.sort(fr)
        for j, sj in enumerate(fr):
            if j == nrow - 1 and zJ > z_collar_top + 0.004:
                z = z_collar_top; p = H.neck_wall_point(R, np.array([z]))[0]; dd = p - C; rows_dirs[j][c] = dd / np.linalg.norm(dd); wall_pos[(j, c)] = p     # horizontal collar-top row
            elif sj <= LA:
                tj = np.interp(sj, cumA, ts_grid); rows_dirs[j][c] = slerp(uBc[c][None, :], uJ[None, :], tj)[0]
            else:
                z = zJ - (sj - LA); p = H.neck_wall_point(R, np.array([z]))[0]; dd = p - C; rows_dirs[j][c] = dd / np.linalg.norm(dd); wall_pos[(j, c)] = p
    verts = [u for u in U]
    ridx = []
    for r, rd in enumerate(rows_dirs):
        ids = []
        for c in range(nB):
            verts.append(rd[c]); ids.append(len(verts) - 1)
        ridx.append(ids)
    collar = []
    for k in range(nK):
        verts.append(uK[k]); collar.append(len(verts) - 1)
    faces = [list(map(int, q)) for q in quads]
    kind = [0] * len(faces)
    Bs = [B[(c + s) % nB] for c in range(nB)]
    for c in range(nB):                                                              # B -> R_0 (quads)
        faces.append([Bs[c], Bs[(c + 1) % nB], ridx[0][(c + 1) % nB], ridx[0][c]]); kind.append(2)
    for r in range(nrow - 1):
        for c in range(nB):
            faces.append([ridx[r][c], ridx[r][(c + 1) % nB], ridx[r + 1][(c + 1) % nB], ridx[r + 1][c]]); kind.append(2)
    last = ridx[-1]
    for k in range(nK):                                                              # 60 -> 30 transition at the neck base
        b0, b1, b2 = last[(2 * k) % nB], last[(2 * k + 1) % nB], last[(2 * k + 2) % nB]
        r0, r1 = collar[k], collar[(k + 1) % nK]
        faces += [[r0, b0, b1], [r0, b1, r1], [r1, b1, b2]]; kind += [1, 1, 1]
    pinned = {int(collar[k]): ring_sorted[k] for k in range(nK)}
    for (j, c), p in wall_pos.items(): pinned[int(ridx[j][c])] = p
    V = np.array(verts)
    faces = make_consistent(faces)
    # global sense: the first (top-cap) quad must face outward
    p = V[faces[0]]; c = p.mean(0)
    if np.dot(np.cross(p[1] - p[0], p[3] - p[0]), c) < 0: faces = [f[::-1] for f in faces]
    return dict(u=V, faces=faces, kind=kind, pinned=pinned, B=[int(b) for b in B], rows=ridx, collar=collar, shift=s, collar_order=oK)
