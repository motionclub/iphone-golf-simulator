"""Luminance-profile descriptors of the butt in the MAIN back view (plate vs rig render), used as a numeric/visual objective.
 H(z): horizontal profile across the cleft at heights z: dip% = (shoulder - centre)/shoulder, with shoulder = mean L at |x| in [0.030,0.045] and the profile shape
 V(u): vertical profiles at |x| = u, normalised to the value at z=0.93 (above the lobes) from z=0.74..0.93
python3 prof.py show <tag...>  -> prints tables ; module API: descriptors(img_back4)"""
import sys, json, numpy as np
from PIL import Image
import crop_cmp as CC
W = CC.W; R = CC.R
c = CC.CAM['bald_back']; mpp = c['metres_per_pixel']; cx = c['centre_x']; sy = c['sole_y']
PL = np.asarray(Image.open(R / 'ArtDir/hero/base_lock/male_body_bald.jpg').convert('L')).astype(float)
def blur1(a, s):
    r = int(3 * s + 1); k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2); k /= k.sum(); return np.convolve(np.pad(a, r, mode='edge'), k, 'valid')
def lum_at(img, K, x, z, hx=0.0025, hz=0.0025):
    """mean luminance in a small box around (x, z); back view: image column = cx - x/mpp"""
    r0 = (sy - (z + hz) / mpp) * K; r1 = (sy - (z - hz) / mpp) * K; c0 = (cx - (x + hx) / mpp) * K; c1 = (cx - (x - hx) / mpp) * K
    return float(img[int(round(r0)):max(int(round(r1)), int(round(r0)) + 1), int(round(c0)):max(int(round(c1)), int(round(c0)) + 1)].mean())
ZH = [0.76, 0.78, 0.80, 0.82, 0.84, 0.86, 0.88, 0.90, 0.92]
XH = np.arange(-0.10, 0.1001, 0.005)
UV = [0.0, 0.03, 0.055, 0.09, 0.13]; ZV = np.arange(0.74, 0.9301, 0.01)
def descriptors(img, K):
    d = {}
    for z in ZH:
        row = np.array([lum_at(img, K, x, z) for x in XH]); sh = 0.5 * (row[(np.abs(XH) >= 0.030) & (np.abs(XH) <= 0.045)].mean()); cen = row[np.abs(XH) <= 0.004].mean()
        d[('H', z)] = dict(dip=(sh - cen) / max(sh, 1.0), row=row / max(sh, 1.0))
    for u in UV:
        col = np.array([0.5 * (lum_at(img, K, u, z) + lum_at(img, K, -u, z)) for z in ZV]); d[('V', u)] = col / max(col[-1], 1.0)
    return d
def load(tag):
    if tag == 'PLATE': return PL, 1
    im = np.asarray(Image.open(W / f'r/{tag}_c/back@4.png').convert('L')).astype(float); return im, 4
if __name__ == '__main__':
    tags = sys.argv[2:]; D = {}
    for t in ['PLATE'] + tags: img, K = load(t); D[t] = descriptors(img, K)
    print('cleft dip % (shoulder-centre)/shoulder at |x|=30-45mm:'); print('z       ' + ''.join(f'{t:>9s}' for t in D))
    for z in ZH: print(f'{z:.2f}   ' + ''.join(f'{100*D[t][("H",z)]["dip"]:9.1f}' for t in D))
    print('\nvertical profile L(z)/L(0.93) at |x| columns:')
    for u in UV:
        print(f'|x|={u*1000:3.0f}mm  z: ' + ' '.join(f'{z:.2f}' for z in ZV[::2]))
        for t in D: print(f'  {t:8s}   ' + ' '.join(f'{v:4.2f}' for v in D[t][('V', u)][::2]))
