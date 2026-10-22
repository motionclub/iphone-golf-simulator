import numpy as np
from PIL import Image, ImageDraw
B = '../../ArtDir/hero/base_lock/'
M = np.load('data/plate_masks.npz')
bald = Image.open(B+'female_body_bald.jpg').convert('RGB'); multi = Image.open(B+'female_multiangle_body.jpg').convert('RGB')
ROIS = [('bald_front vL', bald, 'bald_front', (320, 338, 380, 424)), ('bald_front vR', bald, 'bald_front', (500, 338, 560, 424)),
        ('bald_back vL', bald, 'bald_back', (730, 338, 790, 424)), ('bald_back vR', bald, 'bald_back', (910, 338, 970, 424)),
        ('sheet_front vL', multi, 'sheet_front', (105, 175, 150, 230)), ('sheet_front vR', multi, 'sheet_front', (190, 175, 235, 230)),
        ('sheet_back vL', multi, 'sheet_back', (425, 175, 470, 230)), ('sheet_back vR', multi, 'sheet_back', (500, 175, 545, 230))]
tiles = []
for name, im, mk, box in ROIS:
    sc = 8 if im is bald else 10
    c = im.crop(box); c = c.resize((c.width*sc, c.height*sc), Image.LANCZOS)
    m = M[mk][box[1]:box[3], box[0]:box[2]]
    mm = Image.fromarray(np.uint8(m)*255).resize(c.size, Image.NEAREST)
    # edge of the mask
    arr = np.array(c).copy(); mk2 = np.array(mm) > 127
    edge = mk2 ^ np.roll(mk2, 1, 0) | mk2 ^ np.roll(mk2, 1, 1)
    arr[edge] = (255, 40, 40)
    t = Image.fromarray(arr); ImageDraw.Draw(t).text((4, 4), name, fill=(255, 230, 0)); tiles.append(t)
W = sum(t.width for t in tiles[:4]) + 18; H = max(t.height for t in tiles[:4]) + max(t.height for t in tiles[4:]) + 6
S = Image.new('RGB', (max(W, sum(t.width for t in tiles[4:]) + 18), H), (20, 20, 24)); x = 0
for t in tiles[:4]: S.paste(t, (x, 0)); x += t.width + 6
x = 0; y = max(t.height for t in tiles[:4]) + 6
for t in tiles[4:]: S.paste(t, (x, y)); x += t.width + 6
S.save('proof/_mask_roi_check.png'); print(S.size)
