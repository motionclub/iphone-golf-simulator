import sys, math, importlib.util
import numpy as np
REPO="/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec=importlib.util.spec_from_file_location("d",REPO+"/blender/scripts/hole10_design.py"); D=importlib.util.module_from_spec(spec); spec.loader.exec_module(D)
YD=0.9144
shore=np.array([(x*YD,d*YD) for x,d in D.SHORE]); cl=[(x*YD,d*YD) for x,d in D.CENTERLINE]
W=D.SCENERY["wall_ring"]; cx,cy=W["cx"]*YD,W["cd"]*YD
def seg_d(P,a,b):
    a=np.array(a);b=np.array(b);ab=b-a
    t=np.clip(((P[:,0]-a[0])*ab[0]+(P[:,1]-a[1])*ab[1])/max(ab@ab,1e-9),0,1)
    return np.hypot(P[:,0]-(a[0]+t*ab[0]),P[:,1]-(a[1]+t*ab[1]))
def dshore(P):
    out=np.full(len(P),1e9); a=shore; b=np.roll(shore,-1,axis=0)
    for i in range(len(a)): out=np.minimum(out,seg_d(P,a[i],b[i]))
    return out
def inside(P):
    x,y=P[:,0],P[:,1]; ins=np.zeros(len(P),bool); n=len(shore)
    for i in range(n):
        x1,y1=shore[i]; x2,y2=shore[(i+1)%n]
        c=((y1>y)!=(y2>y))&(x<(x2-x1)*(y-y1)/(y2-y1+1e-12)+x1); ins^=c
    return ins
R=260; g=np.arange(-R,R,2.0)
X,Y=np.meshgrid(cx+g,cy+g); P=np.stack([X.ravel(),Y.ravel()],1)
rho=np.hypot(P[:,0]-cx,P[:,1]-cy)
floor=rho<214*YD-6
sd=dshore(P); land=inside(P)
line=np.min([seg_d(P,cl[i],cl[i+1]) for i in range(len(cl)-1)],axis=0)
chord=seg_d(P,cl[0],cl[3])
print("floor area yd2 (rho<208yd):", floor.sum()*4/YD**2)
for sg,lg,cg in ((24,38,25),(22,30,22),(20,26,20),(18,22,16)):
    ok=floor&(~land)&(sd>=sg*YD)&(line>=lg*YD)&(chord>=cg*YD)
    print(f"shore>={sg} line>={lg} chord>={cg}: crust-capable area {ok.sum()*4/YD**2:.0f} yd2 = {ok.sum()/floor.sum():.0%} of the floor")
sg,lg,cg=24,38,25
ok=floor&(~land)&(sd>=sg*YD)&(line>=lg*YD)&(chord>=cg*YD)
img=np.zeros((len(g),len(g),3),np.uint8); img[floor.reshape(len(g),len(g))]=(200,40,0)
img[ok.reshape(len(g),len(g))]=(30,30,40); img[land.reshape(len(g),len(g))]=(0,200,0)
from array import array
open("/tmp/mask_probe.ppm","wb").write(b"P6 %d %d 255\n"%(len(g),len(g))+img[::-1].tobytes())
