"""Round 5 installed Game view (reviewed) vs round 5 Blender preview vs round 6 Blender preview, tee seam + arch slab, with 2x crops. python3 sheet_round6.py (system python, Pillow only).
Round 5 Game stills = ArtDir/screenshots/golf_postcards/look (the integrator's Unity render of the installed round-5 build; NOT touched here). Blender previews are NOT Game-view proof."""
from PIL import Image, ImageDraw
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/"
H = R + "work/postcard-look/v2/hole08/"
G = R + "ArtDir/screenshots/golf_postcards/look/"
def crop(p, box, size):
    return Image.open(p).convert("RGB").crop(box).resize(size, Image.LANCZOS)
cells = [("round 5 Game view: tee seam (reviewed)", crop(G + "hole08_1_tee.png", (0, 560, 500, 800), (500, 240))),
         ("round 5 Blender: tee seam", crop(H + "r6/previews_r5/hole08_tee_blender.png", (0, 560, 500, 800), (500, 240))),
         ("round 6 Blender: tee seam", crop(H + "previews/hole08_tee_blender.png", (0, 560, 500, 800), (500, 240))),
         ("round 5 Game view: arch foreground (slab)", crop(G + "hole08_3_arch.png", (0, 1100, 900, 1600), (500, 278))),
         ("round 5 Blender: arch foreground", crop(H + "r6/previews_r5/hole08_arch_blender.png", (0, 1100, 900, 1600), (500, 278))),
         ("round 6 Blender: arch foreground", crop(H + "previews/hole08_arch_blender.png", (0, 1100, 900, 1600), (500, 278)))]
full = [("round 5 Game: tee", G + "hole08_1_tee.png"), ("round 6 Blender: tee", H + "previews/hole08_tee_blender.png"), ("round 5 Game: arch", G + "hole08_3_arch.png"), ("round 6 Blender: arch", H + "previews/hole08_arch_blender.png")]
W = 500
sheet = Image.new("RGB", (W * 3, 40 + 240 + 278 + 40 + 4 * 0 + 360 * 0), (24, 24, 30))
d = ImageDraw.Draw(sheet)
for i, (t, im) in enumerate(cells[:3]):
    sheet.paste(im, (i * W, 20)); d.text((i * W + 4, 4), t, fill=(230, 230, 230))
for i, (t, im) in enumerate(cells[3:]):
    sheet.paste(im, (i * W, 20 + 240 + 20)); d.text((i * W + 4, 20 + 240 + 4), t, fill=(230, 230, 230))
sheet.save(H + "previews/sheet_round6_crops.jpg", quality=90)
fw, fh = 300, 533
s2 = Image.new("RGB", (fw * 4, fh + 20), (24, 24, 30))
d2 = ImageDraw.Draw(s2)
for i, (t, p) in enumerate(full):
    s2.paste(Image.open(p).convert("RGB").resize((fw, fh), Image.LANCZOS), (i * fw, 20)); d2.text((i * fw + 4, 4), t, fill=(230, 230, 230))
s2.save(H + "previews/sheet_round6_full.jpg", quality=90)
print("wrote previews/sheet_round6_crops.jpg and sheet_round6_full.jpg")
