"""before/after sheet of the ruin: round-1 Unity Game-view still (hole09_3_ruin.png, ArtDir) vs the round-2 stage as a BLENDER PREVIEW (EEVEE, same camera; NOT a Game-view proof). system python3 + Pillow."""
from PIL import Image, ImageDraw
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/"
O = R + "work/postcard-look/v2/hole09/"
a = Image.open(R + "ArtDir/screenshots/golf_postcards/look/hole09_3_ruin.png").convert("RGB")      # Unity Game view, round-1 stage installed
b = Image.open(O + "previews/hole09_ruin.png").convert("RGB")                                      # Blender EEVEE preview of the staged round-2 build, same camera
w, h = 450, 800
sheet = Image.new("RGB", (w * 2 + 30, h + 50), (24, 24, 24))
sheet.paste(a.resize((w, h), Image.LANCZOS), (10, 40))
sheet.paste(b.resize((w, h), Image.LANCZOS), (w + 20, 40))
d = ImageDraw.Draw(sheet)
d.text((12, 12), "BEFORE: round-1 stage, Unity Game view (ArtDir still 2026-10-04 22:56)", fill=(235, 235, 235))
d.text((w + 22, 12), "AFTER: round-2 stage, Blender EEVEE preview (NOT Game view)", fill=(235, 235, 235))
sheet.save(O + "r6/ruin_before_after.jpg", quality=90)
# 2x crops of the arch
for nm, im in (("before", a), ("after", b)):
    im.crop((100, 860, 700, 1260)).resize((900, 600), Image.LANCZOS).save(O + f"r6/arch_crop_{nm}.png")
print("ok")
