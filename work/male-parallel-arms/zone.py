import numpy as np, sys
from zonelib import *
V,T,polys=load(); n=len(V); E=edges_of(polys,n); nb=adjacency(E,n)
def comp(side):
    cand=(side*V[:,0]>0.215)&(V[:,2]>0.78)&(V[:,2]<1.42)
    seen=np.zeros(n,bool); comps=[]
    for s in np.nonzero(cand)[0]:
        if seen[s]: continue
        st=[s]; seen[s]=True; c=[s]
        while st:
            u=st.pop()
            for v in nb[u]:
                if cand[v] and not seen[v]: seen[v]=True; st.append(v); c.append(v)
        comps.append(c)
    big=max(comps,key=len); m=np.zeros(n,bool); m[big]=True
    return m,[len(c) for c in comps]
zR,cr=comp(+1); zL,cl=comp(-1)
print('R comps',cr,'L comps',cl,'R',zR.sum(),'L',zL.sum(),'overlap',(zR&zL).sum())
zone=zR|zL
np.save('data/zone_R.npy',zR); np.save('data/zone_L.npy',zL); np.save('data/zone.npy',zone)
for nm,z in (('R',zR),('L',zL)):
    print(nm,'x',V[z,0].min(),V[z,0].max(),'y',V[z,1].min(),V[z,1].max(),'z',V[z,2].min(),V[z,2].max())
# mirror symmetry check of the arms (x -> -x): nearest distance
import numpy as np
A=V[zR]; B=V[zL]*np.array([-1,1,1])
# for each A find nearest B (brute force on subsets)
d=np.sqrt(((A[:,None,:]-B[None,:,:])**2).sum(2)).min(1)
print('R vs mirrored L nearest distance mm: mean',1000*d.mean(),'p95',1000*np.percentile(d,95),'max',1000*d.max())
