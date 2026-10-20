"""Micro1i helpers (plain numpy + Pillow; run with Blender's python3.13 and PYTHONPATH=pylib)."""
import sys, pickle, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i')
R = W.parent.parent
sys.path.insert(0, str(W.parent / 'male-micro1h'))
import h1lib as H
K = H.K; TOP = H.TOP
PLATE = Image.open(R / 'ArtDir/hero/base_lock/male_head_detail.jpg').convert('RGB')


def load(tag='h0'):
    """vertices for `tag`; topology/loops come from the tag's own files if present, else from the Micro1h start (h0) -- all Micro1i edits keep topology"""
    V = np.load(W / f'data/V_{tag}.npy')
    fF = W / f'data/F_{tag}.pkl'; fL = W / f'data/loops_{tag}.pkl'
    F = pickle.load(open(fF if fF.exists() else W / 'data/F_h0.pkl', 'rb'))
    loops = pickle.load(open(fL if fL.exists() else W / 'data/loops_h0.pkl', 'rb'))
    return V, F, loops


def edges_of(F):
    E = set()
    for f in F:
        m = len(f)
        for i in range(m):
            a, b = int(f[i]), int(f[(i + 1) % m]); E.add((min(a, b), max(a, b)))
    return np.array(sorted(E))


def plane_section(V, E, axis, val, mask=None):
    """points where edges cross the plane V[:,axis]==val"""
    a = V[E[:, 0], axis] - val; b = V[E[:, 1], axis] - val
    m = (a * b) < 0
    if mask is not None:
        m &= mask[E[:, 0]] & mask[E[:, 1]]
    e = E[m]
    t = (val - V[e[:, 0], axis]) / (V[e[:, 1], axis] - V[e[:, 0], axis])
    return V[e[:, 0]] + (V[e[:, 1]] - V[e[:, 0]]) * t[:, None]


def rowz(z): return 76.0 + (TOP - z) / K
def zrow(r): return TOP - (r - 76.0) * K
def colx(x, cx=H.CX): return cx + x / K
def coly(y): return 712.0 - (0.065 - y) / K


def section_curve(V, E, z, mask=None):
    """ordered closed-ish (x,y) section polyline at height z of the head region: points sorted by angle around the centroid"""
    pts = plane_section(V, E, 2, z, mask)
    if len(pts) < 8: return pts[:, :2]
    c = pts[:, :2].mean(axis=0)
    ang = np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0])
    return pts[np.argsort(ang), :2]


def plot_sections(curves, out, S=5.0, xr=(-95, 95), yr=(-135, 35), labels=None, cols=None):
    """curves: list of (N,2) arrays in metres (x,y).  front of face (y<0) at the top."""
    Wd = int((xr[1] - xr[0]) * S); Hd = int((yr[1] - yr[0]) * S)
    im = Image.new('RGB', (Wd, Hd), (20, 20, 24)); d = ImageDraw.Draw(im)
    X = lambda x: (x * 1000 - xr[0]) * S
    Y = lambda y: (y * 1000 - yr[0]) * S
    for xm in range(int(xr[0] // 10 * 10), int(xr[1]) + 1, 10):
        d.line((X(xm / 1000), 0, X(xm / 1000), Hd), fill=(60, 60, 70) if xm % 50 else (110, 110, 120))
    for ym in range(int(yr[0] // 10 * 10), int(yr[1]) + 1, 10):
        d.line((0, Y(ym / 1000), Wd, Y(ym / 1000)), fill=(60, 60, 70) if ym % 50 else (110, 110, 120)); d.text((2, Y(ym / 1000) + 1), f'{ym}', fill=(140, 140, 160))
    palette = cols or [(255, 90, 90), (255, 170, 50), (255, 255, 0), (90, 255, 90), (0, 255, 255), (90, 160, 255), (200, 110, 255), (255, 255, 255)]
    for i, c in enumerate(curves):
        col = palette[i % len(palette)]
        pts = [(X(p[0]), Y(p[1])) for p in c]
        if len(pts) > 1: d.line(pts + ([pts[0]] if len(pts) > 10 else []), fill=col, width=1)
        for p in pts: d.ellipse((p[0] - 1.2, p[1] - 1.2, p[0] + 1.2, p[1] + 1.2), fill=col)
        if labels: d.text((8, 6 + 13 * i), labels[i], fill=col)
    im.save(out); return im.size


Q3 = {'q3L': dict(box=(5, 390, 433, 668), az=41.0, pm=176.5), 'q3R': dict(box=(433, 390, 834, 668), az=36.0, pm=589.5)}


def q3_project(P, name):
    """plate-px (col,row) in the full plate for 3D points P under the fitted 3/4 camera of plate `name`"""
    import math
    v = Q3[name]; a = math.radians(v['az'])
    u = P[:, 0] * math.cos(a) + (P[:, 1] + 0.1254) * math.sin(a)
    col = v['pm'] + u / K; row = 397 + (TOP - P[:, 2]) / K
    depth = P[:, 0] * math.sin(a) - P[:, 1] * math.cos(a)
    return col, row, depth


def front_project(P):
    return colx(P[:, 0]), rowz(P[:, 2])
