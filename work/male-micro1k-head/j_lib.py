"""Micro1j helpers (numpy + Pillow; run with Blender's python3.13 and PYTHONPATH=pylib)."""
import sys, pickle, json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1k-head')
R = W.parent.parent
I1 = W.parent / 'male-micro1i'; H1 = W.parent / 'male-micro1h'
for p in (str(W), str(I1), str(H1)):
    if p not in sys.path: sys.path.insert(0, p)
K = 0.0013043874429196725; TOP = 1.7046599388122559; CX = 227.6
PLATE = Image.open(R / 'ArtDir/hero/base_lock/male_head_detail.jpg').convert('RGB')
BOXES = {'front': (5, 62, 433, 352), 'left': (433, 62, 834, 352), 'right': (834, 62, 1271, 352), 'q3L': (5, 390, 433, 668), 'q3R': (433, 390, 834, 668)}
SK = {'front': (22, 95, 6), 'left': (22, 95, 6), 'right': (22, 95, 6), 'q3L': (35, 100, 0), 'q3R': (35, 100, 0)}
YOFF = {'left': 712.0, 'right': 1123.0}      # col of the y=0.065 reference in each profile panel (face looks to image-left)


def rowz(z): return 76.0 + (TOP - np.asarray(z, float)) / K
def zrow(r): return TOP - (np.asarray(r, float) - 76.0) * K
def prof_col(y, panel='left'): return YOFF[panel] - (0.065 - np.asarray(y, float)) / K
def prof_y(c, panel='left'): return 0.065 - (YOFF[panel] - np.asarray(c, float)) * K


def load_start(tag='start'):
    V = np.load(W / f'data/V_{tag}.npy'); F = pickle.load(open(W / 'data/F_start.pkl', 'rb')); loops = pickle.load(open(W / 'data/loops_start.pkl', 'rb'))
    return V, F, loops


def edges_of(F):
    E = set()
    for f in F:
        m = len(f)
        for i in range(m):
            a, b = int(f[i]), int(f[(i + 1) % m]); E.add((min(a, b), max(a, b)))
    return np.array(sorted(E))


def plane_section(V, E, axis, val, mask=None):
    a = V[E[:, 0], axis] - val; b = V[E[:, 1], axis] - val
    m = (a * b) < 0
    if mask is not None: m &= mask[E[:, 0]] & mask[E[:, 1]]
    e = E[m]
    t = (val - V[e[:, 0], axis]) / (V[e[:, 1], axis] - V[e[:, 0], axis])
    return V[e[:, 0]] + (V[e[:, 1]] - V[e[:, 0]]) * t[:, None]


def plate_skin(name):
    box = BOXES[name]; p = np.asarray(PLATE.crop(box)).astype(int)
    rb, rmin, rg = SK[name]
    return ((p[..., 0] - p[..., 2]) > rb) & (p[..., 0] > rmin) & ((p[..., 0] - p[..., 1]) > rg)


def plate_profile_extent(panel, rows):
    """skin-mask (front-most col, back-most col) per plate row for a profile panel (full-plate px)"""
    m = plate_skin(panel); box = BOXES[panel]; out = {}
    for r in rows:
        rr = int(round(r)) - box[1]
        if rr < 0 or rr >= m.shape[0]: continue
        cs = np.where(m[rr])[0]
        if len(cs): out[int(r)] = (box[0] + cs.min(), box[0] + cs.max())
    return out


def section_curve(V, E, z, mask=None):
    pts = plane_section(V, E, 2, z, mask)
    if len(pts) < 8: return pts[:, :2]
    c = pts[:, :2].mean(axis=0)
    ang = np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0])
    return pts[np.argsort(ang), :2]


def plot_sections(curves, out, S=6.0, xr=(-80, 80), yr=(-110, 70), labels=None, cols=None, title=None):
    Wd = int((xr[1] - xr[0]) * S); Hd = int((yr[1] - yr[0]) * S)
    im = Image.new('RGB', (Wd, Hd), (20, 20, 24)); d = ImageDraw.Draw(im)
    X = lambda x: (x * 1000 - xr[0]) * S
    Y = lambda y: (y * 1000 - yr[0]) * S
    for xm in range(int(xr[0] // 10 * 10), int(xr[1]) + 1, 10):
        d.line((X(xm / 1000), 0, X(xm / 1000), Hd), fill=(60, 60, 70) if xm % 50 else (110, 110, 120))
    for ym in range(int(yr[0] // 10 * 10), int(yr[1]) + 1, 10):
        d.line((0, Y(ym / 1000), Wd, Y(ym / 1000)), fill=(60, 60, 70) if ym % 50 else (110, 110, 120)); d.text((2, Y(ym / 1000) + 1), f'{ym}', fill=(140, 140, 160))
    palette = cols or [(255, 90, 90), (255, 170, 50), (255, 255, 0), (90, 255, 90), (0, 255, 255), (90, 160, 255), (200, 110, 255), (255, 255, 255), (255, 120, 200)]
    for i, c in enumerate(curves):
        col = palette[i % len(palette)]
        pts = [(X(p[0]), Y(p[1])) for p in c]
        if len(pts) > 1: d.line(pts + ([pts[0]] if len(pts) > 10 else []), fill=col, width=1)
        for p in pts: d.ellipse((p[0] - 1.2, p[1] - 1.2, p[0] + 1.2, p[1] + 1.2), fill=col)
        if labels: d.text((8, 6 + 13 * i), labels[i], fill=col)
    if title: d.text((Wd // 2 - 60, Hd - 14), title, fill=(200, 200, 200))
    im.save(out); return im.size


def plate_fg(panel, thr=88):
    """foreground (skin or grey shirt) mask of a plate panel: max channel above the dark studio backdrop"""
    box = BOXES[panel]; p = np.asarray(PLATE.crop(box)).astype(int)
    return p.max(axis=2) > thr


def plate_sil_rows(panel, rows, thr=88, xlim=None):
    """(front-most col, back-most col) of the foreground per plate row, only for the connected central blob (ignores image-edge junk)"""
    m = plate_fg(panel, thr); box = BOXES[panel]; out = {}
    for r in rows:
        rr = int(round(r)) - box[1]
        if rr < 0 or rr >= m.shape[0]: continue
        cs = np.where(m[rr])[0]
        if len(cs): out[int(r)] = (box[0] + cs.min(), box[0] + cs.max())
    return out


def coronal_curve(V, E, y, mask=None, side=+1):
    """section of the mesh with the plane y=const, points (x,z) of the half x*side>0 sorted by angle around its centroid is NOT used; return raw points sorted by z"""
    pts = plane_section(V, E, 1, y, mask)
    pts = pts[pts[:, 0] * side > -0.002]
    return pts
