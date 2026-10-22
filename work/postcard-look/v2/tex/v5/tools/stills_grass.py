"""Grass statistics of the target stills (needle / split / crater) at native 1280x720: whole-crop luminance sd and the windowed sd at 8/16/32 px
for hand-picked grass crops (same crops as v2/gates/tools/still_calib.py plus crater crops), and the sd of the 'lower 60 %' analogue.
Run: /Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 stills_grass.py"""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import imgnp
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
crops = {
 "split.jpg": {"fairway_strip": (860,230,900,330), "upper_green": (655,110,790,150), "lower_green": (600,570,700,640), "lower_fairway": (730,470,820,540)},
 "needle.jpg": {"mid_green": (770,265,930,310), "top_green": (880,62,1060,95)},
 "crater.jpg": {"fairway_a": (380,330,470,370), "fairway_b": (300,380,380,420), "pillar_green": (810,350,990,420), "tee_pad": (140,470,300,520)},
}
out = []
for f, cs in crops.items():
    a = imgnp.load(f"{R}/ArtDir/environments/refs/{f}"); l = imgnp.lum(a)
    for n, (x0, y0, x1, y1) in cs.items():
        c = l[y0:y1, x0:x1]; rgb = a[y0:y1, x0:x1].reshape(-1, 3).mean(0)
        h, s, v = imgnp.hsv_of_mean(rgb)
        row = []
        for w in (8, 16, 32):
            sd = imgnp.wsd(c, w)
            row.append(f"w{w} med {np.nanmedian(sd):.4f} ge.03 {np.nanmean(sd >= .03):.0%}")
        out.append(f"{f:11s} {n:14s} {c.shape[1]}x{c.shape[0]} rgb {np.round(rgb*255).astype(int).tolist()} h{h:.0f} S{s:.2f} V{v:.2f} | whole-crop sd {c.std():.4f} ({c.std()*255:.1f}/255) | " + " | ".join(row))
print("\n".join(out))
