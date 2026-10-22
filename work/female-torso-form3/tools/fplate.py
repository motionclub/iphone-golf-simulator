"""Female plate tools (numpy + Pillow only; run with system python3).
 * bald plate front/back registration (S m/px, centres 440/847, sole row 679)  [ArtDir/hero/base_lock/female_body_bald.jpg]
 * vertex normals / visibility (z-buffer) / SH2 lighting fit (lighting is fitted on regions that are NOT being edited)
 * yaw views of the multi-angle sheet (calibrated in calib_yaw.py -> data/yaw_calib.json)
"""
import json, math
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
W = ROOT / 'work/female-torso-form3'
S = 0.0025954198473282443          # m/px, bald plate (1.70 m = 655 px)
FRONT_CX, BACK_CX, SOLE = 440.0, 847.0, 679.0
BALD = np.asarray(Image.open(ROOT / 'ArtDir/hero/base_lock/female_body_bald.jpg').convert('L')).astype(np.float64)
SHEET = np.asarray(Image.open(ROOT / 'ArtDir/hero/base_lock/female_multiangle_body.jpg').convert('L')).astype(np.float64)


def gblur(a, s):
    k = int(max(1, round(3 * s)))
    xs = np.arange(-k, k + 1)
    w = np.exp(-0.5 * (xs / s) ** 2)
    w /= w.sum()
    a = np.apply_along_axis(lambda v: np.convolve(np.pad(v, k, mode='edge'), w, mode='valid'), 0, a)
    return np.apply_along_axis(lambda v: np.convolve(np.pad(v, k, mode='edge'), w, mode='valid'), 1, a)


def dog(img, s1=1.6, s2=9.0):
    a = np.asarray(img, dtype=np.float64)
    return gblur(a, s1) - gblur(a, s2)


def bilinear(img, col, row):
    h, w = img.shape
    c = np.clip(col, 0, w - 1.001)
    r = np.clip(row, 0, h - 1.001)
    c0 = np.floor(c).astype(int)
    r0 = np.floor(r).astype(int)
    fc = c - c0
    fr = r - r0
    return (img[r0, c0] * (1 - fc) * (1 - fr) + img[r0, c0 + 1] * fc * (1 - fr)
            + img[r0 + 1, c0] * (1 - fc) * fr + img[r0 + 1, c0 + 1] * fc * fr)


# ----------------------------------------------------------------------------------------------- mesh
class Mesh:
    def __init__(self, npz='data/cand.npz', zone='data/zone_chat7.npz'):
        d = np.load(W / npz)
        self.co = d['co'].astype(np.float64)
        self.tri = d['tri']
        self.edges = d['edges']
        z = np.load(W / zone)
        self.T = z['torso']
        self.arm = z['arm']
        self.n = len(self.co)

    def normals(self, co=None, weight='angle'):
        return vertex_normals(self.co if co is None else co, self.tri, weight)


def vertex_normals(co, tri, weight='angle'):
    v0, v1, v2 = co[tri[:, 0]], co[tri[:, 1]], co[tri[:, 2]]
    fn = np.cross(v1 - v0, v2 - v0)
    ln = np.linalg.norm(fn, axis=1)
    fn = fn / np.maximum(ln, 1e-18)[:, None]
    n = np.zeros_like(co)
    for k, (a, b, c) in enumerate(((v0, v1, v2), (v1, v2, v0), (v2, v0, v1))):
        e1 = b - a
        e2 = c - a
        cosang = (e1 * e2).sum(1) / np.maximum(np.linalg.norm(e1, axis=1) * np.linalg.norm(e2, axis=1), 1e-18)
        ang = np.arccos(np.clip(cosang, -1, 1)) if weight == 'angle' else 0.5 * ln
        np.add.at(n, tri[:, k], fn * ang[:, None])
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-18)


