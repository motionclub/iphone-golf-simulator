# before_after.py <run dir> <out.jpg> row=label|before_spec|before_caption|after_spec|after_caption ...
# A spec is a path, or path@x0,y0,x1,y1 (crop in the source's pixels). Cells 1100x619, BEFORE left, AFTER right.
import sys
from PIL import Image, ImageDraw, ImageFont

W, H, LABEL = 1100, 619, 150
def font(n):
    for f in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        try: return ImageFont.truetype(f, n)
        except Exception: pass
    return ImageFont.load_default()
F, FS, FT = font(30), font(22), font(40)

def load(spec):
    path, _, box = spec.partition('@')
    im = Image.open(path).convert('RGB')
    if box: im = im.crop(tuple(int(v) for v in box.split(',')))
    return im.resize((W, H), Image.LANCZOS)

out, rows = sys.argv[1], [r.split('|') for r in sys.argv[2:]]
S = Image.new('RGB', (LABEL + 2 * W + 30, 70 + len(rows) * (H + 16)), (16, 18, 24)); d = ImageDraw.Draw(S)
d.text((LABEL + W // 2 - 70, 14), "BEFORE", font=FT, fill=(255, 140, 120))
d.text((LABEL + W + 30 + W // 2 - 60, 14), "AFTER", font=FT, fill=(130, 255, 160))
for i, (label, b, bc, a, ac) in enumerate(rows):
    y = 70 + i * (H + 16)
    for line, text in enumerate(label.split('/')): d.text((12, y + 20 + 38 * line), text, font=F, fill=(255, 255, 255))
    for x, spec, cap in ((LABEL, b, bc), (LABEL + W + 30, a, ac)):
        S.paste(load(spec), (x, y))
        d.rectangle((x, y + H - 34, x + W, y + H), fill=(0, 0, 0)); d.text((x + 10, y + H - 30), cap, font=FS, fill=(255, 235, 120))
S.save(out, quality=88)
print(out, S.size)
