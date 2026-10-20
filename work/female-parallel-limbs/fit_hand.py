import numpy as np, json, sys, copy, time
import shapes, fit2d
from shapes import HAND, hand
xpx,ypx,T,keep=fit2d.hand_zone()
ys=np.arange(-0.06,0.06,0.003)
def score(P):
    S=hand(P); M=fit2d.model_mask(S.eval,xpx,ypx,ys,xsub=2)
    return fit2d.err(M,T,keep)
P=copy.deepcopy(HAND); P.setdefault('dx',0.0); best=score(P); print('start',best,flush=True)
space={'psi':[-10,0,10,20,30,40,50,60],'palm_rx':[0.016,0.0185,0.0215,0.024],'dx':[-0.008,-0.004,0,0.004,0.008,0.012],
       'fscale':[0.5,0.75,1.0,1.25],'flen':[0.9,1.0,1.1],'fr':[0.9,1.0,1.1,1.2],'palm_ry':[0.030,0.0345,0.039]}
t0=time.time()
for rnd in range(2):
    for k,vals in space.items():
        for v in vals:
            Q=copy.deepcopy(P); Q[k]=v; s=score(Q)
            if s<best-1e-4: best,P=s,Q; print(rnd,k,v,round(best,4),flush=True)
print('final',best,{k:P.get(k) for k in space},time.time()-t0)
json.dump({k:P.get(k) for k in space},open('data/hand_fit.json','w'))
