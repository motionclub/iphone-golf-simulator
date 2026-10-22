"""GARMENT PIPELINE: automatic pose-space correctives for any garment.
Per stress pose: posed garment vs its obstacles (the skin under it, limited to the body groups the garment vertex follows, plus the garments
under it). Where a vertex is closer than its margin (outer wall 3 mm, lining 1 mm) it is lifted along the obstacle normal; the lift is spread
over the sewn graph (both walls together) so the cloth bulges smoothly instead of spiking. Lifts are mapped back to rest space (inverse
blended skin rotation) and compressed into <= MAX_SHAPES blend shapes (k-means over poses, per-vertex envelope of the members). An RBF over
the pose features (features.vector) gives each shape's weight; neutral poses pull it to 0. Lift-only: the cloth never moves toward the skin."""
import numpy as np
import features as FT, nearest as NR, graph as GR

MAX_SHAPES = int(__import__('os').environ.get('GP_SHAPES', 16))
MARGIN_OUT, MARGIN_IN = .003, .001
REST_SKIP = -.004        # vertices already this far inside an obstacle at rest are left alone (construction overlaps)
NEAR = .06              # only cloth within this distance of its skin at rest is solved (loose cloth farther out is free)
MAX_LIFT = float(__import__('os').environ.get('GP_MAX_LIFT', .025))   # 3.5 cm tried 10-18 (K7): worse
DEEP_GARMENT = float(__import__('os').environ.get('GP_DEEP_GARMENT', .03))
SMOOTH_ITERS = int(__import__('os').environ.get('GP_LIFT_SMOOTH', 6))
SOLVER = 'fade2'
BULGE_K = float(__import__('os').environ.get('GP_BULGE', 0))     # m of outward bulge per unit of area loss (0 = off)
OWN_R, OWN_DEEP = .05, float(__import__('os').environ.get('GP_OWN_DEEP', 0))   # 0 = off: own-skin deep clearing made K7 worse (131k vs 92k, 10-18)         # bump when the solver changes: corrective checkpoints are keyed on it
DEEP = .03              # deeper penetrations are limbs through the body (hand-clearance solver), not a cloth problem


def blended_rot(item, D):
    """per-vertex blended linear part of the skinning matrices (n,3,3)."""
    M = np.zeros((item.n, 3, 3))
    for k in range(item.bi.shape[1]):
        M += item.bw[:, k, None, None] * D[item.bi[:, k], :3, :3]
    return M


def vertex_groups(item, hero_bones, gnames, bone_group_fn, thr=.15):
    """bool (n, G): body groups each garment vertex follows (weight mass >= thr)."""
    names = [hero_bones[g] for g in (item.gidx if item.gidx is not None else range(len(hero_bones)))]
    bg = np.array([gnames.index(bone_group_fn(n, hero_bones)) for n in names])
    G = np.zeros((item.n, len(gnames)))
    for k in range(item.bi.shape[1]):
        np.add.at(G, (np.arange(item.n), bg[item.bi[:, k]]), item.bw[:, k])
    m = G >= thr
    m[np.arange(item.n), G.argmax(1)] = True
    return m


class Obstacle:
    """a posed surface the garment must stay outside of: (positions per pose callable, tri, per-face group or None).
    inside=True: the garment must stay INSIDE it instead (an outer garment over this one: the shorts waistband under the polo hem is pushed
    in, never out through the hem) - the same solver with the distance and normal flipped."""
    def __init__(self, tag, tri, nverts, fgroup=None, inside=False):
        self.tag, self.tri, self.fgroup, self.inside = tag, tri, fgroup, inside
        self.surf = NR.Surface(tri, nverts)
        self.sub = {}
        if fgroup is not None:
            for g in np.unique(fgroup):
                if g < 0: continue
                sel = np.nonzero(fgroup == g)[0]
                self.sub[int(g)] = (sel, NR.Surface(tri[sel], nverts))


