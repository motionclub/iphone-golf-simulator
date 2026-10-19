"""Male head vs reference sheet 07 (front + right profile), crown+chin frame. Ours = Blender game-preview silhouettes (measure_m.py).
python3 tools/compare_m.py <tag> [tag2 ...]  -> eval/cmp_<view>_<tags>.png overlays (green ref, red tag1, yellow tag2) + mm table.
Both images face LEFT in profile (sheet 07 'RIGHT PROFILE' and our +x camera), so no mirroring. Vertical: crown and chin bottom
mapped onto each other (uniform scale). Profile horizontal: least squares on the cranium outline (crown .. eye line)."""
import sys, json, numpy as np
from PIL import Image
W = __file__.rsplit('/tools/', 1)[0] + '/'
SHEET = W + '../../ArtDir/style/alive/male-reference-pack-2026-10-17/sheets/07-head-skin-neutral.png'
F = json.load(open(W + 'eval/frame.json')); C = F['C']; H = F['H']; RES = 1200; MPP = 2 * H / RES
# sheet 07 landmarks (px, read off eval/ref07_*_ticks.png): crown, eye line, chin bottom, face centre column (front)
REF = {'front': dict(box=(40, 140, 680, 600), crown=150, eye=301, chin=472, cx=359.5),
       'side': dict(box=(1460, 140, 1960, 600), crown=149, eye=305, chin=None)}
def skin(a):
    mx = a.max(-1); mn = a.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-4)
    return (sat > .16) & (a[..., 0] > a[..., 1]) & (a[..., 1] >= a[..., 2] * .92) & (a[..., 0] > .25)
A = np.asarray(Image.open(SHEET).convert('RGB')).astype(float) / 255
def fill_rows(m):
    o = np.zeros_like(m)
    for r in range(m.shape[0]):
        c = np.nonzero(m[r])[0]
        if len(c) > 2: o[r, c.min():c.max() + 1] = True
    return o
def ref_mask(view):
    x0, y0, x1, y1 = REF[view]['box']; m = np.zeros(A.shape[:2], bool); m[y0:y1, x0:x1] = skin(A[y0:y1, x0:x1]); return fill_rows(m)
def chin_jump(fe, rows, lo, hi):
    best = (0, None)
    for r in rows:
        if lo < r < hi and fe.get(r) is not None and fe.get(r + 1) is not None and fe[r + 1] - fe[r] > best[0]: best = (fe[r + 1] - fe[r], r)
    return best[1]
def front_edges(m):
    return {r: (np.nonzero(m[r])[0].min() if m[r].any() else None) for r in range(m.shape[0])}
RM = {v: ref_mask(v) for v in REF}
if REF['side']['chin'] is None:
    fe = front_edges(RM['side']); REF['side']['chin'] = chin_jump(fe, range(400, 560), 400, 560) + .5
def ours(tag, view):
    return np.load(W + f'eval/{tag}_{view}_mask.npy')
def our_land(tag):
    sm = ours(tag, 'side'); rows = np.nonzero(sm.any(1))[0]; crown = C[2] + H - rows[0] * MPP
    fe = front_edges(sm); r0 = int((C[2] + H - 1.52) / MPP); r1 = int((C[2] + H - 1.42) / MPP)
    chin = C[2] + H - (chin_jump(fe, range(r0, r1), r0, r1) + .5) * MPP
    return crown, chin
def mapping(view, crown, chin):
    R = REF[view]; s = (crown - chin) / (R['chin'] - R['crown'])    # metres per sheet px
    zr = lambda z: R['crown'] + (crown - z) / s                      # our z -> sheet row
    return s, zr
def side_shift(sm, s, zr, crown):
    R = REF['side']; rm = RM['side']; best = None
    eye_z = crown - (R['eye'] - R['crown']) * s
    r = int((C[2] + H - eye_z) / MPP); rr = int(round(zr(eye_z)))
    sh0 = (C[1] - H + np.nonzero(sm[r])[0].max() * MPP) - np.nonzero(rm[rr])[0].max() * s
    for sh in np.arange(sh0 - .05, sh0 + .05, .0002):
        e = []
        for r in range(int((C[2] + H - crown) / MPP) + 6, int((C[2] + H - eye_z) / MPP), 6):
            oc = np.nonzero(sm[r])[0]; rr = int(round(zr(C[2] + H - r * MPP)))
            rc = np.nonzero(rm[rr])[0] if 0 <= rr < rm.shape[0] else []
            if not len(oc) or not len(rc): continue
            e += [(C[1] - H + oc.min() * MPP) - (sh + rc.min() * s), (C[1] - H + oc.max() * MPP) - (sh + rc.max() * s)]
        if e:
            v = np.mean(np.abs(e))
            if best is None or v < best[0]: best = (v, sh)
    return best[1]
