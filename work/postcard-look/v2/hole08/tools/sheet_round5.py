"""Round 4 (installed, Game view) vs round 5 (Blender preview) contact sheet of the two reviewed shots. python3 sheet_round5.py (system python, Pillow only).
Round 4 Game stills = ArtDir/screenshots/golf_postcards/look (the integrator's Unity render of the installed round-4 build; NOT touched here); round 4 Blender previews = r5/previews_r4."""
from PIL import Image, ImageDraw
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/"
H = R + "work/postcard-look/v2/hole08/"
cells = [("round 4 Game view: tee (hard line, path jump)", R + "ArtDir/screenshots/golf_postcards/look/hole08_1_tee.png"),
         ("round 4 Blender preview: tee", H + "r5/previews_r4/hole08_tee_blender.png"),
         ("round 5 Blender preview: tee (stripes through the seam, straight path)", H + "previews/hole08_tee_blender.png"),
         ("round 4 Game view: arch (slab, black box, ridge)", R + "ArtDir/screenshots/golf_postcards/look/hole08_3_arch.png"),
         ("round 4 Blender preview: arch", H + "r5/previews_r4/hole08_arch_blender.png"),
         ("round 5 Blender preview: arch (new camera, vines, turf ledges)", H + "previews/hole08_arch_blender.png")]
W, Hh = 360, 640
sheet = Image.new("RGB", (W * 6, Hh + 40), (24, 24, 30))
d = ImageDraw.Draw(sheet)
for i, (t, p) in enumerate(cells):
    im = Image.open(p).convert("RGB").resize((W, Hh), Image.LANCZOS)
    sheet.paste(im, (i * W, 40))
    d.text((i * W + 6, 6), t[:52], fill=(230, 230, 230))
    d.text((i * W + 6, 22), t[52:], fill=(230, 230, 230))
sheet.save(H + "previews/sheet_round4_vs_round5.jpg", quality=88)
print("wrote", H + "previews/sheet_round4_vs_round5.jpg")
