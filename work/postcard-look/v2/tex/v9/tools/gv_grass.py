"""gv_grass.py dir [dir...] : Game-view grass statistics of the address / bandview stills of each dir (python3 + numpy + PIL).
grass mask = hue 52..90, S >= .30, V >= .22 in the lower 60 % (y >= 640); per row band: mean hue/S/V, clipped share (any channel >= 250), luminance sd; the whole-lower-60% luminance sd;
band readability: for rows y 700..1500 the horizontal luminance profile minus a 41 px moving mean -> sd (the stripes show up as a sharp-edged step: reported as the mean abs step at the strongest 8 edges per row)."""
import sys, glob, os
import numpy as np
from PIL import Image
def rgb2hsv(a):
    a = a.astype(np.float64) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1); d = mx - mn
    h = np.zeros_like(mx); m = d > 1e-9
    rm = m & (mx == r); gm = m & (mx == g) & ~rm; bm = m & ~rm & ~gm
    h[rm] = ((g - b)[rm] / d[rm]) % 6; h[gm] = (b - r)[gm] / d[gm] + 2; h[bm] = (r - g)[bm] / d[bm] + 4
    s = np.where(mx > 1e-9, d / np.maximum(mx, 1e-9), 0)
    return h * 60, s, mx
def lum(a): return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
BANDS = (('far y400-700', 400, 700), ('mid y700-1000', 700, 1000), ('near y1000-1300', 1000, 1300), ('foot y1300-1600', 1300, 1600))
def stats(path):
    a = np.asarray(Image.open(path).convert('RGB')); H, W = a.shape[:2]
    hh, ss, vv = rgb2hsv(a); L = lum(a.astype(np.float64))
    mask = (hh >= 52) & (hh <= 90) & (ss >= .30) & (vv >= .22); mask[:int(H * .40)] = False
    out = {}
    low = L[int(H * .40):]
    out['lower60_lum_sd'] = float(low.std())
    for nm, y0, y1 in BANDS:
        m = mask[y0:y1]
        if m.sum() < 500: out[nm] = None; continue
        px = a[y0:y1][m].astype(np.float64)
        mh, ms, mv = rgb2hsv(px.mean(0)[None, None, :])
        out[nm] = dict(n=int(m.sum()), rgb=tuple(int(round(x)) for x in px.mean(0)), hue=float(mh[0, 0]), S=float(ms[0, 0]), V=float(mv[0, 0]),
                       hue_p5_p95=tuple(float(x) for x in np.percentile(hh[y0:y1][m], [5, 95])), clip=float((px.max(1) >= 250).mean()), lum_sd=float(L[y0:y1][m].std()))
    # stripe readability: mean absolute luminance step across the strongest edges per row, rows 700..1500 (step over 6 px, after a 3 px smoothing)
    steps = []
    for y in range(700, 1500, 10):
        r = np.convolve(L[y], np.ones(3) / 3, 'same'); m = mask[y]
        d = np.abs(r[6:] - r[:-6]); ok = m[6:] & m[:-6]
        d = np.where(ok, d, 0); top = np.sort(d)[-8:]
        steps.append(top.mean())
    out['edge_step_top8'] = float(np.mean(steps))
    return out
if __name__ == '__main__':
    names = ['hole08_1_tee', 'hole08_2_approach', 'hole08_4_bandview', 'hole09_1_tee', 'hole09_2_approach', 'hole09_4_bandview', 'hole10_1_tee', 'hole10_2_approach', 'hole10_4_bandview']
    for d in sys.argv[1:]:
        print('=====', d)
        for n in names:
            p = os.path.join(d, n + '.png')
            if not os.path.exists(p): continue
            s = stats(p)
            print('%-20s lowsd %5.1f edge %5.1f | ' % (n, s['lower60_lum_sd'], s['edge_step_top8']) + ' | '.join(
                '%s %s' % (nm.split()[0], ('h%.1f S%.2f V%.2f clip%.1f%% sd%.0f' % (s[nm]['hue'], s[nm]['S'], s[nm]['V'], s[nm]['clip'] * 100, s[nm]['lum_sd'])) if s[nm] else '-') for nm, _, _ in BANDS))
