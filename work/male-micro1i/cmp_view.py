"""plate | mesh | overlay for ONE panel at 2x plate scale.  python3 cmp_view.py <panels_dir> <name> <out.png> [crop x0 y0 x1 y1 in 2x px]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageChops
R = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
pdir = Path(sys.argv[1]); name = sys.argv[2]; out = Path(sys.argv[3])
crop = [int(v) for v in sys.argv[4:8]] if len(sys.argv) >= 8 else None
plate = Image.open(R / 'ArtDir/hero/base_lock/male_head_detail.jpg').convert('RGB')
BOX = {'front': (5, 62, 433, 352), 'left': (433, 62, 834, 352), 'right': (834, 62, 1271, 352), 'q3L': (5, 390, 433, 668), 'q3R': (433, 390, 834, 668)}
BG = (56, 56, 60)
p = plate.crop(BOX[name]); p = p.resize((p.width * 2, p.height * 2), Image.LANCZOS)
m = Image.open(pdir / f'{name}.png').convert('RGBA').resize(p.size, Image.LANCZOS)
bg = Image.new('RGBA', p.size, BG + (255,)); mm_ = Image.alpha_composite(bg, m).convert('RGB')
a = m.split()[3].point(lambda v: 255 if v > 127 else 0)
edge = ImageChops.subtract(a.filter(ImageFilter.MaxFilter(3)), a.filter(ImageFilter.MinFilter(3)))
ov = Image.composite(Image.blend(p, mm_, 0.5), p, a); ov.paste((255, 40, 40), mask=edge)
tiles = [p, mm_, ov]
if crop: tiles = [t.crop(crop) for t in tiles]
W = sum(t.width for t in tiles) + 10 * (len(tiles) - 1)
row = Image.new('RGB', (W, tiles[0].height), (0, 0, 0)); x = 0
for t in tiles: row.paste(t, (x, 0)); x += t.width + 10
row.save(out); print(out, row.size)
