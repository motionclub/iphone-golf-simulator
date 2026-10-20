"""Horizontal luminance profiles across the butt in the back view at several heights: plate vs render(s) (x from -0.2 to 0.2).  python3 lumprofx.py out.png tag..."""
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFont
import crop_cmp as CC
W = CC.W; R = CC.R
c = CC.CAM['bald_back']; mpp = c['metres_per_pixel']; cx = c['centre_x']; sy = c['sole_y']
PL = np.asarray(Image.open(R / 'ArtDir/hero/base_lock/male_body_bald.jpg').convert('L')).astype(float)
def blur1(a, s):
    r = int(3 * s + 1); k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2); k /= k.sum(); return np.convolve(np.pad(a, r, mode='edge'), k, 'valid')
def row(img, K, z, xs, hz=0.004):
    out = []
    for x in xs:
        cc = int(round((cx - x / mpp) * K)); vals = [img[int(round((sy - (z + dz) / mpp) * K)), cc] for dz in np.linspace(-hz, hz, 5)]   # back view: image x flips (x>0 = body left = image left)
        out.append(np.mean(vals))
    return np.array(out)
if __name__ == '__main__':
    out = sys.argv[1]; tags = sys.argv[2:]
    zl = [0.78, 0.80, 0.82, 0.84, 0.86, 0.88, 0.90, 0.94]; xs = np.arange(-0.19, 0.1901, 0.002)
    F = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 14)
    cols = 4; rows = 2; pw, ph = 420, 250; im = Image.new('RGB', (cols * (pw + 10) + 10, rows * (ph + 30) + 10), (22, 22, 26)); d = ImageDraw.Draw(im)
    for zi, z in enumerate(zl):
        x0 = 10 + (zi % cols) * (pw + 10); y0 = 30 + (zi // cols) * (ph + 30)
        d.rectangle([x0, y0, x0 + pw, y0 + ph], outline=(60, 60, 80)); d.text((x0 + 4, y0 - 20), f'z = {z:.2f}   (x axis: -0.19 .. +0.19 m, image-left = body left)', fill=(255, 205, 70), font=F)
        d.line([(x0 + pw / 2, y0), (x0 + pw / 2, y0 + ph)], fill=(50, 50, 70))
        curves = [('PLATE', row(PL, 1, z, xs), (255, 205, 70))]
        for ti, t in enumerate(tags):
            im_ = np.asarray(Image.open(W / f'r/{t}_c/back@4.png').convert('L')).astype(float); curves.append((t, row(im_, 4, z, xs), [(110, 190, 255), (110, 255, 150), (255, 120, 120)][ti % 3]))
        for nm, cv, col in curves:
            cv = blur1(cv, 2.0); lo, hi = np.percentile(cv, 5), np.percentile(cv, 99); n = (cv - lo) / max(hi - lo, 1e-6)
            d.line([(x0 + 6 + (i / (len(xs) - 1)) * (pw - 12), y0 + ph - 10 - np.clip(n[i], -0.2, 1.2) * (ph - 30)) for i in range(len(xs))], fill=col, width=2)
    d.text((10, 6), 'PLATE (yellow)  ' + '  '.join(tags), fill=(255, 205, 70), font=F)
    im.save(out); print(out, im.size)
