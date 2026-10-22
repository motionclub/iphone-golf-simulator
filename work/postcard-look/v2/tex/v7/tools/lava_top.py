import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
rgb = np.load(os.path.join(HERE, '..', sys.argv[1], 'rgb.npy')).astype(np.float32)
import importlib.util
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
L = g.lum(rgb / 255) * 255
gg = np.maximum(np.abs(np.roll(L, -1, 1) - L), np.abs(np.roll(L, -1, 0) - L))
thr = np.percentile(gg, 99.95)
ys, xs = np.nonzero(gg >= thr)
# cluster by coarse grid cells
cells = {}
for y, x in zip(ys, xs): cells.setdefault((y // 48, x // 48), []).append((y, x))
best = sorted(cells.items(), key=lambda kv: -len(kv[1]))[:6]
tiles = []
for (cy, cx), pts in best:
    y0 = int(np.mean([p[0] for p in pts])); x0 = int(np.mean([p[1] for p in pts]))
    y0 = min(max(y0 - 24, 0), 1024 - 48); x0 = min(max(x0 - 24, 0), 1024 - 48)
    crop = rgb[y0:y0 + 48, x0:x0 + 48]
    big = np.kron(crop, np.ones((6, 6, 1)))
    tiles.append(big)
    print('cluster at (y %d, x %d): %d texels >= %.0f' % (y0 + 24, x0 + 24, len(pts), thr))
sheet = np.concatenate([np.concatenate(tiles[:3], 1), np.concatenate(tiles[3:6], 1)], 0)
g.write_png(os.path.join(HERE, '..', sys.argv[1], 'top_clusters.png'), np.clip(sheet, 0, 255).astype(np.uint8))
