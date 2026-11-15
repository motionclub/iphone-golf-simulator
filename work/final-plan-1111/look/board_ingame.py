#!/usr/bin/env python3
"""board_ingame.py <out.jpg>: both characters as the game renders them now. Him: the studio body, fitted tops and rounded shoes
loaded into a project copy (HERO_STUDIO preview hook); her: as she is in the game today. Game-shader turnarounds
(look/turnaround_new, turnaround_new_golf) and scene captures (look/ingame_new)."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
OUT = sys.argv[1]; L = os.path.dirname(os.path.abspath(__file__))
def font(n, bold=False):
    try: return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", n, index=1 if bold else 0)
    except Exception: return ImageFont.load_default()
PAD, GAP = 18, 12
def fit(path, w, h, box=None):
    im = Image.open(os.path.join(L, path)).convert("RGB")
    if box: im = im.crop(box)
    s = max(w / im.width, h / im.height); im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2; return im.crop((x, y, x + w, y + h))
T = lambda hero, shot: f"{'turnaround_new_golf' if hero == 'GolfKitHero_Male' else 'turnaround_new'}/{hero}/{shot}.png"
CW, CH = 262, 349
sections = [("Him in tennis, golf and bowling  (game shaders; new body, fitted tops, rounded shoes, loaded in a project copy)", CW, CH, [
        [(T(h, s), None, lab) for s, lab in (("ready_full_front", f"{name}: front"), ("ready_full_front_left", "three-quarter"), ("ready_full_back", "back"), ("ready_top_front", "shirt"), ("ready_shoes_front", "shoes, front"), ("ready_shoes_left", "shoes, side"))]
        for h, name in (("MatchHero_Male", "tennis"), ("GolfKitHero_Male", "golf"), ("BowlingKitHero_Male", "bowling"))]),
    ("Her, as she is in the game today  (game shaders; nothing of hers has changed)", CW, CH, [
        [(T(h, s), None, lab) for h, s, lab in (("MatchHero_Female", "ready_full_front", "tennis: front"), ("MatchHero_Female", "ready_full_front_left", "tennis: three-quarter"), ("GolfKitHero_Female", "ready_full_front", "golf: front"),
                                                ("GolfKitHero_Female", "ready_full_front_left", "golf: three-quarter"), ("BowlingKitHero_Female", "ready_full_front", "bowling: front"), ("BowlingKitHero_Female", "ready_full_front_left", "bowling: three-quarter"))]]),
    ("In the game's scenes  (real captures from the project copy)", 536, 320, [
        [("ingame_new/tennis_store/tennis_rally_wide.png", (1700, 620, 2868, 1317), "tennis: him, mid-rally"), ("ingame_new/tennis_venue/resort_9_hero_postcard.png", (560, 420, 1560, 1017), "tennis: him at gameplay distance"), ("ingame_new/tennis_venue/resort_8_rivalintro.png", (760, 150, 1560, 628), "tennis: her, intro")],
        [("ingame_new/golf_store/golf_hole1_tee.png", (700, 380, 1900, 1096), "golf: him at address"), ("ingame_new/bowl_tiki/stills/react.jpg", (300, 130, 1100, 608), "bowling: him, reaction shot"), ("ingame_new/bowl_tiki/stills/setup.jpg", (240, 250, 1040, 728), "bowling: him at the line")],
        [("ingame_new/hub_male/locker_look-mirror_0.png", (934, 300, 1934, 897), "locker room: him"), ("ingame_new/hub/locker_look-mirror_0.png", (934, 300, 1934, 897), "locker room: her"), ("ingame_new/tennis_store/tennis_live.png", (700, 560, 1900, 1276), "tennis: him serving")]]),
]
W = PAD * 2 + 6 * CW + 5 * GAP
H = 64 + sum(40 + len(rows) * (ch + 30) for _, cw, ch, rows in sections) + 30
im = Image.new("RGB", (W, H), "#fcfcfb"); d = ImageDraw.Draw(im)
d.text((PAD, 18), "Our characters in the game now  (rendered by the game, 2026-11-12)", font=font(25, True), fill="#0b0b0b")
y = 64
for title, cw, ch, rows in sections:
    d.text((PAD, y), title, font=font(19, True), fill="#0b0b0b"); y += 34
    for row in rows:
        for k, (p, box, lab) in enumerate(row):
            x = PAD + k * (cw + GAP)
            if os.path.exists(os.path.join(L, p)): im.paste(fit(p, cw, ch, box), (x, y))
            else: d.rectangle((x, y, x + cw, y + ch), fill="#dddddd"); d.text((x + 8, y + 8), "missing", font=font(15), fill="#0b0b0b")
            d.text((x + 2, y + ch + 5), lab, font=font(16), fill="#0b0b0b")
        y += ch + 30
    y += 6
im.save(OUT, quality=90); print(OUT, im.size)
