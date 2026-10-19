"""GARMENT PIPELINE: the stress test. Per frame, GPU id renders from 24 orthographic views:
  TEAR   pixel shows body skin that a garment covers in the bind pose, with that garment's surface less than DELTA behind it
         (skin poked through the cloth; skin legitimately exposed beside a lifted hem has no cloth just behind it, so it does not count)
  LAYER  same for a garment covered by another garment (shorts waistband through the polo, sock through the shoe)
Noise filter: 3x3 opening per view (isolated specks of one or two pixels are dropped). Pixel size = Renderer.mpp (3.1 mm)."""
import hashlib, os
import numpy as np
import render as RD
import classify as CL

DELTA = .025


def item_key(it):
    h = hashlib.sha1()
    for a in (it.P, it.tri): h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()[:16]


def pose_key(it):
    """item_key + everything that changes the POSED garment (weights, corrective shapes and their driver): for pose-dependent checkpoints."""
    h = hashlib.sha1(item_key(it).encode())
    for a in (getattr(it, 'bi', None), getattr(it, 'bw', None), getattr(it, 'shapes', None)):
        if a is not None: h.update(np.ascontiguousarray(a).tobytes())
    c = getattr(it, 'corr', None)
    if c is not None: h.update(np.ascontiguousarray(c.C).tobytes())
    return h.hexdigest()[:16]


def fib_dirs(n):
    i = np.arange(n) + .5
    phi = np.arccos(1 - 2 * i / n); th = np.pi * (1 + 5 ** .5) * i
    return np.stack([np.cos(th) * np.sin(phi), np.cos(phi), np.sin(th) * np.sin(phi)], 1)


def coverage_vertices(items, ndirs=96, res=1024, escape_frac=.08, cone=.3):
    """GPU version of the covered test. Per item, per vertex: uint32 bitmask of the items that cover it in the REST pose.
    Over the directions within ~72 deg of the vertex normal: the vertex escapes when it is visible from more than escape_frac of them;
    otherwise it is covered by every garment that lies in front of it along at least one of them. Body triangles: all (the FULL body)."""
    R = RD.Renderer(res, res, 1.05)
    cov_ids = [k for k, i in enumerate(items) if i.kind != 'body' and not i.tag.startswith('Acc_Cap')]
    allb = [R.batch(it.P, it.tri, np.full(len(it.tri), k + 1, np.uint32)) for k, it in enumerate(items)]
    centre = items[0].P.mean(0)
    N = [CL.vnormals(it.P, it.tri) for it in items]
    vis = [np.zeros(len(it.P)) for it in items]; tested = [np.zeros(len(it.P)) for it in items]
    bits = [np.zeros(len(it.P), np.uint32) for it in items]
    for d in fib_dirs(ndirs):
        el = float(np.arcsin(np.clip(d[1], -1, 1))); az = float(np.arctan2(d[0], d[2]))
        V = RD.view_matrix(centre, az, el)
        Vn = np.array(V)
        _, DF = R.draw(allb, V)
        DC = {c: R.draw([allb[c]], V)[1] for c in cov_ids}
        for k, it in enumerate(items):
            cosn = N[k] @ d
            sel = cosn >= cone
            if not sel.any(): continue
            q = it.P[sel] @ Vn[:3, :3].T + Vn[:3, 3]
            px = np.clip(((q[:, 0] / R.half_w + 1) * .5 * R.W).astype(int), 0, R.W - 1)
            py = np.clip(((1 - (q[:, 1] / R.half_h + 1) * .5) * R.H).astype(int), 0, R.H - 1)
            z = -q[:, 2]
            tan = np.sqrt(np.maximum(1 - cosn[sel] ** 2, 0)) / np.maximum(cosn[sel], .2)
            eps = .0015 + .75 * R.mpp * tan
            ok = DF[py, px] >= z - eps
            idx = np.nonzero(sel)[0]
            vis[k][idx] += ok; tested[k][idx] += 1
            for c in cov_ids:
                if c == k: continue
                on = DC[c][py, px] < z - eps
                bits[k][idx[on]] |= np.uint32(1 << c)
    # a garment is a victim only on its outward-facing surface (its lining faces the skin and is never seen from outside)
    import nearest as NR
    body = items[0]
    bs = NR.Surface(body.tri, len(body.P)); bn = CL.vnormals(body.P, body.tri)
    out = []
    outer_tri = {}
    for k, it in enumerate(items):
        esc = vis[k] > escape_frac * np.maximum(tested[k], 1)
        b = np.where(esc, 0, bits[k]).astype(np.uint32)
        if it.kind != 'body':
            _, _, f, bc, _ = bs.query(body.P, it.P)
            nb = (bc[:, :, None] * bn[body.tri[f]]).sum(1)
            outward = (N[k] * nb).sum(1) >= 0
            b[~outward] = 0
            outer_tri[k] = it.tri[outward[it.tri].all(1)]
        out.append(b)
    # skin INSIDE a garment's outer wall is covered by it even where the multi-ray test escapes through an opening (a foot seen down
    # the collar of a shoe, a chest seen down the neckline): signed distance to the garment's outward-facing surface < 0
    for c in cov_ids:
        if c not in outer_tri or not len(outer_tri[c]): continue
        it = items[c]
        lo, hi = it.P.min(0) - .05, it.P.max(0) + .05
        m = ((body.P > lo) & (body.P < hi)).all(1)
        if not m.any(): continue
        sd, *_ = NR.Surface(outer_tri[c], len(it.P)).signed(it.P, body.P[m])
        ins = np.nonzero(m)[0][(sd < 0) & (sd > -.08)]
        out[0][ins] |= np.uint32(1 << c)
    return out


