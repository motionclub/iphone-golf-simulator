"""Per-pixel hue distribution and clipping of the central lower third (x .25-.75, y .5-.83) of Game-view frames. usage: gameview_hue.py <img> ..."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import imgnp
for p in sys.argv[1:]:
    a = imgnp.load(p); H, W = a.shape[:2]
    c = a[int(H * .5):int(H * .83), int(W * .25):int(W * .75)].reshape(-1, 3)
    mx = c.max(1); mn = c.min(1); d = np.maximum(mx - mn, 1e-6)
    r, g, b = c[:, 0], c[:, 1], c[:, 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    hp = np.percentile(h, [5, 50, 95])
    print(f"{os.path.basename(os.path.dirname(p))}/{os.path.basename(p):26s} hue p5/p50/p95 {hp[0]:.0f}/{hp[1]:.0f}/{hp[2]:.0f} share in 62..76: {np.mean((h>=62)&(h<=76)):.0%} | clipped (any channel >=250): {np.mean(mx*255>=250):.2%}  (>=255: {np.mean(mx*255>=254.5):.2%})")
