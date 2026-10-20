"""Achievable silhouette floor per limb zone: how well a single mirror-symmetric silhouette can match the four plate silhouettes
(front-L, front-R, back-L, back-R), measured in the same zones as sil.py. Floor = error of the pixelwise-best symmetric mask."""
import sys, json, numpy as np
sys.path.insert(0,'../../Tools/HeroBase')
from plate_profiles import FEMALE as F
from PIL import Image, ImageDraw
def poly(pts):
    im=Image.new('L',(1280,720),0); ImageDraw.Draw(im).polygon(pts,fill=255); return np.array(im)>0
PF=poly(F['front_outline']); PB=poly(F['back_outline'])
H,Wd=720,1280
yy,xx=np.mgrid[0:H,0:Wd]
# half-body masks in (|dx|) space: columns 0..139
def half(P,cx,sd):
    cols=np.clip(np.round(cx+sd*np.arange(0,140)).astype(int),0,Wd-1)
    return P[:,cols]
views={'frontL':half(PF,440,-1),'frontR':half(PF,440,1),'backL':half(PB,847,-1),'backR':half(PB,847,1)}
dx=np.arange(0,140)[None,:].repeat(H,0); y=yy[:,:140]
zones={'legs':(y>=372)&(dx<110)&~((y>=372)&(y<425)&(dx>=78)),'feet':(y>=640)&(dx<110),'arms':(y>=165)&(y<372)&(dx>=58),'hands':(y>=340)&(y<425)&(dx>=78)}
ms=np.stack(list(views.values()))       # 4,H,140
vote=ms.mean(0)                          # 0..1 per pixel
best=vote>=0.5                           # majority mask (min total disagreement)
res={}
for zn,z in zones.items():
    errs=[]
    for k,m in views.items():
        u=((m|best)&z).sum(); errs.append(((m^best)&z).sum()/u*100 if u else np.nan)
    res[zn]={'floor_mean_pct':round(float(np.nanmean(errs)),2),'per_view':dict(zip(views.keys(),[round(float(e),2) for e in errs]))}
print(json.dumps(res,indent=1)); json.dump(res,open('data/silhouette_floor.json','w'),indent=1)
