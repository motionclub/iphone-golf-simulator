"""project the feet onto the fitted smooth implicit foot, then relax tangentially (re-projecting) to even the vertex distribution.
python stepF4.py <in.npy> <params.npy> <out.npy> [relax_iters]"""
import sys; sys.path.insert(0,'.')
from leglib import *
import footsdf as S
V=np.load(sys.argv[1]); p=np.load(sys.argv[2]); out=sys.argv[3]; RI=int(sys.argv[4]) if len(sys.argv)>4 else 40
Vn=V.copy()
HZ=0.14
for sel0,side in ((LEFT,1),(RIGHT,-1)):
    sel=sel0&(V[:,2]<HZ)
    idx=np.nonzero(sel)[0]
    P=V[idx].copy(); P[:,0]*=side
    w=smoothstep(0.135,0.09,P[:,2])           # 1 below 0.09, 0 above 0.135
    Q=S.project(P,p,iters=14,maxd=0.03)
    R=P+w[:,None]*(Q-P)
    # tangential relaxation on the whole mesh adjacency, but only these vertices move
    full=V.copy(); full[idx]=R*np.array([side,1,1])
    for it in range(RI):
        U=umbrella(full)[idx]*np.array([side,1,1])      # in mirrored (left-foot) coordinates
        Rm=full[idx]*np.array([side,1,1])
        g=S.grad(Rm,p); nrm=g/np.maximum(np.linalg.norm(g,axis=1,keepdims=True),1e-12)
        Ut=U-(U*nrm).sum(1,keepdims=True)*nrm
        Rm=Rm+0.5*w[:,None]*Ut
        Qm=S.project(Rm,p,iters=3,maxd=0.03)
        Rm=Rm+w[:,None]*(Qm-Rm)
        full[idx]=Rm*np.array([side,1,1])
    Vn[idx]=full[idx]
d=np.linalg.norm(Vn-V,axis=1)*1000
print('moved',(d>0).sum(),'rms %.2f max %.2f mm'%(np.sqrt((d[d>0]**2).mean()),d.max()),' min z %.5f'%Vn[ZONE,2].min())
np.save(out,Vn)
