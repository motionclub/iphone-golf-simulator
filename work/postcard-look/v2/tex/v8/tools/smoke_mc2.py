"""smoke_mc2.py <cfg> ... : each cfg 'xc0=.42,w1=.14,...' (SMOKE_P overrides on top of the v7 set) -> single-card visible share + Monte Carlo of the hole-10 3-card stack under the live runtime (gain 1.10, power 1.5)."""
import sys, os, importlib.util
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..', '..'))
spec = importlib.util.spec_from_file_location('gl', os.path.join(ROOT, 'blender/scripts/golf_look_textures.py')); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
GAIN, PW = 1.10, 1.5
V7 = dict(g.SMOKE_P); V7.update(g.SMOKE_P_V7)
rng = np.random.default_rng(11)
def card(x, dxw, dyh, s, mir, N_):
    if mir: x = x[:, ::-1]
    ys, xs = np.mgrid[0:N_, 0:N_].astype(np.float32)
    u = (xs + .5) / N_; v = (ys + .5) / N_
    uu = (u - 0.5 - dxw) / s + 0.5; vv = (v - 1.0 - dyh) / s + 1.0
    ok = (uu >= 0) & (uu < 1) & (vv >= 0) & (vv < 1)
    xi = np.clip((uu * N_).astype(int), 0, N_ - 1); yi = np.clip((vv * N_).astype(int), 0, N_ - 1)
    return np.where(ok, x[yi, xi], 0.0)
for cfg in sys.argv[1:]:
    g.SMOKE_P.clear(); g.SMOKE_P.update(V7)
    for kv in cfg.split(','):
        if kv:
            k, v = kv.split('='); g.SMOKE_P[k] = float(v)
    a = np.power(np.clip(g.mat_smoke()['A'] * GAIN, 0, 1), PW); N_ = a.shape[0]
    res = []
    for t in range(40):
        comb = np.ones_like(a)
        for i in range(3):
            k = i - 1.0
            off = k * 0.10 + rng.uniform(-.03, .03); s = 1 + rng.uniform(-.12, .12); dy = rng.uniform(-.04, .04)
            comb *= 1 - card(a, off, dy, s, i % 2 == 1, N_)
        c3 = 1 - comb
        res.append((c3.max(), (c3 >= .5).mean(), (c3 >= .07).mean(), np.percentile(c3[c3 >= .07], 95) if (c3 >= .07).any() else 0))
    res = np.array(res)
    print('%-52s single peak %.3f vis(>=.07) %.4f | stack: max %.3f p95-of-visible %.3f share>=.5 %.4f visible(>=.07) %.4f' % (cfg or 'v7', a.max(), (a >= .07).mean(), res[:, 0].mean(), res[:, 3].mean(), res[:, 1].mean(), res[:, 2].mean()))
