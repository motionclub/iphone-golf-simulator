"""Cheek relief metric: RMS / p95 / max of the normal-direction residual (V - lowpass(V)) over the cheek region, for several V arrays.
python3.13 relief_metric.py <name=path.npy|h0|i|inst> ..."""
import sys; sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from k_edit import *
ctx = KCtx(); w = cheek_weight(ctx, ctx.V0); reg = (w > 0.5)
big = feather(ctx, (w > 1e-3).astype(float), 8); big[~ctx.zone] = 0
srcs = {}
for a in sys.argv[1:]:
    name, _, path = a.partition('=')
    if name == 'h0': srcs[name] = np.load(I1 / 'data/V_h0.npy')
    elif name == 'i': srcs[name] = np.load(W / 'data/V_micro1i_start.npy')
    elif name == 'inst': srcs[name] = ctx.V0
    else: srcs[name] = np.load(path)
print('cheek region verts (w>0.5): %d' % reg.sum())
for name, V in srcs.items():
    row = []
    N = vertex_normals(V, ctx.F)
    for its in (10, 25, 60):
        Vlp = ctx.M.taubin(V, big, iters=its, lam=0.5, mu=-0.53)
        r = ((V - Vlp) * N).sum(1)[reg] * 1000
        row.append('it%d: rms %.2f p95|.| %.2f max %.2f' % (its, np.sqrt((r ** 2).mean()), np.percentile(np.abs(r), 95), np.abs(r).max()))
    print('%-8s ' % name + ' | '.join(row))
