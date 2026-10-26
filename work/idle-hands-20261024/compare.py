"""Before/after sheets for IDLE HANDS (10-24). Usage: python3 compare.py <before shots> <after shots> <out dir>"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

before, after, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 26)

def sheet(name, rows, cell_h):
    """rows: [(label, dir, [(file, caption)])]"""
    cells = [[(Image.open(os.path.join(d, f)), c) for f, c in items if os.path.exists(os.path.join(d, f))] for _, d, items in rows]
    cells = [[(im.resize((round(im.width * cell_h / im.height), cell_h), Image.LANCZOS), c) for im, c in row] for row in cells]
    W = max(sum(im.width + 6 for im, _ in row) for row in cells); H = len(cells) * (cell_h + 50)
    S = Image.new("RGB", (W, H), (24, 24, 28)); dr = ImageDraw.Draw(S); y = 0
    for (label, d, _), row in zip(rows, cells):
        x = 0; col = (255, 140, 120) if d == before else (140, 230, 150)
        for im, c in row:
            S.paste(im, (x, y + 44)); dr.text((x + 8, y + 8), f"{label} · {c}", fill=col, font=font); x += im.width + 6
        y += cell_h + 50
    S.save(os.path.join(out, name), quality=90); print(name, S.size)

for sex, t in (("MALE", "m"), ("FEMALE", "f")):
    rows = []
    for s in ("L", "R"):
        for tag, d in (("BEFORE", before), ("AFTER", after)):
            rows.append((f"{tag} {sex} {s}", d, [(f"{t}_hand{s}_{v}.jpg", v) for v in ("out", "frontout", "front", "back")]))
    sheet(f"hands_{t}.jpg", rows, 360)
rows = []
for sex, t in (("MALE", "m"), ("FEMALE", "f")):
    for tag, d in (("BEFORE", before), ("AFTER", after)):
        rows.append((f"{tag} {sex}", d, [(f"{t}_arms_{a:03d}.jpg", n) for a, n in ((270, "left side"), (315, "3/4 L"), (0, "front"), (45, "3/4 R"), (90, "right side"))]))
sheet("arms.jpg", rows, 520)
