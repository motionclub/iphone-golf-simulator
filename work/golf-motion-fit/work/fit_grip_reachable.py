"""Fit finger flexion against the golf cylinder using the actual immutable skin.
Outputs editable golf-specific hand frames and finger angles, not racket poses.
"""
import bpy,json,sys,math
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];R=W.parents[1]
sys.path.insert(0,str(R/'work/match-anim-set/scripts'));import kin
args=sys.argv[sys.argv.index('--')+1:];sex=args[0];hand=args[1] if len(args)>1 else 'RH';tag=sex.lower();body=bpy.data.objects['Body_'+('F' if sex=='Female' else 'M')]
k=kin.Rig(str(R/f'work/match-anim-set/data/rig_{tag}.json'));old=json.loads((R/f'work/match-anim-set/data/hands_{tag}.json').read_text())
co=np.array([tuple(v.co) for v in body.data.vertices]);coh=np.c_[co,np.ones(len(co))]
weights=np.zeros((len(co),k.n));names={g.index:g.name for g in body.vertex_groups}
for v in body.data.vertices:
 for g in v.groups:
  if names[g.group] in k.idx:weights[v.index,k.idx[names[g.group]]]=g.weight
restInv=np.linalg.inv(k.Mrest);result={}
for glove in [bpy.data.objects.get('Golf_Glove_Left'),bpy.data.objects.get('Golf_Glove_Right')]:
 if not glove:continue

 extra=np.array([tuple(v.co) for v in glove.data.vertices]);gw=np.zeros((len(extra),k.n));gn={g.index:g.name for g in glove.vertex_groups}
 for v in glove.data.vertices:
  for g in v.groups:
   if gn[g.group] in k.idx:gw[v.index,k.idx[gn[g.group]]]=g.weight
 co=np.concatenate([co,extra]);coh=np.c_[co,np.ones(len(co))];weights=np.concatenate([weights,gw])
for side,sd in [('R','Right'),('L','Left')]:
 anchor=np.array(old['T_hand_R_in_racket' if side=='R' else 'left_handle']['T_hand_in_racket'] if side=='L' else old['T_hand_R_in_racket'],float)
 anchor[0,3]*=.95;anchor[1,3]=(-.020 if sex=='Female' else .010) if side=='R' else -.065
 if side=='L':anchor[0,3]-=.004;anchor[2,3]+=.004
 if hand=='LH':
  other='L' if side=='R' else 'R';anchor=np.array(old['left_handle']['T_hand_in_racket'] if other=='L' else old['T_hand_R_in_racket'],float);anchor[0,3]*=.95;anchor[1,3]=(-.020 if sex=='Female' else .010) if other=='R' else -.065
  if other=='L':anchor[0,3]-=.004;anchor[2,3]+=.004
  reflection=np.diag([-1.,1.,1.]);anchor[:3,:3]=reflection@anchor[:3,:3]@reflection;anchor[:3,3]=reflection@anchor[:3,3]
 h=k.idx[sd+'Hand']
 anchor[2,3]-=.020
 localToHandle=anchor@restInv[h]
 bones=[k.idx[nm] for nm in k.names if nm.startswith(sd) and ('Hand' in nm or any(d in nm for d in ['Index','Middle','Ring','Little','Thumb']))]
 across=k.Mrest[k.idx[sd+'LittleProximal'],:3,3]-k.Mrest[k.idx[sd+'IndexProximal'],:3,3];across/=np.linalg.norm(across)
 flexAxes={nm:(k.Rrest[k.idx[nm]].T@across).tolist() for nm in k.names if nm.startswith(sd) and any(d in nm for d in ['Index','Middle','Ring','Little'])}
 def rotation(nm,value,spread):
  axis=np.array(flexAxes.get(nm,[1,0,0]));return kin.rz(math.radians(spread))@kin.axis_angle(axis,math.radians(value))
 angles={nm:float(old['open_'+side].get(nm,0)) for nm in k.names if nm.startswith(sd) and any(d in nm for d in ['Index','Middle','Ring','Little','Thumb'])}
 spreads={}
 relative={bi:restInv[k.parent[bi]]@k.Mrest[bi] for bi in bones if bi!=h}
 def poses(ang,spread):
  M=k.Mrest.copy()
  for bi in bones:
   nm=k.names[bi]
   if nm not in ang:continue
   B=np.eye(4);B[:3,:3]=rotation(nm,ang[nm],spread.get(nm,0));M[bi]=M[k.parent[bi]]@relative[bi]@B
  return M
 def skin(ang,indices,spread=None):
  M=poses(ang,spread or spreads);out=np.zeros((len(indices),3));X=coh[indices]
  for bi in bones:
   w=weights[indices,bi]
   if not w.any():continue
   out+=w[:,None]*(X@(localToHandle@M[bi]@restInv[bi]).T)[:,:3]
  residual=1-weights[indices][:,bones].sum(1);out+=residual[:,None]*(X@localToHandle.T)[:,:3]
  return out
 def gap(X):
  # Finite cylinder, including the ends of the rubber grip.
  radial=np.linalg.norm(X[:,[0,2]],axis=1)-.014
  axial=np.abs(X[:,1])-.145
  return np.minimum(np.maximum(radial,axial),0)+np.linalg.norm(np.maximum(np.c_[radial,axial],0),axis=1)
 gaps={};diagnostics={}
 for digit in ('Index','Middle','Ring','Little','Thumb'):
  db=[k.idx[sd+digit+seg] for seg in ('Proximal','Intermediate','Distal')]
  ids=np.where(weights[:,db].sum(1)>.45)[0]
  if not len(ids):raise RuntimeError('No digit vertices '+sd+digit)
  ratios=[.35,.45,.275] if digit!='Thumb' else [-.15,.32,.20]
  best=None
  # Find the first surface contact along a coherent three-joint closure.
  for spread in ([0,-6,6,-12,12,-18,18,-24,24,-30,30] if digit in ['Little','Thumb','Index'] else [0]):
   localSpreads=dict(spreads);localSpreads[sd+digit+'Proximal']=spread
   closures=np.r_[np.linspace(-270,-75,66),np.linspace(75,270,66)] if digit!='Thumb' else np.linspace(75 if digit!='Thumb' else 0,270,66 if digit!='Thumb' else 91)
   for closure in closures:
    a=dict(angles)
    for seg,ratio,limit in zip(('Proximal','Intermediate','Distal'),ratios,[95,110,80]):a[sd+digit+seg]=max(-limit if digit!='Thumb' else -35,min(limit,angles[sd+digit+seg]+closure*ratio))
    X=skin(a,ids,localSpreads);dg=gap(X);distal=weights[ids,db[-1]]>.55
    if not distal.any():distal=weights[ids,db[-1]]>.25
    minimum=float(dg[distal].min());penetration=float(dg.min())
    score=abs(minimum-.0003)+max(0,-penetration-.001)*8+abs(spread)*.000001
    if best is None or score<best[0]:best=(score,a,minimum,localSpreads)
  # Refine each joint independently; a single three-joint ratio cannot fit
  # different finger lengths and the overlap hand's narrower grip region.
  if best and digit!='Thumb':
   for step in [15,8,4]:
    for seg,limit in zip(('Proximal','Intermediate','Distal'),[95,110,80]):
     nm=sd+digit+seg;center=best[1][nm]
     for value in np.arange(max(-limit,center-30),min(limit,center+30)+.1,step):
      a=dict(best[1]);a[nm]=float(value);X=skin(a,ids,best[3]);dg=gap(X);distal=weights[ids,db[-1]]>.25;minimum=float(dg[distal].min());penetration=float(dg.min())
      score=abs(minimum-.0003)+max(0,-penetration-.001)*8
      if score<best[0]:best=(score,a,minimum,best[3])
  if best:angles=best[1];gaps[digit]=best[2];spreads=best[3]
  else:gaps[digit]=float(gap(skin(angles,ids)).min())
  X=skin(angles,ids);at=int(np.argmin(gap(X)));diagnostics[digit]=dict(closest=X[at].tolist(),bounds=[X.min(0).tolist(),X.max(0).tolist()])
 # Overlap / reverse-overlap exceptions are authored individually after closure.
 result[side]=dict(anchor=anchor.tolist(),angles=angles,spreads=spreads,flexAxes=flexAxes,gapsM=gaps,diagnostics=diagnostics)
 print('GRIP',sex,side,gaps,flush=True)
