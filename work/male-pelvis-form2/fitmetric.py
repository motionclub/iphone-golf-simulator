"""Fit metric: multi-view, multi-scale band-pass similarity between the plate and rig renders (standard rig, 'manneq' look).
render_fit(tag, src) renders margin crops of the views into r/<tag>_f/ ; score(tag) -> dict of per-view/per-scale correlations and the scalar loss."""
import os, sys, json, subprocess
import numpy as np
from pathlib import Path
from PIL import Image
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-pelvis-form2'); R = W.parent.parent
CAMS = {c['name']: c for c in json.load(open(R / 'work/male-silhouette/reference-cameras.json'))['views']}
PLATE_MAIN = np.asarray(Image.open(R / 'ArtDir/hero/base_lock/male_body_bald.jpg').convert('L')).astype('float32')
PLATE_SHEET = np.asarray(Image.open(R / 'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('L')).astype('float32')
def blur(a, s):
    r = int(3 * s + 1); k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2); k /= k.sum(); p = np.pad(a, ((r, r), (r, r)), mode='edge')
    t = np.apply_along_axis(lambda v: np.convolve(v, k, 'valid'), 1, p); return np.apply_along_axis(lambda v: np.convolve(v, k, 'valid'), 0, t)
def dog(a, s1, s2): return blur(a, s1) - blur(a, s2)
# views: name -> (rig view spec builder, plate image, margin box (x0,y0,x1,y1) in source px, ROI box in source px, magnification, sigma factor, weight)
def axroi(view, z0, z1, xh):
    c = CAMS['bald_' + view]; mpp = c['metres_per_pixel']; cx = c['centre_x']; sy = c['sole_y']
    return (int(cx - xh / mpp), int(sy - z1 / mpp), int(cx + xh / mpp), int(sy - z0 / mpp))
def axmargin(roi, m=34): return (roi[0] - m, roi[1] - m, roi[2] + m, roi[3] + m)
ROI_BACK = axroi('back', 0.745, 1.00, 0.17); ROI_FRONT = axroi('front', 0.745, 0.95, 0.15)
VIEWS = {
    'back':  dict(spec='back@{m}:{b}', plate=PLATE_MAIN, margin=axmargin(ROI_BACK), roi=ROI_BACK, m=3, f=1.0, w=1.0),
    'bl':    dict(spec='reg_q3BL_{b}_{m}', plate=PLATE_SHEET, margin=(715, 465, 895, 630), roi=(735, 495, 870, 600), m=3, f=0.7, w=0.7),
    'br':    dict(spec='reg_q3BR_{b}_{m}', plate=PLATE_SHEET, margin=(990, 465, 1170, 630), roi=(1010, 495, 1145, 600), m=3, f=0.7, w=0.7),
    'left':  dict(spec='left@{m}:{b}', plate=PLATE_SHEET, margin=(745, 130, 865, 260), roi=(772, 160, 832, 238), m=3, f=0.7, w=0.5),
    'right': dict(spec='right@{m}:{b}', plate=PLATE_SHEET, margin=(1000, 130, 1110, 260), roi=(1028, 160, 1078, 238), m=3, f=0.7, w=0.5),
    'front': dict(spec='front@{m}:{b}', plate=PLATE_MAIN, margin=axmargin(ROI_FRONT), roi=ROI_FRONT, m=3, f=1.0, w=1.0),
    'fl':    dict(spec='reg_q3FL_{b}_{m}', plate=PLATE_SHEET, margin=(95, 450, 275, 615), roi=(125, 480, 245, 590), m=3, f=0.7, w=0.7),
    'fr':    dict(spec='reg_q3FR_{b}_{m}', plate=PLATE_SHEET, margin=(390, 450, 570, 615), roi=(420, 480, 540, 590), m=3, f=0.7, w=0.7),
}
SCALES = [(1.5, 6.0), (2.5, 10.0), (4.0, 16.0)]
def vspec(name):
    v = VIEWS[name]; x0, y0, x1, y1 = v['margin']
    if name in ('bl', 'br', 'fl', 'fr'): return v['spec'].format(b=f'{x0}_{x1}_{y0}_{y1}', m=v['m'])      # reg_<panel>_c0_c1_r0_r1_mag
    return v['spec'].format(b=f'{x0}_{y0}_{x1}_{y1}', m=v['m'])
def fname(name): return vspec(name)
def render_fit(tag, names, src=None, look='manneq', light=None, suffix=''):
    src = src or (f'data/V_{tag}.npy' if tag != 'start' else 'baseline/HeroBase_Male_Silhouette.blend')
    env = dict(os.environ, PYTHONPATH=str(R / 'work/male-micro1i/pylib'))
    if light: env['GRAZE'] = light
    specs = []
    for n in names:
        v = VIEWS[n]
        if n in ('left', 'right'): x0, y0, x1, y1 = v['margin']; specs.append(f'{n}@{v["m"]}:{x0}_{y0}_{x1}_{y1}')
        else: specs.append(vspec(n))
    r = subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', '--python', 'rig.py', '--', src, f'r/{tag}_f{suffix}', ','.join(specs), look, '0.886,0.627,0.431'], cwd=W, env=env, capture_output=True, text=True)
    if 'Traceback' in r.stdout or 'Error' in r.stderr[-300:]: print(r.stdout[-1200:], r.stderr[-600:], file=sys.stderr)
_plate_cache = {}
def plate_bp(name, s1, s2):
    key = (name, s1, s2)
    if key not in _plate_cache:
        v = VIEWS[name]; x0, y0, x1, y1 = v['margin']; img = v['plate'][y0:y1, x0:x1]; _plate_cache[key] = dog(img, s1 * v['f'], s2 * v['f'] * (0.6 / 0.7 if v['f'] < 1 else 1))
    return _plate_cache[key]
def load_render(tag, name, suffix=''):
    v = VIEWS[name]; fn = fname(name)
    im = np.asarray(Image.open(W / f'r/{tag}_f{suffix}/{fn}.png').convert('L')).astype('float32'); m = v['m']
    H, Wd = im.shape; x0, y0, x1, y1 = v['margin']; h1, w1 = y1 - y0, x1 - x0
    im = im[:h1 * m, :w1 * m].reshape(h1, m, w1, m).mean(axis=(1, 3)); return im
def view_score(tag, name, suffix=''):
    v = VIEWS[name]; x0, y0, x1, y1 = v['margin']; rx0, ry0, rx1, ry1 = v['roi']
    img = load_render(tag, name, suffix); out = []
    for (s1, s2) in SCALES:
        s2b = s2 * (0.6 / 0.7 if v['f'] < 1 else 1)
        A = plate_bp(name, s1, s2)[ry0 - y0:ry1 - y0, rx0 - x0:rx1 - x0]; B = dog(img, s1 * v['f'], s2 * v['f'] * (0.6 / 0.7 if v['f'] < 1 else 1))[ry0 - y0:ry1 - y0, rx0 - x0:rx1 - x0]
        r = float(np.corrcoef(A.ravel(), B.ravel())[0, 1]); sr = float(B.std() / max(A.std(), 1e-6)); out.append((r, sr))
    return out
def score(tag, names, suffix=''):
    res = {}; loss = 0.0; wsum = 0.0
    for n in names:
        sc = view_score(tag, n, suffix); res[n] = sc; w = VIEWS[n]['w']
        loss += w * sum((1 - r) + 0.15 * abs(np.log(max(sr, 1e-3))) for r, sr in sc) / len(sc); wsum += w
    return loss / wsum, res
if __name__ == '__main__':
    names = sys.argv[2].split(',') if len(sys.argv) > 2 else ['back', 'bl', 'br', 'left', 'right']
    RELIT = '0.35,0.55,0.65'
    for tag in sys.argv[1].split(','):
        for suf, light in (('', None), ('h', RELIT)):
            render_fit(tag, names, light=light, suffix=suf); L, res = score(tag, names, suf)
            print(f'{tag:8s}{"(hi-key)" if suf else "(std)   "} loss {L:.4f}  ' + '  '.join(f'{n}: ' + '/'.join(f'{r:+.2f}' for r, sr in res[n]) + ' sr ' + '/'.join(f'{sr:.2f}' for r, sr in res[n]) for n in names))
