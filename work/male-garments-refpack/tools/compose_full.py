"""compose_full.py <sheet> <prefix> <out> [title] : the master sheet's 4 cardinal views over our 4 renders."""
import sys; sys.path.insert(0,'tools'); from seg import S
from PIL import Image, ImageDraw
sheet, pre, out = sys.argv[1:4]; title = sys.argv[4] if len(sys.argv) > 4 else ''
ref = Image.open(S + sheet + '.png').convert('RGB')
xs = [(0, 300), (300, 520), (500, 810), (800, 1024)]          # 1024x688 masters: front | right side | back | left side
names = ['front', 'right', 'back', 'left']
H = 640; tiles = []
for (x0, x1), nm in zip(xs, names):
    r = ref.crop((x0, 70, x1, 600)); o = Image.open('%s_%s.png' % (pre, nm)).convert('RGB')
    r = r.resize((int(r.width * H / r.height), H)); o = o.resize((int(o.width * H / o.height), H))
    t = Image.new('RGB', (r.width + o.width + 4, H), (30, 30, 34)); t.paste(r, (0, 0)); t.paste(o, (r.width + 4, 0)); tiles.append(t)
W = sum(t.width for t in tiles) + 8 * 3
img = Image.new('RGB', (W, H + 30), (30, 30, 34)); d = ImageDraw.Draw(img); d.text((8, 8), title, fill=(255, 255, 255)); x = 0
for t in tiles: img.paste(t, (x, 30)); x += t.width + 8
img.save(out, quality=88); print(out, img.size)
