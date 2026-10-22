"""seam / crease metrics for the torso zone: dihedral angles between adjacent triangles, border displacement steps"""
import sys; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/tools')
from torso2 import *
_tri=TRI
_ek=np.concatenate([_tri[:,[0,1]],_tri[:,[1,2]],_tri[:,[2,0]]]); _ek.sort(axis=1)
_key=_ek[:,0].astype(np.int64)*N+_ek[:,1]; _tid=np.tile(np.arange(len(_tri)),3)
_o=np.argsort(_key,kind='stable'); _ks=_key[_o]; _ts=_tid[_o]
_same=np.where(_ks[1:]==_ks[:-1])[0]
PAIR_A=_ts[_same]; PAIR_B=_ts[_same+1]; PAIR_E=_ek[_o][_same]            # triangle pairs sharing an edge + the edge verts
ZPAIR=T[PAIR_E[:,0]]&T[PAIR_E[:,1]]
def fnorm(co):
    v0,v1,v2=co[_tri[:,0]],co[_tri[:,1]],co[_tri[:,2]]; n=np.cross(v1-v0,v2-v0); return n/np.maximum(np.linalg.norm(n,axis=1),1e-18)[:,None]
def dihedral(co):
    n=fnorm(co); c=(n[PAIR_A]*n[PAIR_B]).sum(1); return np.degrees(np.arccos(np.clip(c,-1,1)))
def stats(co,label=''):
    a=dihedral(co); az=a[ZPAIR]
    out={'edges':int(ZPAIR.sum()),'mean_deg':float(az.mean()),'p95_deg':float(np.percentile(az,95)),'p99_deg':float(np.percentile(az,99)),'max_deg':float(az.max()),'n_gt30':int((az>30).sum()),'n_gt40':int((az>40).sum())}
    return out
def border_steps(co):
    d=np.linalg.norm(co-CO0,axis=1)*1000
    e=(T[EA]&T[EB])&(BORDER[EA]^BORDER[EB]); st=np.abs(d[EA]-d[EB])[e]
    cls=np.where(BORDER[EA],CLS[EA],CLS[EB])[e]
    return {n:{'max_mm':float(st[cls==c].max()) if (cls==c).any() else 0.0,'p95_mm':float(np.percentile(st[cls==c],95)) if (cls==c).any() else 0.0} for c,n in ((1,'legs'),(2,'arm'),(3,'top'))},float(d[BORDER].max())
if __name__=='__main__':
    for name,path in (('original',None),('chat7_candidate','data/cand_co.npy')):
        co=CO0 if path is None else np.load(WD/path); print(name,json.dumps(stats(co)) if False else stats(co))
    import json
    for p in sys.argv[1:]:
        co=np.load(WD/p); print(p,stats(co)); print('   border steps / max border move',border_steps(co))
