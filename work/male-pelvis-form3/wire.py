"""Wireframe overlay (front-facing faces only) on an orthographic yaw render of rig.py.
python3 wire.py <tag|path.npy> <yaw> <scale> <tz> <w> <h> <pitch> <out.png> [base.png] [tx]
projection identical to rig.yaw_cam (target (tx along right, ty=-0.05, tz))."""
import sys, math
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '.')
from common import F, V0
def project(V, yaw, scale, tz, w, h, pitch=0.0, tx=0.0, ty=-0.05):
    a = math.radians(yaw); pr = math.radians(pitch); right = np.array([math.cos(a), math.sin(a), 0.0])
    t = np.array([0.0, ty, tz]) + right * tx
    viewdir = np.array([math.sin(a) * math.cos(pr), -math.cos(a) * math.cos(pr), math.sin(pr)])   # target -> camera
    up = np.cross(viewdir, right); up /= np.linalg.norm(up); up = -up if up[2] < 0 else up
    d = V - t; sx = d @ right; sy = d @ up; depth = d @ viewdir
    px = (sx / scale + 0.5) * w; py = (0.5 - sy / scale * (w / h)) * h
    return px, py, depth, viewdir
def draw(V, yaw, scale, tz, w, h, pitch, base=None, tx=0.0, color=(200, 40, 40), width=1, ring=None):
    px, py, depth, vd = project(V, yaw, scale, tz, w, h, pitch, tx)
    im = Image.open(base).convert('RGB') if base else Image.new('RGB', (w, h), (200, 200, 200)); dr = ImageDraw.Draw(im)
    # face normals
    for f in F:
        P = V[list(f)]; n = np.cross(P[1] - P[0], P[2] - P[0])
        if n @ vd <= 0: continue
        pts = [(px[i], py[i]) for i in f]
        if max(p[0] for p in pts) < 0 or min(p[0] for p in pts) > w or max(p[1] for p in pts) < 0 or min(p[1] for p in pts) > h: continue
        dr.line(pts + [pts[0]], fill=color, width=width)
    return im
if __name__ == '__main__':
    a = sys.argv[1:]; tag = a[0]; V = np.load(f'data/V_{tag}.npy') if not tag.endswith('.npy') else np.load(tag)
    if tag == 'start': V = V0
    yaw, scale, tz, w, h, pitch = float(a[1]), float(a[2]), float(a[3]), int(a[4]), int(a[5]), float(a[6])
    base = a[8] if len(a) > 8 and a[8] != '-' else None; tx = float(a[9]) if len(a) > 9 else 0.0
    draw(V, yaw, scale, tz, w, h, pitch, base, tx).save(a[7]); print(a[7])
