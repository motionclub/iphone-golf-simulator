"""Extract hand-ROI plate masks (background subtraction like Tools/HeroBase/male_silhouette_refs.py) for the female plates.
python plate_masks.py  -> data/plate_masks.npz (full-frame masks 720x1280 for bald and multi) + proof/_mask_check.png"""
import numpy as np
from collections import deque
from PIL import Image, ImageDraw
B = '../../ArtDir/hero/base_lock/'
def largest_fill(mask):
    seen = np.zeros(mask.shape, bool); best = []
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys, xs):
        if seen[y, x]: continue
        q = deque([(int(y), int(x))]); seen[y, x] = True; comp = []
        while q:
            yy, xx = q.popleft(); comp.append((yy, xx))
            for dy, dx in ((0,1),(1,0),(-1,0),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                yn, xn = yy+dy, xx+dx
                if 0 <= yn < mask.shape[0] and 0 <= xn < mask.shape[1] and mask[yn, xn] and not seen[yn, xn]:
                    seen[yn, xn] = True; q.append((yn, xn))
        if len(comp) > len(best): best = comp
    res = np.zeros(mask.shape, bool)
    for y, x in best: res[y, x] = True
    ext = np.zeros(mask.shape, bool); q = deque()
    for y in range(mask.shape[0]):
        for x in (0, mask.shape[1]-1):
            if not res[y, x] and not ext[y, x]: ext[y, x] = True; q.append((y, x))
    for x in range(mask.shape[1]):
        for y in (0, mask.shape[0]-1):
            if not res[y, x] and not ext[y, x]: ext[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((0,1),(1,0),(-1,0),(0,-1)):
            yn, xn = y+dy, x+dx
            if 0 <= yn < mask.shape[0] and 0 <= xn < mask.shape[1] and not res[yn, xn] and not ext[yn, xn]:
                ext[yn, xn] = True; q.append((yn, xn))
    return ~ext
# (name, file, box(x0,y0,x1,y1), threshold)
VIEWS = [('bald_front', 'female_body_bald.jpg', (300, 20, 590, 690)), ('bald_back', 'female_body_bald.jpg', (700, 20, 990, 690)),
         ('sheet_front', 'female_multiangle_body.jpg', (80, 40, 270, 345)), ('sheet_back', 'female_multiangle_body.jpg', (400, 40, 580, 345)),
         ('sheet_left', 'female_multiangle_body.jpg', (730, 40, 850, 345)), ('sheet_right', 'female_multiangle_body.jpg', (1040, 40, 1160, 345))]
out = {}
panel = []
for name, f, box in VIEWS:
    im = Image.open(B+f).convert('RGB'); crop = np.array(im.crop(box), dtype=np.float32)
    left = np.median(crop[:, :4, :], axis=1); right = np.median(crop[:, -4:, :], axis=1)
    u = np.linspace(0, 1, crop.shape[1])[None, :, None]; bg = left[:, None, :]*(1-u) + right[:, None, :]*u
    diff = np.max(np.abs(crop - bg), axis=2)
    m = largest_fill(diff > 7.5)
    full = np.zeros((720, 1280), bool); full[box[1]:box[3], box[0]:box[2]] = m
    out[name] = full
    ov = np.array(im).copy(); ov[full] = (0.55*ov[full] + 0.45*np.array([40, 230, 130])).astype(np.uint8)
    panel.append((name, Image.fromarray(ov).crop(box)))
    ys, xs = np.nonzero(full); print(name, 'px', int(full.sum()), 'bbox', xs.min(), ys.min(), xs.max(), ys.max())
np.savez_compressed('data/plate_masks.npz', **out)
W = sum(p.width for _, p in panel) + 8*len(panel); H = max(p.height for _, p in panel)
S = Image.new('RGB', (W, H), (20, 20, 24)); x = 0
for n, p in panel:
    S.paste(p, (x, 0)); ImageDraw.Draw(S).text((x+4, 4), n, fill=(255, 230, 120)); x += p.width + 8
S.save('proof/_mask_check.png'); print(S.size)
