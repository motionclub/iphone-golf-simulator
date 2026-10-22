"""Shape-from-shading relief of the plate (oblique light, Tikhonov-regularised directional-derivative inversion in Fourier space).
python3 tools/sfs3.py chest|pelvis out.png [lx lz]"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from viz3 import *
from fplate import BALD, S, FRONT_CX, BACK_CX, SOLE

def region(view, x0, x1, z0, z1):
    """crop of the bald plate (float) in model coords; returns img, xs (model x per column), zs (model z per row)"""
    cx = FRONT_CX if view == 'front' else BACK_CX
    sgn = 1 if view == 'front' else -1
    c0 = int(round(cx + sgn * x0 / S)); c1 = int(round(cx + sgn * x1 / S))
    ca, cb = sorted([c0, c1])
    r0 = int(round(SOLE - z1 / S)); r1 = int(round(SOLE - z0 / S))
    img = BALD[r0:r1, ca:cb + 1].copy()
    cols = np.arange(ca, cb + 1)
    xs = sgn * (cols - cx) * S
    zs = (SOLE - np.arange(r0, r1)) * S
    return img, xs, zs

def highpass(a, s):
    from viz3 import _gblur_np
    return a - _gblur_np(a, s)

def sfs(img, lx, lz, hp_sigma_px=18, eps=0.15, pix=S):
    """img: luminance (rows = down).  returns relief h (m per unit k, arbitrary scale) with +z up rows flipped back.
    model: dI = k*(sx*h_x - sz*h_z), x to the viewer's right (columns), z up (rows reversed)."""
    B = highpass(img.astype(float), hp_sigma_px)
    H, W = B.shape
    # pad to reduce wrap
    pad = 24
    Bp = np.pad(B, pad, mode='reflect')
    ky = np.fft.fftfreq(Bp.shape[0]) * 2 * np.pi        # rows (down)
    kx = np.fft.fftfreq(Bp.shape[1]) * 2 * np.pi
    KX, KY = np.meshgrid(kx, ky)
    # rows go down => d/dz = -d/drow.  dI = sx*dh/dx - sz*dh/dz = sx*dh/dcol + sz*dh/drow
    A = 1j * (lx * KX + lz * KY)
    F = np.fft.fft2(Bp)
    Hh = F * np.conj(A) / (np.abs(A) ** 2 + eps * (KX ** 2 + KY ** 2) + 1e-9)
    h = np.real(np.fft.ifft2(Hh))[pad:-pad, pad:-pad]
    return h * pix        # h in (pixels of intensity)*(m/px): relative

if __name__ == '__main__':
    part = sys.argv[1]; out = sys.argv[2]
    lx = float(sys.argv[3]) if len(sys.argv) > 3 else 0.44
    lz = float(sys.argv[4]) if len(sys.argv) > 4 else 0.62
    if part == 'chest':
        img, xs, zs = region('front', -0.17, 0.17, 1.05, 1.38)
    else:
        img, xs, zs = region('back', -0.20, 0.20, 0.74, 1.06)
    h = sfs(img, lx, lz)
    h = h - np.median(h)
    lo, hi = np.percentile(h, 2), np.percentile(h, 98)
    g = np.clip((h - lo) / (hi - lo), 0, 1)
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((g.shape[1] * 4, g.shape[0] * 4), Image.BICUBIC).convert('RGB')
    src = Image.fromarray(img.astype(np.uint8)).resize(im.size, Image.BICUBIC).convert('RGB')
    strip([src, im], ['plate', f'SfS relief (l=({lx},{lz}))']).save(out)
    print(out, 'relief range', lo, hi)