# ----------------------------------------------------------------------------------------------- views
class View:
    """orthographic plate view.  project(P)->(col,row) in plate pixels; toward = surface->camera direction"""

    def __init__(self, name):
        self.name = name
        self.back = name == 'back'
        self.cx = BACK_CX if self.back else FRONT_CX
        self.mpp = S
        self.sole = SOLE
        self.zmin = 0.0
        self.right = np.array([-1.0, 0, 0]) if self.back else np.array([1.0, 0, 0])
        self.toward = np.array([0, 1.0, 0]) if self.back else np.array([0, -1.0, 0])
        self.img = BALD
        self.shape = (720, 1280)

    def project(self, P):
        return self.cx + (P @ self.right) / self.mpp, self.sole - (P[:, 2] - self.zmin) / self.mpp

    def depth(self, P):
        return P @ self.toward


class ViewYaw(View):
    def __init__(self, name, az, col0, mpp, sole_row, zmin=0.0):
        self.name = name
        self.az = az
        a = math.radians(az)
        self.right = np.array([math.cos(a), math.sin(a), 0.0])
        self.toward = np.array([math.sin(a), -math.cos(a), 0.0])
        self.cx = col0
        self.mpp = mpp
        self.sole = sole_row
        self.zmin = zmin
        self.back = False
        self.img = SHEET
        self.shape = (720, 1280)


def yaw_views():
    p = W / 'data/yaw_calib.json'
    if not p.exists():
        return {}
    cal = json.load(open(p))
    return {k: ViewYaw(k, c['yaw'], c['col0'], c['mpp'], c['sole_row'], c.get('zmin', 0.0)) for k, c in cal.items()}


def zbuffer(view, P, sel, res=2.0, rad=2):
    col, row = view.project(P[sel])
    dep = view.depth(P[sel])
    H, Wd = int(view.shape[0] * res), int(view.shape[1] * res)
    zb = np.full((H, Wd), -1e9)
    ci = np.clip(np.round(col * res).astype(int), 0, Wd - 1)
    ri = np.clip(np.round(row * res).astype(int), 0, H - 1)
    np.maximum.at(zb, (ri, ci), dep)
    out = zb.copy()
    for dy in range(-rad, rad + 1):
        for dx in range(-rad, rad + 1):
            out = np.maximum(out, np.roll(np.roll(zb, dy, 0), dx, 1))
    return out, res


def visible(view, P, N, sel=None, tol=0.006, mincos=0.12, res=2.0, rad=2):
    sel = np.ones(len(P), bool) if sel is None else sel
    zb, res = zbuffer(view, P, sel, res, rad)
    col, row = view.project(P)
    dep = view.depth(P)
    ci = np.clip(np.round(col * res).astype(int), 0, zb.shape[1] - 1)
    ri = np.clip(np.round(row * res).astype(int), 0, zb.shape[0] - 1)
    return sel & (dep >= zb[ri, ci] - tol) & ((N @ view.toward) > mincos)


def sh2c(N, vw):
    """camera-frame, x-symmetric SH2 basis (right, up, toward)"""
    nr = N @ vw.right
    nt = N @ vw.toward
    nu = N[:, 2]
    return np.stack([np.ones_like(nr), nt, nu, nt * nu, 3 * nu * nu - 1, nr * nr - nt * nt], 1)


def sh2c_full(N, vw):
    nr = N @ vw.right
    nt = N @ vw.toward
    nu = N[:, 2]
    return np.stack([np.ones_like(nr), nr, nt, nu, nr * nt, nt * nu, 3 * nu * nu - 1, nr * nu, nr * nr - nt * nt], 1)


def luminance_at(view, P, sigma=2.0):
    col, row = view.project(P)
    return bilinear(gblur(view.img, sigma), col, row)


def fit_sh(view, P, N, fit_mask, sigma=2.5, basis=sh2c, ridge=1e-6):
    vis = visible(view, P, N, sel=fit_mask)
    I = luminance_at(view, P, sigma)
    A = basis(N, view)
    c, *_ = np.linalg.lstsq(A[vis], I[vis], rcond=None)
    p = A @ c
    r2 = 1 - ((I[vis] - p[vis]) ** 2).sum() / ((I[vis] - I[vis].mean()) ** 2).sum()
    return c, r2, vis.sum()
