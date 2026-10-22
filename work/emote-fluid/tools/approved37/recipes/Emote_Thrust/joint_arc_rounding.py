from arc_rounding import *

def gradients(p):
 v=np.diff(p,axis=0);a,b=v[:-1],v[1:];la=np.maximum(np.linalg.norm(a,axis=1),.05);lb=np.maximum(np.linalg.norm(b,axis=1),.05);co=np.sum(a*b,axis=1)/(la*lb);bad=np.maximum(0,.65-co)
 ga=-2*bad[:,None]*(b/(la*lb)[:,None]-co[:,None]*a/(la*la)[:,None]);gb=-2*bad[:,None]*(a/(la*lb)[:,None]-co[:,None]*b/(lb*lb)[:,None])
 grad=np.zeros_like(p);grad[:-2]-=ga;grad[1:-1]+=ga-gb;grad[2:]+=gb;return grad

def joint(paths,locked,rounds=10000):
 original=paths.copy()*1000;free=original.copy();n=paths.shape[1];shift=np.zeros((n,3))
 for a,b in [(18,20),(35,37)]:
  for f in range(a,b+1):shift[f,2]=-4*(f-a)
 for a,b,height,width in [(51,66,12,4),(77,91,5,2)]:
  for f in range(a,b+1):u=(f-a)/(b-a);shift[f,0]=width*(1-np.cos(np.pi*u));shift[f,2]=-height*np.sin(np.pi*u)
 hint=shift.copy();m=np.zeros_like(free);v=np.zeros_like(free);sm=np.zeros_like(shift);sv=np.zeros_like(shift);best=None
 for it in range(1,rounds+1):
  p=free.copy();p[:,locked]=original[:,locked]+shift[locked]
  p[:,[0,-1]]=original[:,[0,-1]]
  g=np.array([gradients(x) for x in p]);sg=g[:,locked].sum(axis=0)
  # Locked fists get only a shared rigid pelvis-weight shift.
  fullsg=np.zeros_like(shift);fullsg[locked]=sg;fullsg+=.000004*(shift-hint);fullsg[[0,-1,18,35,51,77]]=0;fullsg[:67,1]=0
  g+=.000004*(free-original);g[:,locked]=0;g[:,[0,-1]]=0
  m=.9*m+.1*g;v=.999*v+.001*g*g;sm=.9*sm+.1*fullsg;sv=.999*sv+.001*fullsg*fullsg
  lr=.15 if it<7000 else .03
  free-=lr*m/(1-.9**it)/(np.sqrt(v/(1-.999**it))+1e-8);shift-=lr*sm/(1-.9**it)/(np.sqrt(sv/(1-.999**it))+1e-8)
  if it%100==0:
   p=free.copy();p[:,locked]=original[:,locked]+shift[locked];p[:,[0,-1]]=original[:,[0,-1]]
   maximum=max(angles(x/1000).max() for x in p);error=np.linalg.norm(p-original,axis=-1).max();metric=(max(0,maximum-55),error)
   if best is None or metric<best[0]:best=(metric,p.copy(),shift.copy(),it)
  if it%2000==0:print('joint',it,'kink',maximum,'offset',error,'hipshift',np.linalg.norm(shift,axis=-1).max(),flush=True)
 return best[1]/1000,best[2]/1000,dict(kink=float(max(angles(x/1000).max() for x in best[1])),offset_mm=float(best[0][1]),hip_offset_mm=float(np.linalg.norm(best[2],axis=-1).max()),iteration=best[3])
