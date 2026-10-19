"""GARMENT PIPELINE: the body cover (which skin triangles are not drawn) for a hero's whole worn set (Blender headless, GPU).
A skin triangle covered in the bind pose (evaluate.coverage) is hidden unless, in some frame of some clip, it is seen LEGITIMATELY:
visible with no covering garment just behind it (DELTA) - i.e. exposed beside a hem, cuff or opening, not poking through cloth.
Every frame of every clip is tested (step 2 at 30 fps) from 12 views, then a one-ring safety band around everything seen is kept.
Blender -b --factory-startup --python gp/cover.py -- <hero> <run_dir> [step]
Writes <run_dir>/<hero>/body.npz (drawn per source triangle) + cover.json; per-piece hide lists go to out/ via export_cover()."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import rig, scene, candidate as CA
try:                                   # GPU modules exist only inside Blender; export_cover() runs in plain python
    import evaluate as EV, render as RD
except ImportError:
    EV = RD = None
CHUNK = int(os.environ.get('GP_COVER_CHUNK', 250))


DEEP_OPEN = .06


def deep_tris(items, bits):
    """body triangles farther than DEEP_OPEN from every uncovered body vertex: seeing those 'legitimately' would need a rip, not an opening."""
    import nearest as NR
    body = items[0]
    vb = np.zeros(len(body.P), bool); vb[body.tri[bits[0] == 0].ravel()] = True        # vertices of uncovered triangles
    c = body.P[body.tri].mean(1)
    j, d = NR.PointGrid(body.P[vb], DEEP_OPEN).nearest(c)
    return (bits[0] != 0) & ((j < 0) | (d > DEEP_OPEN))


FOOT_OPEN = .025
FOOTWEAR = ('Shoe', 'Boot', 'Sneaker')


def foot_deep(items, bits, bones=None):
    """-> (hide mask, extra cover bits). Footwear is rigid on the foot (designed last): skin INSIDE a shoe (its box below 75 % of its height,
    4 mm in from the sides) counts as covered by it even where bind-pose rays escape up through the collar, and every skin triangle the
    shoe covers farther than FOOT_OPEN from truly uncovered skin is always hidden."""
    import nearest as NR
    body = items[0]
    c = body.P[body.tri].mean(1)
    extra = np.zeros(len(body.tri), np.int64); fw = 0
    for k, it in enumerate(items):
        if not any(w in it.tag for w in FOOTWEAR): continue
        fw |= 1 << k
        # inside = the shoe has a surface directly ABOVE the skin (5 mm height map of the shoe's top per x/z cell): the instep under a low
        # upper is inside, ankle skin in the collar opening is not (a 75 %-height box hid visible ankle skin above low collars, 10-18)
        cell = .005
        g = np.floor(it.P[:, [0, 2]] / cell).astype(np.int64); key = g[:, 0] * 100003 + g[:, 1]
        top = {}
        for kk, y in zip(key.tolist(), it.P[:, 1].tolist()):
            if y > top.get(kk, -9): top[kk] = y
        gc = np.floor(c[:, [0, 2]] / cell).astype(np.int64); kc = gc[:, 0] * 100003 + gc[:, 1]
        ytop = np.array([top.get(int(x), -9.0) for x in kc])
        lo, hi = it.P.min(0), it.P.max(0)
        box = (c[:, 0] > lo[0] + .004) & (c[:, 0] < hi[0] - .004) & (c[:, 2] > lo[2] + .004) & (c[:, 2] < hi[2] - .004) & (c[:, 1] < lo[1] + .5 * (hi[1] - lo[1]))
        ins = (ytop > c[:, 1] + .002) | box          # under the shoe's top surface, or in the lower half of its box (sides + heel; below any ankle)
        extra[ins] |= 1 << k
    if not fw: return np.zeros(len(body.tri), bool), extra
    if os.environ.get('GP_FOOT_ALL') == '1' and bones is not None:      # opt-in (male-garments chat): foot-weighted skin inside a shoe's footprint is always hidden
        fm = foot_mass(body, bones)
        for k, it in enumerate(items):
            if not any(w in it.tag for w in FOOTWEAR): continue
            lo, hi = it.P.min(0), it.P.max(0)
            inxz = (c[:, 0] > lo[0]) & (c[:, 0] < hi[0]) & (c[:, 2] > lo[2]) & (c[:, 2] < hi[2])
            extra[inxz & (fm[body.tri].mean(1) >= .5)] |= 1 << k
        allb = bits[0].astype(np.int64) | extra
        return ((allb & fw) != 0), extra
    allb = bits[0].astype(np.int64) | extra
    return foot_deep_default(items, bits, allb, fw, c), extra


def foot_deep_default(items, bits, allb, fw, c):
    """footwear-covered skin farther than FOOT_OPEN from truly uncovered skin."""
    import nearest as NR
    body = items[0]
    vb = np.zeros(len(body.P), bool); vb[body.tri[allb == 0].ravel()] = True        # vertices of truly uncovered triangles
    j, d = NR.PointGrid(body.P[vb], FOOT_OPEN).nearest(c)
    return ((allb & fw) != 0) & ((j < 0) | (d > FOOT_OPEN))


def foot_mass(body, bones):
    """per body vertex: skin weight on Foot + Toes bones (bones = hero.bones; body.bi index body.gidx when it has one)."""
    pal = [bones[g] for g in body.gidx] if body.gidx is not None else list(bones)
    fb = np.array([('Foot' in n or 'Toes' in n) for n in pal])
    m = np.zeros(len(body.P))
    for j in range(body.bi.shape[1]): m += body.bw[:, j] * fb[body.bi[:, j]]
    return m


def rest_poke(items, bits, near=.02):
    """covered skin already OUTSIDE its garment's outer wall in the bind pose (a construction overlap, e.g. a trouser crotch dipping under
    the skin) can never be seen legitimately: hide it, whatever a frame showed (10-18 crotch patch in standing poses)."""
    import nearest as NR
    body = items[0]; c = body.P[body.tri].mean(1)
    out = np.zeros(len(body.tri), bool)
    for k, it in enumerate(items):
        if it.kind == 'body' or any(w in it.tag for w in FOOTWEAR): continue
        sel = np.nonzero((bits[0].astype(np.int64) >> k) & 1)[0]
        if not len(sel): continue
        fn = np.cross(it.P[it.tri[:, 1]] - it.P[it.tri[:, 0]], it.P[it.tri[:, 2]] - it.P[it.tri[:, 0]])
        # OUTER wall only: faces whose normal points away from the nearest skin (a lining faces the skin and would flip the sign)
        fc = it.P[it.tri].mean(1)
        _, pt, *_ = NR.Surface(body.tri, body.n).query(body.P, fc)
        otri = it.tri[((fc - pt) * fn).sum(1) > 0]
        if not len(otri): continue
        vn = np.zeros_like(it.P)
        for j in range(3): np.add.at(vn, otri[:, j], np.cross(it.P[otri[:, 1]] - it.P[otri[:, 0]], it.P[otri[:, 2]] - it.P[otri[:, 0]]))
        vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
        sd, *_ = NR.Surface(otri, it.n).signed(it.P, c[sel], vn)
        out[sel[(sd > 0) & (sd < near)]] = True
    return out


def legit_seen(S, Ps, views, seen, deep=None):
    """mark body triangles seen legitimately in this pose (in place)."""
    body = S.items[0]
    allb = [S.R.batch(Ps[0], body.tri, (1 << 20) | np.arange(len(body.tri), dtype=np.uint32))]
    gar = [S.R.batch(Ps[k], S.items[k].tri, ((k + 1) << 20) | np.arange(len(S.items[k].tri), dtype=np.uint32)) for k in S.garments]
    for (az, el) in views:
        V = RD.view_matrix(Ps[0].mean(0), az, el)
        ids, dep = S.R.draw(allb + gar, V)
        item = (ids >> 20).astype(np.int64) - 1
        m = item == 0
        if not m.any(): continue
        t = (ids[m] & 0xFFFFF).astype(np.int64)
        b = S.bits[0][t]
        cids, cdep = S.R.draw(gar, V)
        cit = (cids[m] >> 20).astype(np.int64) - 1
        dp = deep[t] if deep is not None else np.zeros(len(t), bool)
        # deep skin seen inside its garment's silhouette is seen through a rip, never legitimately; near an opening the depth rule decides
        through = (b != 0) & (cit >= 0) & (((b >> np.clip(cit, 0, 31).astype(np.uint32)) & 1) == 1) & (dp | (cdep[m] - dep[m] < EV.DELTA))
        seen[t[~through]] = True


def main():
    argv = sys.argv[sys.argv.index('--') + 1:]
    hid, run = argv[0], argv[1]; step = int(argv[2]) if len(argv) > 2 else 2
    h = rig.Hero(hid); R = scene.Rig(h)
    items = scene.items_from_dump(h)
    cand = CA.load_dir(os.path.join(run, hid), h) if os.path.isdir(os.path.join(run, hid)) else {}
    items = [cand.get(i.tag, i) for i in items]
    have = {i.tag for i in items}; items += [v for k, v in sorted(cand.items()) if k not in have and k != 'body']   # brand-new pieces (not in the dump) join the worn set
    items[0].drawn = np.ones(len(items[0].tri), bool)          # start from the FULL body
    bits = EV.limb_filter(items, EV.coverage(items, cache_dir=os.path.join(rig.PIPE, 'cache', hid)), h.bones)
    S = EV.Stress(R, items, bits, R=RD.Renderer(768, 960, 1.0))
    views = RD.view_dirs(6, els=(-10.0, 15.0, 45.0))
    seen = np.zeros(len(items[0].tri), bool)
    deep = deep_tris(items, bits)
    t0 = time.time(); nf = 0
    # resumable: the seen set is checkpointed every 100 frames (key = the worn set + step)
    import hashlib
    ckey = hashlib.sha1(('deep6limb4' + ''.join(EV.pose_key(i) for i in items) + str(step)).encode()).hexdigest()[:10]
    ckp = os.path.join(run, hid, '_cover_ckpt_%s.npz' % ckey)
    done_n = 0
    if os.path.exists(ckp):
        z = np.load(ckp); seen = z['seen'].copy(); done_n = int(z['n']); print('COVER resume at frame', done_n, flush=True)
    from stress import Library
    lib = Library(hid)
    def stream():
        for clip, f, mats, sw in scene.frame_iter(h, step=step): yield mats, sw
        for i in range(len(lib)): yield lib.mats[i], {t: lib.sw[t][i] for t in lib.sw}
    for mats, sw in stream():
        nf += 1
        if nf <= done_n: continue
        Ps = S.posed(mats, CA.shape_weights(items, sw, mats, h, R))
        legit_seen(S, Ps, views, seen, deep)
        if nf % 100 == 0:
            np.savez(ckp, seen=seen, n=nf)
            print('COVER progress %d frames %.0f s' % (nf, time.time() - t0), flush=True)
        if nf - done_n >= CHUNK or RD.footprint_gb() > RD.MEM_LIMIT_GB:   # GPU work is never freed in background Blender: stop at a frame
            # count OR a memory footprint (GP_MEM_GB, default 3 GB), the caller relaunches from the checkpoint
            np.savez(ckp, seen=seen, n=nf); print('COVER chunk done at', nf, flush=True)
            sys.stdout.flush(); os._exit(3)
    body = items[0]
    covered = bits[0] != 0
    hide = covered & ~seen
    # one-ring safety band: keep every triangle sharing a vertex with a drawn (seen or uncovered) triangle
    keepv = np.zeros(len(body.P), bool); keepv[body.tri[~hide].ravel()] = True
    hide &= ~keepv[body.tri].any(1)
    # footwear is rigid on the foot by construction (designed last): skin it covers farther than FOOT_OPEN from uncovered skin is always
    # hidden. A heel or sole poking out of the shoe in some frame is the foot weights leaking past the last, never a view to keep.
    fd, extra = foot_deep(items, bits, h.bones)
    hide |= fd
    if os.environ.get('GP_REST_POKE') == '1': hide |= rest_poke(items, bits)   # OFF by default: hid visible shoulder skin beside sleeveless armholes (K6 holes 9k -> 239k, 10-18)
    drawn = ~hide
    od = os.path.join(run, hid); os.makedirs(od, exist_ok=True)
    np.savez(os.path.join(od, 'body.npz'), tag='body', drawn=drawn, bits=(bits[0].astype(np.int64) | extra).astype(bits[0].dtype))
    old = scene.items_from_dump(h)[0].drawn
    rep = {'hero': hid, 'frames': nf, 'seconds': round(time.time() - t0, 1), 'body_tris': int(len(drawn)), 'covered': int(covered.sum()),
           'hidden_new': int(hide.sum()), 'hidden_today': int((~old).sum()), 'newly_hidden': int((hide & old).sum()), 'newly_drawn': int((~hide & ~old).sum())}
    json.dump(rep, open(os.path.join(od, 'cover.json'), 'w'), indent=1)
    print('COVER', json.dumps(rep))


def export_cover(h, run, out_dir):
    """split the hidden triangles per worn piece (first covering piece), write <Tag>_hide.bin (int32 vertex triplets) like cover.py did."""
    z = np.load(os.path.join(run, h.id, 'body.npz'))
    drawn, bits = z['drawn'], z['bits']
    items = scene.items_from_dump(h)
    cand = CA.load_dir(os.path.join(run, h.id), h) if os.path.isdir(os.path.join(run, h.id)) else {}
    have = {i.tag for i in items}; items += [v for k, v in sorted(cand.items()) if k not in have and k != 'body']   # same order as main()
    tri = items[0].tri
    hid = np.nonzero(~drawn)[0]
    owner = {}
    for t in hid:
        b = int(bits[t])
        k = (b & -b).bit_length() - 1 if b else -1
        owner.setdefault(k, []).append(t)
    os.makedirs(out_dir, exist_ok=True)
    for k, it in enumerate(items):
        if not it.tag.startswith('Kit_'): continue          # every worn kit piece gets a hide list (possibly empty)
        ts = owner.get(k, [])
        open(os.path.join(out_dir, it.tag + '_hide.bin'), 'wb').write(tri[np.array(ts, np.int64)].astype(np.int32).tobytes() if ts else b'')
        print('HIDE %s %s: %d triangles' % (h.id, it.tag, len(ts)))


if __name__ == '__main__' and '--' in sys.argv:
    main()
