"""Round 2 vs round 3 contact sheet of the two phone frames (tee, approach). python3 sheet_round3.py (system python, Pillow only). Round 2 = r3/previews_r2 (copy of the round-2 previews)."""
from PIL import Image, ImageDraw
H = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/hole08/"
cells = [("round 2 tee (path starts 3 yd past the ball, upper frame only)", H + "r3/previews_r2/hole08_tee_blender.png"),
         ("round 3 tee (path along the ball's left, 0.5 m clear, in the lower frame)", H + "previews/hole08_tee_blender.png"),
         ("round 2 approach (path left of the frame, lower frame lawn)", H + "r3/previews_r2/hole08_approach_blender.png"),
         ("round 3 approach (path along the ball's left, in the lower frame)", H + "previews/hole08_approach_blender.png")]
W, Hh = 450, 800
sheet = Image.new("RGB", (W * 4, Hh + 40), (24, 24, 30))
d = ImageDraw.Draw(sheet)
for i, (t, p) in enumerate(cells):
    im = Image.open(p).convert("RGB").resize((W, Hh), Image.LANCZOS)
    sheet.paste(im, (i * W, 40))
    d.text((i * W + 6, 6), t[:60], fill=(230, 230, 230))
    d.text((i * W + 6, 22), t[60:], fill=(230, 230, 230))
sheet.save(H + "previews/sheet_round2_vs_round3.jpg", quality=88)
print("wrote", H + "previews/sheet_round2_vs_round3.jpg")
