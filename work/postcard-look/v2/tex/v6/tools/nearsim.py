"""near-field magnification simulator: luminance of a tile crop (and optional normal-lit shading) magnified by `mag` with bilinear sampling,
then the Game-view gate statistic (8 px windows: flat if sd < .006 or 4x4 block-mean sd < .003).  Calibrated on the current Fairway_C against the real stills."""
import sys, numpy as np
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import golf_look_textures as G
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look/'
def lum709(a):
    a = a[..., :3].astype(np.float64) / 255
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
def up_bilinear(l, mag, size=320):
    h, w = l.shape
    ys = (np.arange(size) + .5) / mag - .5; xs = (np.arange(size) + .5) / mag - .5
    y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int); fy = (ys - y0)[:, None]; fx = (xs - x0)[None, :]
    y0 %= h; x0 %= w; y1 = (y0 + 1) % h; x1 = (x0 + 1) % w
    return (l[y0][:, x0] * (1 - fx) + l[y0][:, x1] * fx) * (1 - fy) + (l[y1][:, x0] * (1 - fx) + l[y1][:, x1] * fx) * fy
def flat_share(l, win=8, flat_sd=0.006, block_sd=0.003):
    H, W = l.shape; h2, w2 = H // win, W // win
    a = l[:h2 * win, :w2 * win].reshape(h2, win, w2, win)
    sd = a.std(axis=(1, 3)); b = a.reshape(h2, win // 4, 4, w2, win // 4, 4).mean(axis=(2, 5)); bsd = b.std(axis=(1, 3))
    return float(((sd < flat_sd) | (bsd < block_sd)).mean()), float(np.median(sd))
def tex_lum(name):
    return lum709(G.read_png(R + name))
if __name__ == '__main__':
    for nm in sys.argv[1:]:
        l = tex_lum(nm)
        out = []
        for mag in (1.5, 2.5, 3.8, 5.5):
            fs = [flat_share(up_bilinear(l[y0:y0 + 90, x0:x0 + 90], mag, 320)) for (y0, x0) in ((0, 0), (300, 500), (700, 200), (150, 800))]
            out.append((mag, round(float(np.mean([f[0] for f in fs])), 3), round(float(np.mean([f[1] for f in fs])), 4)))
        print(nm, out)
