"""Reference sheet-07 front / right profile mapped onto our game-preview frame by TWO vertical anchors (A, B) with uniform scale.
modes: crownchin (crown + chin bottom), eyechin (eye line + chin bottom).  python3 tools/align2.py <mode> <tag> [tag2 ...]"""
import sys, json, numpy as np
from PIL import Image, ImageDraw
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-face-shader/'
SHEET = W + '../../ArtDir/style/alive/neutral-reference-pack-2026-10-15/sheets/07-head-skin-neutral.png'
C = (0, -.05, 1.52); H = .2; RES = 1200; MPP = 2 * H / RES
# reference landmarks, sheet pixels (measured: tools/ref_landmarks in GATE notes)
REF = {'front': dict(box=(30, 60, 500, 470), crown=60 + 87 / 3, eye=234.9, chin=374.0, cx=279.0),
       'side': dict(box=(1030, 60, 1500, 470), crown=60 + 50 / 3, eye=223.8, chin=None)}
def sheet():
    return np.asarray(Image.open(SHEET).convert('RGB')).astype(float) / 255
def skinmask(a):
    mx = a.max(-1); mn = a.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-4)
    return (sat > .16) & (a[..., 0] > a[..., 1]) & (a[..., 1] >= a[..., 2] * .92) & (a[..., 0] > .25)
def ours_landmarks(tag):
    fm = np.load(W + f'eval/{tag}_front_mask.npy'); sm = np.load(W + f'eval/{tag}_side_mask.npy')
    F = json.load(open(W + 'eval/frame.json'))
    rows = np.nonzero(sm.any(1))[0]; crown_z = C[2] + H - rows[0] * MPP
    return dict(crown=crown_z, eye=F['eye'][2] - .0093, fm=fm, sm=sm)
def chin_from_side(sm, zmin=1.40, zmax=1.50):
    # chin bottom = row with the largest backward jump of the front edge (under-chin turn) in the window
    best = (0, None)
    fe = [np.nonzero(sm[r])[0].min() if sm[r].any() else None for r in range(RES)]
    for r in range(RES - 1):
        z = C[2] + H - r * MPP
        if zmin < z < zmax and fe[r] is not None and fe[r + 1] is not None:
            j = fe[r + 1] - fe[r]
            if j > best[0]: best = (j, r)
    return C[2] + H - (best[1] + .5) * MPP
def ref_side_chin(a):
    x0, y0, x1, y1 = REF['side']['box']; m = skinmask(a[y0:y1, x0:x1])[:, ::-1]
    fe = [np.nonzero(m[r])[0].min() if m[r].any() else None for r in range(m.shape[0])]
    best = (0, None)
    for r in range(150, m.shape[0] - 1):
        if fe[r] is not None and fe[r + 1] is not None and fe[r + 1] - fe[r] > best[0]: best = (fe[r + 1] - fe[r], r)
    return y0 + best[1] + .5
def mapping(mode, view, L, a):
    R = REF[view]
    if mode == 'crownchin': (ra, rb), (oa, ob) = (R['crown'], R['chin']), (L['crown'], L['chin'])
    else: (ra, rb), (oa, ob) = (R['eye'], R['chin']), (L['eye'], L['chin'])
    s = (oa - ob) / (rb - ra)        # metres per sheet pixel
    return s, ra, oa
def render(mode, view, tags, out):
    a = sheet(); L = ours_landmarks(tags[0]); L['chin'] = chin_from_side(L['sm'])
    if REF['side']['chin'] is None: REF['side']['chin'] = ref_side_chin(a)
    s, ra, oa = mapping(mode, view, L, a)
    rows = np.arange(RES); zs = C[2] + H - rows * MPP
    sr = np.clip(np.round(ra + (oa - zs) / s).astype(int), 0, a.shape[0] - 1)
    if view == 'front':
        xs = (np.arange(RES) * MPP) - H                       # metres, image right = +x
        sc = np.round(REF['front']['cx'] + xs / s).astype(int)
    else:
        ys = C[1] - H + np.arange(RES) * MPP                 # metres along Blender y (face toward image left)
        # horizontal: least squares on the cranium (front+back edges) between crown and eye line
        x0, y0, x1, y1 = REF['side']['box']; m = skinmask(a[y0:y1, x0:x1])
        best = None
        sm = L['sm']
        for sh in np.arange(-.40, .40, .0005):
            errs = []
            for r in range(int((C[2] + H - L['crown']) / MPP) + 6, int((C[2] + H - L['eye']) / MPP), 6):
                row = sm[r]; oc = np.nonzero(row)[0]
                rr = int(round(ra + (oa - (C[2] + H - r * MPP)) / s)) - y0
                if not len(oc) or rr < 0 or rr >= m.shape[0]: continue
                rc = np.nonzero(m[rr])[0]
                if not len(rc): continue
                # ref is a right profile (face to image right): mirror -> sheet col = x1 - (y - sh)/s
                fr = (x1 - x0 - 1) - rc.max(); br = (x1 - x0 - 1) - rc.min()   # mirrored columns within panel, front edge first
                ofront = C[1] - H + oc.min() * MPP; oback = C[1] - H + oc.max() * MPP
                errs += [ofront - (sh + fr * s), oback - (sh + br * s)]
            e = np.mean(np.abs(errs)) if errs else 9
            if best is None or e < best[0]: best = (e, sh)
        sh = best[1]
        sc = np.round(x1 - 1 - (ys - sh) / s).astype(int)
    ok = (sc >= 0) & (sc < a.shape[1]); sc = np.clip(sc, 0, a.shape[1] - 1)
    img = a[sr][:, sc] * ok[None, :, None]
    refm = skinmask(img) & ok[None]
    # keep only the panel area
    x0, y0, x1, y1 = REF[view]['box']; inpanel = ((sc >= x0) & (sc < x1))[None, :] & ((sr >= y0) & (sr < y1))[:, None]
    refm &= inpanel; img = np.where(inpanel[..., None], img, .9)
    def outline(mm):
        e = np.zeros_like(mm); e[1:-1, 1:-1] = mm[1:-1, 1:-1] & ~(mm[:-2, 1:-1] & mm[2:, 1:-1] & mm[1:-1, :-2] & mm[1:-1, 2:]); return e
    o = (img * 255 * .85).astype(np.uint8)
    o[outline(refm)] = (0, 200, 0)
    for k, t in enumerate(tags):
        mm = np.load(W + f'eval/{t}_{view}_mask.npy'); e = outline(mm); e2 = e.copy(); e2[1:] |= e[:-1]; e2[:, 1:] |= e[:, :-1]
        o[e2] = [(255, 0, 0), (255, 220, 0), (0, 150, 255)][k]
    Image.fromarray(o).save(out)
    return dict(s=s, chin_ours=L['chin'], crown_ours=L['crown'], eye_ours=L['eye'], ref=REF[view])
if __name__ == '__main__':
    mode, tags = sys.argv[1], sys.argv[2:]
    info = {v: render(mode, v, tags, W + f'eval/ov2_{mode}_{v}_{"_".join(tags)}.png') for v in ('front', 'side')}
    print(json.dumps(info, indent=1, default=float))
