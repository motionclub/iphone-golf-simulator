"""band_stats.py <dir> : mow-band statistics of Fairway_C / Green_C / *_N in a Look folder (Blender's python3.13, numpy)."""
import sys, os
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import numpy as np
import golf_look_textures as G
d = sys.argv[1]
for nm, per in (('Fairway', 2), ('Green', 3)):
    c = G.read_png(os.path.join(d, nm + '_C.png'))
    a = c[..., :3].astype(np.float64) / 255
    l = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    N = l.shape[1]
    cm = l.mean(0); uu = (np.arange(N) + .5) / N
    for K in (1, 2, 3):
        p = (uu * K) % 1.0
        Ll = cm[np.minimum(p, 1 - p) < .12].mean(); Ld = cm[np.abs(p - .5) < .12].mean()
        print(nm, 'K=%d' % K, 'amp (Ll-Ld)/(Ll+Ld) = %+.4f' % ((Ll - Ld) / (Ll + Ld)))
    prof = cm.reshape(32, -1).mean(1)
    print(nm, 'u-profile (32 bins):', ' '.join('%.3f' % x for x in prof))
    print(nm, 'mode', c.shape, 'mean', np.round(a.reshape(-1, 3).mean(0) * 255, 1))
    if c.shape[2] == 4:
        al = c[..., 3].astype(float) / 255
        print(nm, 'alpha mean %.3f min %.3f max %.3f' % (al.mean(), al.min(), al.max()))
