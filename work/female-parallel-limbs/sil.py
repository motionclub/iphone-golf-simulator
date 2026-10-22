"""python3 sil.py prefix out_png [json] : per-zone silhouette XOR vs plate polygons."""
import sys, json, numpy as np
sys.path.insert(0,'../../Tools/HeroBase')
from plate_profiles import FEMALE as F
from PIL import Image, ImageDraw
pre=sys.argv[1]; out=sys.argv[2]
def poly(pts):
    im=Image.new('L',(1280,720),0); ImageDraw.Draw(im).polygon(pts,fill=255); return np.array(im)>0
res={}; panels=[]
yy,xx=np.mgrid[0:720,0:1280]
for view,key,cx in (('front','front_outline',440),('back','back_outline',847)):
    P=poly(F[key]); M=np.array(Image.open(f'{pre}_{view}.png'))[:,:,3]>127
    dx=np.abs(xx-cx)
    # mirror-free zones (px): legs = below hip line; arms = outboard of torso, above hip; hands y>=340
    legs=(yy>=372)&(dx<110)
    arms=(yy>=165)&(yy<372)&(dx>=58)
    hands=(yy>=372)&(yy<425)&(dx>=78)
    zones={'legs':legs&~hands,'feet':(yy>=640)&(dx<110),'arms':arms,'hands':(yy>=340)&(yy<425)&(dx>=78)}
    for n,z in zones.items():
        u=((P|M)&z).sum(); x=((P^M)&z).sum()
        res[f'{view}_{n}']=round(float(x/u*100),2) if u else None
    res[f'{view}_all_xor_pct']=round(float((P^M).sum()/(P|M).sum()*100),2)
    rgb=np.zeros((720,1280,3),np.uint8)
    rgb[P&M]=(90,200,90); rgb[P&~M]=(230,60,60); rgb[~P&M]=(60,120,255)
    panels.append(Image.fromarray(rgb).crop((cx-170,0,cx+170,720)))
W=Image.new('RGB',(680,720)); W.paste(panels[0],(0,0)); W.paste(panels[1],(340,0)); W.save(out)
print(json.dumps(res,indent=1))
if len(sys.argv)>3: json.dump(res,open(sys.argv[3],'w'),indent=1)
