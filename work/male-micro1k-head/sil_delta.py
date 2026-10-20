"""Silhouette deltas between START and a variant: max|x| per z (front/back silhouette width), and profile front/back y extents; mm (variant - start)
python3.13 sil_delta.py <tag> [zlo zhi]"""
import sys; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1k-head')
from j_lib import *
tag = sys.argv[1]; zlo = float(sys.argv[2]) if len(sys.argv) > 2 else 1.40; zhi = float(sys.argv[3]) if len(sys.argv) > 3 else 1.56
V0, F, _ = load_start(); E = edges_of(F); V1 = np.load(W / f'data/V_{tag}.npy')
m = (V0[:, 2] > 1.30) & (np.abs(V0[:, 0]) < 0.12)
worst = dict(w=0, f=0, b=0)
print(' z      width(max|x|) start  now   d |  front-y start now d | back-y start now d')
for z in np.arange(zlo, zhi, 0.005):
    a = plane_section(V0, E, 2, z, m); b = plane_section(V1, E, 2, z, m)
    if len(a) < 2 or len(b) < 2: continue
    wa, wb = np.abs(a[:, 0]).max() * 1000, np.abs(b[:, 0]).max() * 1000
    fa, fb = a[:, 1].min() * 1000, b[:, 1].min() * 1000; ba, bb = a[:, 1].max() * 1000, b[:, 1].max() * 1000
    worst['w'] = min(worst['w'], wb - wa); worst['f'] = max(abs(worst['f']), abs(fb - fa)); worst['b'] = max(abs(worst['b']), abs(bb - ba))
    flag = ' <' if abs(wb - wa) > 1.2 or abs(fb - fa) > 1.5 or abs(bb - ba) > 1.5 else ''
    print(f'{z:.3f}   {wa:6.1f} {wb:6.1f} {wb-wa:+5.1f} | {fa:+7.1f} {fb:+7.1f} {fb-fa:+5.1f} | {ba:+6.1f} {bb:+6.1f} {bb-ba:+5.1f}{flag}')
print('worst width shrink %.2f mm, worst |dy| front %.2f back %.2f' % (worst['w'], worst['f'], worst['b']))
