import json, sys
from PIL import Image, ImageDraw
d = json.load(open('fc.json'))
S = 5.0
allp = [p for k in d for p in d[k]['co']]
xs = [p[0] for p in allp]; ys = [p[1] for p in allp]
x0, x1, y0, y1 = min(xs) - 5, max(xs) + 5, min(ys) - 5, max(ys) + 5
W, H = int((x1 - x0) * S), int((y1 - y0) * S)
im = Image.new('RGB', (W, H), (20, 20, 20)); dr = ImageDraw.Draw(im)
def P(p): return ((p[0] - x0) * S, H - (p[1] - y0) * S)
cols = {'FAIRWAY': (60, 120, 60), 'FAIRWAY_FIRSTCUT': (160, 200, 60), 'TEE_BOX': (90, 90, 200), 'GREEN': (40, 220, 120), 'GREEN_APRON': (100, 170, 100), 'BUNKER_01': (220, 200, 120), 'BUNKER_02': (220, 200, 120)}
for k in ('FAIRWAY', 'FAIRWAY_FIRSTCUT', 'GREEN_APRON', 'GREEN', 'TEE_BOX', 'BUNKER_01', 'BUNKER_02'):
    co = d[k]['co']
    for poly in d[k]['polys']:
        pts = [P(co[i]) for i in poly]
        dr.polygon(pts, fill=cols[k] if k != 'FAIRWAY_FIRSTCUT' else None, outline=(0, 0, 0) if k != 'FAIRWAY_FIRSTCUT' else (255, 255, 0))
bad = [641, 640, 639, 638, 343, 306, 616, 477]
co = d['FAIRWAY_FIRSTCUT']['co']
for i in bad:
    pts = [P(co[j]) for j in d['FAIRWAY_FIRSTCUT']['polys'][i]]
    dr.polygon(pts, fill=(255, 0, 0, 120), outline=(255, 255, 255))
im.save(sys.argv[1] if len(sys.argv) > 1 else 'fc_plan.png'); print(im.size)
