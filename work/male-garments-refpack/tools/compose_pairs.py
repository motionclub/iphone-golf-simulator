"""compose_pairs.py <out.jpg> <title> <sheet>:<x0,y0,x1,y1>=<our.png> ... : sheet crop over our render, side by side columns."""
import sys; sys.path.insert(0, 'tools'); from seg import S
from PIL import Image, ImageDraw
out, title = sys.argv[1:3]; H = 380; cols = []
for a in sys.argv[3:]:
    ref, ours = a.split('=')
    sheet, box = ref.split(':'); box = tuple(int(v) for v in box.split(','))
    r = Image.open(S + sheet + '.png').convert('RGB').crop(box); o = Image.open(ours).convert('RGB')
    r = r.resize((int(r.width * H / r.height), H)); o = o.resize((int(o.width * H / o.height), H))
    w = max(r.width, o.width); c = Image.new('RGB', (w, 2 * H + 6), (30, 30, 34)); c.paste(r, ((w - r.width) // 2, 0)); c.paste(o, ((w - o.width) // 2, H + 6)); cols.append(c)
W = sum(c.width for c in cols) + 6 * (len(cols) - 1)
img = Image.new('RGB', (W, 2 * H + 6 + 30), (30, 30, 34)); d = ImageDraw.Draw(img); d.text((8, 8), title, fill=(255, 255, 255)); x = 0
for c in cols: img.paste(c, (x, 30)); x += c.width + 6
img.save(out, quality=88); print(out, img.size)
