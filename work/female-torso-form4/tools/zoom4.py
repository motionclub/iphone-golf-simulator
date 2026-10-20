"""zoom4.py: render SOFT (plate-fit) and optionally CLAY under unique tags and build a zoomed 3/4 + front + side comparison: plate | v1 | v2 ...
python3 tools/zoom4.py out.png soft|clay tag=coords.npy ...   rows: front, 3/4 FL, 3/4 FR, side (chest box zoom)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
import board3
from board3 import sheet_tile, plate_crop
from run4 import SOFT, HERE
px = 420

def main(out, look, items):
    lk = SOFT if look == 'soft' else 'matcap:clay_studio.exr'
    its = [(f'{t}_{look}', p) for t, p in items]
    board3.board('chest', HERE + '/scratch/_tmp_zoom.png', its, look=lk)
    zc, half = 1.20, 0.27
    def load(tag, name):
        m = Image.open(f'{HERE}/scratch/r/bd_chest_{tag}_{name}.png').convert('RGBA')
        bg = Image.new('RGBA', m.size, (225, 225, 228, 255)); bg.alpha_composite(m)
        return bg.convert('RGB')
    plate = {'front': plate_crop('chest', 1.0), 'y25': sheet_tile(168, zc, half, px, enh=1.0), 'y-25': sheet_tile(472, zc, half, px, enh=1.0), 'side': sheet_tile(790, zc, half, px, bottom=False, enh=1.0)}
    boxes = {'front': (0.08, 0.28, 0.92, 0.80), 'y25': (95 / 420, 95 / 420, 335 / 420, 265 / 420), 'y-25': (95 / 420, 95 / 420, 335 / 420, 265 / 420), 'side': (0.18, 0.12, 0.62, 0.62)}
    cellw = 520
    rows = []
    for shot in ('front', 'y25', 'y-25', 'side'):
        tiles = [('PLATE', plate[shot])] + [(t, load(f'{t}_{look}', shot)) for t, _ in items]
        row = []
        for n, im in tiles:
            w, h = im.size
            b = boxes[shot]
            c = im.crop((int(b[0] * w), int(b[1] * h), int(b[2] * w), int(b[3] * h)))
            ch = int(cellw * c.height / c.width)
            c = c.resize((cellw, ch), Image.LANCZOS)
            d = ImageDraw.Draw(c); d.text((6, 6), f'{n} {shot}', fill=(255, 0, 0))
            row.append(c)
        H = max(c.height for c in row)
        r = Image.new('RGB', (cellw * len(row), H), (30, 30, 34))
        for i, c in enumerate(row):
            r.paste(c, (i * cellw, 0))
        rows.append(r)
    W = Image.new('RGB', (rows[0].width, sum(r.height for r in rows)))
    y = 0
    for r in rows:
        W.paste(r, (0, y)); y += r.height
    W.save(out); print(out, W.size)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], [a.split('=', 1) for a in sys.argv[3:]])
