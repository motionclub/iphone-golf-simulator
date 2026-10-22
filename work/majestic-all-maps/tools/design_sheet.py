# design_sheet.py <views_dir> <NN> <out.jpg>
# One design sheet per hole: the top-down map (FWD = up, the map camera looks down with the line of play up) annotated
# with the brief's landmark per direction and the density zones, the 360 strip at mid-fairway, and the brief's text.
import re, sys, os
from PIL import Image, ImageDraw, ImageFont

views, nn, out = sys.argv[1], sys.argv[2], sys.argv[3]
here = os.path.dirname(os.path.abspath(__file__))
brief = open(os.path.join(here, '..', 'design', 'HOLE_BRIEFS.md')).read()

row = None; course = None
for block in re.split(r'\n## ', brief):
    for line in block.splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) >= 7 and cells[0] == str(int(nn)):
            row = cells; course = block.splitlines()[0]
if not row: sys.exit('no brief row for hole ' + nn)
num, name, fwd, back, lr, sets, offl = row[:7]
left = right = lr
m = re.match(r'\s*L(?:/R)?:\s*(.*?)\.\s*R:\s*(.*)', lr)
if m: left, right = m.group(1), m.group(2)
elif lr.startswith('L/R:'): left = right = lr[4:].strip()

def font(sz):
    try: return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', sz)
    except Exception: return ImageFont.load_default()
F1, F2, F3 = font(40), font(24), font(21)

W, H = 2560, 1600
sheet = Image.new('RGB', (W, H), (246, 243, 236)); d = ImageDraw.Draw(sheet)
d.text((40, 24), f'Hole {num} — {name}', fill=(20, 30, 60), font=F1)
d.text((40, 76), course.strip(), fill=(90, 90, 100), font=F2)

def wrap(text, width, f):
    words = text.split(); lines = []; cur = ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) > width: lines.append(cur); cur = w
        else: cur = t
    if cur: lines.append(cur)
    return lines

# map with zones and direction labels
mp = os.path.join(views, f'h{nn}_map.jpg')
mx, my, ms = 40, 120, 1000
if os.path.exists(mp):
    im = Image.open(mp).convert('RGB'); s = min(ms / im.width, ms / im.height)
    im = im.resize((int(im.width * s), int(im.height * s))); ox = mx + (ms - im.width) // 2; oy = my + (ms - im.height) // 2
    sheet.paste(im, (ox, oy))
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    cx, cy = mx + ms // 2, my + ms // 2
    import json, math
    cams = json.load(open(os.path.join(views, f'h{nn}_cameras.json')))['views']
    mc = cams['map']; px, py, pz = mc['pos']
    # the map camera looks straight down, image up = the line of play; world units are yards
    order = [k for k in ('tee', 'mid', 'approach', 'puttFront') if k in cams and 'ball' in cams[k]]
    pts = [cams[k]['ball'] for k in order]
    fx, fz = pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1]; n = math.hypot(fx, fz) or 1; fx, fz = fx / n, fz / n
    rx, rz = fz, -fx
    half = py * math.tan(math.radians(30)); ppy = (im.height / 2) / half   # pixels per yard
    def P(x, z):
        dx, dz = x - px, z - pz
        return (ox + im.width / 2 + (dx * rx + dz * rz) * ppy, oy + im.height / 2 - (dx * fx + dz * fz) * ppy)
    line = [P(x, z) for x, z in pts]
    for yd, col in ((80, (40, 90, 220, 120)), (25, (30, 170, 70, 140)), (8, (255, 205, 40, 170))):
        w = max(2, int(2 * yd * ppy))
        od.line(line, fill=col, width=w, joint='curve')
        for q in (line[0], line[-1]): od.ellipse((q[0] - w / 2, q[1] - w / 2, q[0] + w / 2, q[1] + w / 2), fill=col)
    od.line(line, fill=(255, 255, 255, 230), width=4)
    for k, q in zip(order, line): od.ellipse((q[0] - 7, q[1] - 7, q[0] + 7, q[1] + 7), fill=(20, 30, 60, 255))
    sheet.paste(Image.alpha_composite(sheet.convert('RGBA'), ov).convert('RGB'))
    d = ImageDraw.Draw(sheet)
    def tag(x, y, label, text, anchor):
        lines = wrap(f'{label}: {text}', 330, F3)
        h = 26 * len(lines) + 12; w = 350
        x0 = {'n': x - w / 2, 's': x - w / 2, 'w': x, 'e': x - w}[anchor]; y0 = {'n': y, 's': y - h, 'w': y - h / 2, 'e': y - h / 2}[anchor]
        d.rounded_rectangle((x0, y0, x0 + w, y0 + h), 10, fill=(255, 255, 255), outline=(20, 30, 60), width=2)
        for i, l in enumerate(lines): d.text((x0 + 10, y0 + 6 + 26 * i), l, fill=(20, 30, 60), font=F3)
    tag(cx, my + 8, 'FWD', fwd, 'n'); tag(cx, my + ms - 8, 'BACK', back, 's')
    tag(mx + 8, cy, 'L', left, 'w'); tag(mx + ms - 8, cy, 'R', right, 'e')
    d.text((mx, my + ms + 8), 'zones round the line of play (white): yellow Z0 corridor ±8 yd · green Z1 near to ±25 yd (dense clusters) · blue Z2 mid to ±80 yd (groves, framed gaps) · beyond: Z3 shore band + foam, Z4 far impostor ring', fill=(60, 60, 70), font=F3)

# 360 strip
x0 = 1080; y = 120
d.text((x0, y), '360° at mid-fairway today (0 = toward the green)', fill=(20, 30, 60), font=F2); y += 34
tw = (W - x0 - 40 - 30) // 4; th = tw * 9 // 16
for i, a in enumerate((270, 0, 90, 180)):
    p = os.path.join(views, f'h{nn}_pan{a}.jpg')
    if os.path.exists(p):
        im = Image.open(p).convert('RGB').resize((tw, th)); sheet.paste(im, (x0 + i * (tw + 10), y))
    d.text((x0 + i * (tw + 10) + 6, y + 4), {270: 'L', 0: 'FWD', 90: 'R', 180: 'BACK'}[a], fill=(255, 255, 255), font=F2)
y += th + 24
for label, text in (('Set pieces near the corridor', sets), ('Off-line views must show', offl)):
    d.text((x0, y), label, fill=(20, 30, 60), font=F2); y += 32
    for l in wrap(text, W - x0 - 60, F3): d.text((x0 + 10, y), l, fill=(40, 40, 50), font=F3); y += 27
    y += 12
cb = brief.split('## ' + course.strip())[1].split('\n|')[0] if course else ''
d.text((x0, y), 'Course rules (light, palette, landmark, life, weather)', fill=(20, 30, 60), font=F2); y += 32
for para in [l.strip('- ').strip() for l in cb.splitlines() if l.startswith('- ')]:
    for l in wrap(para.replace('**', ''), W - x0 - 60, F3):
        if y > H - 40: break
        d.text((x0 + 10, y), l, fill=(40, 40, 50), font=F3); y += 26
    y += 6
d.text((W - 620, H - 36), 'chat 10 · work/majestic-all-maps/design', fill=(140, 140, 150), font=F3)
sheet.save(out, quality=88); print(out)