def signed_to(obs, P, Q, vgroups=None, faces=False):
    """signed distance of points Q to obstacle with vertex positions P; restricted per point to the obstacle groups in vgroups (n,G).
    faces=True also returns the hit face (index into obs.tri)."""
    vn = GR_vnormals(P, obs.tri)
    if obs.fgroup is None or vgroups is None:
        sd, pt, f, bc, nn = obs.surf.signed(P, Q, vn)
        if getattr(obs, 'inside', False): sd, nn = -sd, -nn
        return (sd, nn, f) if faces else (sd, nn)
    sd = np.full(len(Q), np.inf); nn = np.zeros((len(Q), 3)); fo = np.zeros(len(Q), np.int64)
    for g, (sel, surf) in obs.sub.items():
        m = vgroups[:, g]
        if not m.any(): continue
        s, pt, f, bc, n_ = surf.signed(P, Q[m], vn)
        idx = np.nonzero(m)[0]
        better = np.abs(s) < np.abs(sd[idx])
        sd[idx[better]] = s[better]; nn[idx[better]] = n_[better]; fo[idx[better]] = sel[f[better]]
    return (sd, nn, fo) if faces else (sd, nn)


_VN = {}


def GR_vnormals(P, tri):
    key = (id(P), id(tri))
    if key in _VN and _VN[key][0] is P: return _VN[key][1]
    if len(_VN) > 8: _VN.clear()
    fn = np.cross(P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]])
    vn = np.zeros_like(P)
    for k in range(3): np.add.at(vn, tri[:, k], fn)
    vn = vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
    _VN[key] = (P, vn)
    return vn


def spread(graph, need_vec, iters=10):
    """smooth bump field that keeps at least the needed lift where it is needed."""
    X = need_vec.copy(); mag = np.linalg.norm(need_vec, axis=1)
    for _ in range(iters):
        A = graph.average(X)
        keep = mag > np.linalg.norm(A, axis=1)
        X = np.where(keep[:, None], need_vec, A)
    return X


def solve_pose(rig_, item, mats, obstacles, graph, inner, pairs, vgroups, rest_ok, rounds=3, base=None, bulge_k=None):
    """-> rest-space lift field (n,3) for one pose."""
    D = rig_.skin(item, mats)
    Rv = blended_rot(item, D)
    det = np.linalg.det(Rv)
    Rinv = np.where((np.abs(det) > .2)[:, None, None], np.linalg.inv(np.where((np.abs(det) > .2)[:, None, None], Rv, np.eye(3))), np.eye(3))
    margin = np.where(inner, MARGIN_IN, MARGIN_OUT)
    total = np.zeros((item.n, 3))
    P0 = item.P if base is None else base
    for _ in range(rounds):
        G = rig_.pose(item, D, base=P0 + total)
        need = np.zeros((item.n, 3))
        for (obs, posed, key) in obstacles:
            sel = np.nonzero(rest_ok[key] > 0)[0]
            if not len(sel): continue
            sd, nn, fh = signed_to(obs, posed, G[sel], vgroups[sel] if obs.fgroup is not None else None, faces=True)
            deep_lim = DEEP if obs.fgroup is not None else DEEP_GARMENT      # a garment under a garment may sink deeper than a limb
            if OWN_DEEP > 0 and obs.fgroup is not None and getattr(obs, 'rest_c', None) is not None:
                # the cloth's OWN skin (it lay within OWN_R of this cloth vertex at rest) is cleared at any depth up to OWN_DEEP: a fold of the
                # back panel sinking 4 cm into protracted shoulder blades is cloth, not a limb passing through (10-18 Thrust slits)
                own = np.linalg.norm(obs.rest_c[fh] - item.P[sel], axis=1) < OWN_R
                deep_lim = np.where(own, OWN_DEEP, deep_lim)
            # the lift fades out between deep/2 and deep (a hard cutoff gave neighbours 0 vs 2.5 cm lifts: crushed / stretched hem bands, 10-18)
            fade = np.clip((sd + deep_lim) / (.5 * deep_lim), 0, 1)
            short = np.where(sd > -deep_lim, (margin[sel] - sd) * fade, 0)
            m = short > 1e-4
            idx = sel[m]
            cur = np.linalg.norm(need[idx], axis=1)
            add = short[m, None] * nn[m]
            need[idx] = np.where((short[m] > cur)[:, None], add, need[idx])
        bk = BULGE_K if bulge_k is None else bulge_k
        if bk > 0:
            # COMPRESSION BULGE: where skinning squeezes the cloth (local area < rest), real fabric buckles OUTWARD, LBS folds it inward
            # into the body (chest in Thrust, shoulder blades). Push it out along its own outward normal by BULGE_K x the area loss.
            if not hasattr(item, '_area0'): item._area0 = vertex_area(item.P, item.tri)
            ratio = vertex_area(G, item.tri) / np.maximum(item._area0, 1e-12)
            for _ in range(2): ratio = graph.average(ratio[:, None])[:, 0]
            comp = np.clip(1 - ratio, 0, .6)
            vnG = GR_vnormals(G, item.tri) * np.where(inner, -1.0, 1.0)[:, None]
            bulge = (bk * comp)[:, None] * vnG
            bigger = np.linalg.norm(bulge, axis=1) > np.linalg.norm(need, axis=1)
            need = np.where(bigger[:, None], bulge, need)
        if not need.any(): break
        lift = spread(graph, need)
        for _ in range(SMOOTH_ITERS): lift = .5 * lift + .5 * graph.average(lift)      # no isolated spikes: cloth lifts as a sheet
        for a, b in pairs:                       # both walls move together: the larger lift wins
            la, lb = lift[a], lift[b]
            big = (np.linalg.norm(la, axis=1) >= np.linalg.norm(lb, axis=1))[:, None]
            lift[a] = np.where(big, la, lb); lift[b] = lift[a]
        total += np.einsum('nij,nj->ni', Rinv, lift)
    mag = np.linalg.norm(total, axis=1)
    total[~np.isfinite(mag) | (mag > .06)] = 0          # degenerate weights
    mag = np.linalg.norm(total, axis=1)
    total *= np.minimum(1, MAX_LIFT / np.maximum(mag, 1e-9))[:, None]   # cloth lifts beyond 2.5 cm read as shredding: cap (the cover hides the rest)
    return total


