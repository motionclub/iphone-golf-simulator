"""Vertical luminance profiles through the glutes in the back view: plate vs render(s), at |x| columns.  python3 lumprof.py out.png tag... (renders from r/<tag>_c/back@4.png)"""
import sys, json, numpy as np
from PIL import Image, ImageDraw, ImageFont
import crop_cmp as CC
W = CC.W; R = CC.R
c = CC.CAM['bald_back']; mpp = c['metres_per_pixel']; cx = c['centre_x']; sy = c['sole_y']
PL = np.asarray(Image.open(R / 'ArtDir/hero/base_lock/male_body_bald.jpg').convert('L')).astype(float)
def blur1(a, s):
    r = int(3 * s + 1); k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2); k /= k.sum(); return np.convolve(np.pad(a, r, mode='edge'), k, 'valid')
def prof(img, K, u, zs, hw=0.006):
    out = []
    for z in zs:
        r0 = (sy - z / mpp) * K; vals = []
        for sgn in (-1, 1):
            cc = (cx + sgn * u / mpp) * K; a = int(round(cc - hw / mpp * K)); b = int(round(cc + hw / mpp * K)) + 1
            vals.append(img[int(round(r0)), a:b].mean())
        out.append(np.mean(vals))
    return np.array(out)
if __name__ == '__main__':
    out = sys.argv[1]; tags = sys.argv[2:]
    zs = np.arange(0.74, 1.00, 0.002); us = [0.0, 0.03, 0.055, 0.09, 0.13]
    F = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 14)
    Wd, Hd = 1700, 520; im = Image.new('RGB', (Wd, Hd), (22, 22, 26)); d = ImageDraw.Draw(im)
    for ui, u in enumerate(us):
        x0 = 20 + ui * 335; pw = 300
        d.rectangle([x0, 30, x0 + pw, Hd - 40], outline=(60, 60, 80)); d.text((x0 + 6, 8), f'|x| = {u*1000:.0f} mm', fill=(255, 205, 70), font=F)
        for z in np.arange(0.76, 1.0, 0.04): yy = 30 + (1.0 - z) / 0.26 * (Hd - 70); d.line([(x0, yy), (x0 + pw, yy)], fill=(44, 44, 62)); d.text((x0 + 2, yy - 14), f'{z:.2f}', fill=(120, 120, 160), font=F)
        curves = [('PLATE', prof(PL, 1, u, zs), (255, 205, 70))]
        for ti, t in enumerate(tags):
            im_ = np.asarray(Image.open(W / f'r/{t}_c/back@4.png').convert('L')).astype(float); curves.append((t, prof(im_, 4, u, zs), [(110, 190, 255), (110, 255, 150), (255, 120, 120)][ti % 3]))
        for nm, cv, col in curves:
            cv = blur1(cv, 2.0); lo, hi = np.percentile(cv, 2), np.percentile(cv, 98); n = (cv - lo) / max(hi - lo, 1e-6)
            pts = [(x0 + 10 + n[i] * (pw - 20), 30 + (1.0 - zs[i]) / 0.26 * (Hd - 70)) for i in range(len(zs))]
            d.line(pts, fill=col, width=2)
            if ui == 0: d.text((x0 + 8, Hd - 36 + 0), '', fill=col, font=F)
    for ti, (nm, col) in enumerate([('PLATE', (255, 205, 70))] + [(t, [(110, 190, 255), (110, 255, 150), (255, 120, 120)][i % 3]) for i, t in enumerate(tags)]): d.text((20 + ti * 160, Hd - 22), nm, fill=col, font=F)
    im.save(out); print(out)
