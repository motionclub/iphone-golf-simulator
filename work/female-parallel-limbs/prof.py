"""python3 prof.py prefix out.json : per-row |dx| interval edges (px) of plate polygons vs model silhouette, front/back averaged."""
import sys, json, numpy as np
sys.path.insert(0,'../../Tools/HeroBase')
from plate_profiles import FEMALE as F
from PIL import Image, ImageDraw
def poly(pts):
    im=Image.new('L',(1280,720),0); ImageDraw.Draw(im).polygon(pts,fill=255); return np.array(im)>0
def runs(row):
    d=np.diff(np.concatenate([[0],row.astype(np.int8),[0]])); s=np.where(d==1)[0]; e=np.where(d==-1)[0]
    return list(zip(s.tolist(),e.tolist()))   # [s,e)
def rowprof(mask,cx,y):
    r=runs(mask[y]); 
    return [(a-cx,b-cx) for a,b in r]
pre=sys.argv[1]; out={}
plate={'front':(poly(F['front_outline']),440),'back':(poly(F['back_outline']),847)}
for y in list(range(160,430,10))+list(range(430,680,10)):
    for view,(P,cx) in plate.items():
        M=np.array(Image.open(f'{pre}_{view}.png'))[:,:,3]>127
        print(y,view,'plate',rowprof(P,cx,y),'model',rowprof(M,cx,y))
