"""gv_bands.py <id dir> <dir> [dir...] : lit band contrast in the Game view. The id dir holds stills rendered with white / black band albedo (make_id_maps.py); light = id V > .45, dark = id V < .22
(eroded by 4 px so edges do not count), restricted to grass pixels (hue 52..90 in the same shot of <dir>) and y >= 450; contrast = (Ll - Ld) / (Ll + Ld) of the mean luminance per row band, per shot."""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from gv_grass import rgb2hsv, lum
def erode(m, r):
    o = m.copy()
    for d in range(1, r + 1):
        o &= np.roll(m, d, 0) & np.roll(m, -d, 0) & np.roll(m, d, 1) & np.roll(m, -d, 1)
    return o
BANDS = (('far y450-700', 450, 700), ('mid y700-1000', 700, 1000), ('near y1000-1300', 1000, 1300), ('foot y1300-1600', 1300, 1600))
names = ['hole08_1_tee', 'hole08_2_approach', 'hole08_4_bandview', 'hole09_1_tee', 'hole09_2_approach', 'hole09_4_bandview', 'hole10_1_tee', 'hole10_2_approach', 'hole10_4_bandview']
idd = sys.argv[1]
for d in sys.argv[2:]:
    print('=====', d)
    tot = []
    for n in names:
        p = os.path.join(idd, n + '.png')
        if not os.path.exists(p): continue
        idi = np.asarray(Image.open(p).convert('RGB')); _, _, vid = rgb2hsv(idi)
        a = np.asarray(Image.open(os.path.join(d, n + '.png')).convert('RGB')); h, s, v = rgb2hsv(a); L = lum(a.astype(float))
        grass = (h >= 52) & (h <= 90) & (s >= .30)
        lt = erode((vid > .45) & grass, 4); dk = erode((vid < .22) & grass, 4)
        row = []
        for nm, y0, y1 in BANDS:
            ml = lt[y0:y1]; md = dk[y0:y1]
            if ml.sum() < 400 or md.sum() < 400: row.append('%s -' % nm.split()[0]); continue
            Ll = L[y0:y1][ml].mean(); Ld = L[y0:y1][md].mean()
            row.append('%s %+.1f%% (L %.0f/%.0f)' % (nm.split()[0], 100 * (Ll - Ld) / (Ll + Ld), Ll, Ld))
        print('%-20s ' % n + ' | '.join(row))
