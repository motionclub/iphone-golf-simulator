"""stretch4.py: contrast-stretched structure comparison of plate vs variants (reads scratch/r/bd_chest_<tag>_<shot>.png written by board3).
python3 tools/stretch4.py out.png tag1 tag2 ...   rows: front, 3/4 FL, 3/4 FR, side"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw
import board3
from board3 import sheet_tile, plate_crop
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
px = 420

def load(tag, name):
    m = Image.open(f'{HERE}/scratch/r/bd_chest_{tag}_{name}.png').convert('RGBA')
    bg = Image.new('RGBA', m.size, (225, 225, 228, 255)); bg.alpha_composite(m)
    return bg.convert('L')

def stretch(im, box, lo_hi=(1, 99)):
    a = np.asarray(im).astype(float); w, h = im.size
    bx = (int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h))
    c = a[bx[1]:bx[3], bx[0]:bx[2]]
    lo, hi = np.percentile(c, lo_hi); a = np.clip((a - lo) / (hi - lo + 1e-9), 0, 1)
    return Image.fromarray((a * 255).astype(np.uint8))

def main(out, tags):
    zc, half = 1.20, 0.27
    plate = {'front': plate_crop('chest', 1.0).convert('L'), 'y25': sheet_tile(168, zc, half, px, enh=1.0).convert('L'),
             'y-25': sheet_tile(472, zc, half, px, enh=1.0).convert('L'), 'side': sheet_tile(790, zc, half, px, bottom=False, enh=1.0).convert('L')}
    boxes = {'front': (0.15, 0.2, 0.85, 0.75), 'y25': (0.27, 0.22, 0.78, 0.65), 'y-25': (0.27, 0.22, 0.78, 0.65), 'side': (0.2, 0.15, 0.8, 0.8)}
    rows = []
    for shot in ('front', 'y25', 'y-25', 'side'):
        tiles = [stretch(plate[shot], boxes[shot])]
        for t in tags:
            tiles.append(stretch(load(t, shot), boxes[shot]))
        hh = px
        ww = [int(t.width * hh / t.height) for t in tiles]
        row = Image.new('L', (sum(ww), hh))
        x = 0
        for t, w in zip(tiles, ww):
            row.paste(t.resize((w, hh), Image.LANCZOS), (x, 0)); x += w
        rows.append(row.convert('RGB'))
        d = ImageDraw.Draw(rows[-1]); x = 0
        for lab, w in zip(['PLATE'] + list(tags), ww):
            d.text((x + 5, 5), f'{lab} {shot}', fill=(255, 255, 0)); x += w
    W = Image.new('RGB', (max(r.width for r in rows), sum(r.height for r in rows)))
    y = 0
    for r in rows:
        W.paste(r, (0, y)); y += r.height
    W.save(out); print(out, W.size)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
