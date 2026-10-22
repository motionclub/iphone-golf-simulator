import sys
from PIL import Image, ImageDraw
out, d = sys.argv[1], sys.argv[2:]   # out dir[:label] ...
shots = ["1_both_front", "2_both_34", "3_left_out", "4_right_out", "5_left_front", "6_right_front"]
rows = []
for a in d:
    p, lab = a.split("=")
    for sex in ("female", "male"): rows.append((lab + " " + sex, [Image.open(f"{p}/hands_{sex}_{s}.jpg").resize((300, 300)) for s in shots]))
sh = Image.new("RGB", (300 * len(shots), 300 * len(rows))); dr = ImageDraw.Draw(sh)
for r, (lab, ims) in enumerate(rows):
    for c, im in enumerate(ims): sh.paste(im, (c * 300, r * 300)); dr.text((c * 300 + 4, r * 300 + 4), lab + " " + shots[c], fill="yellow")
sh.save(out, quality=90)
