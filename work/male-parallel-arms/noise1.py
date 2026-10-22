import numpy as np
from zonelib import *
V,T,polys=load(); n=len(V); E=edges_of(polys,n); nb=adjacency(E,n)
print('edges',len(E),'mean edge len mm',1000*np.linalg.norm(V[E[:,0]]-V[E[:,1]],axis=1).mean())
# right arm candidate set and connected component
cand=(V[:,0]>0.215)&(V[:,2]>0.78)&(V[:,2]<1.42)
seen=np.zeros(n,bool); comps=[]
for s in np.nonzero(cand)[0]:
    if seen[s]: continue
    st=[s]; seen[s]=True; c=[s]
    while st:
        u=st.pop()
        for v in nb[u]:
            if cand[v] and not seen[v]: seen[v]=True; st.append(v); c.append(v)
    comps.append(c)
print('components',[len(c) for c in comps])
arm=np.zeros(n,bool); arm[max(comps,key=len)]=True
print('arm verts',arm.sum(),'x',V[arm,0].min(),V[arm,0].max(),'z',V[arm,2].min(),V[arm,2].max())
# boundary verts of the arm component (neighbour not in arm)
bnd=np.array([arm[i] and any(not arm[j] for j in nb[i]) for i in range(n)])
print('boundary verts',bnd.sum(),'z range of boundary',V[bnd,2].min(),V[bnd,2].max())
w=arm.astype(float); w[bnd]=0
P=taubin(V,E,w,10)
N=vnormals(V,T)
d=P-V; dn=(d*N).sum(1)
print('disp mm: mean',1000*np.linalg.norm(d[arm],axis=1).mean(),'p95',1000*np.percentile(np.linalg.norm(d[arm],axis=1),95),'max',1000*np.linalg.norm(d[arm],axis=1).max())
ax=np.array([0.678,-0.178,-0.713]); c=np.array([0.437,-0.061,1.064]); t=(V-c)@ax
for a in np.arange(-0.30,0.30,0.05):
    m=arm&(t>=a)&(t<a+0.05)
    if m.sum(): print(f't {a:+.2f}..{a+0.05:+.2f} n={m.sum():4d} |d| mean {1000*np.linalg.norm(d[m],axis=1).mean():.2f}mm p95 {1000*np.percentile(np.linalg.norm(d[m],axis=1),95):.2f} max {1000*np.linalg.norm(d[m],axis=1).max():.2f}')
np.save('data/arm_R_comp.npy',np.nonzero(arm)[0])
