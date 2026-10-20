"""generic contact sheet: python3 mksheet.py out.png cols rowlabel:dir ... -- name1 name2 ...  (rows = dirs, cols = names)"""
import sys
from PIL import Image, ImageDraw, ImageFont
a = sys.argv[1:]; out = a[0]; i = a.index('--'); rows = [x.split(':', 1) for x in a[1:i]]; names = a[i + 1:]
try: F = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 18)
except Exception: F = ImageFont.load_default()
ims = [[Image.open(f'{d}/{n}.png').convert('RGB') for n in names] for _, d in rows]
w, h = ims[0][0].size; sc = float(__import__('os').environ.get('SC', 1.0)); w2, h2 = int(w * sc), int(h * sc)
S = Image.new('RGB', (len(names) * (w2 + 6) + 6, len(rows) * (h2 + 26) + 6), (16, 16, 16)); d = ImageDraw.Draw(S)
for r, (lab, _) in enumerate(rows):
    for c, n in enumerate(names):
        im = ims[r][c].resize((w2, h2), Image.LANCZOS) if sc != 1 else ims[r][c]
        S.paste(im, (6 + c * (w2 + 6), 6 + r * (h2 + 26) + 22)); d.text((10 + c * (w2 + 6), 6 + r * (h2 + 26)), lab + '  ' + n[:28], fill=(255, 200, 80), font=F)
S.save(out); print(out, S.size)
