"""sil_metric.py <design> <prefix> [out.png]: per-view silhouette difference between the sheet view and our render (<prefix>_<view>.png).
Silhouettes: sheet = fg segmentation (shadow trimmed below the sole line), ours = non-background pixels. Our silhouette is fitted onto the sheet's
by a uniform scale + offset search (matched camera and scale). difference = XOR / union (= 1 - IoU)."""
import sys, numpy as np; sys.path.insert(0, 'tools')
from seg import load, classify
from PIL import Image
design, pre = sys.argv[1:3]; out = sys.argv[3] if len(sys.argv) > 3 else None
from compose_shoe_boxes import BOX
sheet, boxes = BOX[design]; S = load(sheet); bg = S[5, 5].copy()
def fg_ref(nm):
    crop = S[boxes[nm][1]:boxes[nm][3], boxes[nm][0]:boxes[nm][2]]
    fg, cls = classify(crop, bg)
    lum = crop.mean(2)
    gy = np.abs(np.diff(lum, axis=0, prepend=lum[:1])); gx = np.abs(np.diff(lum, axis=1, prepend=lum[:, :1]))
    sat = crop.max(2) - crop.min(2)
    shadowish = (sat < 16) & (lum > 176) & (lum < bg.mean() - 2)
    solid = fg & ~shadowish
    hard = (np.maximum(gx, gy) > 22) & solid
    # per column: nothing below the lowest solid pixel that has a hard edge (floor shadows are soft and shadow-coloured)
    H = fg.shape[0]; cut = np.full(fg.shape[1], -1)
    for c in range(fg.shape[1]):
        r = np.nonzero(hard[:, c])[0]
        if len(r): cut[c] = r.max()
    keep = np.arange(H)[:, None] <= cut[None, :]
    fg2 = fg & keep
    # largest blob only (labels / stray text)
    from collections import deque
    lab = np.zeros(fg2.shape, np.int32); best = (0, 0); n = 0
    for (y, x) in zip(*np.nonzero(fg2)):
        if lab[y, x]: continue
        n += 1; q = deque([(y, x)]); lab[y, x] = n; cnt = 0
        while q:
            a, b = q.popleft(); cnt += 1
            for da, db in ((1,0),(-1,0),(0,1),(0,-1)):
                u, v = a + da, b + db
                if 0 <= u < H and 0 <= v < fg2.shape[1] and fg2[u, v] and not lab[u, v]: lab[u, v] = n; q.append((u, v))
        if cnt > best[0]: best = (cnt, n)
    fg3 = lab == best[1]
    # fill holes (laces gaps etc. are shoe): rows between the leftmost and rightmost blob pixel
    for r in range(H):
        c = np.nonzero(fg3[r])[0]
        if len(c) > 1: fg3[r, c.min():c.max() + 1] |= fg[r, c.min():c.max() + 1]
    return fg3
def fg_ours(nm, flip):
    a = np.asarray(Image.open('%s_%s.png' % (pre, nm)).convert('RGB')).astype(float)
    b = a[2, 2]; m = np.abs(a - b).sum(2) > 18
    return m[:, ::-1] if flip else m
def bbox(m):
    r = np.nonzero(m.any(1))[0]; c = np.nonzero(m.any(0))[0]; return r.min(), r.max(), c.min(), c.max()
def fit(ref, ours):
    r0, r1, c0, c1 = bbox(ref); R = ref[r0:r1 + 1, c0:c1 + 1]
    q0, q1, d0, d1 = bbox(ours); O = ours[q0:q1 + 1, d0:d1 + 1]
    H, W = R.shape; best = (0, None)
    for s in np.linspace(.85, 1.15, 13):
        sc = min(H / O.shape[0], W / O.shape[1]) * s
        o = np.asarray(Image.fromarray((O * 255).astype(np.uint8)).resize((max(1, int(O.shape[1] * sc)), max(1, int(O.shape[0] * sc))))) > 127
        for dy in range(-12, 13, 3):
            for dx in range(-12, 13, 3):
                C = np.zeros((H + 60, W + 60), bool); Rr = C.copy(); Rr[30:30 + H, 30:30 + W] = R
                y0 = 30 + (H - o.shape[0]) // 2 + dy; x0 = 30 + (W - o.shape[1]) // 2 + dx
                if y0 < 0 or x0 < 0 or y0 + o.shape[0] > C.shape[0] or x0 + o.shape[1] > C.shape[1]: continue
                C[y0:y0 + o.shape[0], x0:x0 + o.shape[1]] = o
                iou = (C & Rr).sum() / (C | Rr).sum()
                if iou > best[0]: best = (iou, (Rr, C))
    return best
FLIP = {'lateral': True, 'medial': True, 'top': True, 'sole': True, 'front': False, 'back': False}
res = {}; tiles = []
for nm in ['lateral', 'medial', 'front', 'back', 'top', 'sole']:
    iou, (Rr, C) = fit(fg_ref(nm), fg_ours(nm, FLIP[nm]))
    res[nm] = 1 - iou
    t = np.full(Rr.shape + (3,), 235, np.uint8); t[Rr & C] = (150, 150, 150); t[Rr & ~C] = (60, 110, 230); t[C & ~Rr] = (230, 60, 60)
    tiles.append(Image.fromarray(t).resize((int(t.shape[1] * 300 / t.shape[0]), 300)))
print(design, ' '.join('%s %.1f%%' % (k, 100 * v) for k, v in res.items()))
if out:
    W = sum(t.width for t in tiles) + 6 * 5; img = Image.new('RGB', (W, 300), (30, 30, 34)); x = 0
    for t in tiles: img.paste(t, (x, 0)); x += t.width + 6
    img.save(out)
