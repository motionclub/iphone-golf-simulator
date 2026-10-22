import json,numpy as np
from pathlib import Path
R=Path.cwd();W=R/'work/reference-rebuild/golf-wrist29';O=W/'continuous-review'
def norm(x): return np.linalg.norm(x,axis=-1)
def dot(a,b):return np.sum(a*b,axis=-1)
def turn(axis,t,v):
 c=np.cos(t)[...,None];s=np.sin(t)[...,None]
 return v*c+np.cross(axis,v)*s+axis*dot(axis,v)[...,None]*(1-c)
def angle(a,b):return np.degrees(np.arccos(np.clip(dot(a,b)/(norm(a)*norm(b)),-1,1)))
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def solve(S,E,H,P,C,A):
 P=P/norm(P)[...,None];a=norm(E-S);b=norm(H-E);d=norm(H-S);f=(H-S)/d[...,None]
 along=dot(E-S,f);pv=E-S-f*along[...,None];r=norm(pv);n=pv/np.maximum(r[...,None],1e-12)
 u=(H-E)/b[...,None];ori=angle(u,P)
 hp=np.cross(A,H-C);dd=dot(f,hp);fp=(hp-f*dd[...,None])/d[...,None]
 lp=.5*(1-(a*a-b*b)/(d*d))*dd
 rp=-along*lp/np.maximum(r,1e-12)
 ep=f*lp[...,None]+fp*along[...,None]+n*rp[...,None]-f*(r*dot(n,fp))[...,None]
 up=(hp-ep)/b[...,None];pp=np.cross(A,P)
 grad=dot(up,P)+dot(u,pp)
 raw=grad/(dot(up-pp,up-pp)+.12+15.23*dot(ep,ep))
 radial=norm(np.cross(A,H-C));margin=np.minimum(a+b-d,d-np.abs(a-b));margin=np.maximum(margin,1e-12)
 q0=margin*.5;dm=d-q0;dx=d+q0
 lm=(a*a-b*b+dm*dm)/(2*dm);lx=(a*a-b*b+dx*dx)/(2*dx)
 rmin=np.sqrt(np.maximum(1e-24,np.minimum(a*a-lm*lm,a*a-lx*lx)))
 lprime=np.maximum(abs(.5*(1-(a*a-b*b)/(dm*dm))),abs(.5*(1-(a*a-b*b)/(dx*dx))))
 sensitivity=a*(1/np.sqrt(d*d-q0*q0)+lprime/rmin)
 rates=np.stack([np.full_like(radial,4/np.pi),radial/.04,radial/q0,radial*sensitivity/.04],-1)
 maximum=rates.max(-1);cap=1/(maximum*np.power(np.sum((rates/maximum[...,None])**8,axis=-1),1/8))
 theta=cap*np.tanh(raw/np.maximum(cap,1e-12))*smooth((ori-35)/15)
 def evaluate(t):
  h=C+turn(A,t,H-C);df=norm(h-S);ff=(h-S)/df[...,None];ll=(a*a-b*b+df*df)/(2*df)
  cross=np.cross(f,ff);cos=dot(f,ff);nn=n+np.cross(cross,n)+np.cross(cross,np.cross(cross,n))/(1+cos)[...,None]
  rr=np.sqrt(np.maximum(0,a*a-ll*ll));e=S+ff*ll[...,None]+nn*rr[...,None]
  return h,e
 h,e=evaluate(theta);return theta,h,e,ori,angle(h-e,turn(A,theta,P))
def qmat(q):
 x,y,z,w=np.moveaxis(q,-1,0)
 return np.stack([1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)],-1).reshape(q.shape[:-1]+(3,3))
def load():
 for sex in ('Male','Female'):
  r=json.loads((R/f'work/reference-rebuild/original-native-adoption1/export/GolfKitHero_{sex}.json').read_text())['rig'];names=r['bones'];raw=(W/f'{sex}.rig.raw').read_bytes()
  for c in r['clips']:
   if not c['id'].startswith('golf'):continue
   tr=np.frombuffer(raw,'<f4',c['frames']*r['trackCount']*10,c['offset']).reshape(c['frames'],r['trackCount'],10).astype(float);club=names.index('Club')
   for side in ('Left','Right'):
    ids=[names.index(side+s) for s in ('UpperArm','LowerArm','Hand','MiddleProximal')];S,E,H,M=np.moveaxis(tr[:,ids,:3],1,0);C=tr[:,club,:3];A=qmat(tr[:,club,3:7])@np.array([0.,0.,1.]);A/=norm(A)[:,None]
    yield sex,c,side,(S,E,H,M-H,C,A),tr,ids,club
if __name__=='__main__':
 rows=[]
 for sex,c,side,v,tr,ids,club in load():
  roll,H,E,old,new=solve(*v);dw=H-v[2];de=E-v[1];improve=old-new;active=old>35
  rows.append(dict(sex=sex,clip=c['id'],side=side,frames=c['frames'],maxRoll=float(abs(np.degrees(roll)).max()),maxWristShift=float(norm(dw).max()*1000),maxElbowShift=float(norm(de).max()*1000),maxNeighborWristDelta=float(norm(np.diff(dw,axis=0)).max()*1000),maxNeighborElbowDelta=float(norm(np.diff(de,axis=0)).max()*1000),maxNeighborRollDelta=float(abs(np.diff(np.degrees(roll))).max()),meanImprovement=float(improve[active].mean()),worstRegression=float(-improve.min()),maxImprovement=float(improve.max()),address=[float(old[0]),float(new[0])],oldMax=float(old.max()),newMax=float(new.max())))
 print(json.dumps(rows,indent=2));(O/'trial.json').write_text(json.dumps(rows,indent=2)+'\n')
