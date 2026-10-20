"""Edge plot of the mesh zone (orthographic, facing edges only).  Run with Blender python3.13 (numpy+PIL).
python3.13 wireplot.py <out.png> <view back|front|left|right|below|above> <x0 x1 z0 z1> <scale px/m> <npy1[,npy2]> [colors]
npy = Nx3 positions (default start). If two npy given, 2nd drawn in red over 1st (grey)."""
import sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-pelvis-form2')
from common import *
out, view = sys.argv[1], sys.argv[2]; a0, a1, b0, b1 = [float(v) for v in sys.argv[3:7]]; sc = float(sys.argv[7])
srcs = sys.argv[8].split(',') if len(sys.argv) > 8 else ['start']
def load(s): return V0 if s == 'start' else np.load(s)
# horizontal axis h, vertical axis v, toward-camera direction t
if view == 'back':   H = lambda P: -P[:, 0]; Vv = lambda P: P[:, 2]; T = np.array([0, 1.0, 0])
elif view == 'front': H = lambda P: P[:, 0];  Vv = lambda P: P[:, 2]; T = np.array([0, -1.0, 0])
elif view == 'left':  H = lambda P: P[:, 1];  Vv = lambda P: P[:, 2]; T = np.array([1.0, 0, 0])
elif view == 'right': H = lambda P: -P[:, 1]; Vv = lambda P: P[:, 2]; T = np.array([-1.0, 0, 0])
elif view == 'below': H = lambda P: P[:, 0];  Vv = lambda P: -P[:, 1]; T = np.array([0, 0, -1.0])
elif view == 'above': H = lambda P: P[:, 0];  Vv = lambda P: P[:, 1]; T = np.array([0, 0, 1.0])
else: raise SystemExit('view')
W_, H_ = int((a1 - a0) * sc), int((b1 - b0) * sc)
im = Image.new('RGB', (W_, H_), (24, 24, 28)); d = ImageDraw.Draw(im)
cols = [(120, 125, 135), (255, 90, 70), (80, 220, 120)]
for si, s in enumerate(srcs):
    V = load(s); N = vnormals(V); h = (H(V) - a0) * sc; v = (b1 - Vv(V)) * sc; fac = (N @ T) > 0.05
    for f in F:
        n = len(f)
        for k in range(n):
            p, q = f[k], f[(k + 1) % n]
            if fac[p] and fac[q]:
                x0_, y0_, x1_, y1_ = h[p], v[p], h[q], v[q]
                if max(x0_, x1_) < 0 or min(x0_, x1_) > W_ or max(y0_, y1_) < 0 or min(y0_, y1_) > H_: continue
                d.line([(x0_, y0_), (x1_, y1_)], fill=cols[si % 3], width=1)
im.save(out); print(out, im.size)
