import sys, json, numpy as np
sys.path.insert(0,'hand'); sys.path.insert(0,'../male-micro1e')
import roles, run
P=json.load(open('hand/params_m1f_final.json'))
R=roles.roles(P)   # (side, mf_index) -> role (right side has side=+1)
def sets(side):
    th=[fi for (s,fi),r in R.items() if s==side and r.startswith('thumb') and not r.startswith('thumb m0')]
    f0=[fi for (s,fi),r in R.items() if s==side and r.startswith('finger0')]
    f1=[fi for (s,fi),r in R.items() if s==side and r.startswith('finger1')]
    palm=[fi for (s,fi),r in R.items() if s==side and r.startswith('palm')]
    return np.array(th),np.array(f0),np.array(f1),np.array(palm)
def mind(A,B):
    d=np.linalg.norm(A[:,None,:]-B[None,:,:],axis=2); return d.min()*1000, np.unravel_index(d.argmin(),d.shape)
def report(tag):
    if tag=='base': mf=run.MF0
    else:
        V=np.load(f'data/it/{tag}_cur.npy')
        mf=np.zeros_like(run.MF0)
        ok=run.IDX>=0
        mf[ok]=V[run.IDX[ok]]
    out={}
    for side in (+1,-1):
        th,f0,f1,palm=sets(side)
        # skip palm verts near the thumb root: only palm verts farther than 3cm from loop? report thumb<->finger0 and thumb tip rows <-> palm
        out[side]=dict(thumb_index_mm=round(mind(mf[th],mf[f0])[0],2),thumb_mid_mm=round(mind(mf[th],mf[f1])[0],2))
    return out
if __name__=='__main__':
    for tag in sys.argv[1:]: print(tag,report(tag))
