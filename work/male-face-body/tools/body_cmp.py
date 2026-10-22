"""Body silhouette: sheet 15 (front, right side, back) vs our unclothed Unity body renders (MaleFaceReview set=body), both normalised to
crown..sole height.  python3 tools/body_cmp.py <unity_out body dir> <tag>  -> eval/body_<tag>_<view>.png overlays + width table (% of height)."""
import sys, numpy as np
from PIL import Image
SHEET = '../../ArtDir/style/alive/male-reference-pack-2026-10-17/sheets/15-body-cardinal-no-clothes.png'
A = np.asarray(Image.open(SHEET).convert('RGB')).astype(int)
PANELS = {'front': (20, 120, 600, 1200), 'right90': (600, 120, 1000, 1200), 'back': (930, 120, 1600, 1200)}
def refmask(view):
    x0, y0, x1, y1 = PANELS[view]; a = A[y0:y1, x0:x1]
    bg = np.median(np.concatenate([a[:10].reshape(-1, 3), a[:, :10].reshape(-1, 3)]), 0)
    m = np.abs(a - bg).sum(-1) > 30
    rows = np.nonzero(m.sum(1) > 2)[0]; return m, rows[0], rows[-1]
def ourmask(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(int); m = np.abs(a - [227, 227, 222]).sum(-1) > 14
    rows = np.nonzero(m.sum(1) > 2)[0]; return m, rows[0], rows[-1]
def widths(m, top, bot, fr):
    out = []
    for f in fr:
        r = int(top + f * (bot - top)); c = np.nonzero(m[r])[0]
        out.append((c.max() - c.min()) / (bot - top) if len(c) else np.nan)
    return np.array(out)
def outline(mm): e = np.zeros_like(mm); e[1:-1, 1:-1] = mm[1:-1, 1:-1] & ~(mm[:-2, 1:-1] & mm[2:, 1:-1] & mm[1:-1, :-2] & mm[1:-1, 2:]); return e
d, tag = sys.argv[1], sys.argv[2]
fr = np.arange(.02, .99, .02)
for view in ('front', 'right90', 'back'):
    rm, rt, rb = refmask(view); om, ot, ob = ourmask(f'{d}/body_{view}.png')
    rw = widths(rm, rt, rb, fr); ow = widths(om, ot, ob, fr)
    # overlay: map ref into our pixel grid by height + centre of mass at hip level
    H, Wd = om.shape; s = (rb - rt) / (ob - ot)
    yy, xx = np.mgrid[0:H, 0:Wd]
    rc = np.nonzero(rm[int(rt + .5 * (rb - rt))])[0].mean(); oc = np.nonzero(om[int(ot + .5 * (ob - ot))])[0].mean()
    ry = np.clip(((yy - ot) * s + rt).astype(int), 0, rm.shape[0] - 1); rx = np.clip(((xx - oc) * s + rc).astype(int), 0, rm.shape[1] - 1)
    rmm = rm[ry, rx]; img = np.asarray(Image.open(f'{d}/body_{view}.png').convert('RGB')).copy()
    img[outline(rmm)] = (0, 180, 0); img[outline(om)] = (255, 0, 0); Image.fromarray(img).save(f'eval/body_{tag}_{view}.png')
    iou = (rmm & om).sum() / (rmm | om).sum(); xor = (rmm ^ om).sum() / om.sum()
    print(view, f'IoU {iou:.3f}  mismatch {xor*100:.1f}% of our area')
    print('  h%  ours  ref  (width / height)', ' '.join(f'{f*100:.0f}:{o:.3f}/{r:.3f}' for f, o, r in zip(fr[::3], ow[::3], rw[::3])))
