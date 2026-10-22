"""lab.py -- preview + metric helpers for the v2 texture pass. Blender's python (numpy) only.

  /Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 lab.py <command> ...
Not a deliverable of the game; evidence/iteration tooling for work/postcard-look/v2/tex.
"""
import os
import sys
import importlib.util

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py'))
gl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gl)
F = np.float32
s2l = gl.s2l
l2s = gl.l2s


def gen(name, shift=(0.0, 0.0)):
    for n, fn, kind, size, tu, tv in gl.MATS:
        if n == name:
            return gl.generate(n, fn, kind, size, extra=shift)
    raise KeyError(name)


def tile(img, n=3):
    return np.tile(img, (n, n, 1))


def down(a, f):
    h, w = a.shape[:2]
    return a[:h - h % f, :w - w % f].reshape(h // f, f, w // f, f, -1).astype(np.float64).mean((1, 3))


def fit(a, w, h=None):
    """box downscale by an integer factor then nearest to w x h (float 0..1 in, out)."""
    h = h or w
    f = max(1, a.shape[0] // h)
    a = down(a, f) if f > 1 else a
    ys = (np.arange(h) * a.shape[0] / h).astype(int); xs = (np.arange(w) * a.shape[1] / w).astype(int)
    return a[ys][:, xs]


def u8(a):
    return np.clip(np.round(np.clip(a, 0, 1) * 255), 0, 255).astype(np.uint8)


def f01(a):
    return a.astype(np.float64) / 255.0


# crater flat-ground light from lit_predict (linear): key (1,.8,.58) 2.3 el32, fill (.62,.55,.9) .55 el35, ambient sky (.34,.24,.40)
def crater_light():
    sys.path.insert(0, HERE)
    import lit_predict as lp
    return np.array(lp.hole_light_linear(lp.parse_lights()[10]))


def lava_game(C, E, mult=(1.2, 1.2, 1.2), albedo_gain=1.0):
    """predicted Game-view colour of the lava: sRGB( clip( lin(C) * L_crater + lin(E) * mult ) ). C,E uint8 (H,W,3)."""
    L = crater_light() * albedo_gain
    lin = s2l(f01(C)) * L + s2l(f01(E)) * np.array(mult)
    return l2s(np.clip(lin, 0, 1))


def persp(tex, T, size=(960, 540), cam_h=8.0, pitch_deg=-9.0, fov_v=60.0, ss=2, offset=(0.0, 0.0), sky=(0.12, 0.08, 0.10)):
    """phone-camera-like view of a flat plane textured with `tex` (float 0..1 sRGB-ish, tile = T metres).
    Camera cam_h above the plane, pitched by pitch_deg (negative = down), vertical FOV fov_v. Mip by pixel footprint."""
    W, H = size
    th = np.tan(np.radians(fov_v) / 2)
    pit = np.radians(pitch_deg); cp, sp = np.cos(pit), np.sin(pit)
    pyr = [tex.astype(np.float64)]
    while pyr[-1].shape[0] > 8:
        pyr.append(down(pyr[-1], 2))
    nl = len(pyr)
    acc = np.zeros((H, W, 3)); cov = np.zeros((H, W))
    for sy in range(ss):
        for sx in range(ss):
            ys = (np.arange(H)[:, None] + (sy + .5) / ss) / H
            xs = (np.arange(W)[None, :] + (sx + .5) / ss) / W
            nx = np.broadcast_to((xs * 2 - 1) * th * (W / H), (H, W))
            ny = np.broadcast_to((1 - ys * 2) * th, (H, W))
            dy = ny * cp + sp; dz = -ny * sp + cp           # forward = (0, sp, cp) for ny = 0
            hit = dy < -1e-4
            t = np.where(hit, cam_h / np.maximum(-dy, 1e-4), 0.0)
            u = ((nx * t + offset[0]) / T) % 1.0; v = ((dz * t + offset[1]) / T) % 1.0
            pxs = (H * ss / 2.0) / th                       # pixels per unit of tangent
            fp = t / pxs / T / np.maximum(-dy, 0.03)        # footprint of one subsample, tile units
            lvl = np.clip(np.log2(np.maximum(fp * tex.shape[1], 1.0)), 0, nl - 1)
            li = np.floor(lvl).astype(int); lf = lvl - li
            lj = np.minimum(li + 1, nl - 1)
            col = np.zeros((H, W, 3))
            for L_ in range(nl):
                for sel, wgt in ((li == L_, 1 - lf), (lj == L_, lf)):
                    if not sel.any():
                        continue
                    img = pyr[L_]; hh, ww = img.shape[:2]
                    ix = np.minimum((u * ww).astype(int), ww - 1); iy = np.minimum(((1 - v) * hh).astype(int), hh - 1)
                    col += img[iy, ix] * (wgt * sel)[..., None]
            acc += np.where(hit[..., None], col, 0.0); cov += hit
    out = acc / (ss * ss)
    hitf = (cov / (ss * ss))[..., None]
    return out + (1 - hitf) * np.array(sky), hitf[..., 0]


def write(path, arr01):
    gl.write_png(path, u8(arr01))


def hstack(imgs, pad=6, bg=0.1):
    h = max(i.shape[0] for i in imgs)
    out = [np.pad(i, ((0, h - i.shape[0]), (0, pad), (0, 0)), constant_values=bg) for i in imgs]
    return np.concatenate(out, 1)


def vstack(imgs, pad=6, bg=0.1):
    w = max(i.shape[1] for i in imgs)
    out = [np.pad(i, ((0, pad), (0, w - i.shape[1]), (0, 0)), constant_values=bg) for i in imgs]
    return np.concatenate(out, 0)


def label(img, txt, scale=2, color=(1, 1, 0.8)):
    img = img.copy()
    gl.text(img, 6, 6, txt, scale, color)
    return img


def lava_stats(game):
    """game: float 0..1 sRGB image. Compares with the main lava pool of crater.jpg (16x16 means / fractions measured 2026-10-04)."""
    g = (game * 255).reshape(-1, 3)
    mx = g.max(1)
    d = dict(mean=tuple(np.round(g.mean(0)).astype(int)), p50=tuple(np.percentile(g, 50, axis=0).astype(int)),
             p95=tuple(np.percentile(g, 95, axis=0).astype(int)),
             dark90=float((mx < 90).mean()), dark50=float((mx < 50).mean()),
             glow=float(((g[:, 0] > 180) & (g[:, 0] > g[:, 1] * 1.15)).mean()),
             yellow=float(((g[:, 0] > 220) & (g[:, 1] > 130)).mean()), cream=float(((g[:, 1] > 200) & (g[:, 2] > 110)).mean()))
    return d


STILL_LAVA = dict(mean=(173, 69, 20), p50=(203, 58, 16), p95=(255, 161, 56), dark90=0.21, dark50=0.11, glow=0.59, yellow=0.10, cream=0.0)


CACHE = os.path.join(ROOT, 'work/postcard-look/v2/tex/.cache')


def load(path):
    """decode a PNG (numpy fallback decoder; cached as .npy keyed by size+mtime)."""
    import hashlib
    os.makedirs(CACHE, exist_ok=True)
    st = os.stat(path)
    key = hashlib.sha1(('%s|%d|%d' % (os.path.abspath(path), st.st_size, int(st.st_mtime))).encode()).hexdigest()[:16]
    f = os.path.join(CACHE, key + '.npy')
    if os.path.exists(f):
        return np.load(f)
    a = gl.read_png(path)
    np.save(f, a)
    return a
