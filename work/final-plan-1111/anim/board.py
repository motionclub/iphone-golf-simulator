"""board.py <round> <out.jpg> [per=3] [view=bend]: the worst wrists the probe photographed, per sport / hero / side / held-or-empty,
before (left) and after (right) the limits, same frame, same camera."""
import sys, os, re, collections
from PIL import Image, ImageDraw, ImageFont
A = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(A, sys.argv[1]); out = sys.argv[2]
per = int(sys.argv[3]) if len(sys.argv) > 3 else 3; view = sys.argv[4] if len(sys.argv) > 4 else "bend"
font = lambda s: ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", s)
groups = collections.defaultdict(list)
for sp in sorted(os.listdir(R)):
    d = os.path.join(R, sp)
    if not os.path.isdir(d) or sp.startswith("film"): continue
    for f in os.listdir(d):
        m = re.match(rf"(.+)_(\d+)_(\d+)to(\d+)_{view}_before\.png$", f)
        if m and os.path.exists(os.path.join(d, f.replace("_before", "_after"))): groups[(sp, m.group(1))].append((int(m.group(3)), int(m.group(4)), int(m.group(2)), os.path.join(d, f)))
S = 300; pad = 8; lab = 26
cells = []
for (sp, key), items in sorted(groups.items()):
    items.sort(reverse=True); chosen = []
    for it in items:                       # the worst, at least 40 frames apart
        if all(abs(it[2] - c[2]) > 40 for c in chosen): chosen.append(it)
        if len(chosen) == per: break
    for b, a, fr, path in chosen: cells.append((sp, key, b, a, path))
cols = 4; rowsN = (len(cells) + cols - 1) // cols
W = pad + cols * (2 * S + pad); H = 60 + rowsN * (S + lab + pad)
img = Image.new("RGB", (W, H), (18, 18, 22)); d = ImageDraw.Draw(img)
d.text((pad, 14), f"Worst wrists in real play ({sys.argv[1]}): before | after the limits, same frame", font=font(26), fill=(255, 255, 255))
for i, (sp, key, b, a, path) in enumerate(cells):
    x = pad + (i % cols) * (2 * S + pad); y = 60 + (i // cols) * (S + lab + pad)
    who = key.split("-")[-1] if "-" in key else key
    d.text((x + 2, y + 2), f"{sp}  {who}   {b} to {a} deg", font=font(17), fill=(255, 220, 150))
    img.paste(Image.open(path).convert("RGB").resize((S, S)), (x, y + lab)); img.paste(Image.open(path.replace("_before", "_after")).convert("RGB").resize((S, S)), (x + S, y + lab))
img.save(out, quality=88); print(out, img.size, len(cells), "cells")
