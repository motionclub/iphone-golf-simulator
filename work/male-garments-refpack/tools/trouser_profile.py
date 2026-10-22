"""trouser_profile.py <tag>...: navy-trouser silhouette widths per height, sheet 11 vs our renders (build/<tag>_{front,side}.png).
Height runs 0 (belt bottom) -> 1 (hem); widths are divided by the hip width at 5 % so the cartoon body's scale drops out.
front: single-leg width (mean of both legs) + outer-to-outer; side: leg depth."""
import sys; sys.path.insert(0, 'tools'); from seg import S
import numpy as np
from PIL import Image
def navy(im):
    a = np.asarray(im.convert('RGB')).astype(float); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (b > r + 25) & (b > g + 10) & (b < 200) & (r < 110)
def runs(row):
    x = np.flatnonzero(row); 
    if len(x) == 0: return []
    cut = np.flatnonzero(np.diff(x) > 3); st = np.r_[x[0], x[cut + 1]]; en = np.r_[x[cut], x[-1]]
    rr = [[s, e] for s, e in zip(st, en)]
    m_ = [rr[0]]
    for s, e in rr[1:]:                                  # bridge crease / seam lines (< 9 px) so a leg is one run
        if s - m_[-1][1] < 9: m_[-1][1] = e
        else: m_.append([s, e])
    return [(s, e) for s, e in m_ if e - s > 4]
def profile(m):
    ys = np.flatnonzero(m.sum(1) > 8)                       # longest run of navy rows = belt bottom .. hem (drops the shoes' navy trim)
    cut = np.flatnonzero(np.diff(ys) > 2); st = np.r_[0, cut + 1]; en = np.r_[cut, len(ys) - 1]; k = np.argmax(en - st)
    y0, y1 = ys[st[k]], ys[en[k]]
    out = []
    for f in np.linspace(.05, .97, 24):
        rr = runs(m[int(y0 + f * (y1 - y0))]) or [(0, 0)]; out.append((f, rr))
    hip = out[0][1][-1][1] - out[0][1][0][0]
    return out, hip
def summarise(m, view):
    out, hip = profile(m); res = []
    for f, rr in out:
        tot = (rr[-1][1] - rr[0][0]) / hip
        leg = np.mean([e - s for s, e in rr]) / hip if len(rr) >= 2 else tot
        res.append((f, tot, leg if view == 'front' else tot))
    return res
sheet = Image.open(S + '11-shorts-trousers-construction.png')
src = {'sheet': {'front': sheet.crop((300, 690, 560, 1170)), 'side': sheet.crop((900, 690, 1120, 1170))}}
for t in sys.argv[1:]: src[t] = {v: Image.open('build/%s_%s.png' % (t, v)) for v in ('front', 'side')}
R = {k: {v: summarise(navy(im), v) for v, im in d.items()} for k, d in src.items()}
print('h    ' + ''.join('%-22s' % k for k in R))
print('     ' + ''.join('%-22s' % 'legW  outer  sideD' for k in R))
for i in range(0, 24, 2):
    print('%.2f ' % R['sheet']['front'][i][0] + ''.join('%-22s' % ('%.2f  %.2f  %.2f' % (R[k]['front'][i][2], R[k]['front'][i][1], R[k]['side'][i][1])) for k in R))