def limb_filter(items, tb, bones):
    """a garment covers limb skin only where it FOLLOWS and WRAPS that limb: clear bit k on body triangles whose dominant group is an arm / leg
    group that garment k carries < 2 % of its weight on (the arm under a sleeveless armhole rim at rest moves away from the cloth; it is
    never 'covered' by it, so it is neither hidden nor a tear)."""
    import weights as WT
    body = items[0]
    bpal = [bones[g] for g in body.gidx] if body.gidx is not None else list(bones)
    bgrp = np.array([WT.GNAMES.index(WT.bone_group(n, bpal)) for n in bpal])
    gname = {n: int(g) for n, g in zip(bpal, bgrp)}
    G = np.zeros((len(body.P), len(WT.GNAMES)))
    for j in range(body.bi.shape[1]): np.add.at(G, (np.arange(len(body.P)), bgrp[body.bi[:, j]]), body.bw[:, j])
    fgroup = G[body.tri].sum(1).argmax(1)
    limbs = [WT.GNAMES.index(g) for g in ('AL', 'AR', 'LL', 'LR')]
    out = [t.copy() for t in tb]
    wbody = None
    for k, it in enumerate(items):
        if it.kind == 'body' or it.bi is None: continue
        pal = [bones[g] for g in it.gidx] if it.gidx is not None else list(bones)
        ig = np.array([gname.get(n, 0) for n in pal])          # groups by NAME through the body palette (ArmBlend_x_y index it)
        m = np.zeros(len(WT.GNAMES))
        for j in range(it.bi.shape[1]): np.add.at(m, ig[it.bi[:, j]], it.bw[:, j])
        m /= max(m.sum(), 1e-12)
        # wrapped = the covered skin of that limb surrounds its bone (a sleeve, a trouser leg), the same test the weights use
        if wbody is None: wbody = WT.Body(body, bpal)
        mine = np.zeros(len(body.P), bool); mine[body.tri[(tb[0] >> np.uint32(k)) & 1 == 1].ravel()] = True
        enc = WT.limb_enclosed(wbody, mine, it.P)
        for g in limbs:
            if m[g] < .02 or not enc[WT.GNAMES[g]]:
                sel = fgroup == g
                out[0][sel] &= ~np.uint32(1 << k)
    return out


