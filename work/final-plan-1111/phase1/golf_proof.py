#!/usr/bin/env python3
"""golf_proof.py: the Phase 1 golf landing chart, from golf_model.py (the same arithmetic as BallFlight.BounceOff; the game's
own numbers are held by GolfLandingTests). After the pitch mark: old landing above new, one scale per shot."""
import os, math
from PIL import Image, ImageDraw, ImageFont
import golf_model as gm

HERE = os.path.dirname(os.path.abspath(__file__))
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
OLD, NEW = "#eb6834", "#2a78d6"
def font(size, bold=False):
    try: return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size, index=1 if bold else 0)
    except Exception: return ImageFont.load_default()

SHOTS = [("Driver", "fairway", "Driver onto fairway", 26), ("7 Iron", "fairway", "7 iron onto fairway", 26), ("PW", "green", "Pitching wedge onto a green", 26),
         ("LW", "green", "Lob wedge onto a green", 26), ("7 Iron", "rough", "7 iron into rough", 26), ("7 Iron", "bunker", "7 iron into a bunker", 26)]
W, PAD, PH = 1600, 36, 150
H = 70 + len(SHOTS) * (PH + 62) + 30
img = Image.new("RGB", (W, H), SURF); d = ImageDraw.Draw(img)
d.text((PAD, 20), "Golf: what the ball does after it pitches, before and after (full shots, level ground)", font=font(26, True), fill=INK)
d.rectangle([PAD, 58, PAD + 26, 62], fill=OLD); d.text((PAD + 34, 50), "before (10-28 landing)", font=font(16), fill=INK)
d.rectangle([PAD + 260, 58, PAD + 286, 62], fill=NEW); d.text((PAD + 294, 50), "after (11-11 landing)", font=font(16), fill=INK)
y = 96
for club, surf, title, span in SHOTS:
    ref, smash, ang, spin, total = gm.CLUBS[club]; cs = gm.calibrate(club)
    carry, t, vt, vn, sp, apex = gm.air(cs * smash, ang, spin)
    to, tn = [(0, 0)], [(0, 0)]
    # the old landing judged the whole bounce by the lie it first touched: soft/grab from the old table
    soft, grab = {"green": (.15, .1), "rough": (.45, .5), "bunker": (.9, .85)}.get(surf, (0, 0))
    def old_land(trace):
        x = 0; v_t, v_n, s_ = vt, vn, sp; first = True
        for i in range(12):
            rest = max(0.30, min(0.46, 0.46 - 0.006 * max(0, v_n)))
            vy = v_n * min(0.85, rest) * (1 - soft)
            if first: v_t *= max(0.08, 0.6 - 0.5 * (s_ * 60 / (2 * math.pi)) / 10000) * (1 - grab); first = False
            else: v_t *= 0.6 * (1 - grab)
            if vy < 1.2: break
            T = 2 * vy / 9.81
            for k in range(25): tt = T * k / 24; trace.append((x + v_t * tt, vy * tt - 4.905 * tt * tt))
            x += v_t * T; v_n = vy
        trace.append((x, 0)); x += v_t * v_t / (2 * gm.NEW[surf].roll if surf != "fairway" else 6.4); trace.append((x, 0))
        return x
    xo = old_land(to)
    xn, hops, first, _ = gm.land(vt, vn, sp, gm.NEW[surf], trace=tn)
    x0, x1 = PAD + 70, W - PAD - 20
    X = lambda m: x0 + (m / gm.YD + 6) / (span + 6) * (x1 - x0)
    d.text((PAD, y), f"{title}   ·   carry {carry / gm.YD:.0f} yd, lands at {math.degrees(math.atan2(vn, vt)):.0f}° and {math.hypot(vt, vn) * 2.237:.0f} mph with {sp * 60 / (2 * math.pi):.0f} rpm", font=font(19, True), fill=INK)
    y0 = y + 34; base = y0 + PH
    Y = lambda h: base - h / 2.2 * PH
    for h in (0, 1, 2):
        d.line([(x0, Y(h)), (x1, Y(h))], fill=GRID, width=1); d.text((x0 - 40, Y(h) - 9), f"{h} m", font=font(14), fill=INK2)
    for yd in range(0, span + 1, 10):
        d.line([(X(yd * gm.YD), base), (X(yd * gm.YD), base + 5)], fill=INK2, width=1); d.text((X(yd * gm.YD) - 14, base + 7), f"{yd} yd", font=font(13), fill=INK2)
    d.text((X(0) - 62, base - 22), "pitch mark", font=font(13), fill=INK2)
    for tr, col in ((to, OLD), (tn, NEW)):
        d.line([(X(px), Y(max(0, py))) for px, py in tr], fill=col, width=3)
    for xr, col, row, tag in ((xo, OLD, 0, "before"), (xn, NEW, 1, "after")):
        d.ellipse([X(xr) - 6, base - 6, X(xr) + 6, base + 6], fill=col, outline=SURF, width=2)
        ly = y0 + 6 + row * 24
        d.rectangle([x1 - 300, ly + 6, x1 - 282, ly + 10], fill=col)
        d.text((x1 - 274, ly), f"{tag}: stops {xr / gm.YD:+.1f} yd from its pitch mark", font=font(15), fill=INK)
    y += PH + 62
out = f"{HERE}/proof_golf_landing_before_after.jpg"; img.save(out, quality=90); print(out, img.size)
