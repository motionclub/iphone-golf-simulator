import sys, json
from PIL import Image, ImageDraw
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-hands-form3'
sys.path.insert(0, W)
from sheetlib import font
F = W + '/proof/final/'
a = json.load(open(W + '/data/allmetrics_FORM2.json')); b = json.load(open(W + '/data/allmetrics_final.json'))
pa, pb = a['palm']['R'], b['palm']['R']
vol = json.load(open(W + '/data/palmvol.json'))
sn = json.load(open(W + '/data/sil_native.json')); k = list(sn.keys()); sb = sn[[x for x in k if 'before' in x][0]]; sa = sn[[x for x in k if 'after' in x][0]]
def pc(x, y): return '%+.0f%%' % (100 * (y / x - 1))
lines = ['MALE HANDS FORM3 (palm scale + round tips) - FORM2 (top) vs FORM3 (bottom), R | L, plates male_body_bald.jpg + male_multiangle_body.jpg',
 'PALM (R, wrist line w=-44 mm -> web line): length %.0f -> %.0f mm (%s) | breadth at web %.0f -> %.0f mm (%s), mid-palm %.0f -> %.0f mm (%s) | planform area %.0f -> %.0f mm2 (%s) | volume %s | palm : middle finger %.2f -> %.2f' % (
   pa['palm_length_mm'], pb['palm_length_mm'], pc(pa['palm_length_mm'], pb['palm_length_mm']), pa['palm_breadth_web_mm'], pb['palm_breadth_web_mm'], pc(pa['palm_breadth_web_mm'], pb['palm_breadth_web_mm']),
   pa['palm_breadth_mid_mm'], pb['palm_breadth_mid_mm'], pc(pa['palm_breadth_mid_mm'], pb['palm_breadth_mid_mm']), pa['palm_planform_area_mm2'], pb['palm_planform_area_mm2'], pc(pa['palm_planform_area_mm2'], pb['palm_planform_area_mm2']),
   vol['pct'], pa['palm_over_middle_finger'], pb['palm_over_middle_finger']),
 'fingertip reach kept (+2..+8 mm vs FORM2), so finger length from the web %s mm -> %s mm (middle %.0f -> %.0f); 9-row round pad caps (FORM2: 6 rows, chisel rim); thumb thenar mound %.1f mm, root dihedral %.0f deg (gate 75)' % (
   '/'.join('%.0f' % x for x in pa['finger_len_from_web_mm']), '/'.join('%.0f' % x for x in pb['finger_len_from_web_mm']), pa['finger_len_from_web_mm'][1], pb['finger_len_from_web_mm'][1], b['extra']['R']['T1_thenar_mound_mm'], b['extra']['R']['T5_dihedral']['max']),
 'zone audit: 0 vertices outside the two hand shells, weld ring moved 0.000 mm, arms/torso/head/legs bit-identical | Blender-native bald silhouette XOR/union (gate <= 5.0%%): front %.2f%% -> %.2f%%, back %.2f%% -> %.2f%% | %d tris (was %d)' % (
   sb['bald_front']['pct'], sa['bald_front']['pct'], sb['bald_back']['pct'], sa['bald_back']['pct'], b['tris'], a['tris'])]
def header(width, lines):
    im = Image.new('RGB', (width, 16 + 30 * len(lines)), (14, 14, 16)); d = ImageDraw.Draw(im)
    for i, l in enumerate(lines): d.text((12, 10 + i * 30), l, fill=(255, 230, 120) if i == 0 else (225, 225, 225), font=font(24 if i == 0 else 18))
    return im
r = Image.open(F + '_hands_R.png').convert('RGB'); l = Image.open(F + '_hands_L.png').convert('RGB')
body = Image.new('RGB', (r.width + l.width + 20, r.height), (18, 18, 20)); body.paste(r, (0, 0)); body.paste(l, (r.width + 20, 0))
h = header(body.width, lines); S = Image.new('RGB', (body.width, h.height + body.height)); S.paste(h, (0, 0)); S.paste(body, (0, h.height))
S = S.resize((S.width * 3 // 5, S.height * 3 // 5), Image.LANCZOS); S.save(F + '03d_hands_form3_palm_before_after.png'); print(S.size)
