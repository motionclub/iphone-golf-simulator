# sheet.py out.jpg cols label file[:caption] ... -> a contact sheet of captures (480x270 cells)
import sys
from PIL import Image, ImageDraw
out, cols, label, files = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4:]
W, H = 480, 270
rows = (len(files) + cols - 1) // cols
S = Image.new('RGB', (W * cols, H * rows + 28), (17, 17, 17)); d = ImageDraw.Draw(S)
for i, spec in enumerate(files):
    path, _, cap = spec.partition(':')
    im = Image.open(path).convert('RGB').resize((W, H), Image.LANCZOS)
    x, y = (i % cols) * W, (i // cols) * H
    S.paste(im, (x, y)); d.rectangle((x, y, x + W, y + 18), fill=(0, 0, 0)); d.text((x + 4, y + 3), cap or path.split('/')[-1], fill=(255, 255, 0))
d.text((6, H * rows + 8), label, fill=(255, 255, 255))
S.save(out, quality=86)
