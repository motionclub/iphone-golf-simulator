"""python3 tools/sheet.py out.png "label:dir" ... : rows = sources (ref first if 'ref'), cols = front/tq45/right90 (+ lower crops)"""
import sys
from PIL import Image, ImageDraw
out = sys.argv[1]; rows = [a.split(':', 1) for a in sys.argv[2:]]
views = ['front', 'tq45', 'right90', 'front_lower', 'right90_lower']
REF = {'front': 's07_front.png', 'tq45': 's07_tq45.png', 'right90': 's07_right90.png', 'front_lower': 's07_front.png', 'right90_lower': 's07_right90.png'}
T = 360
sheet = Image.new('RGB', (T * len(views), (T + 22) * len(rows)), (255, 255, 255)); d = ImageDraw.Draw(sheet)
for r, (lab, src) in enumerate(rows):
    for c, v in enumerate(views):
        if src == 'ref':
            a = Image.open('refs/' + REF[v]).convert('RGB'); a = a.crop(((a.width - a.height) // 2, 0, (a.width + a.height) // 2, a.height))
            if v.endswith('lower'):
                w = a.width; a = a.crop((int(w * .3), int(w * .45), int(w * .7), int(w * .85))) if v == 'front_lower' else a.crop((int(w * .45), int(w * .42), int(w * .85), int(w * .82)))
        else:
            try: a = Image.open(f'{src}/{v}.png').convert('RGB')
            except FileNotFoundError: continue
        sheet.paste(a.resize((T, T), Image.LANCZOS), (c * T, r * (T + 22) + 22))
        d.text((c * T + 6, r * (T + 22) + 5), f'{lab} {v}', fill=(0, 0, 0))
sheet.save(out)
