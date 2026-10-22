"""Calibration of the LOOK_FILES window-sd statistic against the target stills (needle.jpg / split.jpg): windowed luminance sd of grass crops
at native still pixels. Prints, per crop, the median / p10 / p90 of the sd of non-overlapping w x w windows (w = 8, 16, 32, 64)."""
import sys, os
import numpy as np, bpy
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
def load(p):
    img = bpy.data.images.load(p)
    w, h = img.size
    a = np.empty(w*h*4, np.float32); img.pixels.foreach_get(a)
    a = a.reshape(h, w, 4)[::-1]       # row 0 = top
    bpy.data.images.remove(img)
    return a[..., :3]
def lum(a): return a[...,0]*.2126 + a[...,1]*.7152 + a[...,2]*.0722
def wsd(l, w):
    H, W = l.shape; h2, w2 = H//w, W//w
    if h2 == 0 or w2 == 0: return np.array([np.nan])
    return l[:h2*w, :w2*w].reshape(h2, w, w2, w).std(axis=(1,3)).ravel()
crops = {   # file: {name: (x0,y0,x1,y1) in 1280x720 coordinates}
 "split.jpg": {"fairway_strip": (860,230,900,330), "upper_green": (655,110,790,150), "lower_green": (600,570,700,640),
               "fairway_mid": (800,260,860,330), "lower_fairway": (730,470,820,540)},
 "needle.jpg": {"mid_green": (770,265,930,310), "top_green": (880,62,1060,95), "left_fairway": (230,200,330,260)},
 "crater.jpg": {},
}
for f, cs in crops.items():
    a = load(f"{R}/ArtDir/environments/refs/{f}")
    H, W = a.shape[:2]
    sx, sy = W/1280.0, H/720.0
    print(f, "size", W, H)
    l = lum(a)
    for n, (x0,y0,x1,y1) in cs.items():
        c = l[int(y0*sy):int(y1*sy), int(x0*sx):int(x1*sx)]
        rgb = a[int(y0*sy):int(y1*sy), int(x0*sx):int(x1*sx)].reshape(-1,3).mean(0)
        row = []
        for w in (8, 16, 32, 64):
            s = wsd(c, w)
            row.append(f"w{w}: med {np.nanmedian(s):.4f} p10 {np.nanpercentile(s,10):.4f} p90 {np.nanpercentile(s,90):.4f} ge.03 {np.nanmean(s>=0.03):.0%}")
        print(f"  {n:14s} crop {c.shape[1]}x{c.shape[0]} px mean rgb {np.round(rgb*255).astype(int).tolist()} | " + " | ".join(row))
