import sys; sys.path.insert(0, '.')
from relcorr import *
from PIL import Image
import numpy as np
def measure(tags):
    c = CAM['bald_front']; mpp = c['metres_per_pixel']; xs = [-0.13, -0.11, -0.09, -0.07, 0.07, 0.09, 0.11, 0.13]; zs = np.arange(1.10, 1.34, 0.005)
    def prof(img):
        a = np.asarray(img.convert('L')).astype('float32'); out = []
        for z in zs:
            row = int(round(c['sole_y'] - z / mpp)); out.append(np.mean([a[row - 1:row + 2, int(round(c['centre_x'] + x / mpp)) - 1:int(round(c['centre_x'] + x / mpp)) + 2].mean() for x in xs]))
        return np.array(out)
    res = {}
    for nm, img in [('plate', PL)] + [(t, Image.open(f'r/{t}sh/front.png')) for t in tags]:
        v = prof(img); lo_m = (zs > 1.12) & (zs < 1.22); up_m = (zs > 1.21) & (zs < 1.30)
        res[nm] = dict(drop_lum=round(float(v[up_m].max() - v[lo_m].min()), 1), crease_z=round(float(zs[lo_m][np.argmin(v[lo_m])]), 3), crest_z=round(float(zs[up_m][np.argmax(v[up_m])]), 3))
    return res
