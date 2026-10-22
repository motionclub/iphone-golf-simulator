"""gv_sheen.py <id dir> <ctrl dir> <variant dir> [...] : what the per-band sheen adds in the Game view = (variant - ctrl) render, per band: mean delta luminance, mean delta B-R (the sky reflection is blue-white), delta saturation, p95 |delta lum|,
light vs dark band, per row band, over the 9 shots (the ctrl render has identical albedo / normals, flat smoothness)."""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from gv_grass import rgb2hsv, lum
from gv_bands import erode, BANDS, names
idd, cd = sys.argv[1], sys.argv[2]
for d in sys.argv[3:]:
    print('=====', d, 'minus', cd)
    acc = {k: [] for k in ('lL', 'lD', 'sL', 'sD', 'bL', 'bD')}
    for n in names:
        p = os.path.join(idd, n + '.png')
        idi = np.asarray(Image.open(p).convert('RGB')); _, _, vid = rgb2hsv(idi)
        a = np.asarray(Image.open(os.path.join(d, n + '.png')).convert('RGB')).astype(float); c = np.asarray(Image.open(os.path.join(cd, n + '.png')).convert('RGB')).astype(float)
        h, s, v = rgb2hsv(a.astype(np.uint8)); h2, s2, v2 = rgb2hsv(c.astype(np.uint8))
        grass = (h2 >= 52) & (h2 <= 90) & (s2 >= .30)
        lt = erode((vid > .45) & grass, 4); dk = erode((vid < .22) & grass, 4)
        row = []
        for nm, y0, y1 in BANDS:
            ml = lt[y0:y1]; md = dk[y0:y1]
            if ml.sum() < 400 or md.sum() < 400: continue
            dl = lum(a[y0:y1]) - lum(c[y0:y1]); ds = s[y0:y1] - s2[y0:y1]; db = (a[y0:y1, :, 2] - a[y0:y1, :, 0]) - (c[y0:y1, :, 2] - c[y0:y1, :, 0])
            row.append('%s: light dL %+.1f dS %+.3f d(B-R) %+.1f | dark dL %+.1f dS %+.3f d(B-R) %+.1f' % (nm.split()[0], dl[ml].mean(), ds[ml].mean(), db[ml].mean(), dl[md].mean(), ds[md].mean(), db[md].mean()))
            acc['lL'].append(dl[ml].mean()); acc['lD'].append(dl[md].mean()); acc['sL'].append(ds[ml].mean()); acc['sD'].append(ds[md].mean()); acc['bL'].append(db[ml].mean()); acc['bD'].append(db[md].mean())
        print('%-20s ' % n + ' || '.join(row))
    print('MEAN over shots/bands: light dL %+.2f dS %+.4f d(B-R) %+.2f | dark dL %+.2f dS %+.4f d(B-R) %+.2f' % (np.mean(acc['lL']), np.mean(acc['sL']), np.mean(acc['bL']), np.mean(acc['lD']), np.mean(acc['sD']), np.mean(acc['bD'])))
