import numpy as np, pickle
V=np.load('baseline/mesh.npz')['co']; F=pickle.load(open('baseline/faces.pkl','rb'))
# connected components of horizontal slice contour: use edges crossing plane z=c; points = intersection; cluster by linking edges that share a face
E={}
for fi,f in enumerate(F):
    for k in range(len(f)):
        a,b=f[k],f[(k+1)%len(f)]; E.setdefault((min(a,b),max(a,b)),[]).append(fi)
def slice_loops(c):
    # intersect edges, link through faces
    pts={}
    for (a,b),fs in E.items():
        za,zb=V[a,2]-c,V[b,2]-c
        if za*zb<0: pts[(a,b)]=V[a]+(V[b]-V[a])*(za/(za-zb))
    # union-find via faces
    par={k:k for k in pts}
    def fd(x):
        while par[x]!=x: par[x]=par[par[x]]; x=par[x]
        return x
    byface={}
    for k in pts:
        for fi in E[k]: byface.setdefault(fi,[]).append(k)
    for ks in byface.values():
        for k in ks[1:]: par[fd(k)]=fd(ks[0])
    comp={}
    for k,p in pts.items(): comp.setdefault(fd(k),[]).append(p)
    return [np.array(v) for v in comp.values()]
for c in np.arange(0.70,1.43,0.02):
    L=slice_loops(c); s=[]
    for P in sorted(L,key=lambda P:P[:,0].mean()):
        s.append(f'x[{P[:,0].min():+.3f},{P[:,0].max():+.3f}] y[{P[:,1].min():+.3f},{P[:,1].max():+.3f}]')
    print(f'z {c:.2f}: '+' | '.join(s))
