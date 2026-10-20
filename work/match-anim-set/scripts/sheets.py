"""Compose the proof contact sheets from proof/_cells/*.png (system python + Pillow):  python3 sheets.py
Writes proof/Sheet_<Hero>_Behind.png and proof/Sheet_<Hero>_Side.png - every clip, one cell at contact (or mid-clip for the movement clips) and one at the
held finish (or the last frame), two clips per row."""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, '..'))
PROOF = WORK + '/proof'
CELLS = PROOF + '/_cells'
CLIPS = ['ReadyIdle', 'SplitToForehand', 'SplitToBackhand', 'RecoverCenter', 'Forehand', 'ForehandOpen', 'ForehandWide', 'ForehandShort',
         'Backhand', 'BackhandWide', 'SliceApproach', 'Serve', 'Return', 'VolleyForehand', 'VolleyBackhand', 'Overhead']
try:
    FONT = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 14)
    FONT_B = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 16)
except Exception:
    FONT = FONT_B = ImageFont.load_default()
CW, CH = 360, 450

for tag, label in (('male', 'Male'), ('female', 'Female')):
    meta = json.load(open(f'{WORK}/data/bake_{tag}.json'))['clips']
    cells = json.load(open(f'{CELLS}/{tag}_cells.json'))
    for view in ('behind', 'side'):
        rows = (len(CLIPS) + 1) // 2
        sheet = Image.new('RGB', (4 * CW, rows * (CH + 26) + 30), (24, 26, 30))
        d = ImageDraw.Draw(sheet)
        d.text((10, 6), f'{label} - {"behind-the-court camera" if view == "behind" else "side camera (racket-hand side)"} - cell 1: contact, cell 2: held finish (movement clips: mid, end)', fill=(235, 235, 235), font=FONT_B)
        for i, clip in enumerate(CLIPS):
            r, col = i // 2, (i % 2) * 2
            m = meta[clip]
            labs = list(cells[clip].keys())
            for j, lab in enumerate(labs):
                fr = cells[clip][lab]
                im = Image.open(f'{CELLS}/{tag}_{clip}_{lab}_{view}.png').convert('RGB').resize((CW, CH), Image.LANCZOS)
                x, y = (col + j) * CW, 30 + r * (CH + 26)
                sheet.paste(im, (x, y + 26))
                d.rectangle([x, y, x + CW, y + 26], fill=(40, 44, 52))
                tag_s = f'{clip}  {lab} f{fr} t={fr / 30.0:.2f}s'
                if lab == 'contact' and m['thin']:
                    tag_s += '  THIN'
                d.text((x + 6, y + 5), tag_s, fill=(255, 220, 120) if lab == 'contact' else (225, 225, 225), font=FONT)
        out = f'{PROOF}/Sheet_{label}_{"Behind" if view == "behind" else "Side"}.png'
        sheet.save(out)
        print('saved', out, sheet.size)
