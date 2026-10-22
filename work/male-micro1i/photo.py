"""Photometric comparison: camera-space normal map (EXR) vs plate luminance.  Runs in Blender's python (bpy for EXR) with PYTHONPATH=pylib.
blender -b --factory-startup --python photo.py -- <nrmdir> <outdir> [views]"""
import sys, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
from pathlib import Path
import numpy as np
import bpy
from PIL import Image
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
K = H.K
PLATE = Image.open(R / 'ArtDir/hero/base_lock/male_head_detail.jpg').convert('L')
BOX = {'front': (5, 62, 433, 352), 'left': (433, 62, 834, 352), 'right': (834, 62, 1271, 352), 'q3L': (5, 390, 433, 668), 'q3R': (433, 390, 834, 668)}
# dome-only pixel boxes (panel px: r0, r1, c0, c1)  (from shade2.py)
DOME = {'front': (16, 66, 170, 275), 'q3L': (14, 66, 160, 262), 'q3R': (14, 66, 140, 252), 'left': (16, 70, 130, 270), 'right': (16, 70, 130, 270)}
FACE = {'front': (145, 120, 305, 300), 'q3L': (130, 440, 315, 620), 'q3R': (520, 440, 740, 620), 'left': (470, 100, 640, 300), 'right': (900, 100, 1080, 300)}


def load_exr(path):
    img = bpy.data.images.load(str(path), check_existing=False)
    w, h = img.size
    a = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(a); a = a.reshape(h, w, 4)[::-1]
    bpy.data.images.remove(img)
    return a


def load_normals(path):
    a = load_exr(path)
    n = a[..., :3] * 2 - 1
    n[..., 2] *= -1.0          # Eevee camera-space z points away from the camera; flip so +z = toward the camera
    m = a[..., 3] > 0.5
    ln = np.linalg.norm(n, axis=2, keepdims=True)
    n = n / np.maximum(ln, 1e-6)
    return n, m


def light_vec(az, el):
    """camera-space unit vector toward the light: az (deg, +right), el (deg, +up); camera looks down -z (z toward camera)"""
    a = math.radians(az); e = math.radians(el)
    return np.array([math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e)])


def plate_lum(name, up=2):
    box = BOX[name]
    p = PLATE.crop(box)
    return np.asarray(p.resize((p.width * up, p.height * up), Image.LANCZOS)).astype(float)


def fit_light(N, mask, lum, name, up=2, azs=range(-80, 81, 4), els=range(-20, 81, 4)):
    r0, r1, c0, c1 = [v * up for v in DOME[name]]
    # DOME is given as (r0,r1,c0,c1) in panel px
    m = mask[r0:r1, c0:c1]; Ns = N[r0:r1, c0:c1][m]; Ls = lum[r0:r1, c0:c1][m]
    best = None
    for az in azs:
        for el in els:
            l = light_vec(az, el)
            s = np.clip(Ns @ l, 0, None)
            A = np.stack([np.ones_like(s), s], axis=1)
            sol = np.linalg.lstsq(A, Ls, rcond=None)[0]
            rms = np.sqrt(np.mean((A @ sol - Ls) ** 2))
            if best is None or rms < best[0]: best = (rms, az, el, sol[0], sol[1])
    return best


def lowpass(a, sig):
    k = int(max(1, round(sig * 3)))
    xs = np.arange(-k, k + 1); g = np.exp(-0.5 * (xs / sig) ** 2); g /= g.sum()
    a = np.apply_along_axis(lambda v: np.convolve(np.pad(v, k, mode='edge'), g, mode='valid'), 0, a)
    a = np.apply_along_axis(lambda v: np.convolve(np.pad(v, k, mode='edge'), g, mode='valid'), 1, a)
    return a


def sheet(name, nrm_dir, out_dir, up=2, light=None):
    N, m = load_normals(Path(nrm_dir) / f'{name}_nrm.exr')
    lum = plate_lum(name, up)
    assert N.shape[:2] == lum.shape, (N.shape, lum.shape)
    if light is None:
        rms, az, el, a, b = fit_light(N, m, lum, name, up)
        print(f'{name}: light az {az} el {el}  a {a:.1f} b {b:.1f}  dome rms {rms:.2f}')
    else:
        az, el, a, b = light
    l = light_vec(az, el)
    pred = a + b * np.clip(N @ l, 0, None)
    res = lum - pred
    fx0, fy0, fx1, fy1 = FACE[name]; bx = BOX[name]
    sl = (slice((fy0 - bx[1]) * up, (fy1 - bx[1]) * up), slice((fx0 - bx[0]) * up, (fx1 - bx[0]) * up))

    def g(arr, mask=None):
        im = np.clip(arr, 0, 255).astype(np.uint8)
        if mask is not None: im = np.where(mask, im, 40).astype(np.uint8)
        return np.stack([im] * 3, axis=2)
    rr = np.clip(res / 50.0, -1, 1)
    rgb = np.zeros(res.shape + (3,))
    rgb[..., 0] = np.where(rr > 0, 255, 255 * (1 + rr)); rgb[..., 1] = 255 * (1 - np.abs(rr)); rgb[..., 2] = np.where(rr < 0, 255, 255 * (1 - rr))
    rgb[~m] = 40
    tiles = [g(lum)[sl], g(pred, m)[sl], rgb.astype(np.uint8)[sl]]
    Hh, Ww = tiles[0].shape[:2]
    S = np.zeros((Hh, Ww * 3 + 20, 3), np.uint8)
    for i, t in enumerate(tiles): S[:, i * (Ww + 10):i * (Ww + 10) + Ww] = t
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    Image.fromarray(S).save(Path(out_dir) / f'photo_{name}.png')
    return (az, el, a, b), res, m


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:]
    nd, od = argv[0], argv[1]
    views = argv[2].split(',') if len(argv) > 2 else ['front', 'q3L', 'q3R', 'left']
    for v in views:
        sheet(v, nd, od)
