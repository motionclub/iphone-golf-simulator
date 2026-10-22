import sys, os
import numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/tex/v7/tools')
import lava_try as lt
g = lt.g
d = sys.argv[1]
C, E, N = (g.read_png(os.path.join(d, 'Lava_%s.png' % k)) for k in 'CEN')
sp = g.lava_spec()
r = lt.hair(C, E, N, sp)
print(r['longest'], r['hairlines_len60'])
# save the shader image with the region around the longest line
h, rgb = g.lava_shader_model(C, E, N, sp)
(ln, row, col, depth) = r['longest'][0]
y0 = max(0, row - 90); x0 = max(0, col - 90)
crop = rgb[y0:y0 + 180, x0:x0 + 180].astype(np.uint8)
big = np.kron(crop, np.ones((4, 4, 1), np.uint8))
g.write_png(os.path.join(d, 'hair_longest.png'), big)
print('row', row, 'col', col)
