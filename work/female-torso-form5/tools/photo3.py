"""Photometric comparison of a model surface against the bald plate (front / back views), in the plate's own pixel grid.

  shade   : per-vertex linear shading I = c0 + c1*n_right + c2*n_up + c3*n_toward   (coefficients fitted on UNEDITED regions of the plate,
            data/plate_light_fit.json; plate lit from above / slightly front / viewer's right)
  raster  : Gouraud rasteriser with z-buffer at the plate pixel grid inside a ROI box (numpy only)
  compare : band-pass (DoG) of plate and model inside the ROI, NCC + amplitude ratio (+ MSE with gain fixed at 1)

python3 tools/photo3.py diag        -> NCC of unedited regions (validates the lighting model) and of bust / glute for the stored candidates
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from fplate import BALD, S, FRONT_CX, BACK_CX, SOLE, vertex_normals, gblur, View

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = np.load(HERE + '/data/orig.npz')
TRI = O['tri']
LIGHT = np.array(json.load(open(HERE + '/data/plate_light_fit.json')))


def view_of(name):
    return View(name)


def roi_box(view, x0, x1, z0, z1):
    """plate pixel box (c0,r0,c1,r1) of a model-space box"""
    vw = view_of(view)
    sgn = 1 if view == 'front' else -1
    cs = sorted([vw.cx + sgn * x0 / S, vw.cx + sgn * x1 / S])
    c0, c1 = int(np.floor(cs[0])), int(np.ceil(cs[1]))
    r0, r1 = int(np.floor(SOLE - z1 / S)), int(np.ceil(SOLE - z0 / S))
    return c0, r0, c1, r1


def shade_vertices(co, N, view, light=None):
    vw = view_of(view)
    c = LIGHT if light is None else np.asarray(light)
    nr = N @ vw.right
    nu = N[:, 2]
    nt = N @ vw.toward
    return c[0] + c[1] * nr + c[2] * nu + c[3] * nt


def raster_shaded(co, shade, view, box, tris=None):
    """Gouraud-shaded image of the surface inside box=(c0,r0,c1,r1); returns (img, mask)"""
    vw = view_of(view)
    c0, r0, c1, r1 = box
    W, H = c1 - c0, r1 - r0
    col, row = vw.project(co)
    dep = vw.depth(co)
    tri = TRI if tris is None else tris
    # keep triangles whose pixel bbox intersects the box and that face the camera
    v0, v1, v2 = co[tri[:, 0]], co[tri[:, 1]], co[tri[:, 2]]
    fn = np.cross(v1 - v0, v2 - v0)
    facing = (fn @ vw.toward) > 0
    tc = np.stack([col[tri[:, 0]], col[tri[:, 1]], col[tri[:, 2]]], 1)
    tr = np.stack([row[tri[:, 0]], row[tri[:, 1]], row[tri[:, 2]]], 1)
    keep = facing & (tc.max(1) >= c0 - 1) & (tc.min(1) <= c1 + 1) & (tr.max(1) >= r0 - 1) & (tr.min(1) <= r1 + 1)
    idx = np.where(keep)[0]
    img = np.zeros((H, W)); zb = np.full((H, W), -1e9); mask = np.zeros((H, W), bool)
    for t in idx:
        a, b, c = tri[t]
        x = np.array([col[a], col[b], col[c]]) - c0 + 0.5
        y = np.array([row[a], row[b], row[c]]) - r0 + 0.5
        xmin, xmax = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), W - 1))
        ymin, ymax = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), H - 1))
        if xmax < xmin or ymax < ymin:
            continue
        den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(den) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
        l0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
        l1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
        l2 = 1 - l0 - l1
        ins = (l0 >= -1e-9) & (l1 >= -1e-9) & (l2 >= -1e-9)
        if not ins.any():
            continue
        d = l0 * dep[a] + l1 * dep[b] + l2 * dep[c]
        s = l0 * shade[a] + l1 * shade[b] + l2 * shade[c]
        sub = zb[ymin:ymax + 1, xmin:xmax + 1]
        upd = ins & (d > sub)
        sub[upd] = d[upd]
        img[ymin:ymax + 1, xmin:xmax + 1][upd] = s[upd]
        mask[ymin:ymax + 1, xmin:xmax + 1][upd] = True
    return img, mask


def dog(a, s1, s2):
    return gblur(a, s1) - gblur(a, s2)


def plate_patch(view, box, pad=30):
    vw = view_of(view)
    c0, r0, c1, r1 = box
    big = BALD[max(r0 - pad, 0):r1 + pad, max(c0 - pad, 0):c1 + pad]
    return big, (c0 - max(c0 - pad, 0), r0 - max(r0 - pad, 0))


def plate_bp(view, box, s1=1.6, s2=9.0, pad=30):
    big, (oc, orow) = plate_patch(view, box, pad)
    b = dog(big, s1, s2)
    c0, r0, c1, r1 = box
    return b[orow:orow + (r1 - r0), oc:oc + (c1 - c0)]


def plate_gray(view, box):
    c0, r0, c1, r1 = box
    return BALD[r0:r1, c0:c1]


def model_bp(co, view, box, s1=1.6, s2=9.0, light=None, pad=30, normals=None):
    """band-passed shaded model image inside box (rasterised with padding so the filter has context)"""
    c0, r0, c1, r1 = box
    N = vertex_normals(co, TRI) if normals is None else normals
    sh = shade_vertices(co, N, view, light)
    pb = (c0 - pad, r0 - pad, c1 + pad, r1 + pad)
    img, mask = raster_shaded(co, sh, view, pb)
    # fill the background with the mean of the foreground so the filter does not ring at the silhouette
    if mask.any():
        img = np.where(mask, img, img[mask].mean())
    b = dog(img, s1, s2)
    return b[pad:pad + (r1 - r0), pad:pad + (c1 - c0)], mask[pad:pad + (r1 - r0), pad:pad + (c1 - c0)], img[pad:pad + (r1 - r0), pad:pad + (c1 - c0)]


def model_multi_bp(co, view, box, scales, light=None, pad=36, normals=None):
    """band-passed shaded model image for several (s1,s2) pairs from one rasterisation; returns (list of arrays, mask)"""
    c0, r0, c1, r1 = box
    N = vertex_normals(co, TRI) if normals is None else normals
    sh = shade_vertices(co, N, view, light)
    pb = (c0 - pad, r0 - pad, c1 + pad, r1 + pad)
    img, mask = raster_shaded(co, sh, view, pb)
    if mask.any():
        img = np.where(mask, img, img[mask].mean())
    outs = []
    for s1, s2 in scales:
        b = dog(img, s1, s2)
        outs.append(b[pad:pad + (r1 - r0), pad:pad + (c1 - c0)])
    return outs, mask[pad:pad + (r1 - r0), pad:pad + (c1 - c0)]


def compare(co, view, box, inner=None, s1=1.6, s2=9.0, light=None, normals=None):
    """returns dict(ncc, amp_ratio, mse_n, n_px). `inner`: optional boolean mask (same shape as the box) restricting the evaluation"""
    pb = plate_bp(view, box, s1, s2)
    mb, mask, img = model_bp(co, view, box, s1, s2, light, normals=normals)
    # exclude pixels near the model silhouette (erode 5 px) and where the plate is the arm gap (very dark)
    from scipy_free import erode
    m = erode(mask, 6)
    if inner is not None:
        m &= inner
    a, b = pb[m], mb[m]
    if len(a) < 20:
        return dict(ncc=0.0, amp_ratio=0.0, mse_n=9.0, n_px=int(m.sum()))
    a0, b0 = a - a.mean(), b - b.mean()
    ncc = float((a0 * b0).sum() / np.sqrt((a0 ** 2).sum() * (b0 ** 2).sum() + 1e-12))
    return dict(ncc=ncc, amp_ratio=float(b0.std() / (a0.std() + 1e-12)), mse_n=float(((a0 - b0) ** 2).mean() / (a0.var() + 1e-12)), n_px=int(m.sum()))


# ----------------------------------------------------------------------------------------------- held-out validation on the multi-angle sheet
from fplate import SHEET
S_SHEET = 1.7039 / 288.5
SHEET_PANELS = {'front': dict(col0=168.0, row0=338.5, back=False), 'back': dict(col0=485.0, row0=338.5, back=True)}


class SheetView:
    def __init__(self, panel):
        c = SHEET_PANELS[panel]
        self.back = c['back']
        self.cx = c['col0']
        self.sole = c['row0']
        self.mpp = S_SHEET
        self.right = np.array([-1.0, 0, 0]) if self.back else np.array([1.0, 0, 0])
        self.toward = np.array([0, 1.0, 0]) if self.back else np.array([0, -1.0, 0])

    def project(self, P):
        return self.cx + (P @ self.right) / self.mpp, self.sole - P[:, 2] / self.mpp

    def depth(self, P):
        return P @ self.toward


def compare_sheet(co, panel, x0, x1, z0, z1, light=None, s1=0.8, s2=4.2, shift=(0, 0), search=3):
    """held-out check against the multi-angle sheet figure (lower resolution, same studio light assumed); searches +-`search` px shifts"""
    vw = SheetView(panel)
    sgn = 1 if panel == 'front' else -1
    cs = sorted([vw.cx + sgn * x0 / S_SHEET, vw.cx + sgn * x1 / S_SHEET])
    c0, c1 = int(np.floor(cs[0])), int(np.ceil(cs[1]))
    r0, r1 = int(np.floor(vw.sole - z1 / S_SHEET)), int(np.ceil(vw.sole - z0 / S_SHEET))
    N = vertex_normals(co, TRI)
    c = LIGHT if light is None else np.asarray(light)
    nr = N @ vw.right; nu = N[:, 2]; nt = N @ vw.toward
    sh = c[0] + c[1] * nr + c[2] * nu + c[3] * nt
    pad = 12
    pbx = (c0 - pad, r0 - pad, c1 + pad, r1 + pad)
    # rasteriser expects a View-like object: temporarily reuse raster_shaded with a shim
    global view_of
    old = view_of
    view_of = lambda name: vw
    try:
        img, mask = raster_shaded(co, sh, 'sheet', pbx)
    finally:
        view_of = old
    if mask.any():
        img = np.where(mask, img, img[mask].mean())
    mb = dog(img, s1, s2)
    best = None
    for dy in range(-search, search + 1):
        for dx in range(-search, search + 1):
            pr0, pc0 = r0 + dy, c0 + dx
            patch = SHEET[pr0 - pad:r1 + dy + pad, pc0 - pad:c1 + dx + pad]
            pb = dog(patch, s1, s2)
            a = pb[pad:-pad, pad:-pad]; b = mb[pad:-pad, pad:-pad]
            from scipy_free import erode
            m = erode(mask[pad:-pad, pad:-pad], 2)
            if m.sum() < 15:
                continue
            a_, b_ = a[m] - a[m].mean(), b[m] - b[m].mean()
            ncc = float((a_ * b_).sum() / np.sqrt((a_ ** 2).sum() * (b_ ** 2).sum() + 1e-12))
            if best is None or ncc > best[0]:
                best = (ncc, dx, dy, float(b_.std() / (a_.std() + 1e-12)))
    return dict(ncc=best[0], shift=(best[1], best[2]), amp_ratio=best[3])
