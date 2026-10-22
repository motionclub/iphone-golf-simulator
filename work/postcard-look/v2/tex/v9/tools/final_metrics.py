"""final_metrics.py : writes v9/METRICS_v9.md from the real-project stills (stills_real9, stills_real_grass) vs the round-1 stills in ArtDir (python3 + numpy + PIL)."""
import sys, os, json, subprocess, io, contextlib
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from gv_grass import stats, rgb2hsv, lum
from PIL import Image
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
V = R + '/work/postcard-look/v2/tex/v9'
BASE = R + '/ArtDir/screenshots/golf_postcards/look/'
names9 = ['hole08_1_tee', 'hole08_2_approach', 'hole08_3_arch', 'hole09_1_tee', 'hole09_2_approach', 'hole09_3_ruin', 'hole10_1_tee', 'hole10_2_approach', 'hole10_3_lavarim']
def lap(L):
    return (-4 * L[1:-1, 1:-1] + L[:-2, 1:-1] + L[2:, 1:-1] + L[1:-1, :-2] + L[1:-1, 2:])
out = ['# POSTCARD_LOOK v9 (area T) - Game-view numbers, real project, stills of work/postcard-look/v2/tex/v9/stills_real9 (cfg_9.json = the 9 proof shots) vs the round-1 stills in ArtDir/screenshots/golf_postcards/look (04:20 Oct 5)', '']
out.append('| shot | lower-60 % luminance sd round-1 -> v9 | grass hue (px-weighted, rows y400-1600) | share of grass px with a channel >= 250 | near Laplacian sd y1200-1600 round-1 -> v9 |')
out.append('|---|---|---|---|---|')
for n in names9:
    a = stats(BASE + n + '.png'); b = stats(V + '/stills_real9/' + n + '.png')
    rows = [v for k, v in b.items() if isinstance(v, dict)]
    if rows:
        w = sum(v['n'] for v in rows); hue = sum(v['hue'] * v['n'] for v in rows) / w; clip = sum(v['clip'] * v['n'] for v in rows) / w
    else:
        hue = clip = float('nan')
    L0 = lum(np.asarray(Image.open(BASE + n + '.png').convert('RGB')).astype(float)); L1 = lum(np.asarray(Image.open(V + '/stills_real9/' + n + '.png').convert('RGB')).astype(float))
    nl0 = lap(L0[1200:1600, 0:600]).std(); nl1 = lap(L1[1200:1600, 0:600]).std()
    out.append('| %s | %.1f -> %.1f (%+.1f) | %.1f | %.2f %% | %.2f -> %.2f |' % (n, a['lower60_lum_sd'], b['lower60_lum_sd'], b['lower60_lum_sd'] - a['lower60_lum_sd'], hue, 100 * clip, nl0, nl1))
open(V + '/METRICS_v9.md', 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
