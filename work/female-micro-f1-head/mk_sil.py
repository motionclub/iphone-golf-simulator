"""plate silhouette tables -> data/sil.json  (rows 70..252)"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np
import fl
a = fl.load_plate(); fg = fl.fg_mask(a)
def ext(r, x0, x1):
    xs = np.where(fg[r, x0:x1])[0] + x0
    return (int(xs.min()), int(xs.max())) if len(xs) else None
out = {'front': {}, 'left': {}, 'right': {}}
for r in range(66, 253):
    out['front'][r] = ext(r, 85, 430); out['left'][r] = ext(r, 440, 800); out['right'][r] = ext(r, 830, 1195)
json.dump(out, open(fl.W / 'data/sil.json', 'w'))
# print summary every 8 rows
for r in range(70, 253, 8):
    print(r, 'F', out['front'][r], 'L', out['left'][r], 'R', out['right'][r])
