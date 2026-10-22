"""Audit/proof metrics on venue captures (reads PNGs, prints numbers). Usage: measure_shots.py <dir> [prefix]"""
import sys, numpy as np
from PIL import Image

def load(p): return np.asarray(Image.open(p).convert('RGB')).astype(np.float32) / 255

def hsv(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1); mn = a.min(-1); d = mx - mn + 1e-9
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    s = np.where(mx > 0, d / (mx + 1e-9), 0)
    return h, s, mx

def lum(a): return a @ np.array([.2126, .7152, .0722], dtype=np.float32)

def grad(a):
    l = lum(a)
    gx = np.abs(np.diff(l, axis=1))[:-1, :]
    gy = np.abs(np.diff(l, axis=0))[:, :-1]
    return gx, gy

BALL = np.array([.72, .80, .27], dtype=np.float32)   # mean of the three measured gameplay balls

def background_report(path, rows=(0, 440), cols=(0, 1920)):
    a = load(path)[rows[0]:rows[1], cols[0]:cols[1]]
    h, s, v = hsv(a)
    ball_hue = ((h > 50) & (h < 90) & (s > .35) & (v > .40)).mean()
    dist = np.sqrt(((a - BALL) ** 2).sum(-1))
    near = (dist < .25).mean()
    gx, gy = grad(a)
    return dict(ball_hue_frac=ball_hue, rgb_near_ball=near, edge_density=float((gx.mean() + gy.mean()) / 2),
                aniso_x_over_y=float(gx.mean() / max(gy.mean(), 1e-6)), lum_mean=float(lum(a).mean()), lum_std=float(lum(a).std()))

def region_report(path, box):
    x0, y0, x1, y1 = box
    a = load(path)[y0:y1, x0:x1]
    gx, gy = grad(a)
    return dict(mean_rgb=a.reshape(-1, 3).mean(0).round(3).tolist(), lum_std=float(lum(a).std()),
                aniso_x_over_y=float(gx.mean() / max(gy.mean(), 1e-6)))

if __name__ == '__main__':
    d = sys.argv[1].rstrip('/') + '/'
    pre = sys.argv[2] if len(sys.argv) > 2 else ''
    for n in ['skyscraper', 'volcano', 'resort']:
        p = f'{d}{pre}{n}_1_gameplay.png'
        try: r = background_report(p)
        except FileNotFoundError: continue
        print(n, 'gameplay background band rows 0-440:', {k: round(v, 4) for k, v in r.items()})
