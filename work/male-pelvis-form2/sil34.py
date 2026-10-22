"""3/4-back silhouette edge offsets (plate - mesh, mm along the panel's horizontal axis) vs z for the registered panels q3BL/q3BR (and q3FL/q3FR).
python3 sil34.py <tag> [zlo zhi step]   needs r/<tag>_s/<reg views> from overlay.py render  (6x)"""
import sys, numpy as np
from PIL import Image
import panel_cmp as PC
W = PC.W; R = PC.R; M = PC.M
L = np.asarray(Image.open(R / 'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('L')).astype(float)
SH = {'q_bl': ('q3BL', (146.0, 794.4566521263387, 0.00588, 673)), 'q_br': ('q3BR', (-147.5, 1072.7706942572954, 0.00584, 674)),
      'q_fl': ('q3FL', (20.0, 185.3449344808188, 0.00572, 673)), 'q_fr': ('q3FR', (-22.0, 477.7293057427045, 0.00572, 676))}
def plate_runs(panel, r, c0, c1, bgcols):
    bg = np.median(np.concatenate([L[r, bgcols[0]:bgcols[1]], L[r, bgcols[2]:bgcols[3]]])); m = L[r, c0:c1] > bg + 9
    idx = np.where(m)[0]
    if len(idx) == 0: return None
    br = np.where(np.diff(idx) > 1)[0]; st = [idx[0]] + [idx[b + 1] for b in br]; en = [idx[b] for b in br] + [idx[-1]]
    return [(s + c0, e + c0 + 1) for s, e in zip(st, en)]
BG = {'q_bl': (676, 690, 884, 898), 'q_br': (1000, 1008, 1146, 1154), 'q_fl': (88, 98, 272, 282), 'q_fr': (381, 391, 565, 575)}
def mesh_runs(panel, tag, r):
    t, c0, c1, r0, r1 = PC.BOX[panel]
    a = np.asarray(Image.open(W / f'r/{tag}_s/{PC.vname(panel)}.png'))[..., 3] > 127
    rr = (r - r0) * M; row = a[rr:rr + M].any(0); idx = np.where(row)[0]
    if len(idx) == 0: return None
    br = np.where(np.diff(idx) > 1)[0]; st = [idx[0]] + [idx[b + 1] for b in br]; en = [idx[b] for b in br] + [idx[-1]]
    return [(s / M + c0, (e + 1) / M + c0) for s, e in zip(st, en)]
def central(runs, cen, hw=60):
    rs = [(s, e) for s, e in runs if e >= cen - hw and s <= cen + hw]
    return (min(s for s, e in rs), max(e for s, e in rs)) if rs else None
if __name__ == '__main__':
    tag = sys.argv[1]; zlo, zhi, st = (float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0.30, 1.02, 0.02)
    for panel in ('q_bl', 'q_br'):
        yaw, col0, mpp, sole = SH[panel][1]; t, c0, c1, r0, r1 = PC.BOX[panel]; cen = col0
        print(f'--- {panel}  (offset = plate - mesh in mm; + means plate edge is further right in the image)  cols: z | L-edge off | R-edge off')
        for z in np.arange(zhi, zlo - 1e-9, -st):
            r = int(round(sole - (z - 0.00247) / mpp))
            if r < r0 or r >= r1:
                continue
            # plate runs need wider crop columns: use the whole panel range 690..890 (q_bl) / 980..1180 (q_br)
            cc0, cc1 = (690, 890) if panel == 'q_bl' else (980, 1180)
            pr = plate_runs(panel, r, cc0, cc1, BG[panel]); mr = mesh_runs(panel, tag, r)
            if pr is None or mr is None: continue
            p = central(pr, cen); m = central(mr, cen)
            if p is None or m is None: continue
            print(f'z {z:.2f}  L {(p[0]-m[0])*mpp*1000:+6.1f}   R {(p[1]-m[1])*mpp*1000:+6.1f}   (plate width {(p[1]-p[0])*mpp*1000:5.0f}, mesh {(m[1]-m[0])*mpp*1000:5.0f})')
