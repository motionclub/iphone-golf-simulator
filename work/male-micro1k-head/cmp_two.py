"""Side-by-side sheet of the same views from several render dirs.  python3.13 cmp_two.py <out.png> <S> <views,comma> <dirA:labelA> <dirB:labelB> ..."""
import sys
from PIL import Image, ImageDraw
out = sys.argv[1]; S = int(sys.argv[2]); views = sys.argv[3].split(','); dirs = [a.split(':') for a in sys.argv[4:]]
sheet = Image.new('RGB', (S * len(views), S * len(dirs)))
for r, (d, lab) in enumerate(dirs):
    for c, v in enumerate(views):
        im = Image.open(f'{d}/{v}.png').convert('RGB').resize((S, S), Image.LANCZOS)
        ImageDraw.Draw(im).text((6, 4), f'{lab} {v}', fill=(255, 255, 0)); sheet.paste(im, (c * S, r * S))
sheet.save(out); print(out, sheet.size)