(W/(f'data/grip_{sex}'+('' if hand=='RH' else '_LH')+'.json')).write_text(json.dumps(result,indent=2)+'\n')
# Contact-fit the two overlap exceptions to the other hand's actual skin, rather
# than assuming that a finger curl against the shaft also creates an overlap.
def finger_points(side,digit,angles=None,spread=None):
 sd='Left' if side=='L' else 'Right';row=result[side];aa=dict(row['angles']);aa.update(angles or {});ss=dict(row['spreads']);ss.update(spread or {})
 B=np.tile(np.eye(3),(k.n,1,1))
 for nm,value in aa.items():B[k.idx[nm]]=kin.rz(math.radians(ss.get(nm,0)))@kin.axis_angle(np.array(row.get('flexAxes',{}).get(nm,[1,0,0])),math.radians(value))
 Q,P=k.fk(B);local=np.array(row['anchor'])@restInv[k.idx[sd+'Hand']]
 ids=np.where(weights[:,[k.idx[sd+digit+seg] for seg in ('Proximal','Intermediate','Distal')]].sum(1)>.45)[0];X=coh[ids];out=np.zeros((len(ids),3))
 for bi,nm in enumerate(k.names):
  w=weights[ids,bi]
  if not w.any():continue
  M=np.eye(4);M[:3,:3]=Q[bi];M[:3,3]=P[bi];out+=w[:,None]*(X@(local@M@restInv[bi]).T)[:,:3]
 return out
for side,digit,other,targetDigit,field in ([('R','Little','L','Index','overlapAngles'),('L','Index','R','Little','reverseOverlapAngles')] if hand=='RH' else [('L','Little','R','Index','overlapAngles'),('R','Index','L','Little','reverseOverlapAngles')]):
 sd='Left' if side=='L' else 'Right';target=finger_points(other,targetDigit);best=None
 for spread in range(-24,25,6):
  for closure in (range(-200,201,4)):
   aa={sd+digit+seg:closure*ratio for seg,ratio in zip(('Proximal','Intermediate','Distal'),(.35,.45,.275))}
   X=finger_points(side,digit,aa,{sd+digit+'Proximal':spread});distance=np.sqrt(((X[:,None]-target[None,:])**2).sum(2)).min();shaft=float(gap(X).min())
   score=abs(float(distance)-.0005)+max(0,-shaft-.0003)*5
   if best is None or score<best[0]:best=(score,aa,spread,float(distance),shaft)
 result[side][field]=best[1];result[side][field+'Spread']=best[2];result[side][field+'ContactGapM']=best[3];result[side][field+'ShaftGapM']=best[4]
 print('OVERLAP',sex,field,best[3],best[4],flush=True)
(W/(f'data/grip_{sex}'+('' if hand=='RH' else '_LH')+'.json')).write_text(json.dumps(result,indent=2)+'\n')
