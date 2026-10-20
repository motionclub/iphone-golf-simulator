"""compose a preview sheet from anim_run.py output (system python + Pillow).  python3 tile.py <prefix_sheet.json> <out.png> [cols]"""
import json, sys
from PIL import Image, ImageDraw, ImageFont
js = json.load(open(sys.argv[1])); out = sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
mode = sys.argv[4] if len(sys.argv) > 4 else 'both'     # both | behind | side
cells = js['cells']
w, h = 360, 480
rows_per_cell = 2 if mode == 'both' else 1
try:
    font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 13)
except Exception:
    font = ImageFont.load_default()
nrows = (len(cells) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, nrows * (h * rows_per_cell + 22)), (30, 30, 34))
d = ImageDraw.Draw(sheet)
for i, c in enumerate(cells):
    cx, cy = (i % cols) * w, (i // cols) * (h * rows_per_cell + 22)
    files = c['files'] if mode == 'both' else [c['files'][0 if mode == 'behind' else 1]]
    for j, f in enumerate(files):
        im = Image.open(f).convert('RGB')
        sheet.paste(im, (cx, cy + 22 + j * h))
    mark = ' CONTACT' if js.get('contact') is not None and abs(c['t'] - js['contact']) < 0.017 else ''
    d.text((cx + 4, cy + 3), f"{js['clip']} t={c['t']:.2f}{mark}  {','.join(c['src'])[:34]}", fill=(255, 220, 120) if mark else (230, 230, 230), font=font)
    dg = c.get('diag', {})
    d.text((cx + 4, cy + 22 + 2 * h - 36), f"sweet r{c['sweet'][0]:+.2f} f{c['sweet'][1]:+.2f} u{c['sweet'][2]:+.2f}  wr {dg.get('R_wrist_swing_deg', 0):.0f}/{dg.get('R_wrist_twist_deg', 0):.0f} cl {dg.get('R_wrist_clamp_deg', 0):.0f}", fill=(200, 255, 200), font=font)
    d.text((cx + 4, cy + 22 + 2 * h - 20), f"elb {dg.get('R_elbow_flex_deg', 0):.0f} short {dg.get('R_arm_short', 0) * 100:.1f}/{dg.get('L_arm_short', 0) * 100:.1f}cm shift {dg.get('racket_shift', 0) * 100:.1f} kn {dg.get('lf_knee_flex_deg', 0):.0f}/{dg.get('rf_knee_flex_deg', 0):.0f}", fill=(200, 255, 200), font=font)
sheet.save(out)
print('saved', out, sheet.size)
