"""near_lap.py still.png ... : Laplacian sd (luminance 0..255, 3x3 discrete Laplacian) in the near (y1200-1600), mid (y700-900) bands of a 900x1600 still -- the review's hole 9 metric."""
import sys
import numpy as np
from PIL import Image
def lum(a): return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
def lap(L):
    return (-4 * L[1:-1, 1:-1] + L[:-2, 1:-1] + L[2:, 1:-1] + L[1:-1, :-2] + L[1:-1, 2:])
for p in sys.argv[1:]:
    a = np.asarray(Image.open(p).convert('RGB')).astype(np.float64); L = lum(a)
    out = []
    for nm, (y0, y1, x0, x1) in (('near y1200-1600', (1200, 1600, 0, 600)), ('mid y700-900', (700, 900, 0, 600)), ('y1000-1200', (1000, 1200, 0, 600))):
        l = lap(L[y0:y1, x0:x1]); gx = np.abs(np.diff(L[y0:y1, x0:x1], axis=1)).mean(); gy = np.abs(np.diff(L[y0:y1, x0:x1], axis=0)).mean()
        out.append('%s: lap sd %.2f grad x/y %.2f/%.2f' % (nm, l.std(), gx, gy))
    print(p.split('/')[-1], ' | '.join(out))
