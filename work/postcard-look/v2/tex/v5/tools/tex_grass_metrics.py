"""Texture-level grass statistics of the Look PNGs (Fairway_C, Green_C, Rough_C, Scrub_C): mean sRGB, hue of the mean, luminance sd (global, and
after removing the lengthwise/low-frequency part), window sd at 1/16 tile (the LOOK_FILES footprint) and at ~1.5 m (the footprint where the stills
were calibrated, still_calib.txt), share of windows >= .03, hue spread (p5/p50/p95 and share inside 60..76), stripe contrast.
usage: tex_grass_metrics.py <dir with the PNGs> [Name ...]   (Blender's python3.13)"""
import sys, os, colorsys, importlib.util, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); gl = importlib.util.module_from_spec(spec); spec.loader.exec_module(gl)
TILE_M = dict(Fairway=10.0, Green=6.0, Rough=12.0, Scrub=12.0)
def lum(a): return a[..., 0] * .2126 + a[..., 1] * .7152 + a[..., 2] * .0722
def wsd(l, w):
    H, W = l.shape; h2, w2 = H // w, W // w
    return l[:h2 * w, :w2 * w].reshape(h2, w, w2, w).std(axis=(1, 3)).ravel()
def hue_deg(a):
    mx = a.max(-1); mn = a.min(-1); d = mx - mn + 1e-9
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h
def report(d, name):
    p = os.path.join(d, name + '_C.png'); a = gl.read_png(p)[..., :3].astype(np.float32) / 255
    N = a.shape[0]; l = lum(a); mean = a.reshape(-1, 3).mean(0)
    h, s, v = colorsys.rgb_to_hsv(*[float(x) for x in mean])
    w16 = N // 16; w15 = max(8, int(round(1.5 / TILE_M[name] * N)))
    s16 = wsd(l, w16); s15 = wsd(l, w15)
    hu = hue_deg(a); sat = (a.max(-1) - a.min(-1)) / (a.max(-1) + 1e-9)
    hq = np.percentile(hu, [5, 50, 95])
    colm = l.mean(0); colm_row = l.mean(1)       # column means (stripes along v vary with u)
    print(f"{name:7s} mean {np.round(mean*255).astype(int).tolist()} h{h*360:.1f} S{s:.2f} V{v:.2f} | lum sd {l.std():.4f} | w1/16 ({w16}px) med {np.median(s16):.4f} ge.03 {np.mean(s16>=.03):.0%} | w1.5m ({w15}px) med {np.median(s15):.4f} ge.03 {np.mean(s15>=.03):.0%} | hue p5/50/95 {hq[0]:.0f}/{hq[1]:.0f}/{hq[2]:.0f} in60-76 {np.mean((hu>=60)&(hu<=76)):.0%} | col-mean sd {colm.std():.4f} row-mean sd {colm_row.std():.4f}")
if __name__ == '__main__':
    d = sys.argv[1]; names = sys.argv[2:] or ['Fairway', 'Green', 'Rough', 'Scrub']
    for n in names: report(d, n)
