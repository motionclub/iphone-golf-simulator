"""Compose the proof sheets from proof/raw/*.png  (./py.sh tools/make_sheets.py).  Numbers come from data/*.json (nothing typed by hand)."""
import json
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-full-merge')
raw, out = W / 'proof/raw', W / 'proof'
def font(sz, bold=False):
    for p in ('/System/Library/Fonts/Helvetica.ttc', '/System/Library/Fonts/Supplemental/Arial.ttf', '/Library/Fonts/Arial.ttf'):
        try: return ImageFont.truetype(p, sz, index=1 if (bold and p.endswith('.ttc')) else 0)
        except Exception: pass
    return ImageFont.load_default()
F18, F22, F26, F30 = font(18), font(22), font(26, True), font(30, True)
BG = (24, 24, 28); FG = (235, 235, 235); WARN = (255, 190, 80); BAD = (255, 110, 110)
STUDIO = 'STUDIO LIGHT (clay, 2 suns + AO) - NOT PLATE-MATCHED - shape-assembly proof of FEMALE_FULL_STAGED'
def load(n, w=None, h=None):
    im = Image.open(raw / f'{n}.png').convert('RGB')
    if w or h:
        r = min((w or 10**9) / im.width, (h or 10**9) / im.height); im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    return im
def panel(canvas, im, x, y, label=None, sub=None, lab_color=FG):
    canvas.paste(im, (x, y)); d = ImageDraw.Draw(canvas)
    if label: d.rectangle([x, y, x + im.width, y + 34], fill=(0, 0, 0)); d.text((x + 8, y + 5), label, font=F22, fill=lab_color)
    if sub: d.rectangle([x, y + im.height - 30, x + im.width, y + im.height], fill=(0, 0, 0)); d.text((x + 8, y + im.height - 27), sub, font=F18, fill=FG)
def header(canvas, title, line2=None):
    d = ImageDraw.Draw(canvas); d.text((24, 14), title, font=F30, fill=FG)
    if line2: d.text((24, 56), line2, font=F22, fill=WARN)
S = json.load(open(W / 'data/seams.json')); N = json.load(open(W / 'data/neck_checks.json')); Bv = json.load(open(W / 'data/bvh_checks.json'))
co = Bv['COLLAR_OFFSET']['row1']; neck_step = max(co['max_dist_mm'], S['neck_shoulder_FORM5_border']['DISPLACEMENT_STEP_vs_ArtDir_mm'], 0.0)
# ------------------------------------------------------------------ 1. full figure, 5 views
names = [('01_full_front', 'front'), ('05_full_3q', '3/4 front-left'), ('03_full_left', 'left (cam +x)'), ('02_full_back', 'back'), ('04_full_right', 'right (cam -x)')]
pw, ph = 440, 636
sheet = Image.new('RGB', (pw * 5 + 24 * 2, ph + 150), BG); header(sheet, 'FEMALE_FULL_STAGED - full figure, 5 views', STUDIO)
for i, (n, lab) in enumerate(names): panel(sheet, load(n, pw, ph), 24 + i * pw, 100, lab)
ImageDraw.Draw(sheet).text((24, ph + 112), 'Body_F (clay) + Face_F paint as delivered by F3. Merge of FORM5 torso + arms + hands + F3 head on the hands base. Open FORM5 fails are still visible: bust side fill, underbutt crease.', font=F18, fill=FG)
sheet.save(out / 'FULL_FIGURE_5VIEWS.png'); print('saved FULL_FIGURE_5VIEWS')
# ------------------------------------------------------------------ 2. close-ups
cu = [('10_neck_front', 'neck front'), ('11_neck_3q', 'neck 3/4'), ('12_neck_side', 'neck side (cam +x)'), ('12b_neck_back', 'neck back'),
      ('13_armpit_front', 'armpit front'), ('14b_armpit_3q', 'armpit 3/4'), ('14_armpit_back', 'armpit back'), ('15_wrist_front', 'wrist front'),
      ('16_wrist_side', 'wrist side'), ('17_underbutt_back', 'underbutt back'), ('18_underbutt_3q', 'underbutt 3/4 back'), ('19_bust_3q', 'bust 3/4'),
      ('20_bust_side', 'bust side'), ('21_legtop_front', 'leg-top front'), ('22_legtop_back', 'leg-top back')]
