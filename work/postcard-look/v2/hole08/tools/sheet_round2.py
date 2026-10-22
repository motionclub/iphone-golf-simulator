"""Round 1 vs round 2 contact sheet of the two phone frames (tee, approach) + the plan map of the mow stripes. python3 sheet_round2.py (system python, Pillow only)."""
from PIL import Image, ImageDraw
H = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/hole08/"
cells = [("round 1 tee (reviewer: lower 60% almost flat)", H + "r2/r1_previews/hole08_tee_blender.png"),
         ("round 2 tee (stripe edge, cross-mown tee box, path in the lower frame)", H + "previews/hole08_tee_blender.png"),
         ("round 1 approach", H + "r2/r1_previews/hole08_approach_blender.png"),
         ("round 2 approach (stripe edge 0.5 m right of the line, path crosses the frame)", H + "previews/hole08_approach_blender.png")]
W, Hh = 450, 800
sheet = Image.new("RGB", (W * 4, Hh + 40), (24, 24, 30))
d = ImageDraw.Draw(sheet)
for i, (t, p) in enumerate(cells):
    im = Image.open(p).convert("RGB").resize((W, Hh), Image.LANCZOS)
    sheet.paste(im, (i * W, 40))
    d.text((i * W + 6, 6), t[:60], fill=(230, 230, 230))
    d.text((i * W + 6, 22), t[60:], fill=(230, 230, 230))
sheet.save(H + "previews/sheet_round1_vs_round2.jpg", quality=88)
print("wrote", H + "previews/sheet_round1_vs_round2.jpg")
