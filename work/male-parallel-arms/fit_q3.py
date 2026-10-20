import numpy as np, sys, json
from PIL import Image
from rast import raster
D=np.load('data/mesh_start.npz'); V,T=D['V'],D['T']
S0=1/0.005822
panels={'q3FL':(30,370,340,680),'q3FR':(340,370,650,680),'q3BL':(650,370,960,680),'q3BR':(960,370,1270,680)}
arm=(np.abs(V[:,0])>0.215)&(V[:,2]>0.78)&(V[:,2]<1.40)
sel=~arm[T].any(1)
def fit(name,yaw_range):
    x0,y0,x1,y1=panels[name]
    pm=np.array(Image.open(f'data/plate_{name}_mask.png'))[y0:y1,x0:x1]>127
    H,W=pm.shape
    ys_,xs_=np.nonzero(pm); cx=xs_.mean()
    best=(-1,None)
    for yaw in yaw_range:
        for sc in (S0*0.985,S0,S0*1.015):
            ty=(672-y0)
            m0=raster(V,T,yaw,sc,W/2,ty,pm.shape,ss=1,sel=sel)
            zrow=(ty-np.arange(H))/sc
            rows=(zrow<0.75)|(zrow>1.43)
            pr=pm[rows]
            for dx in range(-60,61,2):
                for dy in range(-6,7,2):
                    # shift the model mask by (dx_total, dy)
                    shx=int(round(cx-W/2))+dx//2
                    m=np.roll(np.roll(m0,shx,1),dy,0)[rows]
                    iou=(m&pr).sum()/max((m|pr).sum(),1)
                    if iou>best[0]: best=(iou,(yaw,sc,W/2+shx,ty+dy))
    return best
if __name__=='__main__':
    name=sys.argv[1]; lo,hi,st=map(int,sys.argv[2:5])
    b=fit(name,range(lo,hi+1,st)); print(name,b)
