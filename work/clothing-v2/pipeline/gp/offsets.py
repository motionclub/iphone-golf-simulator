"""GARMENT PIPELINE: per-garment body offsets for the hand/arm clearance solver (chat 3; format in work/delegation-2026-10-17/REQUESTS.md).
For every body vertex a worn piece covers (rest coverage), the distance from the FULL body skin to the piece's outward surface, grouped by the
body bone with the largest weight (ArmBlend_* folded into their arm bone). rest p50 / p95, and p95 / max over every 5th stress pose."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import rig, scene, candidate as CA, nearest as NR, stress as ST


def fold(name, palette):
    if name.startswith('ArmBlend_'):
        a = name.split('_'); return palette[int(a[2])] if int(a[3]) >= 4 else palette[int(a[1])]
    return name


def HANDISH(n):
    return any(f in n for f in ('Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Little'))


LIMB = {}


def limb_wrap(h, body, names, cov, it):
    """{limb group: wrapped by this piece} with the same test the weights and the cover use (weights.limb_enclosed)."""
    import weights as WT
    wb = WT.Body(body, names)
    for n in names: LIMB[n] = WT.bone_group(n, names)
    mine = np.zeros(body.n, bool); mine[cov] = True
    enc = WT.limb_enclosed(wb, mine, it.P)
    enc.update({g: True for g in WT.GNAMES if g not in enc})
    return enc


def write(hid, run, out):
    h = rig.Hero(hid); R = scene.Rig(h)
    items = scene.items_from_dump(h)
    d = os.path.join(run, hid)
    cand = CA.load_dir(d, h) if os.path.isdir(d) else {}
    items = [cand.get(i.tag, i) for i in items]
    have = {i.tag for i in items}; items += [v for k, v in sorted(cand.items()) if k not in have and k != 'body']
    body = items[0]
    names = [h.bones[g] for g in body.gidx]
    dom = [fold(names[j], names) for j in body.bi[np.arange(body.n), body.bw.argmax(1)]]
    bn = np.zeros_like(body.P)
    fn = np.cross(body.P[body.tri[:, 1]] - body.P[body.tri[:, 0]], body.P[body.tri[:, 2]] - body.P[body.tri[:, 0]])
    for k in range(3): np.add.at(bn, body.tri[:, k], fn)
    lib = ST.Library(hid); poses = range(0, len(lib), 5)
    res = {'version': 1, 'hero': hid, 'units': 'm', 'pieces': [], 'bones': {}}
    for it in items[1:]:
        if not it.tag.startswith('Kit_'): continue
        inner = np.zeros(it.n, bool)
        z = os.path.join(d, it.tag + '.npz')
        if os.path.exists(z) and 'inner' in np.load(z).files: inner = np.load(z)['inner'].astype(bool)
        otri = it.tri[~inner[it.tri].any(1)]
        surf = NR.Surface(otri, it.n)
        lo, hi = it.P.min(0) - .02, it.P.max(0) + .02
        m = ((body.P > lo) & (body.P < hi)).all(1)
        sd, *_ = surf.signed(it.P, body.P[m])
        inn = (sd < 0) & (sd > -.08)
        cov = np.nonzero(m)[0][inn]                                          # skin inside the outer wall = covered
        rest = -sd[inn]
        foot = any(w in it.tag for w in ('Shoe', 'Boot'))
        if foot:                                                             # footwear: the foot inside the shoe's box (as the cover does)
            ins = m & (body.P[:, 1] < lo[1] + .02 + .75 * (hi[1] - lo[1] - .04)) & np.array(['Foot' in dm or 'Toes' in dm for dm in dom])
            cov = np.nonzero(ins)[0]
            s_, *_ = surf.signed(it.P, body.P[cov]); rest = np.abs(s_)
        # only skin this piece really carries: never hands / fingers (unless the piece is a glove), never a limb the piece does not wrap
        # (a hand hanging against the skirt read 0.6 m of 'cloth' once it moved away, 10-18)
        glove = 'Glove' in it.tag
        enc = limb_wrap(h, body, names, cov, it)
        keep = np.array([(glove or not HANDISH(dom[i])) and (foot or enc.get(LIMB.get(dom[i]), True)) for i in cov], bool)
        cov, rest = cov[keep], rest[keep]
        if not len(cov): continue
        posed = []
        for p in poses:
            mats = lib.mats[p]; sw = {t: lib.sw[t][p] for t in lib.sw}
            sw = CA.shape_weights([body, it], sw, mats, h, R)
            Pb = R.posem(body, mats, sw.get('body')); Pg = R.posem(it, mats, sw.get(it.tag))
            s2, *_ = surf.signed(Pg, Pb[cov]); posed.append(np.abs(s2) if foot else -s2)
        posed = np.array(posed)
        posed = np.where(posed > .08, np.nan, posed)                          # moved out from under this cloth in that pose
        per = {}
        for b in sorted(set(dom[i] for i in cov)):
            sel = np.array([dom[i] == b for i in cov])
            if sel.sum() < 5: continue
            pp = posed[:, sel]
            if not np.isfinite(pp).any(): continue
            per[b] = {'rest_p50': round(float(np.percentile(rest[sel], 50)), 4), 'rest_p95': round(float(np.percentile(rest[sel], 95)), 4),
                      'pose_p95': round(float(np.nanpercentile(pp, 95)), 4), 'max': round(float(np.nanmax(pp)), 4)}
            res['bones'][b] = max(res['bones'].get(b, 0.0), per[b]['pose_p95'])
        res['pieces'].append({'piece': it.tag, 'bones': per})
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, 'w'), indent=1)
    print('OFFSETS', hid, out, json.dumps(res['bones']))


if __name__ == '__main__':
    write(sys.argv[1], sys.argv[2], sys.argv[3])
