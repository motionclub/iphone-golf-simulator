"""lattice.py IMG MASKIMG : periodicity of the glow lattice on the wall = mean over wall rows of the highest normalised autocorrelation (lags 3..40 px) of the
high-passed luminance of the 'rock' (blue in the mask) pixels of that row. A regular dash lattice ('windows / ladders') scores high, irregular embers low."""
import sys
import numpy as np
from PIL import Image
def lattice(img, mask, lag=(3, 40), min_px=400):
    a = np.asarray(Image.open(img).convert("RGB")).astype(np.float32)
    lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    m = np.asarray(Image.open(mask).convert("RGB")).astype(np.float32)
    rock = (m[..., 2] > 150) & (m[..., 0] < 100) & (m[..., 1] < 100)
    peaks = []
    for y in range(lum.shape[0]):
        xs = np.where(rock[y])[0]
        if len(xs) < min_px:
            continue
        # longest contiguous run
        d = np.diff(xs)
        cuts = np.where(d > 1)[0]
        runs = np.split(xs, cuts + 1)
        r = max(runs, key=len)
        if len(r) < min_px:
            continue
        v = lum[y, r[0]:r[-1] + 1]
        k = np.ones(9) / 9.0
        hp = v - np.convolve(v, k, mode="same")
        hp = hp[8:-8]
        if hp.std() < 1e-3:
            continue
        hp = hp - hp.mean()
        ac = np.correlate(hp, hp, mode="full")[len(hp) - 1:]
        ac = ac / ac[0]
        peaks.append(float(ac[lag[0]:lag[1]].max()))
    return (float(np.mean(peaks)) if peaks else float("nan")), len(peaks)
if __name__ == "__main__":
    v, n = lattice(sys.argv[1], sys.argv[2])
    print(f"lattice peak {v:.3f} over {n} wall rows")
