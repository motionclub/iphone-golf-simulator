"""Build a Micro1l candidate: python3.13 run_l.py <tag> key=value ...
  base=pre|cur      pre = the current blend with Micro1k's crest removed (default), cur = the current blend as is
  jaw=<scale>       jaw crest + U-drop on/off; jawkw={json} kwargs of l_jaw.jaw
  cheek=<alpha>     cheek de-fat (l_cheek.defat) ; cheekkw={json}
  lips=<scale>      fuller lips (l_lips.lips) ; lipskw={json}
Writes data/V_<tag>.npy, D_<tag>.npy (relative to the CURRENT blend data/V_start.npy), N_<tag>.npy (custom vertex normals)."""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head')
from l_edit import *
tag = sys.argv[1]; kw = dict(a.split('=', 1) for a in sys.argv[2:]); f = lambda k, d: float(kw.get(k, d))
ctx = LCtx(); V = ctx.V0.copy(); masks = {}; stages = {}
if kw.get('base', 'pre') == 'pre': V = np.load(W / 'data/V_precrest.npy')
stages['s0_precrest'] = V.copy()
if f('cheek', 0) > 0:
    import l_cheek as C
    V, w = C.lowpass(ctx, V, alpha=f('cheek', 1.0), **json.loads(kw.get('cheekkw', '{}'))); masks['cheek'] = w > 1e-3; stages['s1_lowpass'] = V.copy()
if f('deflate3', 0) > 0:
    import l_cheek as C
    V, w2 = C.deflate3(ctx, V, base=f('deflate3', 3.0), **json.loads(kw.get('deflate3kw', '{}'))); masks['deflate3'] = w2 > 1e-3; stages['s2_deflate'] = V.copy()
if f('deflate2', 0) > 0:
    import l_cheek as C
    V, w2 = C.deflate2(ctx, V, base=f('deflate2', 2.0), **json.loads(kw.get('deflate2kw', '{}'))); masks['deflate2'] = w2 > 1e-3; stages['s2_deflate'] = V.copy()
if f('deflate', 0) > 0:
    import l_cheek as C
    V, w2 = C.deflate(ctx, V, amount=f('deflate', 2.0), **json.loads(kw.get('deflatekw', '{}'))); masks['deflate'] = w2 > 1e-3; stages['s2_deflate'] = V.copy()
if f('jaw', 0) > 0:
    import l_jaw as J
    Vpre = V.copy()
    V, m = J.jaw(ctx, V, **json.loads(kw.get('jawkw', '{}'))); masks['jaw'] = m; stages['s3_jaw'] = V.copy()
    if f('trim', -1) >= 0:
        import k_mand as KM
        V, tinfo = KM.width_trim_blob(ctx, V, Vpre, target=f('trim', 0.0), **json.loads(kw.get('trimkw', '{}'))); masks['trim'] = np.linalg.norm(V - stages['s3_jaw'], axis=1) > 1e-7; stages['s3b_trim'] = V.copy()
        print('TRIM excess_mm per iter', [round(v, 2) for v in tinfo['excess_mm_per_iter']])
if f('lips', 0) > 0:
    import l_lips as LP
    fn = LP.lips2 if kw.get('lipsmode', 'old') == 'abs' else LP.lips
    V, m = fn(ctx, V, scale=f('lips', 1.0), plan_out=str(W / f'data/lipplan_{tag}.json'), **json.loads(kw.get('lipskw', '{}'))); masks['lips'] = m; stages['s4_lips'] = V.copy()
V = ctx.enforce_zone(V)
np.save(W / f'data/V_{tag}.npy', V); np.save(W / f'data/D_{tag}.npy', V - ctx.V0)
for k_, v_ in stages.items(): np.save(W / f'data/V_{tag}_{k_}.npy', v_)
Nn = updated_normals(ctx, V)
if f('nsharp', 0) > 0:        # shading-only edge boost on the jaw band (feathered)
    wn = np.zeros(ctx.n)
    for k_, m_ in masks.items():
        if k_ in ('jaw',): wn = np.maximum(wn, feather(ctx, m_.astype(float), 3))
    Nn = sharpen_normals(ctx, Nn, wn, k=f('nsharp', 1.0), iters=int(f('nsharp_it', 6)))
if f('nboost', 0) > 0 and f('jaw', 0) > 0:     # analytic crest slope added to the shading normals (smooth by construction, positions untouched)
    import l_jaw as J
    NB = J.jaw.last_nb; NBF = J.jaw.last_nb_full
    wnb = feather(ctx, (np.linalg.norm(NBF, axis=1) > 1e-9).astype(float), 2)
    for _ in range(int(f('nb_smooth', 2))): NB = NB + 0.5 * wnb[:, None] * (ctx.M.nbr_mean(NB) - NB); NBF = NBF + 0.5 * wnb[:, None] * (ctx.M.nbr_mean(NBF) - NBF)
    if f('nb_smooth_chin', 0) > 0:        # the chin mesh is sparse (valence 3-5): extra smoothing of the tilt field there removes triangular darts at the chin bottom edge
        wch = feather(ctx, ((np.abs(V[:, 0]) < 0.040) & (V[:, 2] < 1.478) & (V[:, 1] < -0.09) & (np.linalg.norm(NBF, axis=1) > 1e-9)).astype(float), 3)
        for _ in range(int(f('nb_smooth_chin', 0))): NB = NB + 0.5 * wch[:, None] * (ctx.M.nbr_mean(NB) - NB); NBF = NBF + 0.5 * wch[:, None] * (ctx.M.nbr_mean(NBF) - NBF)
    # extra tilt = k * (full-height crest slope) + (full - geometric) slope: the shading edge is uniform along the arc even where the geometric crest is kept small for the 3/4 silhouettes
    Nn = Nn + f('nboost', 0.6) * NBF + (NBF - NB); Nn /= np.maximum(np.linalg.norm(Nn, axis=1, keepdims=True), 1e-12)
np.save(W / f'data/N_{tag}.npy', Nn)
d = np.linalg.norm(V - ctx.V0, axis=1); mv = d > 0
print('MOVED', json.dumps(dict(moved=int(mv.sum()), max_mm=float(d.max() * 1000), min_z=float(ctx.V0[mv, 2].min()) if mv.any() else None, below_zone=int((mv & ~ctx.zone).sum()))))
