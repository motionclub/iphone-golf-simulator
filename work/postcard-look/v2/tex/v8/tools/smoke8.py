"""smoke8.py [key=value ...]: SMOKE_P overrides -> mat_smoke -> the stack the hole-10 builder makes (smoke_group: n cards, spread .10, every second mirrored, jitter) -> combined alpha stats (Blender python)."""
import sys, os, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
out = None
for kv in sys.argv[1:]:
    k, v = kv.split('=')
    if k == 'out': out = v; continue
    g.SMOKE_P[k] = tuple(float(x) for x in v.split(',')) if ',' in v else float(v)
r = g.mat_smoke(); a = np.clip(r['A'] * 1.35, 0, 1)
def sh(x, dx, dy, mir):
    if mir: x = x[:, ::-1]
    return np.roll(np.roll(x, int(round(dx * x.shape[1])), 1), int(round(dy * x.shape[0])), 0)
print('single card: max eff alpha %.3f, share>=.30 %.3f' % (a.max(), (a >= .30).mean()))
for sp in (0.0, 0.10, 0.20):
    b = sh(a, sp, 0.02, True); c = sh(a, -sp, 0.04, False)
    two = 1 - (1 - a) * (1 - b); three = 1 - (1 - a) * (1 - b) * (1 - c)
    print(' spread %.2f: 2-card max %.3f  3-card max %.3f  share(3)>=.30 %.3f >=.75 %.4f >=.85 %.4f' % (sp, two.max(), three.max(), (three >= .30).mean(), (three >= .75).mean(), (three >= .85).mean()))
if out:
    import numpy as np
    c = r['C']; al = r['A'][..., None]
    bg = np.array([0.24, 0.16, 0.16], np.float32)[None, None]
    img = c * al + bg * (1 - al)
    b = sh(a, 0.10, 0.02, True); c3 = sh(a, -0.10, 0.04, False)
    three = 1 - (1 - a) * (1 - b) * (1 - c3)
    comp = np.concatenate([img, np.repeat(three[..., None], 3, 2)], 1)
    g.write_png(out, g.enc(comp))

# Monte Carlo of the hole-10 stack (hole10_look.smoke_group): n cards, off = k*spread + U(-.03,.03), size 1 +- .12, height +- .04, every second card mirrored
rng = np.random.default_rng(7)
N_ = a.shape[0]
def card(x, dxw, dyh, s, mir):
    if mir: x = x[:, ::-1]
    # world card of width s*W: sample texture at (u - dx)/s about the card centre
    ys, xs = np.mgrid[0:N_, 0:N_].astype(np.float32)
    u = (xs + .5) / N_; v = (ys + .5) / N_
    uu = (u - 0.5 - dxw) / s + 0.5; vv = (v - 1.0 - dyh) / s + 1.0           # bottom-centre anchored
    ok = (uu >= 0) & (uu < 1) & (vv >= 0) & (vv < 1)
    xi = np.clip((uu * N_).astype(int), 0, N_ - 1); yi = np.clip((vv * N_).astype(int), 0, N_ - 1)
    return np.where(ok, x[yi, xi], 0.0)
res = []
for t in range(60):
    for n, spread in ((3, 0.10),):
        comb = np.ones_like(a)
        for i in range(n):
            k = i - (n - 1) / 2.0
            off = k * spread + rng.uniform(-.03, .03); s = 1 + rng.uniform(-.12, .12); dy = rng.uniform(-.04, .04)
            comb *= 1 - card(a, off, dy, s, i % 2 == 1)
        c3 = 1 - comb
        res.append((float(c3.max()), float((c3 >= .75).mean()), float((c3 >= .30).mean())))
res = np.array(res)
print('MC stack of 3 (60 draws): max combined alpha p50 %.3f p90 %.3f max %.3f | share>=.75 mean %.4f p90 %.4f | share>=.30 mean %.3f' % (np.percentile(res[:, 0], 50), np.percentile(res[:, 0], 90), res[:, 0].max(), res[:, 1].mean(), np.percentile(res[:, 1], 90), res[:, 2].mean()))

if out:
    # composite one stack (3 cards, spread .10, every second mirrored) of the colour card over a dark wall + a pale sky, effective alpha
    rng = np.random.default_rng(3)
    col = r['C']; al = np.clip(r['A'] * 1.35, 0, 1)
    def cardc(x, dxw, dyh, s, mir):
        if mir: x = x[:, ::-1]
        ys, xs = np.mgrid[0:N_, 0:N_].astype(np.float32)
        u = (xs + .5) / N_; v = (ys + .5) / N_
        uu = (u - 0.5 - dxw) / s + 0.5; vv = (v - 1.0 - dyh) / s + 1.0
        ok = (uu >= 0) & (uu < 1) & (vv >= 0) & (vv < 1)
        xi = np.clip((uu * N_).astype(int), 0, N_ - 1); yi = np.clip((vv * N_).astype(int), 0, N_ - 1)
        return np.where(ok[..., None] if x.ndim == 3 else ok, x[yi, xi], 0.0)
    wall = np.zeros((N_, N_, 3), np.float32) + np.array([0.10, 0.07, 0.07], np.float32); sky = np.zeros((N_, N_, 3), np.float32) + np.array([0.62, 0.40, 0.40], np.float32)
    outs = []
    for bg in (wall, sky):
        img = bg.copy()
        for i in range(3):
            k = i - 1.0
            off = k * 0.10 + rng.uniform(-.03, .03); s = 1 + rng.uniform(-.12, .12); dy = rng.uniform(-.04, .04)
            a_i = cardc(al, off, dy, s, i % 2 == 1); c_i = cardc(col, off, dy, s, i % 2 == 1)
            img = c_i * a_i[..., None] + img * (1 - a_i[..., None])
        outs.append(img)
    g.write_png(out.replace('.png', '_stack.png'), g.enc(np.concatenate(outs, 1)))
