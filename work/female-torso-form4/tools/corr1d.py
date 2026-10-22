"""1-D luminance profile correlation along mound / lobe centre columns (plate vs plate-lit).  python3 tools/corr1d.py tag ..."""
import sys,json; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form4/tools')
from platelit import *
from PIL import Image
def prof(img,u,zs,half=2):
    rows=SOLE-zs/S; return np.array([img[int(round(r)),int(round(u))-half:int(round(u))+half+1].mean() for r in rows])
SPECS={'dome_L':('front',-0.0755,(1.14,1.32)),'dome_R':('front',0.0755,(1.14,1.32)),'lobe_L':('back',-0.080,(0.84,1.02)),'lobe_R':('back',0.080,(0.84,1.02))}
def one(tag):
    bald=gblur(BALD,1.5); out={}
    for name,(view,x,(z0,z1)) in SPECS.items():
        cx=FRONT_CX if view=='front' else BACK_CX; sg=1 if view=='front' else -1
        u=cx+sg*x/S; zs=np.arange(z0,z1,0.004)
        a=prof(bald,u,zs); img=gblur(np.asarray(Image.open(W/f'proof/scratch/pl_{tag}_{view}.png').convert('L')).astype(float),1.5); b=prof(img,u,zs)
        # remove per-profile linear trend (global lighting gradients) before correlating
        t=np.arange(len(zs)); 
        ra=a-np.polyval(np.polyfit(t,a,1),t); rb=b-np.polyval(np.polyfit(t,b,1),t)
        out[name]=dict(r_raw=float(np.corrcoef(a,b)[0,1]),r_detrended=float(np.corrcoef(ra,rb)[0,1]),peak_z_plate=float(zs[np.argmax(a)]),peak_z_model=float(zs[np.argmax(b)]))
    return out
if __name__=='__main__':
    res={t:one(t) for t in sys.argv[1:]}
    for t,r in res.items(): print(f'{t:8s}',' | '.join(f"{k} r={v['r_raw']:+.2f}/{v['r_detrended']:+.2f} pk {v['peak_z_model']:.3f}({v['peak_z_plate']:.3f})" for k,v in r.items()))
    json.dump(res,open(W/'proof/scratch/corr1d_last.json','w'),indent=1)