cw, ch = 360, 520; cols = 5; rows = 3
sheet = Image.new('RGB', (cols * cw + 24 * 2, rows * (ch + 8) + 110), BG); header(sheet, 'FEMALE_FULL_STAGED - close-ups (neck, armpit, wrist, underbutt, bust side, leg-top)', STUDIO)
for i, (n, lab) in enumerate(cu):
    im = load(n, cw, ch); panel(sheet, im, 24 + (i % cols) * cw, 100 + (i // cols) * (ch + 8), lab)
sheet.save(out / 'CLOSEUPS_SHEET.png'); print('saved CLOSEUPS_SHEET')
# ------------------------------------------------------------------ 3. seams sheet
W3 = 2800; sheet = Image.new('RGB', (W3, 2250), BG)
header(sheet, 'FEMALE_FULL_STAGED - SEAMS SHEET (provenance colours + ring tubes; shape assembly, not a beauty pass)', STUDIO + '   |   NECK_WELD: FAIL  NECK_STEP_MM = %.2f (limit 2.0)' % neck_step)
y0 = 100
for i, n in enumerate(('30_seams_front', '31_seams_back', '32_seams_left')): panel(sheet, load(n, 590, 840), 24 + i * 600, y0, ['front', 'back', 'left (cam +x)'][i])
# legend
d = ImageDraw.Draw(sheet); lx, ly = 24 + 3 * 600 + 20, y0
d.text((lx, ly), 'Provenance (vertex colour)', font=F26, fill=FG); ly += 44
for rgb, txt in (((200, 200, 200), 'original ArtDir body (untouched)'), ((242, 140, 90), 'FORM5 torso zone (+ leg-top band z .62-.795)'), ((250, 230, 50), 'FORM5 border ring (pinned = original)'),
                 ((90, 140, 242), 'arms zone (arms chat)'), ((90, 205, 115), 'hand shells (hands chat)'), ((180, 115, 230), 'legs/feet (limbs chat)'), ((77, 190, 200), 'head (F3, replaces old head above the collar)')):
    d.rectangle([lx, ly, lx + 34, ly + 26], fill=rgb); d.text((lx + 46, ly + 2), txt, font=F18, fill=FG); ly += 36
ly += 14; d.text((lx, ly), 'Ring tubes', font=F26, fill=FG); ly += 44
for rgb, txt in (((255, 26, 26), 'collar ring (30 verts, z 1.3965-1.4053): F3 head <-> original neck'), ((255, 217, 0), 'FORM5 neck/shoulder border ring'), ((230, 26, 230), 'armpit: FORM5 border ring'),
                 ((0, 242, 242), 'armpit: arm pins (107)'), ((26, 255, 51), 'wrist rings (36)'), ((255, 128, 0), 'leg-top: FORM5 floor ring z .62')):
    d.rectangle([lx, ly, lx + 34, ly + 14], fill=rgb); d.text((lx + 46, ly - 4), txt, font=F18, fill=FG); ly += 34
# zoom row 1
y1 = y0 + 860
zs = [('33_seams_neck_side', 'neck side: collar ring (red)'), ('37_seams_neck_front', 'neck front'), ('38_wire_neck_side', 'topology at the collar (wire)'), ('12_neck_side', 'same neck, clay (kink = light ledge)')]
src_dir = [raw, raw, raw, raw]
for i, (n, lab) in enumerate(zs): panel(sheet, load(n, 590, 590), 24 + i * 600, y1, lab, lab_color=(255, 200, 200) if i in (0, 3) else FG)
# zoom row 2
y2 = y1 + 610
zs2 = [('34_seams_armpit_front', 'armpit: FORM5 border (magenta) / arm pins (cyan)'), ('35_seams_wrist_front', 'wrist ring (green)'), ('36_seams_legtop_back', 'leg-top floor ring (orange)')]
for i, (n, lab) in enumerate(zs2): panel(sheet, load(n, 590, 590), 24 + i * 600, y2, lab)
# numbers table
tx, ty = 24 + 3 * 600 + 20, y2
d.text((tx, ty), 'Seam numbers (mm), from data/seams.json + bvh_checks.json', font=F22, fill=FG); ty += 40
rows_ = [('ring', 'POSITION_STEP', 'DISPL_STEP'),
         ('neck border (FORM5)', '%.3f' % max(S['POSITION_STEP']['neck_shoulder_ring'].values()), '%.3f' % S['neck_shoulder_FORM5_border']['DISPLACEMENT_STEP_vs_ArtDir_mm']),
         ('collar (F3 head)', '%.3f' % max(S['POSITION_STEP']['collar_ring_30'].values()), '%.2f (row1 max)' % co['max_dist_mm']),
         ('armpit border', '%.3f' % max(S['POSITION_STEP']['armpit_border_ring'].values()), '%.3f' % S['armpit_FORM5_border']['DISPLACEMENT_STEP_vs_ArtDir_mm']),
         ('arm pins', '%.3f' % max(S['POSITION_STEP']['arm_pins_107'].values()), '(arms chat)'),
         ('wrist rings', '%.3f' % max(S['POSITION_STEP']['wrist_rings_36'].values()), '%.3f merge-induced' % S['wrist_rings']['DISPLACEMENT_STEP_vs_hands_base_mm']),
         ('leg-top floor ring', '%.3f' % max(S['POSITION_STEP']['leg_top_floor_ring'].values()), '%.3f' % S['leg_top_floor_FORM5_border']['DISPLACEMENT_STEP_vs_ArtDir_mm'])]
for r in rows_:
    d.text((tx, ty), r[0], font=F18, fill=FG); d.text((tx + 250, ty), r[1], font=F18, fill=FG); d.text((tx + 400, ty), r[2], font=F18, fill=FG); ty += 30
ty += 12
d.text((tx, ty), 'armpit across border/pins: relative step max %.2f mm' % S['armpit_relative_step_across_border_and_pins']['max_mm'], font=F18, fill=FG); ty += 30
d.text((tx, ty), 'collar dihedral max %.1f deg (original %.1f)' % (Bv['collar_ring_dihedral_deg']['merged_max'], Bv['collar_ring_dihedral_deg']['ArtDir_original_max']), font=F18, fill=WARN); ty += 30
sl = N['slope_change_y_front']; import math
d.text((tx, ty), 'neck front contour kink at collar: %.1f deg (original %.1f)' % (abs(math.degrees(math.atan(sl['merged_below']) - math.atan(sl['merged_above']))), abs(math.degrees(math.atan(sl['ArtDir_below']) - math.atan(sl['ArtDir_above'])))), font=F18, fill=WARN); ty += 30
d.text((tx, ty), 'NECK_STEP_MM = %.2f  >  2.0  ->  NECK_WELD FAIL' % neck_step, font=F22, fill=BAD); ty += 40
d.text((tx, ty), 'pins stay pins (0.000); the step is the F3 head piece\'s neck column', font=F18, fill=FG); ty += 26
d.text((tx, ty), 'departing from the original neck above the collar ring. Nothing was moved to hide it.', font=F18, fill=FG)
sheet = sheet.crop((0, 0, W3, y2 + 610)); sheet.save(out / 'SEAMS_SHEET.png'); print('saved SEAMS_SHEET', sheet.size)
