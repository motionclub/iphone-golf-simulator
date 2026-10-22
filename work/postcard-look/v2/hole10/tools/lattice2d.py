"""lattice2d.py IMG MASKIMG [rows y0 y1] : 2D autocorrelation peak (offsets 4..64 px, outside the central lobe) of the high-passed luminance of a wall patch
(the widest all-rock column range over the given rows). Regular glow lattice -> high, irregular embers -> low."""
import sys
import numpy as np
from PIL import Image
def patch(img, mask, y0, y1):
    a = np.asarray(Image.open(img).convert("RGB")).astype(np.float32)
    lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    m = np.asarray(Image.open(mask).convert("RGB")).astype(np.float32)
    rock = (m[..., 2] > 150) & (m[..., 0] < 100) & (m[..., 1] < 100)
    allrock = rock[y0:y1].all(axis=0)
    xs = np.where(allrock)[0]
    if len(xs) < 64:
        return None
    cuts = np.where(np.diff(xs) > 1)[0]
    runs = np.split(xs, cuts + 1)
    r = max(runs, key=len)
    return lum[y0:y1, r[0]:r[-1] + 1]
def lattice2d(img, mask, y0, y1):
    p = patch(img, mask, y0, y1)
    if p is None or p.shape[1] < 96 or p.shape[0] < 48:
        return float("nan"), None
    from numpy.fft import rfft2, irfft2
    # high-pass: subtract an 11x11 box mean
    k = 11
    c = np.cumsum(np.cumsum(np.pad(p, ((k, k), (k, k)), mode="edge"), 0), 1)
    box = (c[2 * k:, 2 * k:] - c[:-2 * k, 2 * k:] - c[2 * k:, :-2 * k] + c[:-2 * k, :-2 * k]) / (2 * k) ** 2
    hp = p - box[:p.shape[0], :p.shape[1]]
    hp = hp - hp.mean()
    F = rfft2(hp, s=(hp.shape[0] * 2, hp.shape[1] * 2))
    ac = irfft2(np.abs(F) ** 2)
    ac = ac / ac[0, 0]
    H, W = hp.shape
    best = 0.0
    for dy in range(0, min(64, H // 2)):
        for dx in range(0, min(64, W // 2)):
            if dx * dx + dy * dy < 16:
                continue
            best = max(best, float(ac[dy, dx]))
    return best, p.shape
if __name__ == "__main__":
    y0, y1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (400, 500)
    print(lattice2d(sys.argv[1], sys.argv[2], y0, y1))
