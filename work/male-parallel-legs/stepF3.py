"""python stepF3.py <in.npy> <params.npy> <out.npy> : project both feet onto the fitted smooth implicit foot (blend weight by height)"""
import sys; sys.path.insert(0,'.')
from leglib import *
import footsdf as S
V=np.load(sys.argv[1]); p=np.load(sys.argv[2]); out=sys.argv[3]
Vn=V.copy()
for sel0,side in ((LEFT,1),(RIGHT,-1)):
    sel=sel0&(V[:,2]<0.14)
    P=V[sel].copy(); P[:,0]*=side
    Q=S.project(P,p,iters=14,maxd=0.03)
    w=smoothstep(0.135,0.09,P[:,2])[:,None]
    R=P+w*(Q-P); R[:,0]*=side
    Vn[sel]=R
d=np.linalg.norm(Vn-V,axis=1)*1000
print('moved',(d>0).sum(),'rms %.2f max %.2f mm'%(np.sqrt((d[d>0]**2).mean()),d.max()))
print('min z',Vn[ZONE,2].min(),' (start min z %.5f)'%V0[:,2].min())
np.save(out,Vn)
