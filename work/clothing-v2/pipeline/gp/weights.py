"""GARMENT PIPELINE: general skin-weight transfer for any garment (one method for every piece, no per-garment binder).
1. panels = UV islands / separate construction pieces (unwelded connectivity). Each panel may only take weights from the body groups it
   lies over (>= 20 % of its nearest-skin mass), so a sleeve never takes torso skin and a side panel never takes arm skin.
2. outer-wall vertices close to that skin (distance <= dmax, normals agree) copy the skin weights at the nearest surface point
   (barycentric over the FULL body, i.e. the cover source, not the trimmed body).
3. lining / inner-wall vertices copy the weights of their own shell (nearest outer face of the SAME panel group), so the two walls of a
   garment always move together.
4. everything else (loose cloth, far skirt pleats) is filled harmonically over the sewn graph, then the whole field is diffused over the
   sewn graph (welded UV splits + seams) so no hard steps remain (e.g. the Neck 1.0 step at a collar).
Result: dense weights over the body palette (global bone ids)."""
import os
import numpy as np
import graph as GR
import nearest as NR

GROUPS = {
    'T': ['Spine', 'Chest', 'UpperChest', 'Neck', 'Head', 'LeftShoulder', 'RightShoulder'],
    'P': ['Hips', 'Root'],
    'AL': ['LeftUpperArm', 'LeftLowerArm', 'LeftHand'], 'AR': ['RightUpperArm', 'RightLowerArm', 'RightHand'],
    'LL': ['LeftUpperLeg', 'LeftLowerLeg', 'LeftFoot', 'LeftToes'], 'LR': ['RightUpperLeg', 'RightLowerLeg', 'RightFoot', 'RightToes'],
}
GNAMES = list(GROUPS)


