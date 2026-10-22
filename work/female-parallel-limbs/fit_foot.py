import numpy as np, json, copy, time, fit2d
from shapes import FOOT, foot, finalize_foot
xpx,ypx,T,keep=fit2d.foot_zone()
ys=np.arange(-0.2,0.13,0.004)
def mk(P):
    W=finalize_foot(foot(P),P); return W
def score(P):
    M=fit2d.model_mask(mk(P).eval,xpx,ypx,ys,xsub=2); return fit2d.err(M,T,keep)
# floor
for P,cx,nm in ((fit2d.PF,440,'front'),(fit2d.PB,847,'back')):
    for sd,sn in ((-1,'L'),(1,'R')):
        cols=np.clip(np.round(cx+sd*xpx).astype(int),0,1279); m=P[np.ix_(ypx.astype(int),cols)].astype(float)
        print(nm+sn,'vs mean',round(fit2d.err(m,T,keep),3),'area',int(m.sum()))
P=copy.deepcopy(FOOT); best=score(P); print('start',round(best,4),'area model',round(fit2d.model_mask(mk(P).eval,xpx,ypx,ys,xsub=2).sum()),'plate',round(T.sum()),flush=True)
space={'heel_rx':[0.020,0.024,0.027,0.029],'heel_w':[0.7,0.8,0.9,1.0],'sect_n':[2.0,2.3,2.6],'toe_out':[3,6,9],'dxs':[0.006,0.012,0.018],'wscale':[1.0,1.1,1.2]}
t0=time.time()
for rnd in range(2):
    for k,vals in space.items():
        for v in vals:
            Q=copy.deepcopy(P); Q[k]=v; s=score(Q)
            if s<best-1e-4: best,P=s,Q; print(rnd,k,v,round(best,4),flush=True)
print('final',round(best,4),{k:P.get(k) for k in space},time.time()-t0)
json.dump({k:P.get(k) for k in space},open('data/foot_fit.json','w'))
