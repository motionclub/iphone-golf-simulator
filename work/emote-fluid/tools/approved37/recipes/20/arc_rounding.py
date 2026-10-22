from pathlib import Path
import numpy as np,json
def angles(p):
 v=np.diff(p,axis=0);d=np.linalg.norm(v[:-1],axis=1)*np.linalg.norm(v[1:],axis=1)
 return np.degrees(np.arccos(np.clip(np.divide(np.sum(v[:-1]*v[1:],axis=1),d,out=np.ones_like(d),where=d>1e-10),-1,1)))
def solve(p,lock,rounds=8000):
 original=p.copy();best=None;mom=np.zeros_like(p);var=np.zeros_like(p)
 # mm coordinates for numerically stable gradients.
 p=p*1000;orig=p.copy()
 for it in range(1,rounds+1):
  v=np.diff(p,axis=0);a,b=v[:-1],v[1:];la=np.linalg.norm(a,axis=1);lb=np.linalg.norm(b,axis=1)
  la=np.maximum(la,.05);lb=np.maximum(lb,.05);co=np.sum(a*b,axis=1)/(la*lb);bad=np.maximum(0,.65-co)
  # Clear geometry turn penalty. Fit keeps displacement small and boundaries remain fixed.
  ga=-2*bad[:,None]*(b/(la*lb)[:,None]-co[:,None]*a/(la*la)[:,None]);gb=-2*bad[:,None]*(a/(la*lb)[:,None]-co[:,None]*b/(lb*lb)[:,None])
  grad=np.zeros_like(p);grad[:-2]-=ga;grad[1:-1]+=ga-gb;grad[2:]+=gb
  grad+=.000004*(p-orig)
  grad[lock]=0
  mom=.9*mom+.1*grad;var=.999*var+.001*grad*grad
  lr=.15 if it<6000 else .04
  p-=lr*(mom/(1-.9**it))/(np.sqrt(var/(1-.999**it))+1e-8);p[lock]=orig[lock]
  if it%100==0:
   ang=angles(p/1000);maximum=ang.max();error=np.linalg.norm(p-orig,axis=1).max()
   metric=(max(0,maximum-55),error)
   if best is None or metric<best[0]:best=(metric,p.copy(),it)
  if it%2000==0:print('iter',it,'kink',maximum,'offset',error,flush=True)
 return best[1]/1000,dict(kink=float(angles(best[1]/1000).max()),offset_mm=float(best[0][1]),iteration=best[2])
