"""crops.py out.jpg cam f0 f1 W H  label=dir ...  -> rows of cropped frames (centre crop of the golfer cam)"""
import sys
from PIL import Image, ImageDraw
out, cam, f0, f1, W, H = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
rows = [a.split("=") for a in sys.argv[7:]]
idx = list(range(f0, f1 + 1)); cols = len(idx)
sh = Image.new("RGB", (W * cols, H * len(rows))); d = ImageDraw.Draw(sh)
for r, (lab, p) in enumerate(rows):
    for c, i in enumerate(idx):
        im = Image.open(f"{p}/{cam}/f_{i:05d}.jpg"); w, h = im.size
        im = im.crop((w // 2 - 170, 60, w // 2 + 170, h - 120)).resize((W, H)); sh.paste(im, (c * W, r * H)); d.text((c * W + 4, r * H + 4), f"{lab} f{i}", fill="yellow")
sh.save(out, quality=90)
