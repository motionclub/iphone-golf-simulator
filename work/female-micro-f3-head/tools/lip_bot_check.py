import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import numpy as np, lips3
raw = json.load(open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/data/lip_plate_raw.json'))
p = lips3.P0
print(' x(mm)  plate_bot  F3_bot  diff(mm) | plate_thick F3_thick | top plate/F3 | seam plate/F3')
rows = []
for r in raw:
    x = r['x']
    if abs(x) > 0.0285 or abs(x) < 0.0009: continue
    sz = lips3.seam_z(x, p); bot = sz - lips3.lo_thick(x, p); top = lips3.top_z(x, p)
    rows.append((x, r['bot'], bot, r['top'], top, r['seam'], sz))
for x, pb, fb, pt, ft, ps, fs in rows[::2]:
    print('%+6.1f  %.4f  %.4f  %+5.1f  |  %5.1f  %5.1f | %.4f/%.4f | %.4f/%.4f' % (x * 1000, pb, fb, (fb - pb) * 1000, (ps - pb) * 1000, (fs - fb) * 1000, pt, ft, ps, fs))
core = [(fb - pb) * 1000 for x, pb, fb, *_ in rows if abs(x) <= 0.0145]
mid = [(fb - pb) * 1000 for x, pb, fb, *_ in rows if 0.0145 < abs(x) <= 0.0285]
print('bottom border diff |x|<=14.5 mm: mean %+.2f rms %.2f max %.2f ; 14.5-28.5 mm: mean %+.2f rms %.2f max %.2f' % (np.mean(core), np.sqrt(np.mean(np.square(core))), np.abs(core).max(), np.mean(mid), np.sqrt(np.mean(np.square(mid))), np.abs(mid).max()))
