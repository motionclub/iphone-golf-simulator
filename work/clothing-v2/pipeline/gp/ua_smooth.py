"""ua_smooth.py <in Kit_Top.npz> <out dir> [--iters 20] [--r0 .10] [--r1 .20] [--no-corr] [--lining 1]
His polo armpit (11-14): the serve camera shows the armpit cloth breaking into shards (neighbouring cloth on different bones, the lining
crossing the outer shirt). Inside a zone around each armpit: (1) the lining takes the weights of the outer shirt next to it, (2) the weights
are smoothed over the cloth (graph Laplacian, seams welded), (3) pruned to 4 bones. Writes <out dir>/MatchHero_Male/Kit_Top.npz."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, rig, scene, graph as GR, weights as WT, nearest as NR

a = sys.argv[1:]; src, out = a[0], a[1]
opt = {}; i = 2
while i < len(a):
    if a[i] == '--no-corr': opt['no-corr'] = True; i += 1
    else: opt[a[i][2:]] = float(a[i + 1]); i += 2
iters, r0, r1, lining = int(opt.get('iters', 20)), opt.get('r0', .10), opt.get('r1', .20), opt.get('lining', 1) > 0
h = rig.Hero('MatchHero_Male'); body = scene.items_from_dump(h)[0]
z = dict(np.load(src, allow_pickle=False)); P, tri = z['P'], z['tri'].astype(np.int64)
nb = len(h.bones)
W = np.zeros((len(P), nb)); np.add.at(W, (np.repeat(np.arange(len(P)), 4), z['bi'].ravel()), z['bw'].ravel())
# armpit zone (same armpit points as ua_mask2: lowest part of the chest / upper-arm weight transition, each side)
m = np.zeros(len(P))
for side, ua in ((-1, 'LeftUpperArm'), (1, 'RightUpperArm')):
    aw = W[:, h.bidx[ua]]
    sel = (aw > .3) & (aw < .7) & (P[:, 0] * side > .1)
    A = P[sel & (P[:, 1] < np.percentile(P[sel, 1], 10))].mean(0)
    t = np.clip((r1 - np.linalg.norm(P - A, axis=1)) / (r1 - r0), 0, 1); m = np.maximum(m, t * t * (3 - 2 * t))
W0 = W.copy()
# (1) lining follows the outer shirt
inner = z['inner'].astype(bool) if 'inner' in z else np.zeros(len(P), bool)
if not inner.any():   # not flagged: lining = a vertex with more of the shirt 2-15 mm IN FRONT of it along its own normal, within 4 mm sideways
    fn = np.cross(P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]]); N = np.zeros_like(P)
    for k in range(3): np.add.at(N, tri[:, k], fn)
    N /= np.maximum(1e-12, np.linalg.norm(N, axis=1, keepdims=True))
    from collections import defaultdict
    cell = .015; K = np.floor(P / cell).astype(int); grid = defaultdict(list)
    for v, k in enumerate(map(tuple, K)): grid[k].append(v)
    offs = [(x, y, w) for x in (-1, 0, 1) for y in (-1, 0, 1) for w in (-1, 0, 1)]
    for v in range(len(P)):
        k = K[v]; c = np.array(sum((grid.get((k[0] + dx, k[1] + dy, k[2] + dz), []) for dx, dy, dz in offs), []))
        dv = P[c] - P[v]; along = dv @ N[v]; side = np.linalg.norm(dv - np.outer(along, N[v]), axis=1)
        inner[v] = bool(np.any((along > .002) & (along < .015) & (side < .004)))
    print('lining detected: %d of %d vertices' % (inner.sum(), len(P)))
if lining and inner.any():
    oi, ii = np.nonzero(~inner)[0], np.nonzero(inner)[0]
    j, d = NR.PointGrid(P[oi], .02).nearest(P[ii]); ok = (j >= 0) & (d < .02)
    W[ii[ok]] = W[oi[j[ok]]]
    print('lining: %d of %d inner vertices take the outer weights' % (ok.sum(), len(ii)))
# (2) smooth inside the zone, seams welded; (3) blend by the zone, prune
weld = WT.weld_labels(P, .002); G = GR.Graph(P, tri)
for k in range(iters):
    S = G.smooth(W, 1); W = WT.group_mean(S, weld) * m[:, None] + W * (1 - m[:, None])
bi, bw = WT.prune(W, 4)
z['bi'], z['bw'] = bi.astype(z['bi'].dtype), bw.astype(z['bw'].dtype)
if opt.get('no-corr'):
    z['shapes'] = z['shapes'][:0]; z['shape_names'] = z['shape_names'][:0]
    z['corr_coef'] = z['corr_coef'][:, :0]
d = os.path.join(out, 'MatchHero_Male'); os.makedirs(d, exist_ok=True)
np.savez(os.path.join(d, 'Kit_Top.npz'), **z)
ch = np.abs(W - W0).sum(1) / 2
print('zone: %d vertices > .5; weight change mean %.3f, max %.3f (in zone)' % ((m > .5).sum(), ch[m > .5].mean(), ch.max()))