def outline(m):
    e = np.zeros_like(m); e[1:-1, 1:-1] = m[1:-1, 1:-1] & ~(m[:-2, 1:-1] & m[2:, 1:-1] & m[1:-1, :-2] & m[1:-1, 2:]); return e
def run(tags, out_tbl=True):
    crown, chin = our_land(tags[0]); rows = np.arange(RES); zs = C[2] + H - rows * MPP; res = {}
    for view in ('front', 'side'):
        s, zr = mapping(view, crown, chin); sr = np.clip(np.round(zr(zs)).astype(int), 0, A.shape[0] - 1)
        if view == 'front':
            sc = np.round(REF['front']['cx'] + (np.arange(RES) * MPP - H) / s).astype(int)
        else:
            sh = side_shift(ours(tags[0], 'side'), s, zr, crown); res['side_shift'] = sh
            sc = np.round(((C[1] - H + np.arange(RES) * MPP) - sh) / s).astype(int)
        sc = np.clip(sc, 0, A.shape[1] - 1)
        img = A[sr][:, sc]; rm = RM[view][sr][:, sc]
        o = (img * 255 * .85).astype(np.uint8); o[outline(rm)] = (0, 200, 0)
        for k, t in enumerate(tags):
            e = outline(ours(t, view)); e2 = e.copy(); e2[1:] |= e[:-1]; e2[:, 1:] |= e[:, :-1]; o[e2] = [(255, 0, 0), (255, 220, 0), (0, 150, 255)][k]
        Image.fromarray(o).save(W + f'eval/cmp_{view}_{"_".join(tags)}.png'); res[view] = (s, rm)
    # reference tables in the game face frame (mm): y up from the eye, front half-width, profile front edge (z forward)
    eye = np.array(F['eye']); ys, half, front = [], [], []
    for r in range(RES):
        z = C[2] + H - r * MPP; c = np.nonzero(res['front'][1][r])[0]; rc = np.nonzero(res['side'][1][r])[0]
        ys.append((z - eye[2]) * 1000); half.append((c.max() - c.min()) / 2 * MPP * 1000 if len(c) > 2 else np.nan)
        front.append(-((C[1] - H + rc.min() * MPP) - eye[1]) * 1000 if len(rc) > 2 else np.nan)
    np.savez(W + 'eval/ref07_tables.npz', y=np.array(ys), half=np.array(half), front=np.array(front), crown=crown, chin=chin)
    if out_tbl:
        print(f'crown {crown:.4f} chin {chin:.4f} head {1000*(crown-chin):.1f} mm  (sheet px: {REF})')
        print(' z     dy_eye | front half: ' + ' '.join(tags) + ' ref | profile front edge (mm, + = forward of ref)')
        eye_z = F['eye'][2]
        for z in np.arange(crown - .004, chin - .03, -.004):
            r = int(round((C[2] + H - z) / MPP)); line = f'{z:.3f} {1000*(z-eye_z):6.1f} |'
            for t in tags:
                c = np.nonzero(ours(t, 'front')[r])[0]; line += f' {(c.max()-c.min())/2*MPP*1000:6.1f}' if len(c) else '    -  '
            c = np.nonzero(res['front'][1][r])[0]; line += f' {(c.max()-c.min())/2*MPP*1000:6.1f} |' if len(c) else '    -   |'
            rc = np.nonzero(res['side'][1][r])[0]
            for t in tags:
                c = np.nonzero(ours(t, 'side')[r])[0]
                line += f' {(rc.min()-c.min())*MPP*1000:6.1f}' if len(c) and len(rc) else '    -  '
            print(line)
    return res
if __name__ == '__main__':
    run(sys.argv[1:])
