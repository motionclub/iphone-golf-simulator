# tools/sheet.py <tag> [<tag2>] : annotated sheet from out/<tag>/{tennis,golf}; with tag2 = before/after rows per panel
import sys
from PIL import Image, ImageDraw, ImageFont
ME = __file__.rsplit('/tools/', 1)[0]
F = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 22); FB = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 30)
# (file, crop or None, [(cx, cy, r, label)])
ROWS = {
 'tennis': [
  ('tennis/tennis_front', None, [(250,1110,85,'T3'),(590,1110,85,'T3')]),
  ('tennis/tennis_torso_tq', None, [(520,560,260,'T1')]),
  ('tennis/tennis_forehand_back', None, [(480,600,120,'T2')]),
  ('tennis/tennis_serve_back', None, [(470,560,130,'T2')]),
  ('tennis/tennis_face_tq', None, [(460,447,45,'F1'),(260,680,100,'F3')]),
  ('tennis/tennis_face_front', (230,330,680,560), [(387,440,30,'F2'),(567,442,30,'F2'),(318,447,30,'F1')]),
 ],
 'golf': [
  ('golf/golf_back', None, [(450,475,150,'G1')]),
  ('golf/golf_backtq', None, []),
  ('golf/golf_contact_back', None, [(520,490,100,'G2')]),
  ('golf/golf_finish_tq', None, [(420,605,60,'G3'),(300,1065,70,'G4')]),
  ('golf/golf_torso_tq', None, [(500,560,260,'T1')]),
 ]}
H = 520
def panel(tag, f, crop, marks, draw_marks):
    im = Image.open(f'{ME}/out/{tag}/{f}.png').convert('RGB')
    ox, oy = 0, 0
    if crop: im = im.crop(crop); ox, oy = crop[0], crop[1]
    d = ImageDraw.Draw(im)
    if draw_marks:
        for cx, cy, r, lab in marks:
            cx -= ox; cy -= oy
            for k in range(4): d.ellipse((cx-r-k, cy-r-k, cx+r+k, cy+r+k), outline=(255, 40, 40))
            d.text((cx+r*.7, cy-r*.9-10), lab, fill=(255, 40, 40), font=FB, stroke_width=3, stroke_fill=(255, 255, 255))
    s = H / im.height
    return im.resize((int(im.width*s), H))
tags = sys.argv[1:]
for sport, items in ROWS.items():
    rows = []
    for t in tags:
        ps = [panel(t, f, c, m, True) for f, c, m in items]
        W = sum(p.width for p in ps); row = Image.new('RGB', (W, H+36), 'white'); x = 0
        for p in ps: row.paste(p, (x, 36)); x += p.width
        ImageDraw.Draw(row).text((10, 4), f'{sport.upper()} — {t}', fill='black', font=FB)
        rows.append(row)
    sheet = Image.new('RGB', (max(r.width for r in rows), sum(r.height for r in rows)), 'white'); y = 0
    for r in rows: sheet.paste(r, (0, y)); y += r.height
    sheet.save(f'{ME}/proof/{"_vs_".join(tags)}_{sport}.jpg', quality=88)
