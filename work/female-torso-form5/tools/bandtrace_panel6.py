"""bandtrace_panel6.py: trace the dark under-butt fold line in the RENDERED proof panels (what the eye / the critics see), plate vs FORM4 vs FORM5.
Reads proof/06z_underbutt_zoom_soft_clay.png (5 columns: plate | F4 soft | F4 clay | F5 soft | F5 clay; row 0 = back view).  Panel pixel scale ~0.8 px/mm.
Fold row = centroid (beyond half depth) of the high-pass (sigma 10 px) luminance deficit around its minimum, per column at dx = +-45..105 px from the cleft (x ~ 201 px).
usage: python3 tools/bandtrace_panel6.py [proof/06z_underbutt_zoom_soft_clay.png] [--json out.json]"""
import sys, os, json
import numpy as np
from PIL import Image, ImageFilter
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CX = 201
DXS = [-105, -90, -75, -60, -45, 45, 60, 75, 90, 105]

def _hp(p, s=10):
    a = np.asarray(p, dtype=np.float32); b = np.asarray(p.filter(ImageFilter.GaussianBlur(s)), dtype=np.float32); return a - b

WIN = (150, 235)        # fixed row window (the plate / FORM4 / FORM5 fold bands all lie inside it)

def trace_panel(p, s=10, thr_frac=0.3):
    """ROBUST trace (round 5 fix): per column, the centroid of the high-pass deficit over the FIXED window WIN (threshold = thr_frac of the column's deepest deficit).
    The first version (argmin +-35 rows inside rows 100-260) flipped between competing features at the faint outer columns: the render-domain search exploited that flip
    (a fake +10 px 'smile' from an outlier at dx -105) - see honest notes."""
    h = _hp(p, s); out = {}
    lo, hi = WIN
    for dx in DXS:
        x = CX + dx
        col = h[lo:hi, max(0, x - 3):x + 4].mean(axis=1)
        col = np.convolve(col, np.ones(5) / 5.0, mode='same')
        d = -np.minimum(col, 0); thr = d.max() * thr_frac
        w = np.maximum(d - thr, 0)
        out[dx] = (float((w * (np.arange(lo, hi))).sum() / max(w.sum(), 1e-9)), float(d.max()))
    return out

def crest_grad(p, rows):
    """upper-edge crispness of the fold band: max brightness INCREASE per px going UP the image just above the traced band centre (grey/px), mean over the columns (raw luminance, columns +-3 px, 2-px smoothed)"""
    a = np.asarray(p, dtype=np.float32); gs = []
    for dx in DXS:
        x = CX + dx; r0 = int(round(rows[dx]))
        col = a[:, max(0, x - 3):x + 4].mean(axis=1)
        col = np.convolve(col, np.ones(3) / 3.0, mode='same')
        seg = col[max(r0 - 45, 2):r0 + 1]
        g = seg[:-1] - seg[1:]          # row r-1 minus row r (positive = brighter above)
        gs.append(float(g.max()) if len(g) else 0.0)
    return float(np.mean(gs))


def analyse(path):
    im = Image.open(path).convert('L'); W = im.size[0] // 5; H = im.size[1] // 4
    names = {'plate': 0, 'F4soft': 1, 'F4clay': 2, 'F5soft': 3, 'F5clay': 4}
    T = {n: trace_panel(im.crop((i * W, 0, (i + 1) * W, H))) for n, i in names.items()}
    res = {}
    for n in names:
        rows = {dx: T[n][dx][0] for dx in DXS}
        res[n] = rows
    def err(n):
        e = np.array([res[n][dx] - res['plate'][dx] for dx in DXS]); return e
    def rise(n):          # lateral rise of the fold line: mean row at |dx|=45 minus mean row at |dx|=105 (px, positive = fold rises laterally = smile)
        return 0.5 * ((res[n][-45] + res[n][45]) - (res[n][-105] + res[n][105]))
    panels = {n: im.crop((i * W, 0, (i + 1) * W, H)) for n, i in names.items()}
    summary = {n: dict(rms_err_px=float(np.sqrt((err(n) ** 2).mean())), rise_px=float(rise(n)), crest_grad=crest_grad(panels[n], res[n]),
                       mean_offset_px=float(err(n).mean()), shape_err_px=float(np.sqrt(((err(n) - err(n).mean()) ** 2).mean()))) for n in names if n != 'plate'}
    summary['plate'] = dict(rise_px=float(rise('plate')), crest_grad=crest_grad(panels['plate'], res['plate']))
    return res, summary

if __name__ == '__main__':
    path = next((a for a in sys.argv[1:] if not a.startswith('--') and a.endswith('.png')), HERE + '/proof/06z_underbutt_zoom_soft_clay.png')
    res, sm = analyse(path)
    print('dx       ' + ' '.join(f'{d:5d}' for d in DXS))
    for n in res: print(f'{n:8s} ' + ' '.join(f'{res[n][d]:5.0f}' for d in DXS))
    for n, v in sm.items(): print(n, {k: round(x, 1) for k, x in v.items()})
    if '--json' in sys.argv:
        json.dump(dict(rows={n: {str(d): r for d, r in res[n].items()} for n in res}, summary=sm), open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