def bone_group(name, palette):
    if name.startswith('ArmBlend_'):
        a = name.split('_'); x, y, k = int(a[1]), int(a[2]), int(a[3])
        gx, gy = bone_group(palette[x], palette), bone_group(palette[y], palette)
        return gy if k >= 4 else gx
    for g, ns in GROUPS.items():
        for n in ns:
            if name == n or (n.endswith('Hand') and name.startswith(n)):        # LeftHand* (finger bones); was startswith('Left'): legs fell into the arm groups
                return g
    for side, g in (('Left', 'AL'), ('Right', 'AR')):
        if name.startswith(side) and any(f in name for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Little')): return g
    return 'T'


def dense(bi, bw, nb):
    W = np.zeros((len(bi), nb))
    for k in range(bi.shape[1]): np.add.at(W, (np.arange(len(bi)), bi[:, k]), bw[:, k])
    return W


def prune(W, k=4):
    idx = np.argsort(-W, axis=1)[:, :k]
    w = np.take_along_axis(W, idx, 1); w = np.maximum(w, 0)
    s = w.sum(1, keepdims=True); w = np.where(s > 0, w / np.maximum(s, 1e-12), 0)
    return idx, w


class Body:
    """full body (cover source) in root rest space with dense weights over its palette, groups per vertex and per face."""
    def __init__(self, item, palette_names):
        self.P, self.tri = item.P, item.tri
        nb = len(palette_names)
        self.names = palette_names
        self.W = dense(item.bi, item.bw, nb)
        bg = np.array([GNAMES.index(bone_group(n, palette_names)) for n in palette_names])
        G = np.zeros((len(self.P), len(GNAMES)))
        for g in range(len(GNAMES)): G[:, g] = self.W[:, bg == g].sum(1)
        self.vgroup_mass = G
        self.fgroup = G[self.tri].sum(1).argmax(1)
        fn = np.cross(self.P[self.tri[:, 1]] - self.P[self.tri[:, 0]], self.P[self.tri[:, 2]] - self.P[self.tri[:, 0]])
        self.fn = fn / np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
        self._trees = {}

    def tree(self, groups):
        key = tuple(sorted(groups))
        if key not in self._trees:
            sel = np.nonzero(np.isin(self.fgroup, [GNAMES.index(g) for g in key]))[0]
            self._trees[key] = (NR.Surface(self.tri[sel], len(self.P)), sel)
        return self._trees[key]

    def nearest(self, Q, groups):
        surf, sel = self.tree(groups)
        dist, loc, f, bc, fn = surf.query(self.P, Q)
        return loc, sel[f], dist

    def weights_at(self, loc, face):
        a, b, c = (self.P[self.tri[face, k]] for k in range(3))
        v0, v1, v2 = b - a, c - a, loc - a
        d00, d01, d11 = (v0 * v0).sum(1), (v0 * v1).sum(1), (v1 * v1).sum(1)
        d20, d21 = (v2 * v0).sum(1), (v2 * v1).sum(1)
        den = np.where(np.abs(d00 * d11 - d01 * d01) > 1e-20, d00 * d11 - d01 * d01, 1e-20)
        v = (d11 * d20 - d01 * d21) / den; w = (d00 * d21 - d01 * d20) / den; u = 1 - v - w
        bc = np.clip(np.stack([u, v, w], 1), 0, 1); bc /= np.maximum(bc.sum(1, keepdims=True), 1e-12)
        return sum(bc[:, k:k + 1] * self.W[self.tri[face, k]] for k in range(3))


def footwear(body, P, side, foot_mass):
    """stiff footwear (a shoe, a boot): rides the Foot bone, flexes with the Toes from the ball of the foot forward, and only the collar
    follows the shin a little (the export2 shoe rule, expressed in a foot frame measured from the body: it works for any shoe on any foot)."""
    n = body.names; idx = lambda nm: n.index(nm)
    fi, ti, li = idx(side + 'Foot'), idx(side + 'Toes'), idx(side + 'LowerLeg')
    footv = (body.W[:, fi] + body.W[:, ti]) > .5
    Q = body.P[footv]
    head = lambda b: (body.W[:, b] > .5)
    fwd = Q[np.argmax(Q @ np.array([0, 0, 1.0]))] - Q[np.argmin(Q @ np.array([0, 0, 1.0]))]
    fwd[1] = 0; fwd /= np.linalg.norm(fwd)
    y0 = (Q @ fwd).min(); L = (Q @ fwd).max() - y0; ground = Q[:, 1].min()
    yq = (P @ fwd - y0) / L; zq = P[:, 1] - ground
    W = np.zeros((len(P), body.W.shape[1]))
    wt = np.clip((yq - .66) / .22, 0, 1) * .55
    wl = np.clip((zq - .06) / .05, 0, 1) * np.clip((.42 - yq) / .15, 0, 1) * .30
    W[:, ti] = wt; W[:, li] = wl; W[:, fi] = 1 - wt - wl
    return W


COVER_D, COVER_COS, COVER_SHARE = .045, .6, .03
TUBE_EASE = float(os.environ.get('GP_TUBE_EASE', '.035'))   # limb tube: cloth within the limb skin radius + this follows the limb


def covered_groups(body, P):
    """bool (G,): body groups with >= COVER_SHARE of the skin this garment covers (skin normal pointing at a garment vertex within COVER_D)."""
    vn = np.zeros_like(body.P)
    for k in range(3): np.add.at(vn, body.tri[:, k], body.fn)
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
    used = np.zeros(len(body.P), bool); used[body.tri.ravel()] = True
    j, d = NR.PointGrid(P, COVER_D).nearest(body.P)
    ok = used & (j >= 0) & (d <= COVER_D)
    cov = np.zeros(len(body.P), bool)
    dv = P[j[ok]] - body.P[ok]
    cov[ok] = (dv * vn[ok]).sum(1) > COVER_COS * np.maximum(np.linalg.norm(dv, axis=1), 1e-9)
    share = body.vgroup_mass[cov].sum(0); share /= max(share.sum(), 1e-12)
    return share >= COVER_SHARE


def limb_enclosed(body, cover_mask, P=None, bins=12, need=8, min_verts=40, near=.04):
    """per limb group: does the covered skin WRAP the limb (a sleeve, a trouser leg), or only touch one side of it (the arm beside a
    sleeveless armhole, a hand hanging against a skirt)? Per bone of the group: covered skin of that bone, angles round the bone's own
    axis (principal axis of its skin), wrapped when >= need of bins sectors are occupied."""
    out = {}
    dom = body.W.argmax(1)
    if P is not None:                       # covered AND close to the cloth (the rim rule marks an elbow 5 cm from an open waistband)
        j, d = NR.PointGrid(P, near).nearest(body.P)
        cover_mask = cover_mask & (j >= 0) & (d <= near)
    for g in ('AL', 'AR', 'LL', 'LR'):
        out[g] = False
        bones = [i for i, n in enumerate(body.names) if bone_group(n, body.names) == g
                 and not any(f in n for f in ('Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Little', 'Toes'))]   # thin ends (a hand against a skirt) never decide
        for bidx in bones:
            allv = np.nonzero(dom == bidx)[0]
            cv = allv[cover_mask[allv]]
            if len(cv) < min_verts or len(allv) < 3 * min_verts // 2: continue
            X = body.P[allv]; c = X.mean(0); U, S_, Vt = np.linalg.svd(X - c, full_matrices=False)
            ax = Vt[0]; e1 = Vt[1]; e2 = Vt[2]
            d = body.P[cv] - c
            ang = np.arctan2(d @ e2, d @ e1)
            occ = np.unique(np.floor((ang + np.pi) / (2 * np.pi) * bins).astype(int) % bins)
            if len(occ) >= need: out[g] = True; break
    return out


def transfer(body, P, tri, cover_mask=None, dmax=.04, max_angle=40.0, smooth_cm=2.0, min_group=.2, inner=None, log=print, transition_cm=0.0):
    """-> dense W (n, nb_body), info dict. P, tri: garment rest (root space). inner: optional bool per vertex (lining)."""
    n = len(P)
    sewn = GR.Graph(P, tri)                                   # welded: UV splits + coincident seams
    raw = GR.Graph(P, tri, weld=False)
    panel = raw.components()
    vn = np.zeros_like(P)
    fn = np.cross(P[tri[:, 1]] - P[tri[:, 0]], P[tri[:, 2]] - P[tri[:, 0]])
    for k in range(3): np.add.at(vn, tri[:, k], fn)
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
    # 1. panel -> allowed body groups
    loc0, face0, d0 = body.nearest(P, GNAMES)
    # stiff footwear: most of the piece lies on foot skin -> the footwear rule instead of skin copying
    fw = body.W[body.tri[face0]].mean(1)
    fw_side = None
    for side in ('Left', 'Right'):
        mass = fw[:, [body.names.index(side + 'Foot'), body.names.index(side + 'Toes')]].sum() / max(fw.sum(), 1e-9)
        if mass > .6:
            if os.environ.get('GP_SHOE_SKINW') == '1':
                # footwear that copies the body's own foot / toe / shin weights (nearest skin, like other garments): shoe and foot move
                # together off the bind pose, so the shoe can be cut closer (male-garments request 10-18). Still footwear: no correctives
                log('  weights: footwear on the %s foot (%.0f%%): SKIN weights (GP_SHOE_SKINW=1)' % (side, 100 * mass))
                fw_side = (side, float(mass)); break
            log('  weights: footwear on the %s foot (%.0f%% of the piece on foot skin): rigid foot + toe flex + collar on the shin' % (side, 100 * mass))
            W = footwear(body, P, side, mass)
            return W, {'footwear': side, 'foot_mass': float(mass)}, dict(panel=np.zeros(n, int), inner=np.zeros(n, bool) if inner is None else inner, dist=d0, face=face0, side=np.zeros(n))
    gm = body.vgroup_mass[body.tri[face0]].mean(1)            # group mass at the nearest skin (n, G)
    # body groups this garment actually COVERS: skin whose normal points at the garment within COVER_D (a sleeve over the arm, a shirt
    # over the chest), not skin that merely lies beside an edge (the arm next to a sleeveless armhole). A panel may only follow covered
    # groups: an armhole binding beside the arm must not stretch up the arm when it rises.
    if cover_mask is not None:
        share = body.vgroup_mass[cover_mask].sum(0); share /= max(share.sum(), 1e-12); cg = share >= COVER_SHARE
        enc = limb_enclosed(body, cover_mask, P)
        for g in ('AL', 'AR', 'LL', 'LR'):
            k = GNAMES.index(g)
            if cg[k] and not enc[g]: cg[k] = False; log('  weights: %s covered %.0f%% but not wrapped (one side only): not followed' % (g, 100 * share[k]))
    else:
        cg = np.ones(len(GNAMES), bool); share = np.zeros(len(GNAMES))               # no coverage given: no restriction (the geometric proxy is too noisy, 10-17)
    allowed = {}
    for p in np.unique(panel):
        m = panel == p
        mass = gm[m].sum(0); mass /= max(mass.sum(), 1e-12)
        mc = mass * cg
        allowed[p] = tuple(GNAMES[g] for g in np.nonzero((mass >= min_group) & cg)[0]) or (GNAMES[int((mc if mc.any() else mass).argmax())],)
    log('  weights: covered body groups %s' % ' '.join('%s %.0f%%' % (GNAMES[g], 100 * share[g]) for g in range(len(GNAMES)) if share[g] > .005))
    # 2. restricted nearest skin per panel group
    loc = np.zeros_like(P); face = np.zeros(n, np.int64); dist = np.zeros(n)
    for key in set(allowed.values()):
        m = np.isin(panel, [p for p, a in allowed.items() if a == key])
        l, f, d = body.nearest(P[m], key)
        loc[m], face[m], dist[m] = l, f, d
    off = P - loc
    side = (off * body.fn[face]).sum(1)                       # >0 outside the skin
    if inner is None:
        inner = (vn * body.fn[face]).sum(1) < -.2             # normal faces the skin: lining / inner wall
    ang = np.degrees(np.arccos(np.clip(np.abs((vn * body.fn[face]).sum(1)), 0, 1)))
    W = np.zeros((n, body.W.shape[1]))
    match = (~inner) & (dist <= dmax) & (ang <= max_angle)
    W[match] = body.weights_at(loc[match], face[match])
    # pieces with no matched vertex (buttons, small trims floating off the skin) take the nearest skin's weights, so every vertex is bound
    comp = raw.components()
    has = np.zeros(comp.max() + 1, bool); has[comp[match]] = True
    orphan = ~has[comp]
    if orphan.any():
        W[orphan] = body.weights_at(loc0[orphan], face0[orphan]); match = match | orphan
    # a limb the garment does not wrap (the arm beside a sleeveless armhole): the weight copied from that limb's bones moves to the
    # limb's root on the torso (UpperArm/ArmBlend -> Shoulder, leg -> Hips), so the cloth attaches at the shoulder instead of riding the arm
    # (the same idea as HeroShoulderDeformation's arm->chest rewrite for today's tank, made general)
    drop = [g for g in ('AL', 'AR', 'LL', 'LR') if not cg[GNAMES.index(g)]] if os.environ.get('GP_LIMB_ROOT', '1') == '1' else []
    if drop:
        root = {'AL': 'LeftShoulder', 'AR': 'RightShoulder', 'LL': 'Hips', 'LR': 'Hips'}
        bg = [bone_group(nm, body.names) for nm in body.names]
        dom = body.vgroup_mass.argmax(1)
        r0, r1 = float(os.environ.get('GP_ROOT_NEAR', .03)), float(os.environ.get('GP_ROOT_FAR', .06))
        for g in drop:
            if root[g] not in body.names: continue
            r = body.names.index(root[g]); cols_ = [i for i, x in enumerate(bg) if x == g]
            # only cloth NEAR that limb's own skin (the binding beside the arm) moves to the root; farther in (the back over the shoulder
            # blade, whose torso skin is partly arm-weighted) the cloth keeps the skin's real weights, fading over r0..r1
            lv = np.nonzero(dom == GNAMES.index(g))[0]
            j_, d_ = NR.PointGrid(body.P[lv], r1).nearest(P) if len(lv) else (np.full(n, -1), np.full(n, 9.0))
            d_ = np.where(j_ < 0, 9.0, d_)
            f_ = 1 - np.clip((d_ - r0) / max(r1 - r0, 1e-6), 0, 1)
            moved = W[:, cols_].sum(1) * f_; W[:, cols_] *= (1 - f_)[:, None]; W[:, r] += moved
            if moved.sum() > 0: log('  weights: %.1f%% of the matched weight moved from %s to %s (limb not wrapped)' % (100 * moved.sum() / max(W.sum(), 1e-9), g, root[g]))
    # LIMB TUBE (10-18): cloth inside the tube round a limb the garment WRAPS (along the upper arm / thigh, within its skin radius + TUBE_EASE, nearer the limb than the torso)
    # takes that limb's own skin weights, faded in past the shoulder / hip. Otherwise a sleeve's underside copies the torso skin it faces
    # in the A-pose and the sleeve splits into strips when the arm rises (golf female raglan R4).
    if os.environ.get('GP_LIMB_TUBE', '1') == '1':
        dom = body.vgroup_mass.argmax(1)
        for g, root_bone in (('AL', 'LeftUpperArm'), ('AR', 'RightUpperArm'), ('LL', 'LeftUpperLeg'), ('LR', 'RightUpperLeg')):
            if not cg[GNAMES.index(g)] or root_bone not in body.names: continue
            bi_ = body.names.index(root_bone)
            bv = np.nonzero(body.W.argmax(1) == bi_)[0]
            if len(bv) < 50: continue
            X = body.P[bv]; c = X.mean(0); ax = np.linalg.svd(X - c, full_matrices=False)[2][0]
            tb = (X - c) @ ax; t0, t1 = np.percentile(tb, 2), np.percentile(tb, 98)
            # orient the axis from the limb root (nearest the body centre) outward
            if np.linalg.norm(c + ax * t0 - body.P.mean(0)) > np.linalg.norm(c + ax * t1 - body.P.mean(0)): ax, t0, t1 = -ax, -t1, -t0
            tv = ((P - c) @ ax - t0) / max(t1 - t0, 1e-6)
            rv = np.linalg.norm((P - c) - np.outer((P - c) @ ax, ax), axis=1)
            # the tube follows the limb's own skin radius (p95 per 10 % of its length) + TUBE_EASE: never the torso panels beside the armpit
            tbn = (tb - t0) / max(t1 - t0, 1e-6); rb = np.linalg.norm((X - c) - np.outer(tb, ax), axis=1)
            edges = np.linspace(0, 1, 11); mids = (edges[:-1] + edges[1:]) / 2
            prof = np.array([np.percentile(rb[(tbn >= a) & (tbn < b)], 95) if ((tbn >= a) & (tbn < b)).sum() > 5 else np.nan for a, b in zip(edges[:-1], edges[1:])])
            ok_ = ~np.isnan(prof); prof = np.interp(mids, mids[ok_], prof[ok_])
            rlim = np.interp(np.clip(tv, 0, 1), mids, prof) + TUBE_EASE
            f = np.clip((tv - .15) / .20, 0, 1) * (rv < rlim) * (tv < 1.3)
            sel = np.nonzero(f > 0)[0]
            if not len(sel): continue
            l2, f2, d2 = body.nearest(P[sel], (g,))
            # and only cloth nearer to this limb's skin than to the torso's (fade over 1 cm)
            dT = body.nearest(P[sel], ('T', 'P'))[2]
            f[sel] *= np.clip((dT - d2) / .01, 0, 1)
            Wl = body.weights_at(l2, f2)
            W[sel] = (1 - f[sel, None]) * W[sel] + f[sel, None] * Wl
            match[sel] = True
            log('  weights: limb tube %s: %d cloth vertices follow %s' % (g, int((f > .5).sum()), root_bone))
    # 3. lining copies its own shell: nearest outer-wall vertex of the same panel group, across the wall (applied after the fill)
    known = match.copy()
    pairs = []
    if inner.any():
        outer_idx = np.nonzero(~inner)[0]
        keys = {a: i for i, a in enumerate(sorted(set(allowed.values())))}
        key_of = np.array([keys[allowed[p]] for p in panel])
        for kv in np.unique(key_of[inner]):
            cand = outer_idx[key_of[outer_idx] == kv]
            if not len(cand): continue
            tgt = np.nonzero(inner & (key_of == kv))[0]
            j, d = NR.PointGrid(P[cand], .02).nearest(P[tgt])
            ok = (j >= 0) & (d < .02)
            pairs.append((tgt[ok], cand[j[ok]]))
    # 4. harmonic fill + diffusion over the sewn graph
    cols = np.nonzero(W[known].any(0))[0]                     # only the bones the matched skin uses
    Wc = sewn.harmonic(W[:, cols], known)
    for tv, ov in pairs: Wc[tv] = Wc[ov]
    step = np.median(sewn.elen[sewn.elen > 1e-4]) if (sewn.elen > 1e-4).any() else .004
    iters = int(round((smooth_cm / 100.0 / step) ** 2 * .5))
    Wc = sewn.smooth(Wc, iters)
    # adaptive: where the weights still change fast (the armhole between a sleeve and the torso, the crotch between the legs) the
    # transition is spread wider, so a raised arm stretches a band of cloth instead of tearing one row of triangles
    if transition_cm > smooth_cm:
        g = np.abs(sewn.average(Wc) - Wc).sum(1)
        m = np.clip(g / max(np.percentile(g, 97), 1e-9), 0, 1)
        m = np.clip(sewn.smooth(m[:, None], int(round((transition_cm / 100.0 / step) ** 2 * .25)))[:, 0] * 3, 0, 1)
        Wc = sewn.smooth(Wc, int(round((transition_cm / 100.0 / step) ** 2 * .5)), mask=m)
    for tv, ov in pairs: Wc[tv] = Wc[ov]
    W = np.zeros_like(W); W[:, cols] = Wc
    W = np.maximum(W, 0); W /= np.maximum(W.sum(1, keepdims=True), 1e-12)
    info = {'panels': int(panel.max() + 1), 'matched': float(match.mean()), 'inner': float(inner.mean()),
            'smooth_iters': iters, 'edge_mm': float(step * 1000), 'allowed': {int(k): v for k, v in allowed.items()},
            'side_mm_p5': float(np.percentile(side[~inner], 5) * 1000)}
    log('  weights: %d panels, matched %.0f%%, inner %.0f%%, smooth %d it (edge %.1f mm)' % (info['panels'], 100 * info['matched'], 100 * info['inner'], iters, info['edge_mm']))
    if fw_side: info.update(footwear=fw_side[0], foot_mass=fw_side[1])
    return W, info, dict(panel=panel, inner=inner, dist=dist, face=face, side=side)


def weld_labels(P, tol):
    """label per vertex: vertices closer than ~tol share a label (grid hashing on two offset grids, union-find)."""
    n = len(P); parent = np.arange(n)
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for off in (0.0, .5):
        q = np.floor(P / tol + off).astype(np.int64)
        key = (q[:, 0] << 42) ^ (q[:, 1] << 21) ^ q[:, 2]
        o = np.argsort(key, kind='stable'); ks = key[o]
        same = np.nonzero(ks[1:] == ks[:-1])[0]
        for i in same:
            a, b = o[i], o[i + 1]
            if np.linalg.norm(P[a] - P[b]) <= tol:
                ra, rb = find(a), find(b)
                if ra != rb: parent[rb] = ra
    roots = np.array([find(i) for i in range(n)])
    _, lab = np.unique(roots, return_inverse=True)
    return lab


def group_mean(X, lab):
    """replace every row by the mean of its label group (rows of any trailing shape)."""
    cnt = np.bincount(lab).astype(float)
    flat = X.reshape(len(X), -1)
    S = np.zeros((cnt.size, flat.shape[1])); np.add.at(S, lab, flat)
    return (S / cnt[:, None])[lab].reshape(X.shape)
