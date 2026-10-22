"""Contact sheets for the hole 10 Blender previews (system python + Pillow). Blender renders (Unity-like patch of tools/render_views.py), NOT Game-view proof."""
import os
from PIL import Image, ImageDraw

R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
S = f"{R}/work/postcard-look/v2/hole10"
P = f"{S}/previews"
P1 = f"{S}/round1/pv"
P2 = f"{S}/round2/pv"
TAG = "Blender EEVEE, Unity-like materials / sky / fog / lava lights, not the Game view"


def label(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, im.width, 22), fill=(14, 14, 18))
    d.text((6, 5), text, fill=(235, 235, 235))
    return im


def fit(path, w=None, h=None):
    im = Image.open(path).convert("RGB")
    if w and h:
        im = im.resize((w, h))
    elif h:
        im = im.resize((round(im.width * h / im.height), h))
    elif w:
        im = im.resize((w, round(im.height * w / im.width)))
    return im


def grid(items, cols, w, h, bg=(20, 20, 24)):
    rows = (len(items) + cols - 1) // cols
    s = Image.new("RGB", (cols * (w + 8) - 8, rows * (h + 30) - 8), bg)
    for k, (path, text) in enumerate(items):
        s.paste(label(fit(path, w, h), text), ((k % cols) * (w + 8), (k // cols) * (h + 30)))
    return s


# 1. oblique aerial vs the reference still (crater.jpg)
ref = label(fit(f"{R}/ArtDir/environments/refs/crater.jpg", h=540), "reference still: ArtDir/environments/refs/crater.jpg")
a1 = label(fit(f"{P}/hole10_aerial2.png", h=540), "staged hole 10, oblique aerial from the NE (" + TAG + ")")
a2 = label(fit(f"{P}/hole10_aerial4.png", h=540), "staged hole 10, aerial from the E")
s = Image.new("RGB", (ref.width + a1.width + a2.width + 20, 540), (20, 20, 24))
s.paste(ref, (0, 0)); s.paste(a1, (ref.width + 10, 0)); s.paste(a2, (ref.width + a1.width + 20, 0))
s.save(f"{S}/sheet_aerial_vs_still.jpg", quality=90)

# 2. all aerial / wall cameras of the staged build
names = [("hole10_aerial", "aerial (SW, above the strip)"), ("hole10_aerial2", "aerial2 (NE)"), ("hole10_aerial3", "aerial3 (S, outside the bowl)"),
         ("hole10_aerial4", "aerial4 (E)"), ("hole10_wallclose", "wallclose (S wall, 100 m)"), ("hole10_wallclose2", "wallclose2 (E wall)")]
grid([(f"{P}/{n}.png", "staged: " + t) for n, t in names], 3, 640, 360).save(f"{S}/sheet_aerials.jpg", quality=90)

# 3. round 1 (top), round 2 (middle, the build the round-2 reviewer failed) and round 3 (bottom, this build): same tool, same cameras
if os.path.exists(f"{P1}/hole10_aerial.png") and os.path.exists(f"{P2}/hole10_aerial.png"):
    pick = [("hole10_aerial", "aerial"), ("hole10_aerial2", "aerial2"), ("hole10_aerial4", "aerial4"), ("hole10_wallclose", "wallclose")]
    top = [(f"{P1}/{n}.png", "round 1: " + t) for n, t in pick]
    mid = [(f"{P2}/{n}.png", "round 2 (failed review): " + t) for n, t in pick]
    bot = [(f"{P}/{n}.png", "round 3 (staged): " + t) for n, t in pick]
    grid(top + mid + bot, 4, 480, 270).save(f"{S}/sheet_round1_2_3.jpg", quality=90)

# 3b. the features the round-3 findings asked for, close up (wall glow in the joints, crust, cone, rim)
feat = [("hole10_wallclose", "wall columns: glow only in the joints, ragged terraced skyline"), ("hole10_wallclose2", "east wall"), ("hole10_cone", "volcano: lava flows + molten crater"),
        ("hole10_aerial2", "crust field cut by lava rivers (NE aerial)"), ("hole10_aerial3", "outer moat + near wall flanking the strip"), ("hole10_aerial4", "E aerial")]
grid([(f"{P}/{n}.png", t) for n, t in feat if os.path.exists(f"{P}/{n}.png")], 3, 640, 360).save(f"{S}/sheet_features.jpg", quality=90)

# 4. the three phone shots: before (old in-game stills, flat) over after (Blender previews of the staged build)
names = [("hole10_tee", "hole10_tee.jpg", "tee (default shot)"), ("hole10_approach", "hole10_approach.jpg", "approach from C"), ("hole10_lavarim", "hole10_rim.jpg", "lava rim landmark")]
W, H = 450, 800
rows = Image.new("RGB", (W * 3 + 20, (H + 22) * 2 + 10), (20, 20, 24))
for k, (n, old, t) in enumerate(names):
    b = label(fit(f"{R}/ArtDir/screenshots/golf_postcards/{old}", w=W, h=H), f"before (flat build, in-game still): {t}")
    a = label(fit(f"{P}/{n}.png", w=W, h=H), f"after (round 3 staged, Blender preview): {t}")
    rows.paste(b, (k * (W + 10), 0))
    rows.paste(a, (k * (W + 10), H + 32))
rows.save(f"{S}/sheet_phone_before_after.jpg", quality=90)

# 5. plan view (mask colours: lava red, wall / rock blue, ground green, cone cyan), round 1 / round 2 / now
if all(os.path.exists(f) for f in (f"{P1}/mask_hole10_plan.png", f"{P2}/mask_hole10_plan.png", f"{P}/mask_hole10_plan.png")):
    grid([(f"{P1}/mask_hole10_plan.png", "round 1 plan (mask colours)"), (f"{P2}/mask_hole10_plan.png", "round 2 plan: near wall, far ring, crust mesas"),
          (f"{P}/mask_hole10_plan.png", "round 3 plan: near wall, far ring, crust field")], 3, 520, 520).save(f"{S}/sheet_plan.jpg", quality=90)

# 6. the staged build's own overview still
ov = f"{S}/stage/hole_10_overview.png"
if os.path.exists(ov):
    label(fit(ov, w=1400), "hole_10_overview.png from the staged build (CAM_HOLE_OVERVIEW, orthographic, no Unity-look patch)").save(f"{S}/sheet_overview.jpg", quality=90)
print("sheets written")
