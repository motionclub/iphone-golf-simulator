# ref_match.py — objective half of the REF_MATCH and NO_EMPTY_VIEW gates (Adnan's eye stays final for REF_MATCH).
#   python3 ref_match.py stats <img>...                 palette/value stats per image (json lines)
#   python3 ref_match.py match <game.jpg> <ref.jpg>      scores a game frame against its target
#   python3 ref_match.py empty <game.jpg>...             NO_EMPTY_VIEW: widest flat, featureless run below the horizon (fraction of width, PASS <= 0.25)
# Scores (game vs ref), all on a 480x270 downsample:
#   value_dist   1D earth-mover distance of luminance histograms (0 = same tonal spread; PASS <= 0.06)
#   chroma_dist  mean distance of the 3x3 grid cells' average a*b* colour, in CIELAB units (PASS <= 18)
#   sky_dist     a*b*L* distance of the top 25 % band (sky/horizon mood; PASS <= 20)
#   detail_ratio game/ref mean gradient energy below the horizon band (PASS 0.6–1.6: as busy as the target, not flat, not noisy)
import sys, json
import numpy as np
from PIL import Image

def load(p, w=480, h=270):
    return np.asarray(Image.open(p).convert('RGB').resize((w, h), Image.BILINEAR), dtype=np.float32) / 255.0

def to_lab(rgb):
    c = np.where(rgb > 0.04045, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    L = 116 * f[..., 1] - 16; a = 500 * (f[..., 0] - f[..., 1]); b = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], -1)

def grad(L):
    gx = np.abs(np.diff(L, axis=1))[:-1, :]; gy = np.abs(np.diff(L, axis=0))[:, :-1]
    return gx + gy

def stats(p):
    lab = to_lab(load(p)); L = lab[..., 0]
    sat = np.hypot(lab[..., 1], lab[..., 2])
    top = lab[: lab.shape[0] // 4].reshape(-1, 3).mean(0)
    return {'file': p, 'L_mean': round(float(L.mean()), 1), 'L_p10': round(float(np.percentile(L, 10)), 1), 'L_p90': round(float(np.percentile(L, 90)), 1),
            'chroma_mean': round(float(sat.mean()), 1), 'sky_Lab': [round(float(x), 1) for x in top],
            'detail': round(float(grad(L)[lab.shape[0] // 3:].mean()), 2)}

def emd1d(a, b, bins=64):
    ha, _ = np.histogram(a, bins, (0, 100)); hb, _ = np.histogram(b, bins, (0, 100))
    ca = np.cumsum(ha / ha.sum()); cb = np.cumsum(hb / hb.sum())
    return float(np.abs(ca - cb).mean())

def match(g, r):
    G = to_lab(load(g)); R = to_lab(load(r))
    value = emd1d(G[..., 0], R[..., 0])
    h, w = G.shape[:2]; cells = []
    for i in range(3):
        for j in range(3):
            sg = G[i * h // 3:(i + 1) * h // 3, j * w // 3:(j + 1) * w // 3, 1:].reshape(-1, 2).mean(0)
            sr = R[i * h // 3:(i + 1) * h // 3, j * w // 3:(j + 1) * w // 3, 1:].reshape(-1, 2).mean(0)
            cells.append(float(np.linalg.norm(sg - sr)))
    sky = float(np.linalg.norm(G[: h // 4].reshape(-1, 3).mean(0) - R[: h // 4].reshape(-1, 3).mean(0)))
    dg = grad(G[..., 0])[h // 3:].mean(); dr = grad(R[..., 0])[h // 3:].mean()
    res = {'value_dist': round(value, 3), 'chroma_dist': round(float(np.mean(cells)), 1), 'sky_dist': round(sky, 1), 'detail_ratio': round(float(dg / max(dr, 1e-6)), 2)}
    res['pass'] = res['value_dist'] <= .06 and res['chroma_dist'] <= 18 and res['sky_dist'] <= 20 and .6 <= res['detail_ratio'] <= 1.6
    return res

def empty(p):
    # Coarse scale (64x36 after a blur) so grass texture and mow stripes vanish and only objects, edges and colour changes
    # remain. In the lower two thirds, the longest run of columns with gradient < 1.5 is a flat, featureless area.
    # Calibrated 10-17: today's frames 0.35-1.0 (FAIL), the targets 0.05-0.22 (PASS); gate <= 0.25 of the frame width.
    from PIL import ImageFilter
    im = Image.open(p).convert('RGB').resize((256, 144), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2.5)).resize((64, 36), Image.BILINEAR)
    lab = to_lab(np.asarray(im, np.float32) / 255.0)
    g = grad(lab[..., 0]) + .5 * grad(lab[..., 1]) + .5 * grad(lab[..., 2])
    # putt views: the green itself is meant to be smooth, so only the backdrop band beyond it (30-55 % of the height) counts
    h = g.shape[0]; band = g[int(h * .30):int(h * .55)] if 'putt' in p else g[h // 3:]
    rows = band < 1.5; best = 0
    for r in rows:
        cur = 0
        for v in r: cur = cur + 1 if v else 0; best = max(best, cur)
    frac = best / g.shape[1]
    return {'file': p, 'widest_flat_fraction': round(frac, 2), 'pass': frac <= .25}

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'stats':
        for p in sys.argv[2:]: print(json.dumps(stats(p)))
    elif cmd == 'match': print(json.dumps(match(sys.argv[2], sys.argv[3])))
    elif cmd == 'empty':
        for p in sys.argv[2:]: print(json.dumps(empty(p)))
