import sys
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image
import fl
tag = sys.argv[1] if len(sys.argv) > 1 else 'b3u'
pl = np.asarray(Image.open(fl.PLATES/'female_head_detail.jpg').convert('RGB')).astype(float)
r = Image.open(fl.W/f'renders/{tag}_front.png').convert('RGBA'); ra = np.asarray(r).astype(float)
x0,y0 = 85,55
pts = {'forehead':(259,100),'forehead_hi':(285,92),'forehead_lo':(259,124),'cheekL':(228,190),'cheekR':(290,190),'chin':(259,236),'nose_tip':(259,193),'temple':(215,140),'jaw_side':(232,222)}
print('region        plate rgb          model rgb         ratio')
rat=[]
for k,(x,y) in pts.items():
    p = pl[y-3:y+4, x-3:x+4].reshape(-1,3).mean(0)
    X=int((x-x0)*3); Y=int((y-y0)*3); m = ra[Y-6:Y+7, X-6:X+7].reshape(-1,4); m = m[m[:,3]>200][:,:3].mean(0)
    print(f'{k:12s} {tuple(int(v) for v in p)}  {tuple(int(v) for v in m)}  {tuple(round(float(a/b),3) for a,b in zip(p,m))}')
    if k in ('forehead','forehead_hi','forehead_lo','cheekL','cheekR','chin','nose_tip'): rat.append(p/m)
print('mean ratio', np.round(np.mean(rat,axis=0),3))