def coverage(items, cache_dir=None, vertices=False):
    """per item: per-triangle uint32 coverer bitmask (bit k = items[k] covers it; body never covers; rigid caps never cover).
    vertices=True also returns the per-vertex masks."""
    key = hashlib.sha1(('v2-inside' + ''.join(item_key(i) + i.tag for i in items)).encode()).hexdigest()[:16]
    path = os.path.join(cache_dir, f'coverg_{key}.npz') if cache_dir else None
    if path and os.path.exists(path):
        z = np.load(path)
        vb = [z['v_' + i.tag] for i in items]
    else:
        vb = coverage_vertices(items)
        if path:
            os.makedirs(cache_dir, exist_ok=True); np.savez(path, **{'v_' + i.tag: b for i, b in zip(items, vb)})
    tb = [v[it.tri[:, 0]] & v[it.tri[:, 1]] & v[it.tri[:, 2]] for v, it in zip(vb, items)]
    return (tb, vb) if vertices else tb


class Stress:
    def __init__(self, rig_, items, cover_bits, views=None, R=None):
        self.rig, self.items, self.bits = rig_, items, cover_bits
        self.R = R or RD.Renderer()
        self.views = views or RD.view_dirs()
        self.garments = [k for k, i in enumerate(items) if i.kind != 'body']
        self.off = np.cumsum([0] + [len(i.tri) for i in items])[:-1]
        self.gbits = np.concatenate(cover_bits).astype(np.uint32)
        # garment triangles that face the skin (lining / inner wall): seeing one where the full body would be in front = a hole
        import nearest as NR
        body = items[0]; bs = NR.Surface(body.tri, len(body.P)); bn = CL.vnormals(body.P, body.tri)
        inner = []
        for it in items:
            if it.kind == 'body': inner.append(np.zeros(len(it.tri), bool)); continue
            c = it.P[it.tri].mean(1)
            fn = np.cross(it.P[it.tri[:, 1]] - it.P[it.tri[:, 0]], it.P[it.tri[:, 2]] - it.P[it.tri[:, 0]])
            _, _, f, bc, _ = bs.query(body.P, c)
            nb = (bc[:, :, None] * bn[body.tri[f]]).sum(1)
            inner.append((fn * nb).sum(1) < 0)
        self.ginner = np.concatenate(inner)
        self.hidden_any = body.kind == 'body' and not body.drawn.all()
        # layer victims grouped so that no member covers another member (one exclusion render per group)
        layered = [g for g in self.garments if self.bits[g].any()]
        covers = {g: {h for h in self.garments if (np.bitwise_or.reduce(self.bits[g]) >> h) & 1} for g in layered}
        self.groups = []
        for g in sorted(layered, key=lambda g: -int((self.bits[g] != 0).sum())):
            for grp in self.groups:
                if all(h not in covers[g] and g not in covers.get(h, ()) for h in grp): grp.append(g); break
            else: self.groups.append([g])

    def posed(self, mats, shape_w, overrides=None):
        out = []
        for it in self.items:
            if overrides and it.tag in overrides: out.append(overrides[it.tag]); continue
            out.append(self.rig.posem(it, mats, shape_w.get(it.tag) if shape_w else None))
        return out

    def _batch(self, Ps, which):
        bs = []
        for k in which:
            it = self.items[k]
            sel = np.nonzero(it.drawn)[0] if it.kind == 'body' else np.arange(len(it.tri))
            ids = ((k + 1) << 20) | sel.astype(np.uint32)
            bs.append(self.R.batch(Ps[k], it.tri[sel], ids))
        return bs

    def frame(self, Ps, keep_masks=False, views=None):
        """-> dict counts {'tear': px, 'layer': px, 'by': {victim_tag: px}, 'views': [px per view]}; masks per view if keep_masks"""
        body = [k for k, i in enumerate(self.items) if i.kind == 'body']
        full = self._batch(Ps, body + self.garments)
        passes = [(np.array(body), self._batch(Ps, self.garments))]
        passes += [(np.array(grp), self._batch(Ps, [h for h in self.garments if h not in grp])) for grp in self.groups]
        centre = Ps[body[0]].mean(0) if body else np.zeros(3)
        res = {'tear': 0, 'layer': 0, 'holes': 0, 'by': {}, 'views': []}
        fullbody = None
        if self.hidden_any:
            b0 = self.items[body[0]]
            fullbody = [self.R.batch(Ps[body[0]], b0.tri, np.full(len(b0.tri), 1, np.uint32))]
        for vi, (az, el) in enumerate(views or self.views):
            V = RD.view_matrix(centre, az, el)
            ids, dep = self.R.draw(full, V)
            item = (ids >> 20).astype(np.int64) - 1
            g = np.where(item >= 0, self.off[np.clip(item, 0, None)] + (ids & 0xFFFFF).astype(np.int64), -1)
            fg = g >= 0
            b = np.zeros(ids.shape, np.uint32); b[fg] = self.gbits[g[fg]]
            cand = fg & (b != 0)
            viol = np.zeros(ids.shape, bool); covit = np.full(ids.shape, -1, np.int64)
            if cand.any():
                for victims, bt in passes:
                    vm = cand & np.isin(item, victims)
                    if not vm.any(): continue
                    cids, cdep = self.R.draw(bt, V)
                    cit = (cids >> 20).astype(np.int64) - 1
                    nv = vm & (cit >= 0) & (((b >> np.clip(cit, 0, 31).astype(np.uint32)) & 1) == 1) & (cdep - dep < DELTA)
                    covit = np.where(nv & ~viol, cit, covit); viol |= nv
            if fullbody is not None:
                _, db = self.R.draw(fullbody, V)
                seen_inner = fg & self.ginner[np.clip(g, 0, None)]
                beh = db < dep - .003
                h_bg, h_in = RD.open3(beh & ~fg), RD.open3(beh & seen_inner)
                h_deep = RD.open3(beh & fg & ~seen_inner & (dep - db > .03))       # an OUTER garment surface > 3 cm behind the hidden skin
                hole = h_bg | h_in | h_deep
                res['holes'] += int(hole.sum())
                # split: background / lining are real see-through; 'deep' is often a solid outer surface (a low shoe upper under a taller
                # cartoon forefoot), shown separately
                res['holes_bg'] = res.get('holes_bg', 0) + int(h_bg.sum()); res['holes_inner'] = res.get('holes_inner', 0) + int(h_in.sum())
                res['holes_deep'] = res.get('holes_deep', 0) + int(h_deep.sum())
                if keep_masks: res.setdefault('hole_masks', []).append(hole)
            clean = RD.open3(viol)
            if clean.any():
                ks, cs = np.unique(item[clean], return_counts=True)
                for k, c in zip(ks, cs):
                    tag = self.items[k].tag
                    res['by'][tag] = res['by'].get(tag, 0) + int(c)
                    res['tear' if self.items[k].kind == 'body' else 'layer'] += int(c)
                pk, pc = np.unique(item[clean] * 64 + covit[clean], return_counts=True)       # victim <- coverer (which garment it tears through)
                for k, c in zip(pk, pc):
                    key = '%s<%s' % (self.items[k // 64].tag, self.items[k % 64].tag if k % 64 < len(self.items) else '?')
                    res.setdefault('pair', {})[key] = res.get('pair', {}).get(key, 0) + int(c)
            res['views'].append(int(clean.sum()))
            if keep_masks: res.setdefault('masks', []).append((clean, ids, dep, V))
        return res
