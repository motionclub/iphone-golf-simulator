"""Build a Micro1k variant: python3.13 run_k.py <tag> key=value ...   (keys: undo=1 cheek=<alpha> cheekkw={json} mand=<scale> mandkw={json} strip=1 fair=...)
Writes data/V_<tag>.npy, D_<tag>.npy (relative to the INSTALLED Micro1j blend = data/V_start.npy), N_<tag>.npy (custom vertex normals)."""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from k_edit import *
tag = sys.argv[1]; kw = dict(a.split('=', 1) for a in sys.argv[2:]); f = lambda k, d: float(kw.get(k, d))
ctx = KCtx(); V = ctx.V0.copy(); masks = {}
if f('undo', 1) > 0: V = undo_jaw(ctx, V)
if f('toh0', 0) > 0:
    V, w = toward_h0(ctx, V, gamma=f('toh0', 0.5), **json.loads(kw.get('toh0kw', '{}'))); masks['toh0'] = w > 1e-3
if f('cheek', 0.6) > 0:
    V, w = soften_cheek(ctx, V, alpha=f('cheek', 0.6), **json.loads(kw.get('cheekkw', '{}'))); masks['cheek'] = w > 1e-3
if f('mand', 0) > 0:
    import k_mand
    Vpre = V.copy()
    V, m = k_mand.mandible(ctx, V, scale=f('mand', 1.0), **json.loads(kw.get('mandkw', '{}'))); masks['mand'] = m
    if f('trim', -1) >= 0:
        V, tinfo = k_mand.width_trim_blob(ctx, V, Vpre, target=f('trim', 0.0), **json.loads(kw.get('trimkw', '{}'))); masks['trim'] = np.linalg.norm(V - Vpre, axis=1) > 1e-7
        print('TRIM excess_mm per iter', tinfo['excess_mm_per_iter'])
if f('strip', 0) > 0:
    import k_mand
    V, m = k_mand.nape_strip(ctx, V, **json.loads(kw.get('stripkw', '{}'))); masks['strip'] = m
if f('dstrip', 0) > 0:        # Adnan-approved nape flatten: the staged Micro1j strip (<= 1.74 mm * scale), tiny/wide tails dropped
    Ds = np.load(W.parent / 'male-micro1j-head/optional_nape_strip/D_strip.npy') * f('dstrip', 1.0)
    keep = (np.linalg.norm(Ds, axis=1) >= 0.05e-3) & (np.abs(ctx.V0[:, 0]) <= 0.0255); Ds[~keep] = 0.0
    V = V + Ds; masks['dstrip'] = keep
V = ctx.enforce_zone(V) if (f('strip', 0) <= 0 and f('dstrip', 0) <= 0) else V
np.save(W / f'data/V_{tag}.npy', V); np.save(W / f'data/D_{tag}.npy', V - ctx.V0)
nw = np.zeros(ctx.n)
for k, m in masks.items(): nw = np.maximum(nw, feather(ctx, m.astype(float), 1))
Nn = updated_normals(ctx, V, extra_smooth=nw if f('nsmooth', 0) > 0 else None, smooth_iters=int(f('nsmooth', 0)))
np.save(W / f'data/N_{tag}.npy', Nn)
d = np.linalg.norm(V - ctx.V0, axis=1); mv = d > 0
print('MOVED', json.dumps(dict(moved=int(mv.sum()), max_mm=float(d.max() * 1000), min_z=float(ctx.V0[mv, 2].min()), below_zone=int((mv & ~ctx.zone).sum()))))
