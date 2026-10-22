import sys, json, textwrap
from PIL import Image, ImageDraw
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-hands-form3'
sys.path.insert(0, W)
from sheetlib import font
a = json.load(open(W + '/data/allmetrics_FORM2.json')); b = json.load(open(W + '/data/allmetrics_final.json'))
pa, pb = a['palm']['R'], b['palm']['R']
im = Image.open(W + '/proof/it/profcmp_final.png').convert('RGB')
lines = ['PALM_SCALE in the plate PROFILE cameras (palm face-on): PLATE | FORM2 | FORM3 (char L hand top, char R hand bottom)',
 'FORM2 palm: %.0f mm long, %.0f mm wide at the web, 0.93 x its middle finger.  FORM3: %.0f mm long, %.0f mm wide at the web (plate profile reading ~117 mm), %.2f x the middle finger (adult anthropometry ~1.3).' % (pa['palm_length_mm'], pa['palm_breadth_web_mm'], pb['palm_length_mm'], pb['palm_breadth_web_mm'], pb['palm_over_middle_finger']),
 'The arm pose differs from the plate in these cameras (profile silhouette XOR 9-10 %), so compare hand proportions (palm vs fingers, breadth vs wrist), not absolute position.']
wr = []
for i, l in enumerate(lines): wr += textwrap.wrap(l, 105 if i == 0 else 190)
h = Image.new('RGB', (im.width, 16 + 28 * len(wr)), (14, 14, 16)); d = ImageDraw.Draw(h)
for i, l in enumerate(wr): d.text((12, 10 + i * 28), l, fill=(255, 230, 120) if i == 0 else (225, 225, 225), font=font(22 if i == 0 else 17))
S = Image.new('RGB', (im.width, h.height + im.height)); S.paste(h, (0, 0)); S.paste(im, (0, h.height)); S.save(W + '/proof/final/03d_hands_form3_palm_profile_vs_plate.png'); print(S.size)
