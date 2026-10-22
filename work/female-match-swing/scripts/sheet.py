"""sheet.py out.jpg W cols  dir:start:end:step[:label] ...   -> contact sheet of frames f_XXXXX.jpg from each dir (rows = specs)"""
import sys
from PIL import Image, ImageDraw
out, W, cols = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
specs = [a.split(":") for a in sys.argv[4:]]
rows = []
for sp in specs:
    d, a, b, st = sp[0], int(sp[1]), int(sp[2]), int(sp[3]); lab = sp[4] if len(sp) > 4 else d.split("/")[-2] + "/" + d.split("/")[-1]
    idx = list(range(a, b + 1, st))[:cols]
    rows.append((lab, [(i, Image.open(f"{d}/f_{i:05d}.jpg")) for i in idx]))
w0, h0 = rows[0][1][0][1].size; H = int(W * h0 / w0)
sheet = Image.new("RGB", (W * cols, H * len(rows)), "white"); dr = ImageDraw.Draw(sheet)
for r, (lab, ims) in enumerate(rows):
    for c, (i, im) in enumerate(ims):
        sheet.paste(im.resize((W, H)), (c * W, r * H)); dr.text((c * W + 4, r * H + 4), f"{lab} f{i}", fill="yellow")
sheet.save(out, quality=90)
