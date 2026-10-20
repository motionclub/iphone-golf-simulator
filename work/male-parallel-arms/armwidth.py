import numpy as np, sys
from PIL import Image
import lockcam as L
D=np.load('data/mesh_start.npz'); V,T=D['V'],D['T']
M='../male-silhouette/'
# arm tris only to keep model arm mask separated from torso: use all tris but crop away torso columns via the slicing region
def widths(mask,p0,p1,stations):
    """slice mask pixels by planes perpendicular to the p0->p1 axis; return perpendicular extent at each station (px)"""
    ys,xs=np.nonzero(mask); P=np.stack([xs,ys],1).astype(float)
    ax=(p1-p0)/np.linalg.norm(p1-p0); nrm=np.array([-ax[1],ax[0]])
    t=(P-p0)@ax; s=(P-p0)@nrm
    out=[]
    # keep only pixels within a band around the axis (arm only)
    for a in stations:
        m=(np.abs(t-a)<1.5)&(np.abs(s)<30)
        out.append(s[m].max()-s[m].min() if m.sum()>3 else np.nan)
    return np.array(out)
views={'bald_front':('bald_front',[((290,230),(130,370)),((415,225),(575,365))]),
       'bald_back':('bald_back',[((870,225),(700,365)),((960,225),(1130,365))]),
       'sheet_front':('sheet_front',[((125,100),(70,205)),((245,100),(300,205))]),
       'sheet_back':('sheet_back',[((420,100),(370,205)),((545,100),(590,205))])}
for vn,(cam,arms) in views.items():
    plate=np.array(Image.open(M+vn+'_target.png').convert('L'))>127
    model=L.raster(V,T,cam)
    for ai,(a,b) in enumerate(arms):
        p0,p1=np.array(a,float),np.array(b,float)
        L_=np.linalg.norm(p1-p0); st=np.linspace(0.20*L_,0.85*L_,8)
        wp=widths(plate,p0,p1,st); wm=widths(model,p0,p1,st)
        print(vn,'arm',ai,'stations(px)',np.round(st).astype(int))
        print('   plate',np.round(wp,1)); print('   model',np.round(wm,1)); print('   diff ',np.round(wm-wp,1))
