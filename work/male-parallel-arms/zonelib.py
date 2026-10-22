import numpy as np, pickle
from pathlib import Path
W=Path(__file__).resolve().parent
def load(mesh='data/mesh_start.npz'):
    D=np.load(W/mesh); V=D['V']; T=D['T']
    polys=pickle.load(open(W/mesh.replace('.npz','_polys.pkl'),'rb'))
    return V,T,polys
def edges_of(polys,n):
    E=set()
    for f in polys:
        for k in range(len(f)):
            a,b=f[k],f[(k+1)%len(f)]; E.add((min(a,b),max(a,b)))
    E=np.array(sorted(E)); return E
def adjacency(E,n):
    nb=[[] for _ in range(n)]
    for a,b in E: nb[a].append(b); nb[b].append(a)
    return nb
def vnormals(V,T):
    n=np.zeros_like(V); fn=np.cross(V[T[:,1]]-V[T[:,0]],V[T[:,2]]-V[T[:,0]])
    for k in range(3): np.add.at(n,T[:,k],fn)
    l=np.linalg.norm(n,axis=1,keepdims=True); return n/np.maximum(l,1e-12)
def taubin(V,E,w,iters,lam=0.5,mu=-0.53):
    """w: per-vertex weight 0..1 (0 = pinned)."""
    n=len(V); deg=np.bincount(E.ravel(),minlength=n).astype(float)
    p=V.copy(); ww=w[:,None]
    def lap(q):
        s=np.zeros_like(q); np.add.at(s,E[:,0],q[E[:,1]]); np.add.at(s,E[:,1],q[E[:,0]])
        return s/np.maximum(deg,1)[:,None]-q
    for _ in range(iters):
        p=p+lam*ww*lap(p); p=p+mu*ww*lap(p)
    return p
