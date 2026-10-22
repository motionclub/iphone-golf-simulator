"""make_contact_sheet.py - contact_sheet_vs_still.jpg (system python3 + Pillow): the reference still next to the staged EEVEE previews (NOT Game view)."""
import os
from PIL import Image, ImageDraw, ImageFont
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
H9 = R + "/work/postcard-look/v2/hole09"
ref = Image.open(R + "/ArtDir/environments/refs/split.jpg").convert("RGB")
P = lambda n: Image.open(f"{H9}/previews/{n}.png").convert("RGB")
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
except Exception:
    font = ImageFont.load_default()
W = 1920
def fit(im, w=None, h=None):
    if w: return im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
rows = []
# row 1: still | oblique aerial
a, b = fit(ref, 950), fit(P("hole09_aerial"), 950)
h1 = max(a.height, b.height)
rows.append([(a, "REFERENCE split.jpg (ArtDir/environments/refs)"), (b, "Blender EEVEE preview: oblique aerial of the staged hole_09 (NOT Game view)")])
# row 2: tee | approach | ruin | bunker 1 | bunker 3 (portrait 900x1600 -> height 520)
cells = [("hole09_tee", "tee shot"), ("hole09_approach", "approach (13.5, 269)"), ("hole09_ruin", "LANDMARK ruin ridge"),
         ("b_bunker1", "bunker 1: sand lobes"), ("b_bunker3", "bunker 3, green")]
row2 = [(fit(P(n), h=520), t) for n, t in cells if os.path.exists(f"{H9}/previews/{n}.png")]
rows.append(row2)
# row 3: ridge + cliff views (landscape, 1400x800)
cells = [("c_ridge_n", "ridge from the tee end (knolls, crags, thickets)"), ("c_ridge_s", "ridge from the green end: scrub boundary chain"), ("e_cliff", "strata cliff + knolls")]
row3 = [(fit(P(n), w=630), t) for n, t in cells if os.path.exists(f"{H9}/previews/{n}.png")]
if row3: rows.append(row3)
pad, cap = 10, 30
H = sum(max(im.height for im, _ in r) + cap + pad for r in rows) + pad
sheet = Image.new("RGB", (W, H), (16, 16, 18))
d = ImageDraw.Draw(sheet)
y = pad
for r in rows:
    x = pad
    rh = max(im.height for im, _ in r)
    for im, t in r:
        d.text((x, y), t, fill=(235, 235, 235), font=font)
        sheet.paste(im, (x, y + cap))
        x += im.width + pad
    y += rh + cap + pad
sheet.save(H9 + "/contact_sheet_vs_still.jpg", quality=88)
print("wrote", H9 + "/contact_sheet_vs_still.jpg", sheet.size)
