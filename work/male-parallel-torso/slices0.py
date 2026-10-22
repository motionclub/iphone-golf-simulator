import numpy as np, pickle
V=np.load('baseline/mesh.npz')['co']; F=pickle.load(open('baseline/faces.pkl','rb'))
# edge lengths per z band in torso
E=set()
for f in F:
    for k in range(len(f)):
        a,b=f[k],f[(k+1)%len(f)]; E.add((min(a,b),max(a,b)))
E=np.array(sorted(E)); L=np.linalg.norm(V[E[:,0]]-V[E[:,1]],axis=1)*1000
zc=(V[E[:,0],2]+V[E[:,1],2])/2; xc=(V[E[:,0],0]+V[E[:,1],0])/2
for z0 in np.arange(0.70,1.46,0.05):
    m=(zc>=z0)&(zc<z0+0.05)&(np.abs(xc)<0.2)
    print(f'z {z0:.2f}-{z0+0.05:.2f} edges {m.sum():5d} mean {L[m].mean():.1f} med {np.median(L[m]):.1f} max {L[m].max():.1f}')
print()
# cross-section: for each z band, vertices; central torso = those with |x| < arm separation. Print x-extent of all verts and the extent of the connected-ish central part
for z in np.arange(0.74,1.46,0.04):
    m=(np.abs(V[:,2]-z)<0.004)
    xs=V[m,0]; ys=V[m,1]
    # sort x, find largest gap structure
    xs_s=np.sort(xs)
    print(f'z {z:.2f} n {m.sum():4d} x[{xs.min():+.3f},{xs.max():+.3f}] y[{ys.min():+.3f},{ys.max():+.3f}]', end=' ')
    # central cluster: |x|<0.25
    c=m&(np.abs(V[:,0])<0.25)
    if c.sum(): print(f'| central x[{V[c,0].min():+.3f},{V[c,0].max():+.3f}] y[{V[c,1].min():+.3f},{V[c,1].max():+.3f}] n {c.sum()}')
    else: print()
