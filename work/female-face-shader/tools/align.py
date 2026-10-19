"""Fit the reference sheet-07 head (front / right profile) onto our game-preview silhouette by the CRANIUM only (crown + skull outline
above the brow: identity-locked), then report jaw/chin/lip outline differences. python3 tools/align.py <tag>"""
import sys, json, numpy as np
from PIL import Image, ImageDraw
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-face-shader/'
SHEET = W + '../../ArtDir/style/alive/neutral-reference-pack-2026-10-15/sheets/07-head-skin-neutral.png'
PANELS = {'front': (30, 60, 500, 470), 'side': (1030, 60, 1500, 470)}
C = (0, -.05, 1.52); H = .2; RES = 1200; MPP = 2 * H / RES
def edges(m):
    out = []
    for r in range(m.shape[0]):
        c = np.flatnonzero(m[r]); out.append((c.min(), c.max()) if len(c) > 2 else None)
    return out
def largest(m):
    # keep the largest 4-connected component (drop stray pixels / text)
    from collections import deque
    lab = np.zeros(m.shape, np.int32); best = (0, 0); n = 0
    H_, W_ = m.shape
    for r0, c0 in zip(*np.nonzero(m)):
        if lab[r0, c0]: continue
        n += 1; q = deque([(r0, c0)]); lab[r0, c0] = n; cnt = 0
        while q:
            r, c = q.popleft(); cnt += 1
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                rr, cc = r+dr, c+dc
                if 0 <= rr < H_ and 0 <= cc < W_ and m[rr, cc] and not lab[rr, cc]: lab[rr, cc] = n; q.append((rr, cc))
        if cnt > best[0]: best = (cnt, n)
    return lab == best[1]
def ref_mask(view, scale=3):
    im = Image.open(SHEET).convert('RGB').crop(PANELS[view]); im = im.resize((im.width * scale, im.height * scale), Image.LANCZOS)
    a = np.asarray(im).astype(float) / 255; mx = a.max(-1); mn = a.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-4)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (sat > .16) & (r > g) & (g >= b * .92) & (r > .25)
    # fill holes inside the head (eyes, brows): row-wise between edges is fine for outline purposes
    m = largest(m)
    if view == 'side': m = m[:, ::-1]; a = a[:, ::-1]
    return m, a, scale
def fit(view, ours, refm):
    oe = edges(ours); re_ = edges(refm)
    orow = [r for r, e in enumerate(oe) if e]; oc = orow[0]
    rrow = [r for r, e in enumerate(re_) if e]; rc = rrow[0]
    # cranium band in OUR frame: crown to 65 mm below the crown (above the brow / ear tops)
    band = range(oc + 4, oc + int(.065 / MPP))
    best = None
    for s in np.linspace(.5, 1.6, 551):          # ref px -> our px
        offs = []; pairs = []
        for r in band:
            rr = int(round(rc + (r - oc) / s))
            if rr < len(re_) and re_[rr] and oe[r]: pairs.append((oe[r], re_[rr]))
        if len(pairs) < 20: continue
        o = np.array([p[0] for p in pairs], float); q = np.array([p[1] for p in pairs], float) * s
        sh = np.median(np.concatenate([o[:, 0] - q[:, 0], o[:, 1] - q[:, 1]]))
        err = np.mean(np.abs(o - q - sh))
        if best is None or err < best[0]: best = (err, s, sh, rc, oc)
    return best
def project(refm, refa, s, sh, rc, oc):
    rows = np.arange(RES); cols = np.arange(RES)
    rr = np.clip(np.round(rc + (rows - oc) / s).astype(int), 0, refm.shape[0] - 1)
    cc = np.round((cols - sh) / s).astype(int); ok = (cc >= 0) & (cc < refm.shape[1]); cc = np.clip(cc, 0, refm.shape[1] - 1)
    m = refm[rr][:, cc] & ok[None]; a = refa[rr][:, cc] * ok[None, :, None] + .9 * (~ok)[None, :, None]
    return m, a
def outline(m):
    e = np.zeros_like(m); e[1:-1, 1:-1] = m[1:-1, 1:-1] & ~(m[:-2, 1:-1] & m[2:, 1:-1] & m[1:-1, :-2] & m[1:-1, 2:]); return e
if __name__ == '__main__':
    tags = sys.argv[1:]
    res = {}
    for view in ('front', 'side'):
        ours = [np.load(W + f'eval/{t}_{view}_mask.npy') for t in tags]
        refm, refa, sc = ref_mask(view)
        err, s, sh, rc, oc = fit(view, ours[0], refm)
        pm, pa = project(refm, refa, s, sh, rc, oc)
        np.save(W + f'eval/ref_{view}_mask.npy', pm); np.save(W + f'eval/ref_{view}_rgb.npy', (pa * 255).astype(np.uint8))
        res[view] = dict(fit_err_px=float(err), fit_err_mm=float(err * MPP * 1000), our_px_per_ref_px=float(s), shift=float(sh), ref_crown=int(rc), our_crown=int(oc),
                         ref_sheet_mm_per_px=float(MPP * 1000 * s * sc))
        img = (pa * .8 * 255).astype(np.uint8).copy()
        img[outline(pm)] = (0, 200, 0)
        cols = [(255, 0, 0), (255, 220, 0), (0, 150, 255)]
        for k, m in enumerate(ours):
            o = outline(m); o2 = o.copy(); o2[1:] |= o[:-1]; o2[:, 1:] |= o[:, :-1]; img[o2] = cols[k]
        Image.fromarray(img).save(W + f'eval/ov_{view}_{"_".join(tags)}.png')
    json.dump(res, open(W + 'eval/align.json', 'w'), indent=1); print(json.dumps(res, indent=1))
