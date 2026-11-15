#!/usr/bin/env python3
"""tennis_proof.py: the Phase 1 tennis proof sheet from film/classic and film/flat (ZTennisFlightFilm):
ball paths from the real game, side on, old ball above new on one scale, then game frames at the top of the flight."""
import csv, glob, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
OLD, NEW = "#eb6834", "#2a78d6"     # validated: dataviz validate_palette.js, light surface
def font(size, bold=False):
    try: return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size, index=1 if bold else 0)
    except Exception: return ImageFont.load_default()

def arcs(mode):
    shots = {}
    for r in csv.DictReader(open(f"{HERE}/film/{mode}/arcs.csv")):
        shots.setdefault((int(r["shot"]), int(r["byPlayer"])), []).append((float(r["z"]), float(r["y"])))
    out = []
    for (shot, by), pts in shots.items():
        if len(pts) < 20: continue
        span = abs(pts[-1][0] - pts[0][0])
        if span < 14: continue                      # a rally ball that crossed the court (serves start high and are left out below)
        if pts[0][1] > 2.2: continue                # serves
        out.append((by, pts))
    return out

W, PAD = 1600, 36
def panel(draw, top, title, colour, shots, height=250):
    x0, x1, y0, y1 = PAD + 60, W - PAD - 20, top + 34, top + height
    X = lambda z: x0 + (z + 13) / 26 * (x1 - x0)
    Y = lambda h: y1 - h / 4.5 * (y1 - y0)
    draw.text((PAD, top), title, font=font(22, True), fill=INK)
    for h in (0, 1, 2, 3, 4):
        draw.line([(x0, Y(h)), (x1, Y(h))], fill=GRID, width=1)
        draw.text((x0 - 44, Y(h) - 9), f"{h} m", font=font(15), fill=INK2)
    draw.line([(X(0), Y(0)), (X(0), Y(.97))], fill=INK2, width=3)                      # the net
    draw.text((X(0) + 6, Y(.97) - 18), "net", font=font(14), fill=INK2)
    for z in (-11.885, 11.885): draw.line([(X(z), Y(0) - 5), (X(z), Y(0) + 5)], fill=INK2, width=2)
    draw.text((X(-11.885) - 28, Y(0) + 8), "baseline", font=font(13), fill=INK2); draw.text((X(11.885) - 28, Y(0) + 8), "baseline", font=font(13), fill=INK2)
    dash = 10
    for xx in range(int(x0), int(x1), dash * 2): draw.line([(xx, Y(1.75)), (xx + dash, Y(1.75))], fill="#b9b8b2", width=1)
    draw.text((x1 - 150, Y(1.75) - 18), "head height 1.75 m", font=font(13), fill=INK2)
    peaks = []
    for by, pts in shots:
        draw.line([(X(z), Y(min(4.5, h))) for z, h in pts], fill=colour, width=2)
        peaks.append(max(h for _, h in pts))
    peaks.sort()
    if peaks:
        med = peaks[len(peaks) // 2]
        draw.text((x0 + 8, y0 + 4), f"{len(peaks)} rally balls  ·  typical top of flight {med:.1f} m  ·  highest {peaks[-1]:.1f} m", font=font(17), fill=INK)
    return top + height + 30

def frames(mode, who, n):
    files = sorted(glob.glob(f"{HERE}/film/{mode}/{who}_*.jpg"))
    return files[:n]

old, new = arcs("classic"), arcs("flat")
fw = (W - 2 * PAD - 20) // 2; fh = fw * 9 // 16
rows = 3
H = 70 + 2 * 280 + 50 + rows * (fh + 44) + 30
img = Image.new("RGB", (W, H), SURF); d = ImageDraw.Draw(img)
d.text((PAD, 20), "Tennis ball flight, before and after (real game, self-play, gameplay camera)", font=font(26, True), fill=INK)
y = 70
y = panel(d, y, "Before: the 10-26 ball", OLD, old)
y = panel(d, y, "After: the 11-11 ball", NEW, new)
d.text((PAD, y), "The frame at the top of each ball's flight", font=font(22, True), fill=INK); y += 40
pairs = list(zip(frames("classic", "rival", 2) + frames("classic", "player", 1), frames("flat", "rival", 2) + frames("flat", "player", 1)))
for a, b in pairs[:rows]:
    for k, (f, colour, tag) in enumerate(((a, OLD, "before"), (b, NEW, "after"))):
        im = Image.open(f).convert("RGB").resize((fw, fh), Image.LANCZOS)
        x = PAD + k * (fw + 20); img.paste(im, (x, y))
        who = "rival's ball" if "rival_" in os.path.basename(f) else "your ball"
        top = os.path.basename(f).split("apex_")[1].replace("m.jpg", "")
        d.rectangle([x, y + fh, x + 10, y + fh + 30], fill=colour)
        d.text((x + 18, y + fh + 6), f"{tag}: {who} at its highest, {top} m", font=font(17), fill=INK)
    y += fh + 44
out = f"{HERE}/proof_tennis_before_after.jpg"
img.save(out, quality=90); print(out, img.size, len(old), len(new))
