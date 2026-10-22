"""Round 7 build (previews saved in r8/previews_r7) vs round 8 build (previews/) from the three stills' cameras + the arch fold crop + the fringe close views.
python3 sheet_round8.py (system python, Pillow only). Blender previews are NOT Game-view proof."""
from PIL import Image, ImageDraw
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/"
H = R + "work/postcard-look/v2/hole08/"
old, new = H + "r8/previews_r7/", H + "previews/"
names = [("tee", "hole08_tee_blender.png"), ("approach", "hole08_approach_blender.png"), ("arch", "hole08_arch_blender.png")]
fw, fh = 300, 533
s = Image.new("RGB", (fw * 6, fh + 20), (24, 24, 30))
d = ImageDraw.Draw(s)
i = 0
for lab, fn in names:
    for tag, root in (("round 7", old), ("round 8", new)):
        s.paste(Image.open(root + fn).convert("RGB").resize((fw, fh), Image.LANCZOS), (i * fw, 20)); d.text((i * fw + 4, 4), f"{tag} Blender: {lab}", fill=(230, 230, 230)); i += 1
s.save(new + "sheet_round8_full.jpg", quality=90)
# the arch fold: the lower third of the arch frame, round 7 above round 8
a = Image.new("RGB", (900, 2 * 400 + 40), (24, 24, 30)); d = ImageDraw.Draw(a)
for j, (tag, root) in enumerate((("round 7", old), ("round 8", new))):
    im = Image.open(root + "hole08_arch_blender.png").convert("RGB").crop((0, 1200, 900, 1600))
    a.paste(im, (0, 20 + j * 420)); d.text((4, 4 + j * 420), f"{tag} Blender: lower third of the arch frame (the reviewer's fold)", fill=(230, 230, 230))
a.save(new + "sheet_round8_arch_fold.jpg", quality=90)
# aerial: the stacks and the arch
a = Image.new("RGB", (1600, 2 * 450 + 40), (24, 24, 30)); d = ImageDraw.Draw(a)
for j, (tag, root) in enumerate((("round 7", old), ("round 8", new))):
    for k, fn in enumerate(("aerial_green_blender.png", "aerial_tee_blender.png")):
        im = Image.open(root + fn).convert("RGB"); im = im.resize((800, int(im.height * 800 / im.width)), Image.LANCZOS).crop((0, 0, 800, 450))
        a.paste(im, (k * 800, 20 + j * 470)); d.text((k * 800 + 4, 4 + j * 470), f"{tag} Blender: {fn[:-12]}", fill=(230, 230, 230))
a.save(new + "sheet_round8_aerial.jpg", quality=90)
# fringe close views
import os
fv = H + "previews/fringe/"
names2 = [n for n in ("tee_rim_low", "tee_rim_right", "mid_rim_right", "green_rim") if os.path.exists(fv + n + ".png")]
if names2:
    b = Image.new("RGB", (1200, 400 * ((len(names2) + 1) // 2) + 20), (24, 24, 30)); d = ImageDraw.Draw(b)
    for k, n in enumerate(names2):
        im = Image.open(fv + n + ".png").convert("RGB").resize((600, 400), Image.LANCZOS)
        b.paste(im, ((k % 2) * 600, 20 + (k // 2) * 400)); d.text(((k % 2) * 600 + 4, 4 + (k // 2) * 400), f"round 8 Blender: {n}", fill=(230, 230, 230))
    b.save(new + "sheet_round8_fringe.jpg", quality=90)
print("wrote sheet_round8_full.jpg, sheet_round8_arch_fold.jpg, sheet_round8_aerial.jpg, sheet_round8_fringe.jpg")
