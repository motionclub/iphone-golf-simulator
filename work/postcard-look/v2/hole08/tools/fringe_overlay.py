"""fringe_overlay: top-down render + the fringe tuft positions as coloured dots (python3, Pillow). usage: python3 fringe_overlay.py DIR  (DIR has top_all.png, top_all.json, fringe_pts.json from fringe_views.py)"""
import json, sys
from PIL import Image, ImageDraw
d = sys.argv[1]
im = Image.open(d + "/top_all.png").convert("RGB")
meta = json.load(open(d + "/top_all.json"))
pts = json.load(open(d + "/fringe_pts.json"))
W, H = im.size
scale = max(W, H) / meta["span"]
dr = ImageDraw.Draw(im)
col = {"PLANT_TUFT_D": (255, 0, 0), "PLANT_TUFT_E": (255, 160, 0), "PLANT_TUFT_S": (0, 200, 255)}
for x, y, k in pts:
    px, py = W / 2 + (x - meta["cx"]) * scale, H / 2 - (y - meta["cy"]) * scale
    dr.ellipse((px - 2, py - 2, px + 2, py + 2), fill=col.get(k, (255, 255, 255)))
im.save(d + "/top_overlay.png")
print("FRINGE_OVERLAY", len(pts), "tufts")
