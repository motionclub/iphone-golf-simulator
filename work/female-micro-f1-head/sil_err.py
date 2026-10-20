"""per-row silhouette error of the model render vs the plate (front and profile).  python3.13 sil_err.py <tag>"""
import sys
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np, json
from PIL import Image
import fl
tag = sys.argv[1] if len(sys.argv) > 1 else 'b3u'
sil = json.load(open(fl.W/'data/sil.json'))
def mask(view):
    r = Image.open(fl.W/f'renders/{tag}_{view}.png').convert('RGBA'); a = np.asarray(r)[...,3] > 128
    return a
for view, key, box in (('front','front',fl.PANELS['front']['box']), ('left','left',fl.PANELS['left']['box'])):
    m = mask(view); x0,y0,x1,y1 = box
    print(view)
    worst = []
    for row in range(72, 252, 6):
        yy = int((row - y0 + 0.5) * 3)
        xs = np.where(m[yy])[0]
        if len(xs) == 0: continue
        mc0, mc1 = xs.min()/3 + x0, (xs.max()+1)/3 + x0
        pc = sil[key][str(row)]
        dl = mc0 - pc[0]; dr = mc1 - (pc[1]+1)
        worst.append((row, round(dl,1), round(dr,1)))
    print(' row  dL(px)  dR(px)  (model-plate; + = model edge is further right)')
    for w in worst: print('  ', w)
