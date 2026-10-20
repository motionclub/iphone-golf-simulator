import numpy as np
from PIL import Image
import lockcam as L
M='../male-silhouette/'
ROIS={ # view: [(name, (x0,y0,x1,y1))]
 'bald_front':[('L',(100,300,205,395)),('R',(500,300,605,395))],
 'bald_back':[('L',(670,300,775,395)),('R',(1060,300,1165,395))],
 'sheet_front':[('L',(45,160,125,225)),('R',(250,160,330,225))],
 'sheet_back':[('L',(355,160,435,225)),('R',(545,160,625,225))],
}
_plate={}
def plate(v):
    if v not in _plate: _plate[v]=np.array(Image.open(M+v+'_target.png').convert('L'))>127
    return _plate[v]
def xor_report(V,T,arm_tris=None,verbose=False):
    res={}
    for v,rois in ROIS.items():
        for nm,(x0,y0,x1,y1) in rois:
            m=L.raster(V,T,v,sel=arm_tris,roi=(x0,y0,x1,y1),ss=2)
            p=plate(v)[y0:y1,x0:x1]
            res[(v,nm)]=(int((m^p).sum()),int((m&p).sum()),int(p.sum()),int(m.sum()))
    tot=sum(r[0] for r in res.values())
    if verbose:
        for k,r in res.items(): print(k,'xor',r[0],'both',r[1],'plate',r[2],'model',r[3])
    return tot,res
if __name__=='__main__':
    D=np.load('data/mesh_start.npz'); V,T=D['V'],D['T']
    # arm triangles only (speed): vertices with |x|>0.2 and z in 0.78..1.4
    arm=(np.abs(V[:,0])>0.2)&(V[:,2]>0.78)&(V[:,2]<1.40)
    sel=arm[T].all(1)
    tot,res=xor_report(V,T,sel,True); print('TOTAL',tot)
