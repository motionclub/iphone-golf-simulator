"""final-index -> builder role map for the hand (right side +1 appended first)"""
import sys, json
from pathlib import Path
W=Path(__file__).resolve().parent; R=W.parents[1]
sys.path[:0]=[str(W),str(R/'male-micro1e')]
import numpy as np
import hand_build as HB0, hand_build2 as HB2, hand_assemble as HA, hand_topo as T
def roles(params):
    HB2.P.update(params); HB0.P.update({k:v for k,v in params.items() if k in HB0.P})
    BASE=np.load(R/'male-micro1e/baseline/mesh.npz')['co'].astype(float); F0=np.load(R/'male-micro1e/faces.npy')
    HA.HB=HB2
    N=len(BASE)
    for nrows in (10,11,12,13):
        HB2.P['n_rows']=nrows
        results=[(s,HB2.build_hand(BASE,F0,s,-0.055)) for s in (+1,-1)]
        ok=True
        for s,r in results:
            used=set(v for f in r['builder'].faces for v in f if v>=N)
            if len(used)<int(r['cut']['Hmask'].sum()): ok=False
        if ok: break
    out={}; extra=0
    for s,r in results:
        B=r['builder']; cut=r['cut']
        used_ids=sorted(set(v for f in B.faces for v in f if v>=N)); freed=list(np.where(cut['Hmask'])[0])
        role={}
        for r_,ids in B.ring.items():
            for i,v in enumerate(ids): role[v]=f'palm r{r_} i{i}'
        for m,ids in enumerate(B.thumb_rows):
            for k,v in enumerate(ids): role[v]=f'thumb m{m} k{k}'
        for k,(rows,C) in B.fin_rows.items():
            for m,rw in enumerate(rows):
                for q,v in enumerate(rw): role[v]=f'finger{k} m{m} q{q}'
            role[C]=f'finger{k} tip'
        for k,vid in enumerate(used_ids):
            if k<len(freed): fi=int(freed[k])
            else: fi=N+extra; extra+=1
            out[(s,fi)]=role.get(vid,f'other {vid-N}')
    return out
if __name__=='__main__':
    p=json.load(open(W/'params_m1f_final.json'))
    o=roles(p)
    for a in [24136,24137,24138,24139,24542,24552,24562,24165,24373,24155,24170,24272,24150,24105,24145,24058,24059]:
        print(a,[ (s,v) for (s,fi),v in o.items() if fi==a])
