import sys, json
from PIL import Image, ImageDraw
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-hands-form3'
sys.path.insert(0, W)
from sheetlib import font
F = W + '/proof/final/'; I = W + '/proof/it/'
a = json.load(open(W + '/data/allmetrics_FORM2.json')); b = json.load(open(W + '/data/allmetrics_final.json'))
import textwrap
def header(width, lines):
    wr = []
    for i, l in enumerate(lines): wr += textwrap.wrap(l, 118 if i == 0 else 185)
    im = Image.new('RGB', (width, 16 + 28 * len(wr)), (14, 14, 16)); d = ImageDraw.Draw(im)
    for i, l in enumerate(wr): d.text((12, 10 + i * 28), l, fill=(255, 230, 120) if i == 0 else (225, 225, 225), font=font(22 if i == 0 else 17))
    return im
def stack(parts, bg=(18, 18, 20)):
    w = max(p.width for p in parts); h = sum(p.height for p in parts); S = Image.new('RGB', (w, h), bg); y = 0
    for p in parts: S.paste(p, (0, y)); y += p.height
    return S
def fit(im, w): return im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
W0 = 1866
hdr = header(W0, ['FINGER_TIP_ROUND - tip profiles: PLATE | FORM2 | FORM3 (profile cameras, then isolated mesh close-ups, R hand; L hand is the exact mirror)',
                  'FORM2: constant-width tube + 6-row elliptical cap whose pole is pulled to the dorsal line (side-contour kink 46 deg; thumb cap L/r 0.77 = blunt).  FORM3: 9-row round pad caps, cap length = 1.2 x mean tip radius, no tip smoothing (side kink 10-12 deg, L/r 1.2-1.3).',
                  'Plate fingertips are only ~4 px wide in these cameras (top panel = context); the mesh close-ups below show the actual tip profile in dorsal / radial / palmar / 3/4 views (window 30 mm fingers, 45 mm thumb).'])
tp = Image.open(I + 'tipplate.png').convert('RGB'); tp = fit(tp, W0)
parts = [hdr, tp]
for nm in ('tips_mid', 'tips_pinky', 'tips_thumb'): parts.append(Image.open(I + nm + '.png').convert('RGB'))
# table
names = ['finger0', 'finger1', 'finger2', 'finger3', 'thumb']; label = {'finger0': 'index', 'finger1': 'middle', 'finger2': 'ring', 'finger3': 'pinky', 'thumb': 'thumb'}
tbl = Image.new('RGB', (W0, 40 + 30 * (len(names) + 3)), (14, 14, 16)); d = ImageDraw.Draw(tbl)
cols = [12, 160, 330, 620, 900, 1220, 1500]
hd = ['digit (R; L = mirror)', 'cap rows F2 -> F3', 'cap length / mean tip radius F2 -> F3', 'max contour turn, side F2 -> F3', 'max contour turn, plan F2 -> F3', 'gate']
d.text((12, 8), 'TIP ROUNDNESS METRICS (measured on the final vertex arrays; gates: cap rows >= 8, cap length / mean radius in [0.9, 1.4], max contour turn <= 25 deg)', fill=(255, 230, 120), font=font(18))
for c, t in zip(cols, hd): d.text((c, 40), t, fill=(200, 200, 200), font=font(16))
ok_all = True
for i, nme in enumerate(names):
    ta, tb = a['tips']['R'][nme], b['tips']['R'][nme]
    ok = tb['cap_rows'] >= 8 and 0.9 <= tb['hemisphere_ratio'] <= 1.4 and tb['max_turn_side_deg'] <= 25 and tb['max_turn_plan_deg'] <= 25; ok_all &= ok
    y = 70 + 30 * i
    row = [label[nme], '%d -> %d' % (ta['cap_rows'], tb['cap_rows']), '%.2f -> %.2f' % (ta['hemisphere_ratio'], tb['hemisphere_ratio']), '%.0f -> %.0f deg' % (ta['max_turn_side_deg'], tb['max_turn_side_deg']), '%.0f -> %.0f deg' % (ta['max_turn_plan_deg'], tb['max_turn_plan_deg']), 'PASS' if ok else 'FAIL']
    for c, t in zip(cols, row): d.text((c, y), t, fill=(120, 230, 150) if (t == 'PASS') else ((255, 120, 120) if t == 'FAIL' else (230, 230, 230)), font=font(17))
parts.append(tbl)
S = stack(parts); S.save(F + '03d_hands_form3_tips_closeup.png'); print(S.size, 'ALL_DIGITS_OK' if ok_all else 'TIP_FAIL')