def vertex_area(P, tri):
    a = np.linalg.norm(np.cross(P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]]), axis=1) / 6
    out = np.zeros(len(P))
    for k in range(3): np.add.at(out, tri[:, k], a)
    return out


def kmeans(X, k, iters=30, seed=0):
    rng = np.random.default_rng(seed)
    C = X[rng.choice(len(X), k, replace=False)]
    for _ in range(iters):
        d = ((X[:, None, :] - C[None]) ** 2).sum(2)
        lab = d.argmin(1)
        for j in range(k):
            if (lab == j).any(): C[j] = X[lab == j].mean(0)
    return lab


def compress(fields, feats, max_shapes=MAX_SHAPES, active_mm=.5):
    """fields (P,n,3) rest lifts, feats (P,K) -> shapes (S,n,3), anchors (P,K), targets (P,S)."""
    amp = np.linalg.norm(fields, axis=2).max(1)
    act = np.nonzero(amp > active_mm / 1000)[0]
    if not len(act):
        return np.zeros((0, fields.shape[1], 3)), feats, np.zeros((len(feats), 0))
    S = min(max_shapes, len(act))
    X = fields[act].reshape(len(act), -1)[:, ::7]
    X = X / np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-12)
    lab = kmeans(X, S) if S < len(act) else np.arange(len(act))
    shapes, T = [], np.zeros((len(feats), 0))
    cols = []
    for j in range(S):
        mem = act[lab == j]
        if not len(mem): continue
        F = fields[mem]
        # one REAL pose field per shape (the member with the largest total lift): coherent across neighbouring vertices
        # (a per-vertex max over members mixed lifts of different poses side by side and shredded the cloth)
        best = int(np.linalg.norm(F.reshape(len(F), -1), axis=1).argmax())
        shapes.append(F[best])
        col = np.zeros(len(feats)); col[mem] = 1; cols.append(col)
    return np.array(shapes), feats, np.stack(cols, 1)


def fit_rbf(anchors, targets, sigma_scale=1.0, lam=1e-3):
    d = np.sqrt(((anchors[:, None] - anchors[None]) ** 2).sum(2))
    nn = np.sort(d + np.eye(len(d)) * 1e9, 1)[:, 0]
    sigma = float(np.median(nn) * sigma_scale * 2.0) or 1.0
    Phi = np.exp(-d ** 2 / (2 * sigma * sigma))
    C = np.linalg.solve(Phi + lam * np.eye(len(d)), targets)
    return sigma, C
