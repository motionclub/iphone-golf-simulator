"""Multi-scale band-pass correlation / amplitude ratio (render vs plate) for the pelvis regions.
python3 metric2.py <tag> [<tag>...]   (renders clay views into r/<tag>_m/ through metric.render if missing)
Regions are boxes in plate px; scales are DoG sigma pairs in plate px (1 px ~ 2.9 mm axial, 5.8 mm sheet)."""
import sys, json
import numpy as np
from PIL import Image
import metric as MT
from metric import PL, SH, CAM, dog, zrow, xcol
SC = [(1.2, 5.0), (2.0, 8.0), (3.0, 12.0), (5.0, 20.0)]
def regions():
    R = []
    R.append(('back_pelvis', PL, (int(xcol('bald_back', 0.17, True)), int(zrow('bald_back', 1.00)), int(xcol('bald_back', -0.17, True)), int(zrow('bald_back', 0.74))), 'back', None))
    R.append(('back_lowglute', PL, (int(xcol('bald_back', 0.17, True)), int(zrow('bald_back', 0.90)), int(xcol('bald_back', -0.17, True)), int(zrow('bald_back', 0.74))), 'back', None))
    R.append(('front_groin', PL, (int(xcol('bald_front', -0.14)), int(zrow('bald_front', 0.92)), int(xcol('bald_front', 0.14)), int(zrow('bald_front', 0.73))), 'front', None))
    R.append(('q3BL', SH, (730, 480, 880, 600), 'reg_q3BL_700_900_480_620_1', (700, 480)))
    R.append(('q3BR', SH, (1010, 480, 1160, 600), 'reg_q3BR_980_1180_480_620_1', (980, 480)))
    R.append(('left', SH, (775, 160, 830, 235), 'left', None))
    R.append(('right', SH, (1030, 160, 1075, 235), 'right', None))
    return R
def score(tag):
    d = MT.render(tag); out = {}
    for name, img, (x0, y0, x1, y1), rf, off in regions():
        m = np.asarray(Image.open(d / f'{rf}.png').convert('L')).astype('float32')
        for (s1, s2) in SC:
            if off is not None:
                A = dog(img, s1 * (0.7 if img is SH else 1), s2 * (0.6 if img is SH else 1))[y0:y1, x0:x1]; B = dog(m, s1 * 0.7, s2 * 0.6)[y0 - off[1]:y1 - off[1], x0 - off[0]:x1 - off[0]]
            else:
                f = 0.7 if img is SH else 1.0; g = 0.6 if img is SH else 1.0
                A = dog(img, s1 * f, s2 * g)[y0:y1, x0:x1]; B = dog(m, s1 * f, s2 * g)[y0:y1, x0:x1]
            out[(name, s2)] = (float(np.corrcoef(A.ravel(), B.ravel())[0, 1]), float(B.std() / max(A.std(), 1e-6)))
    return out
if __name__ == '__main__':
    tags = sys.argv[1:]; res = {t: score(t) for t in tags}
    names = [r[0] for r in regions()]
    for (s1, s2) in SC:
        print(f'--- DoG sigma {s1}/{s2} px (r / sr) ---')
        print(f'{"":8s}' + ''.join(f'{n:>15s}' for n in names) + f'{"mean r":>9s}')
        for t in tags:
            row = [res[t][(n, s2)] for n in names]; print(f'{t:8s}' + ''.join(f'  {r:+.2f}/{s:4.2f}   ' for r, s in row) + f'  {np.mean([r for r, s in row]):+.3f}')
