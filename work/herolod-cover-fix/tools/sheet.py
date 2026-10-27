# tools/sheet.py <dir> <out.jpg> [view]: rows = heroes, columns = off / L1 / L2 per view
import sys, os
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; views = sys.argv[3].split(',') if len(sys.argv) > 3 else ['face', 'body', 'side']
heroes = ['BowlingM', 'BowlingF', 'TennisM', 'TennisF']; tags = ['off', 'L1', 'L2']; S = 360
img = Image.new('RGB', (S * len(views) * 3, S * len(heroes) + 24), 'white'); dr = ImageDraw.Draw(img)
for vi, v in enumerate(views):
    for ti, t in enumerate(tags): dr.text(((vi * 3 + ti) * S + 6, 6), f'{v} {"CHARACTER_LOD=0" if t == "off" else "FORCE=" + t[1]}', fill='black')
for hi, h in enumerate(heroes):
    for vi, v in enumerate(views):
        for ti, t in enumerate(tags):
            p = os.path.join(d, f'{h}_{v}_{t}.jpg')
            if os.path.exists(p): img.paste(Image.open(p).resize((S, S)), ((vi * 3 + ti) * S, 24 + hi * S))
    dr.text((6, 24 + hi * S + 6), h, fill='yellow')
img.save(out, quality=88)
