import sys, numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/tex/v6/tools')
import nearsim as S, golf_look_textures as G
d = sys.argv[1]
for nm in sys.argv[2:]:
    l = S.lum709(G.read_png(f'{d}/{nm}'))
    out = []
    for mag in (1.5, 2.5, 3.0, 3.8, 5.5):
        fs = [S.flat_share(S.up_bilinear(l[y0:y0 + 90, x0:x0 + 90], mag, 320)) for (y0, x0) in ((0, 0), (300, 500), (700, 200), (150, 800))]
        out.append((mag, round(float(np.mean([f[0] for f in fs])), 3), round(float(np.mean([f[1] for f in fs])), 4)))
    print(nm, out)
