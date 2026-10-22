"""costb5.py: front-view band-pass comparison of the chest vs the plate (plate-fit light, gain 2.5) + best-fit amplitude scale.
import costb5; costb5.metrics(co) -> dict(rms, g, rms_scaled, ncc, per-region)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import photo3 as ph
from fplate import BALD, S, FRONT_CX, SOLE
BOX = ph.roi_box('front', -0.17, 0.17, 1.08, 1.36)
C0, R0, C1, R1 = BOX
PLATE = np.asarray(BALD[R0:R1, C0:C1]).astype(float)


def bp(a, s=8.0):
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('L')
    return a - np.asarray(im.filter(ImageFilter.GaussianBlur(s))).astype(float)


def render_front(co, gain=2.5):
    L = np.array(ph.LIGHT, dtype=float).copy(); L[1:] *= gain
    N = ph.vertex_normals(co, ph.TRI); sh = ph.shade_vertices(co, N, 'front', L)
    img, mask = ph.raster_shaded(co, sh, 'front', BOX)
    return np.asarray(img, dtype=float), np.asarray(mask) > 0


def roi_mask(shape, x0=-0.100, x1=0.100, z0=1.15, z1=1.30):
    rows, cols = np.mgrid[0:shape[0], 0:shape[1]]
    x = ((cols + C0) - FRONT_CX) * S; z = (SOLE - (rows + R0)) * S
    return (x >= x0) & (x <= x1) & (z >= z0) & (z <= z1), x, z


def metrics(co, gain=2.5, sig=8.0):
    img, mask = render_front(co, gain)
    m, x, z = roi_mask(img.shape); m = m & mask
    bpp = bp(PLATE, sig); bpm = bp(img, sig)
    a, b = bpp[m], bpm[m]
    rms = float(np.sqrt(((b - a) ** 2).mean()))
    g = float((a * b).sum() / max((b * b).sum(), 1e-9))
    rms_s = float(np.sqrt(((g * b - a) ** 2).mean()))
    ncc = float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum()))
    out = dict(rms=rms, g=g, rms_scaled=rms_s, ncc=ncc, plate_std=float(a.std()), model_std=float(b.std()))
    # regions: viewer's-left mound (x<0), viewer's-right mound (x>0), valley |x|<.025, upper (z>1.26), lower (z<1.2)
    for name, mm in (('Lmound', (x < -0.025)), ('Rmound', (x > 0.025)), ('valley', np.abs(x) <= 0.025), ('upper', z > 1.26), ('lower', z < 1.20), ('Lflank', (x < -0.06) & (z > 1.20)), ('Rcres', (x > 0.03) & (z < 1.23))):
        k = m & mm
        out['rms_' + name] = float(np.sqrt(((bpm[k] - bpp[k]) ** 2).mean()))
    return out


def ring_fracs(img, centres=((0.075, 1.225), (-0.075, 1.225)), radii=(0.035, 0.045, 0.055, 0.065), thr=5.0, n=72):
    """closed-rim detector on the numpy front render (same idea as ring5): fraction of the circle (radius r about each mound centre) darker than the centre by thr; returns (max upper-half fraction, max whole-circle fraction)"""
    def lum(x, z, hw=1):
        col = int(round(FRONT_CX + x / S)) - C0; row = int(round(SOLE - z / S)) - R0
        return img[max(row - hw, 0):row + hw + 1, max(col - hw, 0):col + hw + 1].mean()
    up_max, all_max = 0.0, 0.0
    for r in radii:
        fu, fa = [], []
        for xc, zc in centres:
            L0 = np.mean([lum(xc + 0.012 * np.cos(t), zc + 0.012 * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 8, endpoint=False)])
            th = np.linspace(0, 2 * np.pi, n, endpoint=False)
            L = np.array([lum(xc + r * np.cos(t), zc + r * np.sin(t)) for t in th])
            dark = L < L0 - thr
            up = (th > np.radians(15)) & (th < np.radians(165))
            fu.append(dark[up].mean()); fa.append(dark.mean())
        up_max = max(up_max, float(np.mean(fu))); all_max = max(all_max, float(np.mean(fa)))
    return up_max, all_max


if __name__ == '__main__':
    for p in sys.argv[1:]:
        r = metrics(np.load(p).astype(np.float64))
        print(os.path.basename(p), ' '.join(f'{k}={v:.2f}' for k, v in r.items()))
