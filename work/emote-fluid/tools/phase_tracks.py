"""Build continuous per-bone action tracks with staggered velocity peaks.
Contacts retain the original event frames. Torso destinations lag the contact; hips keep
the original contact orientation. Secondary links continue after the leading bone stops.
"""
import math
import numpy as np
from mathutils import Quaternion,Vector
from timeline import source_times,destination_time

def ease(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
def ramp(t,a,b,peak,base_weight=0.):
 # Construct a discrete velocity profile whose maximum is at the requested
 # ending frame. A sampled continuous triangle can shift a short move by 1f.
 if t<=a:return 0.
 if t>=b:return 1.
 frames=np.arange(int(a)+1,int(b)+1,dtype=float);p=float(np.clip(round(peak+.25),a+1,b))
 weights=np.where(frames<=p,(frames-a)/max(1,p-a),(b+1-frames)/max(1,b+1-p))
 weights=base_weight+(1-base_weight)*weights
 cumulative=np.r_[0,np.cumsum(weights)/sum(weights)]
 return float(np.interp(t,np.r_[a,frames],cumulative))
def build(Q,names,spec,clip):
 dq=Q.copy();ix={nm:i for i,nm in enumerate(names)};n=len(Q);events=[];records=[];bybone={}
 for mi,old in enumerate(spec['moves']):
  a,b=old['start'],old['pose'];chain=old['chain'];lead=int(math.floor((destination_time(n,clip,a)+destination_time(n,clip,b))/2));compact=b-a<=7;ends={};windows={};goals=[lead+j for j in range(len(chain))]
  if clip=='Intro_Pushups' and mi==0:goals=[6+j for j in range(len(chain))]
  peaks=source_times(n,clip,goals)
  for j,nm in enumerate(chain):
   end=b+j
   if nm==old['bone'] and compact:end=b
   if old['name']=='rise with racket' and j>0:end=b+j-1
   if mi==len(spec['moves'])-1 and nm==old['bone']:
    if clip=='Emote_Spike':end=84
    elif clip=='Intro_BringIt':end=80
    elif clip=='Intro_Pushups':end=84
   end=min(n-6,end);ends[nm]=end
  settle=3 if compact or old['name']=='rise with racket' else 4
  if old['name'] in ['extend plank','lower to pickup']:settle=3
  if old['name']=='lower waving hand':settle=4
  if mi==len(spec['moves'])-1 and clip in ['Emote_Spike','Emote_Scuba','Intro_BringIt','Intro_Pushups']:settle=6
  primary=ends[old['bone']];r=dict(old);r.update(source_pose=b,pose=primary,settle=settle,contact_frame=b,peak_targets=goals,source_peak_targets=peaks.tolist(),link_windows=windows);records.append(r)
  for j,nm in enumerate(chain):bybone.setdefault(nm,[]).append((mi,old,a,b,float(peaks[j]),ends[nm],settle if nm==old['bone'] else 0))
 for nm,ev in bybone.items():
  i=ix[nm];previous_end=-1;previous_target=None;last_momentum_axis=None
  for idx,(mi,m,a,b,peak,end,settle) in enumerate(ev):
   start=max(a,previous_end);start=min(start,end-1)
   if clip=='Intro_Pushups' and mi==0:start=min(end-1,m['chain'].index(nm))
   qa=Quaternion(tuple(Q[0 if mi==0 else a,i]));qb=Quaternion(tuple(Q[b,i]));axis=Vector((1,.13,.08)).normalized();delta=qb@qa.inverted();angle=delta.angle
   if angle>math.pi:angle-=2*math.pi
   if previous_target is not None:qa=previous_target.copy()
   delta=qb@qa.inverted();angle=delta.angle
   if angle>math.pi:angle-=2*math.pi
   if abs(angle)<math.radians(.1):
    sign=-1 if m['stretch']=='stretch' or ' up' in m['name'] else 1
    magnitude=2 if nm==m['bone'] else 1.5 if nm=='Hips' else .8
    qb=Quaternion(axis,math.radians(sign*magnitude))@Quaternion(tuple(Q[b,i]))
   delta=qb@qa.inverted();angle=delta.angle
   if angle>math.pi:angle-=2*math.pi
   axis=delta.axis if abs(angle)>1e-8 else axis
   last_momentum_axis=axis.copy() if angle>=0 else -axis
   counter=Quaternion(axis,-math.copysign(math.radians(1.2 if nm=='Hips' else max(.1,abs(angle)*180/math.pi*.12)),angle))@qa
   anti=max(1,a-6)
   anticipation_authored=previous_end<anti
   if anticipation_authored:
    begin=Quaternion(tuple(dq[anti,i]));
    for f in range(anti,a+1):dq[f,i]=np.array(begin.slerp(counter,ease((f-anti)/max(1,a-anti))))
    qa=counter
   over=Quaternion(axis,angle*.12)@qb if settle else qb
   p=float(np.clip(peak-.25,start+.25,end-.25))
   for f in range(max(1,start),min(n-1,end+1)):dq[f,i]=np.array(qa.slerp(over,ramp(f,start,end,p,.9 if clip=='Intro_Pushups' and mi in [0,len(spec['moves'])-1] else 0.)))
   if settle:
    for f in range(end,min(n-1,end+settle+1)):dq[f,i]=np.array(over.slerp(qb,ease((f-end)/settle)))
   finish=end+settle;next_a=ev[idx+1][2] if idx+1<len(ev) else n-1;restore_end=max(finish+1,next_a-6) if idx+1<len(ev) else min(n-1,finish+4)
   restore_end=min(n-1,restore_end);target=Quaternion(tuple(Q[restore_end,i]))
   if restore_end>finish:
    for f in range(finish,min(n-1,restore_end+1)):dq[f,i]=np.array(qb.slerp(target,ease((f-finish)/(restore_end-finish))))
   records[mi]['link_windows'][nm]=[float(start),float(finish)]
   previous_end=finish;previous_target=qb
   events.append(dict(move=m['name'],bone=nm,start=start,end=end,settle_end=finish,peak_target=peak,actual_curve_peak=p,anticipation_authored=anticipation_authored))
 for r in records:
  r['source_start']=r['start'];r['source_action_pose']=r['pose'];r['source_settle_end']=r['pose']+r['settle']
  r['start']=int(round(destination_time(n,clip,r['start'])));r['pose']=int(round(destination_time(n,clip,r['pose'])))
  r['settle']=int(round(destination_time(n,clip,r['source_settle_end'])))-r['pose']
  r['anticipation']=[int(round(destination_time(n,clip,x))) for x in r['anticipation']]
  r['link_windows']={nm:[destination_time(n,clip,a),destination_time(n,clip,b)] for nm,(a,b) in r['link_windows'].items()}
 dq[0]=Q[0];dq[-1]=Q[-1]
 return dq,records,events
