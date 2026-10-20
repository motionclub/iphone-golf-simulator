import sys; sys.path.insert(0,'.')
from leglib import *
import opt_foot as O
inp,outp=sys.argv[1],sys.argv[2]
alpha,heel,toe,leg,xp=map(float,sys.argv[3:8])
V=np.load(inp)
Vn=O.warp(V,alpha,heel,toe,leg,xp)
mv=np.linalg.norm(Vn-V,axis=1); print('moved',(mv>0).sum(),'max mm %.1f'%(mv.max()*1000),'max z moved %.3f'%V[mv>0,2].max())
np.save(outp,Vn)
