"""Front/back silhouette metrics (project frozen framing) + torso visible-edge half-width residuals."""
import numpy as np, sys, json
sys.path.insert(0,'.')
from sil import *
from PIL import Image
d=np.load('data/start.npz'); tri=d['tri']
masks={v:np.asarray(Image.open(f'../../ArtDir/hero/base_lock/proof/masks/F_{v}_target.png').convert('L'))>127 for v in ('front','back')}
def runs(row):
    r=[];s=None
    for x,v in enumerate(row):
        if v and s is None: s=x
        if (not v) and s is not None: r.append((s,x-1)); s=None
    if s is not None: r.append((s,len(row)-1))
    return r
def evaluate(co,label,verbose=True):
    out={}
    v0=int(679-1.37/S); v1=int(679-0.795/S)
    for view in ('front','back'):
        M=raster(project(co,view),tri)
        out[view]={'full':xor_iou(M,masks[view]),'band':xor_iou(M,masks[view],(v0,v1))}
        # visible torso edge residual: rows where plate has 3 runs (arm gaps) z .84-1.15
        res=[]
        cx=440 if view=='front' else 847
        for z in np.arange(0.84,1.16,0.02):
            y=int(round(679-z/S))
            pr=[r for r in runs(masks[view][y]) if r[0]<=cx<=r[1]]
            mr=[r for r in runs(M[y]) if r[0]<=cx<=r[1]]
            if pr and mr:
                pl=(pr[0][1]-pr[0][0]+1)*S/2; ml=(mr[0][1]-mr[0][0]+1)*S/2
                pc=((pr[0][0]+pr[0][1]+1)/2-cx)*S; mc=((mr[0][0]+mr[0][1]+1)/2-cx)*S
                res.append((z,pl,ml,pc,mc))
        res=np.array(res)
        out[view]['halfwidth_err_mm_mean']=float(np.abs(res[:,2]-res[:,1]).mean()*1000)
        out[view]['halfwidth_err_mm_max']=float(np.abs(res[:,2]-res[:,1]).max()*1000)
        out[view]['plate_center_offset_mm']=float(res[:,3].mean()*1000)
    if verbose:
        print(label, {v:{k:round(x,4) for k,x in out[v].items()} for v in out})
    return out
if __name__=='__main__':
    evaluate(d['co'],'before')
    for p in sys.argv[1:]: evaluate(np.load(p),p)
