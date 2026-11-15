#!/usr/bin/env python3
"""golf_film_proof.py [film-dir] [out.jpg]: before/after board of golf landings filmed in the real game (ZGolfLandingFilm).
Top: for the pitching wedge and the lob wedge, game frames around the pin from the moment the ball pitches (old code above, new below).
Bottom: the ball's height over the ground after it pitches, per club, from the same shots (heights.csv)."""
import sys, os, re, csv, glob
from PIL import Image, ImageDraw, ImageFont
root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "golf-film")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "proof_golf_landing_film.jpg")
F = lambda s, b=False: ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if b else "/System/Library/Fonts/Supplemental/Arial.ttf", s)
INK, MUTED, GRID, OLD, NEW, BG = (24, 28, 34), (96, 104, 116), (222, 226, 232), (150, 156, 166), (28, 110, 214), (250, 250, 248)
CELLS, CW, CH, PAD = 6, 384, 216, 28
CROP = (310, 246, 870, 561)          # 560 x 315 around the pin on the game's 1280 x 720 frame, clear of the wind dial
YD = 0.9144

def frames(which, shot):
    r = []
    for f in sorted(glob.glob(f"{root}/{which}/{shot}_*.jpg")):
        m = re.search(r"_t([+-][\d.]+)_h(-?[\d.]+)m", f); r.append((float(m.group(1)), max(0, float(m.group(2))), f))
    return r
def pick(fr, times):
    return [min(fr, key=lambda x: abs(x[0] - t)) for t in times] if fr else []
def summary(which):
    d = {}
    p = f"{root}/{which}/summary.txt"
    for line in open(p) if os.path.exists(p) else []:
        k, v = line.split(":", 1); d[k] = v.strip()
    return d
def heights(which):
    d = {}
    for r in csv.DictReader(open(f"{root}/{which}/heights.csv")):
        d.setdefault(r["shot"], []).append((float(r["t"]), max(0, float(r["heightYards"])) * YD))
    return d

S = {w: summary(w) for w in ("before", "after")}; H = {w: heights(w) for w in ("before", "after")}
W = PAD * 2 + CELLS * CW + (CELLS - 1) * 6
rows = [("pw", "Pitching wedge, about 100 yards"), ("lw", "Lob wedge, about 50 yards")]
chart_h = 330
Ht = 96 + len(rows) * (44 + 2 * (CH + 26) + 26) + 60 + chart_h + 40
img = Image.new("RGB", (W, Ht), BG); d = ImageDraw.Draw(img)
d.text((PAD, 22), "Golf landings filmed in the game: before and after", font=F(34, True), fill=INK)
d.text((PAD, 64), "Same hole, same spot, same full swing, still air. Frames are cropped around the pin; t is seconds after the ball first pitches, h its height over the ground.", font=F(18), fill=MUTED)
y = 104
times = [0.0, 0.2, 0.4, 0.6, 0.9, 1.3]
for shot, title in rows:
    d.text((PAD, y), title, font=F(24, True), fill=INK); y += 40
    for which, label, col in (("before", "Before", OLD), ("after", "After", NEW)):
        fr = frames(which, shot); chosen = pick(fr, times)
        info = S[which].get(shot, "")
        m = re.search(r"run after pitching ([\d.]+) yd.*hops until ([\d.]+) s", info)
        cap = f"{label}: " + (f"ran {m.group(1)} yd after pitching, stopped hopping {m.group(2)} s after it pitched" if m else "")
        d.rectangle((PAD, y + 3, PAD + 14, y + 17), fill=col); d.text((PAD + 22, y), cap, font=F(18, True), fill=INK); y += 26
        for i, t in enumerate(times):
            x = PAD + i * (CW + 6)
            if chosen and abs(chosen[i][0] - t) < 0.12:
                im = Image.open(chosen[i][2]).crop(CROP).resize((CW, CH), Image.LANCZOS); img.paste(im, (x, y))
                tag = f"t {chosen[i][0]:+.2f} s   h {chosen[i][1]:.2f} m"
            else:
                d.rectangle((x, y, x + CW, y + CH), fill=(236, 238, 240)); tag = f"t {t:+.1f} s   at rest (flight over)"
                d.text((x + 14, y + CH // 2 - 10), "ball already at rest", font=F(18), fill=MUTED)
            d.rectangle((x, y + CH - 26, x + CW, y + CH), fill=(255, 255, 255)); d.text((x + 8, y + CH - 23), tag, font=F(16), fill=INK)
        y += CH + 14
    y += 18
# height charts: small multiples, one per club, shared axes
d.text((PAD, y), "Height over the ground after pitching (metres), from the same filmed shots", font=F(24, True), fill=INK); y += 44
clubs = [("driver", "Driver"), ("iron7", "7 iron (pitched in rough)"), ("pw", "Pitching wedge"), ("lw", "Lob wedge")]
gw = (W - 2 * PAD - 3 * 36) // 4; gh = chart_h - 90; tmax, hmax = 2.0, 2.2
for i, (shot, name) in enumerate(clubs):
    x0 = PAD + i * (gw + 36) + 34; y0 = y + 30; x1 = x0 + gw - 34; y1 = y0 + gh
    d.text((x0, y), name, font=F(18, True), fill=INK)
    for hv in (0, 0.5, 1.0, 1.5, 2.0):
        yy = y1 - hv / hmax * gh; d.line((x0, yy, x1, yy), fill=GRID, width=1); d.text((x0 - 32, yy - 9), f"{hv:.1f}", font=F(14), fill=MUTED)
    for tv in (0, 0.5, 1.0, 1.5, 2.0):
        xx = x0 + tv / tmax * (x1 - x0); d.text((xx - 8, y1 + 6), f"{tv:g}", font=F(14), fill=MUTED)
    d.text((x1 - 150, y1 + 26), "seconds after pitching", font=F(14), fill=MUTED)
    for which, col, wd in (("before", OLD, 3), ("after", NEW, 3)):
        pts = [(x0 + t / tmax * (x1 - x0), y1 - min(h, hmax) / hmax * gh) for t, h in H[which].get(shot, []) if 0 <= t <= tmax]
        if len(pts) > 1: d.line(pts, fill=col, width=wd, joint="curve")
        if pts:
            peak = max((h for t, h in H[which].get(shot, []) if t >= 0.05), default=0)
            lx = x1 - 190; ly = y0 + (4 if which == "before" else 26)
            d.rectangle((lx, ly + 4, lx + 14, ly + 14), fill=col); d.text((lx + 20, ly), f"{'Before' if which == 'before' else 'After'}: highest hop {peak:.2f} m", font=F(14), fill=INK)
img.save(out, quality=90); print(out, img.size)
