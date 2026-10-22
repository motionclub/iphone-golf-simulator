"""tri5.py: one candidate (or several), three looks.  rows = views, columns = PLATE | tag:soft | tag:clay | tag:stripe  (or per-candidate groups).
python3 tools/tri5.py out.png chest|pelvis [--looks soft,clay,stripe] [--zoom] tag=coords.npy [tag2=coords2.npy ...]
The plate column is the plate crop in the same framing (stripe/clay have no plate counterpart; plate shown once)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
import board3
from board3 import sheet_tile, plate_crop, shots_for
from run4 import SOFT, HERE
LOOKS = {'soft': SOFT, 'clay': 'matcap:clay_studio.exr', 'stripe': 'matcap:check_reflection_vertical.exr'}
BOX = {'chest': {'front': (0.08, 0.28, 0.92, 0.80), 'y25': (95 / 420, 95 / 420, 335 / 420, 265 / 420), 'y-25': (95 / 420, 95 / 420, 335 / 420, 265 / 420), 'side': (0.18, 0.12, 0.62, 0.62)},
       'pelvis': {'back': (0.05, 0.20, 0.95, 0.90), 'y155': (60 / 420, 110 / 420, 360 / 420, 330 / 420), 'y-155': (60 / 420, 110 / 420, 360 / 420, 330 / 420), 'side': (0.18, 0.18, 0.80, 0.80)}}
FULLBOX = (0, 0, 1, 1)


def load(part, tag, name):
    m = Image.open(f'{HERE}/scratch/r/bd_{part}_{tag}_{name}.png').convert('RGBA')
    bg = Image.new('RGBA', m.size, (225, 225, 228, 255)); bg.alpha_composite(m)
    return bg.convert('RGB')


def main(out, part, items, looks=('soft', 'clay', 'stripe'), zoom=True, cellw=420):
    sh, plate, names = shots_for(part, 420)
    keys = [s['name'] for s in sh]
    for t, p in items:
        for lk in looks:
            board3.board(part, HERE + '/scratch/_tmp_tri.png', [(f'{t}_{lk}', p)], look=LOOKS[lk])
    rows = []
    for k, s in enumerate(sh):
        tiles = [('PLATE', plate[k])]
        for t, _ in items:
            for lk in looks:
                tiles.append((f'{t} {lk}', load(part, f'{t}_{lk}', s['name'])))
        row = []
        for n, im in tiles:
            w, h = im.size
            b = BOX[part][keys[k]] if zoom else FULLBOX
            c = im.crop((int(b[0] * w), int(b[1] * h), int(b[2] * w), int(b[3] * h)))
            ch = int(cellw * c.height / c.width)
            c = c.resize((cellw, ch), Image.LANCZOS)
            ImageDraw.Draw(c).text((6, 6), f'{n} {names[k]}', fill=(255, 0, 0))
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
    out, part = sys.argv[1], sys.argv[2]
    looks = ('soft', 'clay', 'stripe')
    args = sys.argv[3:]
    if '--looks' in args:
        i = args.index('--looks'); looks = tuple(args[i + 1].split(',')); del args[i:i + 2]
    zoom = '--nozoom' not in args
    args = [a for a in args if not a.startswith('--')]
    main(out, part, [a.split('=', 1) for a in args], looks, zoom)
