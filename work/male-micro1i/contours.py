"""Plate vs mesh silhouette/contour comparison in pure numpy (no rendering).
 - plate contours: skin masks per row (cached)   - mesh contours: exact plane sections projected with the fitted plate cameras."""
import sys, math, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i')
from m1i_lib import *

SK = {'front': (22, 95, 6), 'left': (22, 95, 6), 'right': (22, 95, 6), 'q3L': (35, 100, 0), 'q3R': (35, 100, 0)}
BOXES = {'front': (5, 62, 433, 352), 'left': (433, 62, 834, 352), 'right': (834, 62, 1271, 352), 'q3L': (5, 390, 433, 668), 'q3R': (433, 390, 834, 668)}
_cache = {}


def plate_skin(name):
    if name in _cache: return _cache[name]
    box = BOXES[name]; p = np.asarray(PLATE.crop(box)).astype(int)
    rb, rmin, rg = SK[name]
    m = ((p[..., 0] - p[..., 2]) > rb) & (p[..., 0] > rmin) & ((p[..., 0] - p[..., 1]) > rg)
    _cache[name] = m; return m


def plate_extent(name, rows):
    """per plate row (full-plate coords): (min col, max col) of the skin mask in full-plate px, None if empty"""
    m = plate_skin(name); box = BOXES[name]; out = {}
    for r in rows:
        rr = int(round(r)) - box[1]
        if rr < 0 or rr >= m.shape[0]: continue
        cs = np.where(m[rr])[0]
        if len(cs): out[int(round(r))] = (box[0] + cs.min(), box[0] + cs.max())
    return out


def row_z(name, r):
    """z of a plate row in a given panel"""
    return TOP - (r - 397) * K if name in Q3 else TOP - (r - 76) * K


def mesh_extent(V, E, name, rows, head_mask):
    """per plate row: (min col, max col) of the mesh section projected with the plate's camera"""
    out = {}
    for r in rows:
        z = row_z(name, r)
        pts = plane_section(V, E, 2, z, head_mask)
        if len(pts) == 0: continue
        if name in Q3:
            c, _, _ = q3_project(pts, name)
        elif name == 'front':
            c = colx(pts[:, 0])
        else:
            c = coly(pts[:, 1])           # left profile (face to the image left): col = 712 - (0.065 - y)/K
        out[int(r)] = (c.min(), c.max())
    return out


def report_q3(V, E, rows=None, verbose=True, head=None):
    head = head if head is not None else ((V[:, 2] > 1.40) & (np.abs(V[:, 0]) < 0.16))
    rows = rows or list(range(430, 596, 6))
    res = {}
    for name in ('q3L', 'q3R'):
        pe = plate_extent(name, rows); me = mesh_extent(V, E, name, rows, head)
        d = {}
        for r in rows:
            if r in pe and r in me:
                d[r] = ((me[r][0] - pe[r][0]) * K * 1000, (me[r][1] - pe[r][1]) * K * 1000)
        res[name] = d
    if verbose:
        print('row   z     | q3L  L(mm)  R(mm) | q3R  L(mm)  R(mm)    [mesh - plate, +: mesh further right]')
        for r in rows:
            a = res['q3L'].get(r); b = res['q3R'].get(r)
            if a and b: print('%3d %.4f |      %6.1f %6.1f |      %6.1f %6.1f' % (r, row_z('q3L', r), a[0], a[1], b[0], b[1]))
    return res


if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'h0'
    V, F, loops = load(tag); E = edges_of(F)
    report_q3(V, E)


def report_profile(V, E, rows=range(96, 262, 6), verbose=True):
    """front-y / back-y / front half-width vs plate (left profile + front silhouette), mm (mesh - plate)"""
    head = (V[:, 2] > 1.40) & (np.abs(V[:, 0]) < 0.16)
    pe = H.plate_extents()
    out = {}
    for r in rows:
        z = float(H.zrow(r)); pts = plane_section(V, E, 2, z, head)
        if len(pts) == 0: continue
        i = list(pe['rows']).index(r)
        yf_m, yb_m = pts[:, 1].min(), pts[:, 1].max()
        hw_m = np.abs(pts[:, 0]).max()
        out[r] = ((yf_m - pe['yf'][i]) * 1000, (yb_m - pe['yb'][i]) * 1000, (hw_m - pe['hw'][i]) * 1000)
    if verbose:
        print('row   z     | front-y  back-y  half-width  (mesh - plate, mm; half-width incl. ears)')
        for r, (a, b, c) in out.items(): print('%3d %.4f | %6.1f %7.1f %8.1f' % (r, float(H.zrow(r)), a, b, c))
    return out


if __name__ == '__main__' and len(sys.argv) > 2 and sys.argv[2] == 'profile':
    V, F, loops = load(sys.argv[1]); E = edges_of(F); report_profile(V, E)
