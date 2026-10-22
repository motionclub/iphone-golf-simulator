"""Round 6 build (previews saved in r7/previews_r6) vs round 7 build (previews/) from the three stills' cameras + the aerial of the sea stacks / arch.
python3 sheet_round7.py (system python, Pillow only). Blender previews are NOT Game-view proof."""
from PIL import Image, ImageDraw
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/"
H = R + "work/postcard-look/v2/hole08/"
old, new = H + "r7/previews_r6/", H + "previews/"
names = [("tee", "hole08_tee_blender.png"), ("approach", "hole08_approach_blender.png"), ("arch", "hole08_arch_blender.png")]
fw, fh = 300, 533
s = Image.new("RGB", (fw * 6, fh + 20), (24, 24, 30))
d = ImageDraw.Draw(s)
i = 0
for lab, fn in names:
    for tag, root in (("round 6", old), ("round 7", new)):
        s.paste(Image.open(root + fn).convert("RGB").resize((fw, fh), Image.LANCZOS), (i * fw, 20)); d.text((i * fw + 4, 4), f"{tag} Blender: {lab}", fill=(230, 230, 230)); i += 1
s.save(new + "sheet_round7_full.jpg", quality=90)
# aerial: the stacks and the arch
a = Image.new("RGB", (1600, 2 * 450 + 40), (24, 24, 30)); d = ImageDraw.Draw(a)
for j, (tag, root) in enumerate((("round 6", old), ("round 7", new))):
    for k, fn in enumerate(("aerial_green_blender.png", "aerial_tee_blender.png")):
        im = Image.open(root + fn).convert("RGB"); im = im.resize((800, int(im.height * 800 / im.width)), Image.LANCZOS).crop((0, 0, 800, 450))
        a.paste(im, (k * 800, 20 + j * 470)); d.text((k * 800 + 4, 4 + j * 470), f"{tag} Blender: {fn[:-12]}", fill=(230, 230, 230))
a.save(new + "sheet_round7_aerial.jpg", quality=90)
print("wrote sheet_round7_full.jpg, sheet_round7_aerial.jpg")
