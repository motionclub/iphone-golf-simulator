"""Build continuous per-bone action tracks with staggered velocity peaks.
Contacts retain the original event frames. Torso destinations lag the contact; hips keep
the original contact orientation. Secondary links continue after the leading bone stops.
"""
import math
import numpy as np
from mathutils import Quaternion,Vector

def ease(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
def ramp(t,a,b,peak):
 # Construct a discrete velocity profile whose maximum is at the requested
 # ending frame. A sampled continuous triangle can shift a short move by 1f.
 if t<=a:return 0.
 if t>=b:return 1.
 frames=np.arange(int(a)+1,int(b)+1,dtype=float);p=float(np.clip(round(peak+.25),a+1,b))
 weights=np.where(frames<=p,(frames-a)/max(1,p-a),(b+1-frames)/max(1,b+1-p))
 cumulative=np.r_[0,np.cumsum(weights)/sum(weights)]
 return float(np.interp(t,np.r_[a,frames],cumulative))
def build(Q,names,spec):
 dq=Q.copy();ix={nm:i for i,nm in enumerate(names)};n=len(Q);events=[];records=[];bybone={}
 for mi,old in enumerate(spec['moves']):
  a,b=old['start'],old['pose'];chain=old['chain'];lead=int(math.floor((a+b)/2));compact=b-a<=7;ends={}
  for j,nm in enumerate(chain):
   end=b+j
   if nm==old['bone'] and compact:end=b
   if old['name']=='rise with racket' and j>0:end=b+j-1
   end=min(n-6,end);ends[nm]=end
  settle=3 if compact or old['name']=='rise with racket' else 4
  primary=ends[old['bone']];r=dict(old);r.update(source_pose=b,pose=primary,settle=settle,contact_frame=b,peak_targets=[lead+j for j in range(len(chain))]);records.append(r)
  for j,nm in enumerate(chain):bybone.setdefault(nm,[]).append((mi,old,a,b,lead+j,ends[nm],settle if nm==old['bone'] else 0))
 for nm,ev in bybone.items():
  i=ix[nm];previous_end=-1;previous_target=None
  for idx,(mi,m,a,b,peak,end,settle) in enumerate(ev):
   start=max(a,previous_end);start=min(start,end-1)
   qa=Quaternion(tuple(Q[0 if mi==0 else a,i]));qb=Quaternion(tuple(Q[b,i]));axis=Vector((1,.13,.08)).normalized();delta=qb@qa.inverted();angle=delta.angle
   if angle>math.pi:angle-=2*math.pi
   if previous_target is not None and previous_end>=a-6:qa=previous_target.copy()
   if abs(angle)<math.radians(.1):
    sign=-1 if m['stretch']=='stretch' or ' up' in m['name'] else 1
    magnitude=2 if nm==m['bone'] else 1.5 if nm=='Hips' else .8
    qb=Quaternion(axis,math.radians(sign*magnitude))@Quaternion(tuple(Q[b,i]))
   delta=qb@qa.inverted();angle=delta.angle
   if angle>math.pi:angle-=2*math.pi
   axis=delta.axis if abs(angle)>1e-8 else axis
   counter=Quaternion(axis,-math.copysign(math.radians(1.2 if nm=='Hips' else max(.1,abs(angle)*180/math.pi*.12)),angle))@qa
   anti=max(1,a-6)
   anticipation_authored=previous_end<anti
   if anticipation_authored:
    begin=Quaternion(tuple(dq[anti,i]));
    for f in range(anti,a+1):dq[f,i]=np.array(begin.slerp(counter,ease((f-anti)/max(1,a-anti))))
    qa=counter
   over=Quaternion(axis,angle*.12)@qb if settle else qb
   p=float(np.clip(peak-.25,start+.25,end-.25))
   for f in range(max(1,start),min(n-1,end+1)):dq[f,i]=np.array(qa.slerp(over,ramp(f,start,end,p)))
   if settle:
    for f in range(end,min(n-1,end+settle+1)):dq[f,i]=np.array(over.slerp(qb,ease((f-end)/settle)))
   finish=end+settle;next_a=ev[idx+1][2] if idx+1<len(ev) else n-1;restore_end=max(finish+1,next_a-6) if idx+1<len(ev) else min(n-1,finish+4)
   restore_end=min(n-1,restore_end);target=Quaternion(tuple(Q[restore_end,i]))
   if restore_end>finish:
    for f in range(finish,min(n-1,restore_end+1)):dq[f,i]=np.array(qb.slerp(target,ease((f-finish)/(restore_end-finish))))
   previous_end=finish;previous_target=qb
   events.append(dict(move=m['name'],bone=nm,start=start,end=end,settle_end=finish,peak_target=peak,actual_curve_peak=p,anticipation_authored=anticipation_authored))
 dq[0]=Q[0];dq[-1]=Q[-1]
 return dq,records,events
