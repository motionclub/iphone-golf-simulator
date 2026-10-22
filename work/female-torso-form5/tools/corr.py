"""band-pass (DoG) shading correlation, plate vs plate-lit render, inside ROI boxes.  python3 tools/corr.py tag=coords.npy ..."""
import sys; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/tools')
from platelit import *
from PIL import Image
ROIS={'bust_front':('front',(-0.125,0.125),(1.15,1.32)),'chest_all_front':('front',(-0.125,0.125),(1.10,1.34)),
      'glute_back':('back',(-0.16,0.16),(0.84,1.00)),'pelvis_back':('back',(-0.16,0.16),(0.80,1.02))}
def roi_mask(view,xr,zr):
    m=np.zeros((720,1280),bool); cx=FRONT_CX if view=='front' else BACK_CX
    c0,c1=sorted([cx+xr[0]/S,cx+xr[1]/S]); r0=SOLE-zr[1]/S; r1=SOLE-zr[0]/S
    m[int(r0):int(r1),int(c0):int(c1)]=True; return m
def corr(tag,s1=1.6,s2=9.0):
    out={}
    for name,(view,xr,zr) in ROIS.items():
        a=dog(BALD,s1,s2); b=dog(np.asarray(Image.open(W/f'proof/scratch/pl_{tag}_{view}.png').convert('L')).astype(float),s1,s2)
        m=roi_mask(view,xr,zr); out[name]=float(np.corrcoef(a[m],b[m])[0,1])
    return out
if __name__=='__main__':
    import json
    res={}
    for a in sys.argv[1:]:
        tag,npy=a.split('='); render(str(W/npy),tag); res[tag]=corr(tag)
    for tag,r in res.items(): print(f'{tag:12s}',' '.join(f'{k} {v:+.3f}' for k,v in r.items()))
    json.dump(res,open(W/'proof/scratch/corr_last.json','w'),indent=1)
