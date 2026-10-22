"""compose_shoe.py <design> <prefix> <out.jpg> [title]: reference views (top row) over our renders (bottom row), same order."""
import sys; sys.path.insert(0,'tools'); from seg import S
from PIL import Image, ImageDraw
design, pre, out = sys.argv[1:4]; title = sys.argv[4] if len(sys.argv) > 4 else ''
BOX = {'male_tennis': ('13-tennis-shoe-detail', dict(lateral=(40,230,760,640), medial=(770,230,1500,640), front=(1580,210,1980,650), back=(60,750,420,1230), top=(500,840,1260,1160), sole=(1290,850,2040,1170))),
       'male_golf': ('14-golf-shoe-detail', dict(lateral=(30,250,740,620), medial=(770,250,1480,620), front=(1580,220,1980,620), back=(110,760,420,1230), top=(500,820,1260,1170), sole=(1270,820,2040,1180)))}
sheet, boxes = BOX[design]; ref = Image.open(S + sheet + '.png').convert('RGB')
H = 300; tiles = []; FLIP = True
for nm in ['lateral', 'medial', 'front', 'back', 'top', 'sole']:
    r = ref.crop(boxes[nm]); o = Image.open('%s_%s.png' % (pre, nm)).convert('RGB')
    if nm in ('lateral', 'medial', 'top', 'sole') and FLIP: o = o.transpose(Image.FLIP_LEFT_RIGHT)
    w = max(int(r.width * H / r.height), int(o.width * H / o.height))
    t = Image.new('RGB', (w, 2 * H + 4), (30, 30, 34))
    t.paste(r.resize((int(r.width * H / r.height), H)), (0, 0)); t.paste(o.resize((int(o.width * H / o.height), H)), (0, H + 4)); tiles.append(t)
W = sum(t.width for t in tiles) + 6 * (len(tiles) - 1)
img = Image.new('RGB', (W, 2 * H + 4 + 34), (30, 30, 34)); d = ImageDraw.Draw(img)
d.text((8, 8), title, fill=(255, 255, 255)); x = 0
for t in tiles: img.paste(t, (x, 34)); x += t.width + 6
img.save(out, quality=88); print(out, img.size)
