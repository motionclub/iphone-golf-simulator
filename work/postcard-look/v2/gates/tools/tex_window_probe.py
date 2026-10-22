"""AREA U probe: window sd of the live Look/ ground albedos at several GROUND footprints (metres) -> compare with the stills' w8 / w16 floors."""
import sys, os
import numpy as np, bpy
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
LOOK = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv and len(sys.argv) > sys.argv.index("--") + 1 else R + "/Unity/Assets/Resources/Course/Look"
TILE = {"Fairway_C": 10.0, "Green_C": 6.0, "Rough_C": 12.0, "Scrub_C": 12.0, "Sand_C": 6.0}
def load(p):
    img = bpy.data.images.load(p); w, h = img.size
    a = np.empty(w*h*4, np.float32); img.pixels.foreach_get(a); bpy.data.images.remove(img)
    return a.reshape(h, w, 4)
def lum(a): return a[...,0]*.2126 + a[...,1]*.7152 + a[...,2]*.0722
def wsd(l, win):
    H, W = l.shape; h2, w2 = H//win, W//win
    return l[:h2*win, :w2*win].reshape(h2, win, w2, win).std(axis=(1,3)).ravel()
for stem, tile in TILE.items():
    p = f"{LOOK}/{stem}.png"
    if not os.path.isfile(p): continue
    a = load(p); l = lum(a); n = l.shape[0]
    row = []
    for F in (0.4, 0.75, 1.2, 1.6, 2.4):
        win = max(4, int(round(F / tile * n)))
        s = wsd(l, win)
        row.append(f"F {F:.2f} m (win {win:3d} px, n {s.size:4d}): med {np.median(s):.4f} p10 {np.percentile(s,10):.4f} ge.03 {np.mean(s>=.03):.0%}")
    print(f"TEXPROBE {stem} {n}px tile {tile} m global sd {l.std():.4f} | " + " | ".join(row))
