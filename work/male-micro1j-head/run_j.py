"""Build a Micro1j variant: python3.13 run_j.py <tag> [apple=1.0] [nape=1.0] [jaw=...]
Writes data/V_<tag>.npy, data/N_<tag>.npy (custom vertex normals) and prints the moved-vertex report + sagittal contours."""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head')
from j_neck import *
tag = sys.argv[1]
kw = dict(a.split('=') for a in sys.argv[2:])
f = lambda k, d: float(kw.get(k, d))
ctx = Ctx(); V = ctx.V0.copy()
masks = {}
if f('apple', 1.0) > 0:
    V, m = edit_apple(ctx, V, scale=f('apple', 1.0)); masks['apple'] = m
if f('nape', 1.0) > 0:
    fn_ = edit_nape2 if kw.get('napefn', '2') == '2' else edit_nape
    V, m = (fn_(ctx, V, scale=f('nape', 1.0), dys=json.loads(kw['napedy'])) if 'napedy' in kw else fn_(ctx, V, scale=f('nape', 1.0))); masks['nape'] = m
if 'jaw' in kw and f('jaw', 0) > 0:
    import j_jaw
    fn = {'1': j_jaw.edit_jaw, '2': j_jaw.edit_jaw2, '3': j_jaw.edit_jaw3}[kw.get('jawfn', '3')]
    V, m = fn(ctx, V, scale=f('jaw', 1.0), **json.loads(kw.get('jawkw', '{}'))); masks['jaw'] = m
if f('fair', 1) > 0:
    fm = np.zeros(ctx.n, bool)
    for k, m in masks.items():
        if k != 'jaw': fm |= m
    V = (fair_disp if f('dfair', 1) > 0 else fair_region)(ctx, V, fm, iters=int(f('fair_iters', 4)))
if 'jaw' in masks and f('jfair', 0) > 0:
    V = (fair_disp if f('dfair', 1) > 0 else fair_region)(ctx, V, masks['jaw'], iters=int(f('jfair', 2)))
V = ctx.enforce_zone(V)
np.save(W / f'data/V_{tag}.npy', V)
nw = np.zeros(ctx.n)
for k, m in masks.items(): nw = np.maximum(nw, m.astype(float))
Nn = updated_normals(ctx, V, extra_smooth=nw if f('nsmooth', 0) > 0 else None, smooth_iters=int(f('nsmooth', 0)))
np.save(W / f'data/N_{tag}.npy', Nn)
rep = moved_report(ctx, V); print('MOVED', json.dumps(rep))
# front / back midline contour before -> after
cols = np.where((np.abs(ctx.V0[:, 0]) < 0.0075) & (ctx.V0[:, 2] > 1.39) & (ctx.V0[:, 2] < 1.46))[0]
cols = cols[np.argsort(ctx.V0[cols, 2])]
print('  z(mm)     front/back y start -> now (mm)')
for i in cols[::1]:
    if abs(ctx.V0[i, 1] - V[i, 1]) > 1e-9 or True:
        print(f'  {ctx.V0[i,2]*1000:7.1f}  x={ctx.V0[i,0]*1000:+5.1f}  y {ctx.V0[i,1]*1000:+7.2f} -> {V[i,1]*1000:+7.2f}   d={ (V[i,1]-ctx.V0[i,1])*1000:+5.2f}')
