"""lava_compare.py <dir with Lava_C/E/N.png> [...]: compares the GolfLava shader-model render of the maps, downsampled to the still's ground scale (~14 cm / px: 24 m tile = 170 px),
with crater.jpg's lava pool crops (pure lava, no rock): colour, luminance sd (whole / after 4x4 block mean = regional contrast), share dark (max<90) / hot (R>235 & G>105) / yellow-orange (G>130), hue p5/50/95."""
import sys, os, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import imgnp
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools'))
import lab
g = lab.gl
def stats(rgb01, tag):
    f = rgb01.reshape(-1, 3) * 255; mx = f.max(1)
    l = imgnp.lum(rgb01); H, W = l.shape; b = 4
    lb = l[:H // b * b, :W // b * b].reshape(H // b, b, W // b, b).mean((1, 3))
    hue = []
    r, gg, bb = f[:, 0], f[:, 1], f[:, 2]; d = np.maximum(mx - f.min(1), 1e-6)
    h = np.where(mx == r, ((gg - bb) / d) % 6, np.where(mx == gg, (bb - r) / d + 2, (r - gg) / d + 4)) * 60
    print(f"{tag:34s} mean {np.round(f.mean(0)).astype(int).tolist()} p50 {np.round(np.median(f,0)).astype(int).tolist()} | lum sd {l.std()*255:5.1f} block4 sd {lb.std()*255:5.1f} | dark<90 {np.mean(mx<90):5.1%} hot {np.mean((r>235)&(gg>105)):5.1%} G>130 {np.mean(gg>130):5.1%} | hue p5/50/95 {np.percentile(h,5):.0f}/{np.percentile(h,50):.0f}/{np.percentile(h,95):.0f}")
a = imgnp.load(os.path.join(g.ROOT, 'ArtDir/environments/refs/crater.jpg'))
for nm, (x0, y0, x1, y1) in {'still pool A': (720, 560, 940, 700), 'still pool B': (640, 600, 820, 710), 'still pool C': (800, 470, 1000, 560)}.items():
    stats(a[y0:y1, x0:x1], nm)
sp = g.lava_spec()
for d in sys.argv[1:]:
    C, E, N = [g.read_png(os.path.join(d, 'Lava_%s.png' % k)) for k in 'CEN']
    img = g.lava_shader_model(C, E, N, sp)[1] / 255.0
    n = 170; f = img.shape[0] // n
    ds = img[:n * f, :n * f].reshape(n, f, n, f, 3).mean((1, 3)) if f > 0 else img
    stats(ds[:140, :200] if False else ds[:140, :170], os.path.basename(d.rstrip('/')) + ' (14 cm/px)')
