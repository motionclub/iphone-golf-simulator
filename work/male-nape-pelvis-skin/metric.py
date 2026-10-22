"""Band-pass correlation (plate vs clay render) in the glute/pelvis regions of the locked back/front views and the 3/4 panels.
python3.13 metric.py <tag> [<tag>...]   (renders into r/<tag>_m/ if missing; uses data/V_<tag>.npy or 'start')"""
import sys, json, subprocess, os
from pathlib import Path
import numpy as np
from PIL import Image
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-nape-pelvis-skin'); R = W.parent.parent
PL = np.asarray(Image.open(R / 'ArtDir/hero/base_lock/male_body_plain.jpg').convert('L')).astype('float32')
SH = np.asarray(Image.open(R / 'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('L')).astype('float32')
CAM = {c['name']: c for c in json.load(open(R / 'work/male-silhouette/reference-cameras.json'))['views']}
def blur(a, s):
    r = int(3 * s + 1); k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2); k /= k.sum(); p = np.pad(a, ((r, r), (r, r)), mode='edge')
    t = np.apply_along_axis(lambda v: np.convolve(v, k, 'valid'), 1, p); return np.apply_along_axis(lambda v: np.convolve(v, k, 'valid'), 0, t)
def dog(a, s1, s2): return blur(a, s1) - blur(a, s2)
# regions: (name, plate image, box in plate px (x0,y0,x1,y1), render file, render crop offset/size, sigmas)
def zrow(view, z): c = CAM[view]; return c['sole_y'] - z / c['metres_per_pixel']
def xcol(view, x, back=False): c = CAM[view]; return c['centre_x'] + (-x if back else x) / c['metres_per_pixel']
REG = []
cb = CAM['bald_back']; cf = CAM['bald_front']
REG.append(('back_glute', PL, (int(xcol('bald_back', 0.14, True)), int(zrow('bald_back', 0.98)), int(xcol('bald_back', -0.14, True)), int(zrow('bald_back', 0.78))), 'back', None, (1.2, 5.0)))
REG.append(('back_lumbar', PL, (int(xcol('bald_back', 0.14, True)), int(zrow('bald_back', 1.12)), int(xcol('bald_back', -0.14, True)), int(zrow('bald_back', 0.98))), 'back', None, (1.2, 5.0)))
REG.append(('front_groin', PL, (int(xcol('bald_front', -0.14)), int(zrow('bald_front', 0.90)), int(xcol('bald_front', 0.14)), int(zrow('bald_front', 0.76))), 'front', None, (1.2, 5.0)))
REG.append(('q3BL_glute', SH, (745, 505, 850, 590), 'reg_q3BL_700_900_480_620_1', (700, 480), (0.8, 3.0)))
REG.append(('q3BR_glute', SH, (1025, 505, 1130, 590), 'reg_q3BR_980_1180_480_620_1', (980, 480), (0.8, 3.0)))
REG.append(('left_glute', SH, (788, 172, 822, 216), 'left', None, (0.8, 3.0)))
REG.append(('right_glute', SH, (1026, 172, 1060, 216), 'right', None, (0.8, 3.0)))
VIEWS = 'back,front,left,right,reg_q3BL_700_900_480_620_1,reg_q3BR_980_1180_480_620_1'
def render(tag):
    d = W / f'r/{tag}_m'
    if (d / 'back.png').exists() and (d / 'left.png').exists() and (d / 'reg_q3BR_980_1180_480_620_1.png').exists(): return d
    src = f'data/V_{tag}.npy' if tag != 'start' else 'baseline/HeroBase_Male_Silhouette.blend'
    env = dict(os.environ, PYTHONPATH=str(R / 'work/male-micro1i/pylib'))
    subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', '--python', 'rig.py', '--', src, f'r/{tag}_m', VIEWS, 'clay'], cwd=W, env=env, capture_output=True)
    return d
def score(tag):
    d = render(tag); out = {}
    for name, img, (x0, y0, x1, y1), rf, off, (s1, s2) in REG:
        m = np.asarray(Image.open(d / f'{rf}.png').convert('L')).astype('float32')
        if off is not None:   # registered crop render: its pixel (0,0) is sheet pixel off
            a = img[y0:y1, x0:x1]; b = m[y0 - off[1]:y1 - off[1], x0 - off[0]:x1 - off[0]]
            A = dog(img, s1, s2)[y0:y1, x0:x1]; B = dog(m, s1, s2)[y0 - off[1]:y1 - off[1], x0 - off[0]:x1 - off[0]]
        else:
            A = dog(img, s1, s2)[y0:y1, x0:x1]; B = dog(m, s1, s2)[y0:y1, x0:x1]
        out[name] = float(np.corrcoef(A.ravel(), B.ravel())[0, 1]); out[name + '_sr'] = float(B.std() / max(A.std(), 1e-6))   # std_ratio of the band-passed images (render / plate)
    return out
if __name__ == '__main__':
    for t in sys.argv[1:]:
        r = score(t); rr = {k: v for k, v in r.items() if not k.endswith('_sr')}; print(f'{t:8s} ' + ' '.join(f'{k} {v:+.3f}' for k, v in rr.items()) + '   SR ' + ' '.join(f'{k[:-3]} {v:.2f}' for k, v in r.items() if k.endswith('_sr')) + f'   MEAN {np.mean(list(rr.values())):+.3f}')
