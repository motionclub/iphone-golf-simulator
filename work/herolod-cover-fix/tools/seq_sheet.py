import sys, glob, os
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; S = 170
rows = [sorted(glob.glob(f'{d}/SEQ_t{ts}_{h}_*.jpg')) for ts in ['0', '1'] for h in ['BowlingM', 'BowlingF', 'TennisM', 'TennisF']]
rows = [r for r in rows if r]
img = Image.new('RGB', (S * 13, S * len(rows) + 16), 'white'); dr = ImageDraw.Draw(img)
for j, f in enumerate(rows[0]): dr.text((j * S + 2, 2), os.path.basename(f)[:-4].split('_', 4)[-1], fill='black')
for i, r in enumerate(rows):
    for j, f in enumerate(r): img.paste(Image.open(f).resize((S, S)), (j * S, 16 + i * S))
img.save(out, quality=85)
