import sys, json
import numpy as np
from PIL import Image
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/tex/v8/tools')
import lava_gv as G
def mask(px, y0=650):
    hh, ss, vv = G.rgb2hsv(px)
    m = (hh <= 38) & (ss > .6) & (vv > .22)
    m[:y0] = False
    return m
def lap(L):
    return (-4 * L[1:-1, 1:-1] + L[:-2, 1:-1] + L[2:, 1:-1] + L[1:-1, :-2] + L[1:-1, 2:])
for d in sys.argv[1:]:
    for name, crop in (('hole10_3_lavarim', (250, 650, 900, 1600)), ('hole10_2_approach', None)):
        px = np.asarray(Image.open(f'{d}/{name}.png').convert('RGB'))
        m = mask(px, 650 if name.endswith('rim') else 300)
        if name.endswith('approach'): m[:, :] = m & (np.arange(px.shape[0])[:, None] < 560)
        st = G.stats(px, m, d.split('/')[-1] + ':' + name, crop, comp=True)
        L = G.lum(px.astype(float)); l = lap(L); mm = m[1:-1, 1:-1]
        st['lap_sd'] = round(float(l[mm].std()), 2)
        print(json.dumps(st))
