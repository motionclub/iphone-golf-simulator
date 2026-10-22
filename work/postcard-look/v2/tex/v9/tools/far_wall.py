import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import numpy as np
import golf_look_textures as G
d = sys.argv[1]
E = G.read_png(d + '/Basalt_E.png').astype(np.float32) / 255; N = G.read_png(d + '/Basalt_N.png').astype(np.float32) / 255 * 2 - 1
mask = G.lum(E) > 0.04
wallm = np.hypot(N[..., 0], N[..., 1]) > 0.75
nw = np.zeros_like(wallm)
for dx in range(-8, 9): nw |= np.roll(wallm, dx, 1)
for dy in range(-8, 9): nw |= np.roll(wallm, dy, 0)
far = mask & ~nw
print('far-from-wall glow px', far.sum(), 'of', mask.sum(), 'mean E of far px %.3f vs near %.3f' % (G.lum(E)[far].mean(), G.lum(E)[mask & nw].mean()))
img = np.zeros(mask.shape + (3,), np.uint8); img[mask & nw] = (255, 150, 30); img[far] = (60, 200, 255); img[wallm & ~mask] = (60, 60, 60)
G.write_png(d + '/far_wall.png', img)
print('tilt stats around far px: mean hypot(nx,ny) %.2f' % np.hypot(N[..., 0], N[..., 1])[far].mean())
