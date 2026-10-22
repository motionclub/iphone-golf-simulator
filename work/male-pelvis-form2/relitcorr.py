"""Band-pass correlation (plate vs render) in the back-view glute box for the rig pass (_q) and the plate-like top-light pass (_qh).
python3 relitcorr.py tag...   uses r/<tag>_q{,h}/back@4:846_283_985_415.png"""
import sys, numpy as np
from PIL import Image
sys.path.insert(0, '.')
import crop_cmp as CC
from metric import dog
R = CC.R; c = CC.CAM['bald_back']; mpp = c['metres_per_pixel']; cx = c['centre_x']; sy = c['sole_y']
PL = np.asarray(Image.open(R / 'ArtDir/hero/base_lock/male_body_bald.jpg').convert('L')).astype('float32')
X0, Y0, X1, Y1 = 846, 283, 985, 415
def load(tag, h):
    im = Image.open(f'r/{tag}_q{"h" if h else ""}/back@4:{X0}_{Y0}_{X1}_{Y1}.png').convert('L')
    im = im.resize(((X1 - X0), (Y1 - Y0)), Image.BOX); full = np.zeros_like(PL); full[Y0:Y1, X0:X1] = np.asarray(im).astype('float32'); return full
def box(z0, z1, xh):
    return int(cx - xh / mpp), int(sy - z1 / mpp), int(cx + xh / mpp), int(sy - z0 / mpp)
BOXES = {'lowglute z.76-.90 |x|<.15': box(0.76, 0.90, 0.15), 'glute z.76-.96 |x|<.17': box(0.76, 0.96, 0.17), 'pelvis z.74-1.00 |x|<.17': box(0.74, 1.00, 0.17)}
SC = [(1.2, 5.0), (2.0, 8.0), (3.0, 12.0), (5.0, 20.0)]
if __name__ == '__main__':
    tags = sys.argv[1:]
    for h in (0, 1):
        print('=== lighting pass:', 'plate-like top light (_qh)' if h else 'Unity-like rig (_q)')
        for bn, (x0, y0, x1, y1) in BOXES.items():
            print('  box', bn)
            for (s1, s2) in SC:
                A = dog(PL, s1, s2)[y0:y1, x0:x1]; row = []
                for t in tags:
                    B = dog(load(t, h), s1, s2)[y0:y1, x0:x1]; row.append(f'{t} {np.corrcoef(A.ravel(), B.ravel())[0, 1]:+.2f}/{B.std() / A.std():.2f}')
                print(f'    DoG {s1}/{s2}: ' + '   '.join(row))
