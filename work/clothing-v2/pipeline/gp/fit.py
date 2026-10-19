"""GARMENT PIPELINE: fit one garment to one hero (plain python3, numpy only).
python3 gp/fit.py <hero> <source> <run_dir> [--tag Kit_Top] [--smooth 2.0] [--no-corr] [--keep-weights]
  source: dump:<Tag>            the garment the hero wears today (rest geometry from the Unity dump)
          npz:<path>            a builder export (work/clothing-v2/out/<Hero>/unity/<Piece>_final.npz: body mesh space, Z up)
          obj:<path>            any mesh in body mesh space (metres, Z up, hero faces -Y), one piece
Writes <run_dir>/<hero>/<Tag>.npz (candidate: weights over the hero's bones, correctives + RBF driver) and <Tag>_fit.json."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import rig, scene, weights as WT, correctives as CO, features as FT, graph as GR, candidate as CA, stress as ST, nearest as NR


def load_source(h, src, tag):
    kind, _, path = src.partition(':')
    body = h.body
    if kind == 'dump':
        it = next(i for i in scene.items_from_dump(h) if i.tag == path)
        return it.P, it.tri, it.sub, path, None
    if kind == 'npz':
        z = np.load(path, allow_pickle=True)
        P = scene.to_root(body, z['pos']); tri = z['tri'].astype(np.int64)
        sub = z['mat'].astype(np.int32) if 'mat' in z.files else np.zeros(len(tri), np.int32)
        inner = None
        if 'part' in z.files:                     # builder knows its walls: face part 2 = inner
            part = z['part']; inner = np.zeros(len(P), bool); inner[tri[part == 2].ravel()] = True
            outer = np.zeros(len(P), bool); outer[tri[part == 0].ravel()] = True; inner &= ~outer
        return P, tri, sub, tag or os.path.basename(path).replace('_final.npz', ''), inner
    if kind == 'obj':
        V, F = [], []
        for line in open(path):
            s = line.split()
            if not s: continue
            if s[0] == 'v': V.append([float(x) for x in s[1:4]])
            elif s[0] == 'f':
                idx = [int(x.split('/')[0]) - 1 for x in s[1:]]
                for k in range(1, len(idx) - 1): F.append([idx[0], idx[k], idx[k + 1]])
        P = scene.to_root(body, np.array(V)); tri = np.array(F, np.int64)
        return P, tri, np.zeros(len(tri), np.int32), tag or os.path.splitext(os.path.basename(path))[0], None
    raise SystemExit('unknown source ' + src)


def main():
    a = sys.argv[1:]
    hid, src, run = a[0], a[1], a[2]
    opt = {}; i = 3
    while i < len(a):
        if a[i] in ('--no-corr', '--keep-weights', '--layer-bind', '--no-ride'): opt[a[i][2:]] = True; i += 1
        else: opt[a[i][2:]] = a[i + 1]; i += 2
    t0 = time.time()
    h = rig.Hero(hid); R = scene.Rig(h)
    cur = scene.items_from_dump(h)
    P, tri, sub, tag, inner = load_source(h, src, opt.get('tag'))
    od = os.path.join(run, hid); os.makedirs(od, exist_ok=True)
    # garments already fitted in this run replace today's versions (fit inner layers first: socks, bottoms, then tops, shoes, belts)
    done = CA.load_dir(od, h) if os.path.isdir(od) else {}
    cur = [done.get(i.tag, i) if i.tag != tag else i for i in cur]
    log = []
    def say(*x):
        s = ' '.join(str(y) for y in x); print(s, flush=True); log.append(s)
    say(f'FIT {hid} {tag} from {src}: {len(P)} verts {len(tri)} tris')
    # ---- weights over the hero's full body palette (global ids = body palette order)
    body_it = cur[0]
    names = [h.bones[g] for g in body_it.gidx]
    if opt.get('keep-weights') and src.startswith('dump:'):
        it0 = next(i for i in cur if i.tag == tag)
        W = WT.dense(np.searchsorted(body_it.gidx, it0.gidx)[it0.bi] if set(it0.gidx) <= set(body_it.gidx) else it0.bi, it0.bw, len(names))
        info = {'kept': True}; aux = None
    else:
        body = WT.Body(body_it, names)
        # the skin this garment covers in the bind pose (GPU coverage, the same test as the cover): a panel may only follow covered groups
        tmp_it = scene.Item(tag, 'kit', P, tri, np.zeros((len(P), 4), np.int64), np.tile([1., 0, 0, 0], (len(P), 1)), sub=sub, gidx=body_it.gidx, B=body_it.B)
        cov = covered_skin(h, od, tag, tmp_it, body_it, say)
        if cov is not None: np.save(os.path.join(od, '_covmask_%s.npy' % tag), cov)
        # tight knit (median outer-wall gap to the skin < 5 mm, e.g. socks): 2 cm weight smoothing, else 4 cm (a 4 cm blend dragged foot
        # weight up a sock's ankle: sock tears 125k -> 42k px at 2 cm, K5c 10-18). An explicit smooth= always wins.
        if 'smooth' not in opt:
            bS = NR.Surface(body_it.tri, body_it.n); og = P if inner is None else P[~inner]
            gap = float(np.median(bS.query(body_it.P, og)[0]))
            opt['smooth'] = 2.0 if gap < .005 else 4.0
            say('  tightness: median gap %.1f mm -> weight smoothing %.0f cm' % (gap * 1000, opt['smooth']))
        W, info, aux = WT.transfer(body, P, tri, cover_mask=cov, smooth_cm=float(opt.get('smooth', 4.0)), inner=inner, log=say, transition_cm=float(opt.get('transition', 0)))   # 4 cm: best of the 10-17 A/B (2 / 4 / 6)
    # layer binding: where this garment lies UNDER another worn garment (shorts waistband under the polo hem, sock inside a shoe collar),
    # it takes the outer garment's weights there (fading out over 3 cm below the overlap), so the two layers move together and never cross
    # (A/B 10-17: binding the male shorts to the polo dragged the waistband up and crumpled it when the hem rose with the arms: OFF by default)
    outers = [] if not opt.get('layer-bind') else [o for o in cur[1:] if o.tag != tag and o.kind == 'kit' and _covers(o.P, o.tri, scene.Item(tag, 'kit', P, tri, np.zeros((len(P), 1), int), np.ones((len(P), 1))), body_it)]
    for o in outers:
        oW = WT.dense(np.searchsorted(body_it.gidx, o.gidx)[o.bi] if o.gidx is not None else o.bi, o.bw, len(names))
        osurf = NR.Surface(o.tri, o.n)
        d, pt, f, bc, fn = osurf.query(o.P, P)
        Wo = sum(bc[:, k:k + 1] * oW[o.tri[f, k]] for k in range(3))
        t = np.clip((.045 - d) / .030, 0, 1) ** 2                      # 1 within 1.5 cm of the outer garment, 0 beyond 4.5 cm
        t = GR.Graph(P, tri).smooth(t[:, None], 6)[:, 0]
        W = (1 - t[:, None]) * W + t[:, None] * Wo
        say('  layer binding under %s: %d vertices follow it (t > .5)' % (o.tag, int((t > .5).sum())))
    # hem riding: where this garment lies OVER another worn garment (the polo hem over the shorts waistband), its cloth takes that
    # garment's weights within the overlap (fading out over 3 cm above it): a hem rests on the waistband instead of sinking into it
    if not opt.get('no-ride') and not info.get('footwear'):        # footwear stays rigid on the foot: never rides the sock
        Gi = scene.Item(tag, 'kit', P, tri, np.zeros((len(P), 1), int), np.ones((len(P), 1)))
        for u in [u for u in cur[1:] if u.tag != tag and u.kind == 'kit' and _covers(P, tri, u, body_it)]:
            uW = WT.dense(np.searchsorted(body_it.gidx, u.gidx)[u.bi] if u.gidx is not None else u.bi, u.bw, len(names))
            usurf = NR.Surface(u.tri, u.n)
            d, pt, f, bc, fn = usurf.query(u.P, P)
            Wu = sum(bc[:, k:k + 1] * uW[u.tri[f, k]] for k in range(3))
            t = np.clip((.045 - d) / .030, 0, 1) ** 2
            t = GR.Graph(P, tri).smooth(t[:, None], 6)[:, 0]
            W = (1 - t[:, None]) * W + t[:, None] * Wu
            say('  hem riding on %s: %d vertices follow it (t > .5)' % (u.tag, int((t > .5).sum())))
    # sewn seams: vertices that coincide at rest (UV splits, panel seams) take the SAME weights, or the seam opens when posed
    # (10-17: the male polo's sleeve/front seams split up to 118 mm in Thrust; today's installed polo 73 mm)
    weld = WT.weld_labels(P, WELD_TOL)
    W = WT.group_mean(W, weld)
    say('  seams: %d coincident vertices welded into %d groups' % (int((np.bincount(weld)[weld] > 1).sum()), int((np.bincount(weld) > 1).sum())))
    bi, bw = WT.prune(W, 4)
    gidx = body_it.gidx
    item = scene.Item(tag, 'kit', P, tri, bi, bw, sub=sub, gidx=gidx, B=body_it.B)
    say('  weights %.1f s' % (time.time() - t0))
    # ---- correctives over the stress library
    lib = ST.Library(hid)
    if inner is None:
        inner = aux['inner'] if aux is not None else np.zeros(len(P), bool)
    shapes = np.zeros((0, len(P), 3)); anchors = np.zeros((0, 1)); coef = np.zeros((0, 0)); sigma = 1.0
    if info.get('footwear'):
        say('  footwear is stiff: no pose correctives (a rigid shoe cannot bend round the sock; lifts there shredded the collar, A/B 10-17)')
    if not opt.get('no-corr') and not info.get('footwear'):
        t1 = time.time()
        graph = GR.Graph(P, tri)
        pairs = []
        if inner.any():
            oi = np.nonzero(~inner)[0]; ii = np.nonzero(inner)[0]
            j, d = NR.PointGrid(P[oi], .02).nearest(P[ii]); ok = (j >= 0) & (d < .015)
            pairs.append((ii[ok], oi[j[ok]]))
        vg = CO.vertex_groups(item, h.bones, WT.GNAMES, WT.bone_group)
        bodyW = WT.Body(body_it, names)
        # skin deep under this garment (> DEEP_SKIN from any skin it does not cover) is hidden by the cover: it needs no clearance
        fgroup = bodyW.fgroup.copy()
        deep = deep_covered(h, od, tag, item, body_it, say)
        if deep is not None:
            fgroup[deep[body_it.tri].all(1)] = -1                   # group -1 = not an obstacle
            say('  skin deep under %s (hidden, no clearance needed): %d of %d body vertices' % (tag, int(deep.sum()), len(deep)))
        obs_body = CO.Obstacle('body', body_it.tri, body_it.n, fgroup=fgroup)
        obs_body.rest_c = body_it.P[body_it.tri].mean(1)
        # garments this one covers (they must stay under it): from the rest coverage of the worn set
        under = [i for i in cur[1:] if i.tag != tag and i.kind == 'kit' and _covers(P, tri, i, body_it)]
        # garments over this one (the polo over the shorts waistband, the shoe over the sock): this garment must stay INSIDE them
        covered_by = [o for o in cur[1:] if o.tag != tag and o.kind == 'kit' and o not in under and _covers(o.P, o.tri, item, body_it)]
        over = covered_by if os.environ.get('GP_HEM_LAYER', '0') == '1' else []   # OFF by default: ill-defined near an open hem rim (K5_MT shorts layer 37k -> 485k, 10-18)
        # the compression bulge only for OUTER garments: a bulging under-garment pushes through the one over it (K6_MT shorts 58k -> 431k)
        bulge_k = 0.0 if covered_by else None
        if covered_by and CO.BULGE_K > 0: say('  compression bulge off: under ' + ', '.join(o.tag for o in covered_by))
        obs = [(obs_body, body_it, 'body')] + [(CO.Obstacle(u.tag, u.tri, u.n), u, u.tag) for u in under] + [(CO.Obstacle(o.tag, o.tri, o.n, inside=True), o, o.tag + '^') for o in over]
        say('  obstacles: body' + ''.join(' + ' + u.tag for u in under) + ''.join(' + inside ' + o.tag for o in over))
        rest_ok = {}
        Rrest = np.tile(np.eye(4), (len(h.bones), 1, 1))
        for (ob, it_, key) in obs:
            sd, _ = CO.signed_to(ob, it_.P, P, vg if ob.fgroup is not None else None)
            rest_ok[key] = ((sd > CO.REST_SKIP) & (sd < CO.NEAR)).astype(float)
        fields, feats = [], []
        # per-pose checkpoints (the machine can restart mid-run): keyed by the weights + obstacles, resumed automatically
        import hashlib
        ck = hashlib.sha1(bi.tobytes() + bw.astype(np.float32).tobytes() + fgroup.astype(np.int16).tobytes() + (''.join(k for _, _, k in obs) + str(CO.DEEP) + str(CO.DEEP_GARMENT) + str(CO.MARGIN_OUT) + str(CO.MAX_LIFT) + CO.SOLVER + str(CO.SMOOTH_ITERS) + 'b%g' % (CO.BULGE_K if bulge_k is None else bulge_k) + 'o%g' % CO.OWN_DEEP).encode()).hexdigest()[:12]
        ckd = os.path.join(od, 'ckpt_%s_%s' % (tag, ck)); os.makedirs(ckd, exist_ok=True)
        for p in range(len(lib)):
            mats = lib.mats[p]
            cf = os.path.join(ckd, 'p%03d.npy' % p)
            if os.path.exists(cf):
                F_ = np.load(cf).astype(np.float64)
                m_ = np.linalg.norm(F_, axis=1); F_ *= np.minimum(1, CO.MAX_LIFT / np.maximum(m_, 1e-9))[:, None]   # the cap is the solver's last step: idempotent
                fields.append(F_); feats.append(FT.vector(h, mats[None], R.rest)[0]); continue
            sw_p = CA.shape_weights([o[1] for o in obs], {t: lib.sw[t][p] for t in lib.sw}, mats, h, R)
            posed = [(ob, R.posem(it_, mats, sw_p.get(it_.tag)), key) for (ob, it_, key) in obs]
            if p % 25 == 0: say('    pose %d/%d  %.0f s' % (p, len(lib), time.time() - t1))
            fields.append(CO.solve_pose(R, item, mats, posed, graph, inner, pairs, vg, rest_ok, bulge_k=bulge_k))
            feats.append(FT.vector(h, mats[None], R.rest)[0])
            np.save(cf, fields[-1].astype(np.float32))
        fields = np.array(fields); feats = np.array(feats)
        amp = np.linalg.norm(fields, axis=2).max(1) * 1000
        say('  correctives: %d/%d poses need a lift (max %.1f mm, p90 %.1f mm) in %.0f s' % ((amp > .5).sum(), len(amp), amp.max(), np.percentile(amp, 90), time.time() - t1))
        shapes, anchors, T = CO.compress(fields, feats)
        if len(shapes): shapes = np.stack([WT.group_mean(sh, weld) for sh in shapes])      # sewn vertices also share their lifts
        if len(shapes):
            # the bind pose is a neutral anchor: the correctives are exactly zero at rest (the garment's rest shape never changes)
            rest_f = FT.vector(h, R.rest[None], R.rest)[0]
            anchors = np.vstack([anchors, rest_f[None]]); T = np.vstack([T, np.zeros((1, T.shape[1]))])
            sigma, coef = CO.fit_rbf(anchors, T)
            pred = np.clip(np.exp(-((anchors[:, None] - anchors[None]) ** 2).sum(2) / (2 * sigma ** 2)) @ coef, 0, 1)
            say('  %d shapes, RBF sigma %.3f, anchor fit err max %.3f, weight at rest %.4f' % (len(shapes), sigma, np.abs(pred - T).max(), float(pred[-1].max())))
        item.shapes = shapes; item.shape_names = ['GP_Pose%02d' % k for k in range(len(shapes))]
    out = os.path.join(od, tag + '.npz')
    CA.save(out, item, corr_anchor_f=anchors if len(shapes) else np.zeros((0, 1)), corr_coef=coef if len(shapes) else np.zeros((0, 0)),
            corr_sigma=sigma, inner=inner, source=np.array(src))
    json.dump({'hero': hid, 'tag': tag, 'source': src, 'seconds': round(time.time() - t0, 1), 'weights': {k: (str(v) if not isinstance(v, (int, float)) else v) for k, v in info.items()},
               'shapes': len(shapes), 'log': log}, open(os.path.join(od, tag + '_fit.json'), 'w'), indent=1)
    say('FIT DONE %s %s in %.0f s -> %s' % (hid, tag, time.time() - t0, out))


DEEP_SKIN = .03


_COV = {}
WELD_TOL = float(os.environ.get('GP_WELD_TOL', .002))   # 2 mm: binding rings sit ~1.5 mm off the shell (frayed armholes at .75 mm, 10-18)


def EVK(item):
    import hashlib
    hh = hashlib.sha1()
    for a in (item.P, item.tri): hh.update(np.ascontiguousarray(a).tobytes())
    return hh.hexdigest()[:16]


def deep_covered(h, od, tag, item, body_it, say):
    """body vertices covered by this garment in the rest pose and farther than DEEP_SKIN from every body vertex it does not cover."""
    mine = covered_skin(h, od, tag, item, body_it, say)
    if mine is None: return None
    used = np.zeros(body_it.n, bool); used[body_it.tri.ravel()] = True
    free = used & ~mine
    j, d = NR.PointGrid(body_it.P[free], DEEP_SKIN).nearest(body_it.P)
    far = (j < 0) | (d > DEEP_SKIN)
    # GP_COVER_REF=<an earlier run's body.npz cover>: skin that cover still DRAWS (some frame shows it legitimately: the waist under a
    # raised polo, the lower back in a push-up) is not hidden, so it needs clearance however deep it lies (male K8: 3,673 of 7,462 'deep'
    # vertices were drawn, and those were the tears that no corrective could fix: oracle 132,658 = compressed 131,235, 10-18)
    ref = os.environ.get('GP_COVER_REF')
    if ref and os.path.exists(ref):
        drawn = np.load(ref)['drawn']
        if len(drawn) == len(body_it.tri):
            vis = np.zeros(body_it.n, bool); vis[body_it.tri[drawn].ravel()] = True
            say('  cover ref %s: %d of %d deep vertices are drawn -> cleared too' % (ref, int((mine & far & vis).sum()), int((mine & far).sum())))
            far &= ~vis
    return mine & far


def covered_skin(h, od, tag, item, body_it, say):
    """bool per body vertex: covered by this garment in the bind pose (geometry only, cached per tag + geometry)."""
    key = (tag, EVK(item))
    if key in _COV: return _COV[key]
    import subprocess
    tmp = os.path.join(od, '_cov_%s.npz' % tag); cnp = os.path.join(od, '_cand_%s.npz' % tag)
    CA.save(cnp, item)
    import signal
    hv = os.environ.get('GP_HEAVY') or os.path.join(os.path.dirname(__file__), '..', '..', '..', 'delegation-2026-10-17', 'heavy.sh')
    cmd = [hv, 'blender', '/Applications/Blender.app/Contents/MacOS/Blender', '-b', '--factory-startup', '--python', os.path.join(os.path.dirname(__file__), 'cov_cli.py'), '--', h.id, '-', tmp, cnp]
    for attempt in range(3):                       # a Metal context can hang when the display state changes: time out and retry
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            out, err = p.communicate(timeout=1500); break      # includes waiting for a heavy.sh slot
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGTERM); p.communicate()
            say('  (coverage subprocess hung, retry %d)' % (attempt + 1))
            out = err = ''
    class r: stdout, stderr = out, err
    os.remove(cnp)
    if not os.path.exists(tmp): say('  (coverage failed: ' + r.stdout[-300:] + r.stderr[-300:] + ')'); return None
    z = np.load(tmp); bits = z['body_bits']; tags = list(z['tags']); os.remove(tmp)
    k = tags.index(tag)
    mine = ((bits >> k) & 1).astype(bool)
    _COV[key] = mine
    return mine


def _covers(P, tri, under, body_it):
    """True when `under` lies inside this garment where they overlap: its overlapping points are closer to the skin than the
    nearest points of this garment (shorts waistband under the polo hem, sock inside the shoe)."""
    lo, hi = P.min(0) - .03, P.max(0) + .03
    m = ((under.P > lo) & (under.P < hi)).all(1)
    if m.sum() < 50: return False
    surf = NR.Surface(tri, len(P))
    d, pt, *_ = surf.query(P, under.P[m])
    near = d < .03
    if near.sum() < 50: return False
    bs = NR.Surface(body_it.tri, body_it.n)
    du, *_ = bs.query(body_it.P, under.P[m][near])
    dg, *_ = bs.query(body_it.P, pt[near])
    return np.median(du) < np.median(dg)


if __name__ == '__main__':
    main()
