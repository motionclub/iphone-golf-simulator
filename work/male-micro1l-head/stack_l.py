"""stack images vertically (same width), with optional title: python3.13 stack_l.py <out.png> "<title>" in1.png in2.png ..."""
import sys
from PIL import Image, ImageDraw
out = sys.argv[1]; title = sys.argv[2]; ims = [Image.open(p).convert('RGB') for p in sys.argv[3:]]
W = max(i.width for i in ims); rows = []
for i in ims:
    if i.width != W: i = i.resize((W, int(i.height * W / i.width)), Image.LANCZOS)
    rows.append(i)
H = sum(r.height for r in rows) + 6 * (len(rows) - 1) + (24 if title else 0)
sheet = Image.new('RGB', (W, H), (14, 14, 16)); y = 0
if title: ImageDraw.Draw(sheet).text((8, 6), title, fill=(255, 255, 255)); y = 24
for r in rows: sheet.paste(r, (0, y)); y += r.height + 6
sheet.save(out); print(out, sheet.size)
