"""Form-fidelity metric: Pearson r of band-passed (DoG) luminance, plate vs clay render, inside the torso mask.
python3.13 relcorr.py <clay dir tag> [<tag2> ...]   (needs r/<tag>/front.png, back.png from rt.py ... clay)"""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
PL = Image.open(R / 'ArtDir/hero/base_lock/male_body_plain.jpg').convert('L')
CAM = {c['name']: c for c in json.load(open(R / 'work/male-silhouette/reference-cameras.json'))['views']}
def blur(a, s):
    r = int(3 * s + 1); k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2); k /= k.sum()
    p = np.pad(a, ((r, r), (r, r)), mode='edge')
    t = np.apply_along_axis(lambda v: np.convolve(v, k, 'valid'), 1, p)
    return np.apply_along_axis(lambda v: np.convolve(v, k, 'valid'), 0, t)
def dog(img, s1=1.6, s2=9.0):
    a = np.asarray(img).astype('float32'); return blur(a, s1) - blur(a, s2)
def torso_mask(view, z0=0.80, z1=1.36, xhalf=0.165):
    """box mask in plate pixel coords: |x| < xhalf, z in [z0, z1]"""
    c = CAM['bald_' + view]; mpp = c['metres_per_pixel']; m = np.zeros((720, 1280), bool)
    ya, yb = int(c['sole_y'] - z1 / mpp), int(c['sole_y'] - z0 / mpp); xa, xb = int(c['centre_x'] - xhalf / mpp), int(c['centre_x'] + xhalf / mpp)
    m[ya:yb, xa:xb] = True; return m
def corr(view, tag, k=1.0):
    mesh = Image.open(R / f'work/male-parallel-torso/r/{tag}/{view}.png').convert('L')
    a, b = dog(PL), dog(mesh); m = torso_mask(view)
    x, y = a[m], b[m]; return float(np.corrcoef(x, y)[0, 1])
if __name__ == '__main__':
    out = {}
    for t in sys.argv[1:]:
        out[t] = {v: round(corr(v, t), 4) for v in ('front', 'back')}; print(t, out[t])
