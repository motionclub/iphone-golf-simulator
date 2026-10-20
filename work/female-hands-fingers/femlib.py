"""femlib - shared helpers for the female hands+fingers pass (numpy + PIL only; run with ./py.sh).

* Mesh container / topology helpers (adapted from work/male-arms-hands-form2/hlib.py, male constants removed)
* Hand frames: local = (a, n, w)   a = across the palm, +a = thumb side (front), n = palm normal (+n = palm side, medial),
  w = along the hand toward the fingertips.  The -x hand is built in the mirrored +x frame (x -> -x) like the male pass.
* Plate registrations (bald front/back, multi-angle sheet front/back/left/right) + a numpy rasteriser for silhouettes.
"""
import numpy as np
from pathlib import Path
from collections import defaultdict
W = Path(__file__).resolve().parent
R = W.parents[1]

# --------------------------------------------------------------------------------------------- small maths
def smooth01(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)

def unit(v):
    v = np.asarray(v, float); return v / np.linalg.norm(v)

def gauss(x, c, s):
    return np.exp(-((x - c) / s) ** 2)

def pchip(xk, yk, x):
    """monotone cubic (Fritsch-Carlson) interpolation, numpy only"""
    xk = np.asarray(xk, float); yk = np.asarray(yk, float); x = np.asarray(x, float)
    h = np.diff(xk); d = np.diff(yk) / h; n = len(xk); m = np.zeros(n)
    for i in range(1, n - 1):
        if d[i - 1] * d[i] > 0:
            w1 = 2 * h[i] + h[i - 1]; w2 = h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    def endslope(h0, h1, d0, d1):
        sl = ((2 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
        if np.sign(sl) != np.sign(d0): sl = 0.0
        elif np.sign(d0) != np.sign(d1) and abs(sl) > 3 * abs(d0): sl = 3 * d0
        return sl
    m[0] = endslope(h[0], h[1], d[0], d[1]) if n > 2 else d[0]
    m[-1] = endslope(h[-1], h[-2], d[-1], d[-2]) if n > 2 else d[-1]
    idx = np.clip(np.searchsorted(xk, x) - 1, 0, n - 2)
    t = (x - xk[idx]) / h[idx]
    return (2 * t ** 3 - 3 * t ** 2 + 1) * yk[idx] + (t ** 3 - 2 * t ** 2 + t) * h[idx] * m[idx] + (-2 * t ** 3 + 3 * t ** 2) * yk[idx + 1] + (t ** 3 - t ** 2) * h[idx] * m[idx + 1]

def catmull(pts, n=240):
    """open Catmull-Rom spline through pts -> dense polyline"""
    pts = np.asarray(pts, float)
    ext = np.vstack([2 * pts[0] - pts[1], pts, 2 * pts[-1] - pts[-2]])
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for t in np.linspace(0, 1, n // (len(pts) - 1), endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return np.array(out)

# --------------------------------------------------------------------------------------------- mesh container
class Mesh:
    """V (n,3) float32, polys: list of tuples (CCW as stored in Blender)."""
    def __init__(self, V, polys):
        self.V = np.asarray(V); self.polys = [tuple(int(i) for i in p) for p in polys]
    @staticmethod
    def from_npz(path):
        D_ = np.load(path)
        cv, ls, lt = D_['corner_verts'], D_['loop_start'], D_['loop_total']
        polys = [tuple(int(x) for x in cv[s:s + t]) for s, t in zip(ls, lt)]
        return Mesh(D_['V'], polys)
    def tris(self):
        T = []
        for p in self.polys:
            for k in range(1, len(p) - 1):
                T.append((p[0], p[k], p[k + 1]))
        return np.array(T, np.int64)
    def arrays(self):
        sizes = np.array([len(p) for p in self.polys], np.int32)
        ls = np.r_[0, np.cumsum(sizes)[:-1]].astype(np.int32)
        cv = np.array([i for p in self.polys for i in p], np.int32)
        return cv, ls, sizes

def tri_count(polys):
    return sum(len(p) - 2 for p in polys)

def edges_of(polys):
    E = set()
    for f in polys:
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            E.add((min(a, b), max(a, b)))
    return np.array(sorted(E))

def edge_faces(polys):
    ef = {}
    for fi, f in enumerate(polys):
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            ef.setdefault((min(a, b), max(a, b)), []).append(fi)
    return ef

def face_normals(V, polys):
    Nn = np.zeros((len(polys), 3))
    for i, f in enumerate(polys):
        p = V[list(f)].astype(np.float64); q = np.roll(p, -1, 0)
        Nn[i] = [((p[:, 1] - q[:, 1]) * (p[:, 2] + q[:, 2])).sum(), ((p[:, 2] - q[:, 2]) * (p[:, 0] + q[:, 0])).sum(), ((p[:, 0] - q[:, 0]) * (p[:, 1] + q[:, 1])).sum()]
    l = np.linalg.norm(Nn, axis=1, keepdims=True); return Nn / np.maximum(l, 1e-15)

def check_manifold(polys):
    e = defaultdict(list)
    for f in polys:
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            e[(min(a, b), max(a, b))].append((a, b))
    bnd = sum(1 for v in e.values() if len(v) == 1)
    nm = sum(1 for v in e.values() if len(v) > 2)
    bad = sum(1 for v in e.values() if len(v) == 2 and v[0] == v[1])
    return dict(edges=len(e), boundary=bnd, nonmanifold=nm, bad_orient=bad)

def orient_consistently(faces, fixed_faces):
    """faces: list of tuples (new). fixed_faces: trusted orientation. Returns (oriented list, visited flags)."""
    from collections import deque
    allf = [tuple(f) for f in fixed_faces] + [tuple(f) for f in faces]
    nfix = len(fixed_faces)
    edges = defaultdict(list)
    for fi, f in enumerate(allf):
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            edges[(min(a, b), max(a, b))].append((fi, a, b))
    flipped = [False] * len(allf); visited = [False] * len(allf)
    for fi in range(nfix): visited[fi] = True
    seeds = set()
    for e, lst in edges.items():
        if any(fi >= nfix for fi, _, _ in lst):
            for (fi, a, b) in lst:
                if fi < nfix: seeds.add(fi)
    q = deque(sorted(seeds)); seen_q = set(q)
    while q:
        fi = q.popleft(); f = allf[fi]
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            if flipped[fi]: a, b = b, a
            e = (min(a, b), max(a, b))
            for (fj, c, d) in edges[e]:
                if fj == fi or visited[fj]: continue
                cj, dj = (d, c) if flipped[fj] else (c, d)
                if (cj, dj) == (a, b): flipped[fj] = True
                visited[fj] = True
                if fj not in seen_q: seen_q.add(fj); q.append(fj)
    out = []
    for fi in range(nfix, len(allf)):
        f = allf[fi]; out.append(tuple(reversed(f)) if flipped[fi] else f)
    return out, visited

def taubin(V, E, w, iters, lam=0.5, mu=-0.53):
    n = len(V); deg = np.bincount(E.ravel(), minlength=n).astype(float)
    p = V.astype(np.float64).copy(); ww = np.asarray(w, float)[:, None]
    def lap(q):
        s = np.zeros_like(q); np.add.at(s, E[:, 0], q[E[:, 1]]); np.add.at(s, E[:, 1], q[E[:, 0]])
        return s / np.maximum(deg, 1)[:, None] - q
    for _ in range(iters):
        p = p + lam * ww * lap(p); p = p + mu * ww * lap(p)
    return p

# --------------------------------------------------------------------------------------------- hand frames
def make_frame(D_dir, psi_deg=0.0, A_dir=(0.0, -1.0, 0.0)):
    """orthonormal (A, N, D) for the +x hand. D = hand direction (down the fingers), A = across the palm toward the thumb side (front, -y),
    N = D x A = palm normal (medial for the +x hand).  psi rotates the frame about D: positive turns the palm toward the back (+y)."""
    D = unit(D_dir); A0 = np.asarray(A_dir, float); A = A0 - A0.dot(D) * D; A = unit(A)
    N = unit(np.cross(D, A))
    c, s = np.cos(np.radians(psi_deg)), np.sin(np.radians(psi_deg))
    A2 = c * A + s * N; N2 = c * N - s * A
    return A2, N2, D

class Frame:
    def __init__(self, O, D_dir, psi_deg=0.0):
        self.O = np.asarray(O, float); self.A, self.N, self.D = make_frame(D_dir, psi_deg)
    def to_local(self, P, side=+1):
        Q = np.array(P, float).copy()
        if side < 0: Q[:, 0] = -Q[:, 0]
        Rr = Q - self.O
        return np.stack([Rr @ self.A, Rr @ self.N, Rr @ self.D], 1)
    def to_global(self, L, side=+1):
        L = np.asarray(L, float)
        P = self.O + L[:, 0:1] * self.A + L[:, 1:2] * self.N + L[:, 2:3] * self.D
        if side < 0:
            P = P.copy(); P[:, 0] = -P[:, 0]
        return P

def order_ring(ring, L):
    """order the weld ring by the angle about its (a, n) centre: returns ordered ids, monotonic t in [0,1), centre, semi axes.
    t = (-angle/2pi) mod 1  (matches the palm-ring parametrisation t_i = -2 pi i / n)."""
    ring = list(ring); P = L[ring]; c = P.mean(axis=0)
    A_ = 0.5 * (P[:, 0].max() - P[:, 0].min()); B_ = 0.5 * (P[:, 1].max() - P[:, 1].min())
    ang = np.arctan2((P[:, 1] - c[1]) / B_, (P[:, 0] - c[0]) / A_)
    t = (-ang / (2 * np.pi)) % 1.0
    o = np.argsort(t); ring = [ring[i] for i in o]; t = t[o]
    t = (t - t[0]) % 1.0
    return ring, t, c, (A_, B_)

# --------------------------------------------------------------------------------------------- plate registration (female)
S_BALD = 0.0025954198473282443                 # m / px in female_body_bald.jpg (height 655 px = 1.7 m)
S_SHEET = 1.7039 / 288.5                       # m / px in the multi-angle sheet
PLATE_X0 = dict(bald_front=440.0, bald_back=847.0)      # px of x = 0
SHEET_X0 = dict(sheet_front=None, sheet_back=None)      # filled by calibrate_sheet()
Z0_BALD = 679.0                                # row of z = 0 (bald)
Z0_SHEET = 338.5                               # row of z = 0 (sheet)
PROF_Y0 = dict(sheet_left=791.5, sheet_right=1095.5)    # px of y = 0 in the profile panels (left faces left, right faces right)

def project(V, view):
    """orthographic projection to plate pixel coordinates (px, py); V in metres (x right/left, y back, z up)."""
    V = np.asarray(V, float)
    if view == 'bald_front':   return PLATE_X0['bald_front'] + V[:, 0] / S_BALD, Z0_BALD - V[:, 2] / S_BALD
    if view == 'bald_back':    return PLATE_X0['bald_back'] - V[:, 0] / S_BALD, Z0_BALD - V[:, 2] / S_BALD
    if view == 'sheet_front':  return SHEET_X0['sheet_front'] + V[:, 0] / S_SHEET, Z0_SHEET - V[:, 2] / S_SHEET
    if view == 'sheet_back':   return SHEET_X0['sheet_back'] - V[:, 0] / S_SHEET, Z0_SHEET - V[:, 2] / S_SHEET
    if view == 'sheet_left':   return PROF_Y0['sheet_left'] + V[:, 1] / S_SHEET, Z0_SHEET - V[:, 2] / S_SHEET
    if view == 'sheet_right':  return PROF_Y0['sheet_right'] - V[:, 1] / S_SHEET, Z0_SHEET - V[:, 2] / S_SHEET
    raise KeyError(view)

def raster(V, T, view, roi, ss=3, sel=None):
    """binary silhouette of triangles T (n,3) in the pixel box roi=(x0,y0,x1,y1) of the plate view; ss = supersampling."""
    from PIL import Image, ImageDraw
    px, py = project(V, view)
    x0, y0, x1, y1 = roi; w, h = x1 - x0, y1 - y0
    im = Image.new('L', (w * ss, h * ss), 0); d = ImageDraw.Draw(im)
    TT = T if sel is None else T[sel]
    sx = (px - x0) * ss; sy = (py - y0) * ss
    xs = sx[TT]; ys = sy[TT]
    keep = (xs.max(1) >= 0) & (xs.min(1) <= w * ss) & (ys.max(1) >= 0) & (ys.min(1) <= h * ss)
    TT = TT[keep]
    P = np.stack([sx[TT[:, 0]], sy[TT[:, 0]], sx[TT[:, 1]], sy[TT[:, 1]], sx[TT[:, 2]], sy[TT[:, 2]]], 1)
    for p in P: d.polygon([(p[0], p[1]), (p[2], p[3]), (p[4], p[5])], fill=255)
    im = im.resize((w, h), Image.BOX)
    return np.array(im) > 127

def calibrate_sheet():
    """body centre line of the sheet front/back panels from the plate masks (mid of the legs at z=0.35 m)."""
    M = np.load(W / 'data/plate_masks.npz')
    for nm in ('sheet_front', 'sheet_back'):
        r = int(round(Z0_SHEET - 0.35 / S_SHEET)); xs = np.nonzero(M[nm][r])[0]
        SHEET_X0[nm] = 0.5 * (xs.min() + xs.max())
calibrate_sheet()

# hand regions of interest in plate pixels (x0, y0, x1, y1); +x hand = anatomical left, -x hand = anatomical right
ROIS = {
    'bald_front': {+1: (500, 338, 560, 424), -1: (320, 338, 380, 424)},
    'bald_back':  {+1: (730, 338, 790, 424), -1: (910, 338, 970, 424)},
}
