"""contact sheets: python3 contact_sheet.py PREVIEW_DIR  (Pillow). sheet_vs_needle.jpg: needle.jpg beside the aerials; sheet_phone.jpg: before (old in-game stills) over Blender previews of the three shots."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
d = sys.argv[1]
def load(p, w=None, h=None):
    im = Image.open(p).convert("RGB")
    if w and h: im = im.resize((w, h), Image.LANCZOS)
    elif w: im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    elif h: im = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
    return im
def label(im, text):
    dr = ImageDraw.Draw(im); dr.rectangle([0, 0, im.width, 22], fill=(14, 14, 20)); dr.text((6, 5), text, fill=(235, 235, 235))
    return im
# sheet 1
ref = label(load(R + "/ArtDir/environments/refs/needle.jpg", 800), "TARGET: needle.jpg (the still)")
a1 = label(load(d + "/aerial_all_blender.png", 800), "hole 8 build: whole hole (Blender preview, NOT Game view)")
a2 = label(load(d + "/aerial_green_blender.png", 800), "hole 8 build: green pad, arch, waterfall (Blender preview)")
a3 = label(load(d + "/aerial_mid_blender.png", 800), "hole 8 build: from the green end (Blender preview)")
H = max(ref.height, a2.height) + max(a1.height, a3.height)
sheet = Image.new("RGB", (1600, H), (14, 14, 20))
sheet.paste(ref, (0, 0)); sheet.paste(a2, (800, 0))
y = max(ref.height, a2.height)
sheet.paste(a1, (0, y)); sheet.paste(a3, (800, y))
sheet.save(d + "/sheet_vs_needle.jpg", quality=90)
# sheet 2: phone shots, before (old in-game stills) / after (Blender preview from the same Game camera)
before = [("hole08_tee", R + "/ArtDir/screenshots/golf_postcards/hole08_tee.jpg"), ("hole08_approach", R + "/ArtDir/screenshots/golf_postcards/hole08_midpad.jpg"), ("hole08_layup", R + "/ArtDir/screenshots/golf_postcards/hole08_layup.jpg")]
after = [("hole08_tee", "tee"), ("hole08_approach", "approach"), ("hole08_arch", "arch landmark close-up"), ("hole08_pathball", "ball on the tee-pad path")]
W, Hh = 300, 533
cols = []
sheet = Image.new("RGB", (W * 4, Hh * 2 + 44), (14, 14, 20))
for i, (n, t) in enumerate(before[:2]):
    sheet.paste(label(load(t, W, Hh), "BEFORE (flat build, in-game) " + n), (i * W, 0))
sheet.paste(label(Image.new("RGB", (W, Hh), (40, 40, 48)), "(no landmark in the old stills)"), (2 * W, 0))
sheet.paste(label(load(before[2][1], W, Hh), "BEFORE (flat build, in-game) layup"), (3 * W, 0))
for i, (n, t) in enumerate(after):
    sheet.paste(label(load(d + f"/{n}_blender.png", W, Hh), "AFTER (Blender preview) " + t), (i * W, Hh + 22))
sheet.save(d + "/sheet_phone_before_after.jpg", quality=90)
print("ok")
