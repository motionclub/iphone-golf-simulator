"""One handle drives both articulated hands; rig rest transforms are immutable."""
import math
import json
from pathlib import Path
import numpy as np
import kin
from pose import Solver,R_ypr,F_W

class GolfSolver(Solver):
 def __init__(self,rig,racket,hands):
  super().__init__(rig,racket,hands)
  self.min_wrist_r=.15
  self.handedness='RH';self.golf={};self.length=.96
  self.anchors={s:np.array(hands['T_hand_R_in_racket' if s=='R' else 'T_hand_L_mirror_base'],float) for s in 'LR'}
  # Separate lead/trail grip heights. Club +Y points from grip toward head.
  for s in 'LR':
   self.anchors[s][0,3]*=.95
   self.anchors[s][1,3]=.032 if s=='R' else -.065
  path=Path(__file__).resolve().parents[1]/f'data/grip_{rig.tag.title()}.json'
  self.golf_grips=json.loads(path.read_text()) if path.exists() else None
  if self.golf_grips:self.anchors={side:np.array(self.golf_grips[side]['anchor']) for side in 'LR'}
  lh=Path(__file__).resolve().parents[1]/f'data/grip_{rig.tag.title()}_LH.json'
  self.left_grips=json.loads(lh.read_text()) if lh.exists() else None
  self.scale=rig.J['head_top'][2]/1.70465994

 def evaluate(self,p,handedness,length,putting=False):
  self.handedness=handedness;self.golf=p;self.length=length*self.scale;self.putting=putting
  sign=1 if handedness=='RH' else -1
  pel=np.asarray(p['pel_rot'],float).copy();ch=np.asarray(p['chest_rot'],float).copy();pel[[0,2]]*=sign;ch[[0,2]]*=sign
  width=float(p['stance'])*self.scale;f0=-(self.ball_rest['L'][1]-self.O[1])
  drop=float(p['pel_drop'])-(.018 if putting and self.rig.tag=='female' else 0)
  params=dict(pel=[-.035*sign*min(float(p['heel'])/48,1),0,drop],pel_rot=pel,chest_rot=ch,head_rot=[-float(pel[0]+ch[0])*.65,float(p['head'])-8,0],
   lf_foot=[-width/2,f0],rf_foot=[width/2,f0],lf_yaw=-12,rf_yaw=12,
   lf_heel=float(p['heel']) if sign<0 else 0,rf_heel=float(p['heel']) if sign>0 else 0,l_attach=1,l_grip=1,r_fing=1,l_fing=1)
  amp=float(p['walk_amp']);ph=float(p['walk_phase'])
  if amp:
   for side,k in [('L','lf'),('R','rf')]:
    q=ph+(math.pi if side=='R' else 0)
    params[k+'_foot']=[(-1 if side=='L' else 1)*.17,f0+.14*math.cos(q)*amp]
    params[k+'_lift']=.06*max(0,math.sin(q))*amp
  return self.solve(params)

 def _solve_arms(self,P,Q,Pos,put,basis,diag,R_chest):
  rig=self.rig;ix=rig.idx;p=self.golf;sign=1 if self.handedness=='RH' else -1
  h=self.O+kin.a2w(p['handle']);rot=p['orientation'].copy()
  reflection=np.diag([-1.,1.,1.])
  if sign<0:h[0]=-h[0];rot=reflection@rot@reflection
  targets={};frames={};anchors={}
  for s in 'LR':
   source=s if sign>0 else ('R' if s=='L' else 'L');anchor=self.anchors[source].copy()
   if sign<0:
    if self.left_grips:anchor=np.array(self.left_grips[s]['anchor'])
    else:anchor[:3,:3]=reflection@anchor[:3,:3]@reflection;anchor[:3,3]=reflection@anchor[:3,3]
   anchors[s]=anchor;targets[s]=h+rot@anchor[:3,3];frames[s]=rot@anchor[:3,:3]
  # Articulated shoulder girdle follows the arm targets, without moving the rig.
  shoulders={}
  for s in 'LR':
   sd='Left' if s=='L' else 'Right';ic=ix[sd+'Shoulder'];iu=ix[sd+'UpperArm']
   rest=Q[ix['UpperChest']]@rig.rel_rot[ic]
   est=Pos[ix['UpperChest']]+Q[ix['UpperChest']]@rig.rel_off[ic]+rest@rig.rel_off[iu]
   elev=max(0,min(22,(targets[s][2]-est[2]+.12)*65))
   angle=(1 if s=='L' else -1)*math.radians(elev)
   put(ic,kin.axis_angle(F_W,angle)@rest);shoulders[s]=Pos[ic]+Q[ic]@rig.rel_off[iu]
  # Common handle projection, rather than independently detaching either hand.
  original=h.copy();release=float(p.get('release',0));trail='R' if sign>0 else 'L'
  for _ in range(64):
   for s in 'LR':
    if s==trail and release>.999:continue
    target=h+rot@anchors[s][:3,3];delta=target-shoulders[s];dist=np.linalg.norm(delta)
    if dist>(self.a_u+self.a_f)*.991:h-=kin.unit(delta)*(dist-(self.a_u+self.a_f)*.991)
    if dist<self.min_wrist_r+.005:h+=kin.unit(delta)*(self.min_wrist_r+.005-dist)
  for s in 'LR':
   sd='Left' if s=='L' else 'Right';target=h+rot@anchors[s][:3,3]
   if s==trail and release:
    crouch=min(1,abs(float(p.get('pel_drop',0)))/.48)
    free=self.O+kin.a2w(np.array(p['free_hand']) if 'free_hand' in p else (np.array([.12,.35,.82])*(1-crouch)+np.array([.10,.32,.18 if self.rig.tag=='male' else .16])*crouch)*self.scale)
    if sign<0:free[0]=-free[0]
    target=target*(1-release)+free*release
    handFrame=kin.frame_from_yx(kin.a2w([0,.4,-.9]),kin.a2w([sign,0,0]))
    frames[s]=frames[s]@kin.mat_pow(frames[s].T@handFrame,release)
   pole=R_chest@kin.a2w([.32 if s=='R' else -.32,-.18,-.65])
   arm=self._arm_ik(s,shoulders[s],target,pole)
   put(ix[sd+'UpperArm'],arm['Qu']);put(ix[sd+'LowerArm'],arm['Ql']);put(ix[sd+'Hand'],frames[s])
   diag[s+'_short']=float(arm['short']);diag[s+'_near']=float(arm['near'])
  diag['handle_projection_m']=float(np.linalg.norm(h-original))
  self.last_anchors=anchors;self.attached={side:(side!=trail or release<1e-6) for side in 'LR'}
  return dict(handle=h,club_rot=rot,club_contact=h+rot@np.array([0,self.length,0]),sweet=h+rot@np.array([0,self.length,0]))

 def _fingers(self,P,basis,diag):
  # Golf-specific closure (golf grip is smaller than the approved racket grip).
  lead='Left' if self.handedness=='RH' else 'Right';trail='Right' if self.handedness=='RH' else 'Left'
  for sd in (lead,trail):
   side='R' if sd=='Right' else 'L';grips=self.golf_grips if self.handedness=='RH' else self.left_grips;srcside=side
   source=self.grip_R if sd=='Right' else self.grip_Lh
   for digit in ('Index','Middle','Ring','Little','Thumb'):
    for seg in ('Proximal','Intermediate','Distal'):
     nm=sd+digit+seg;base=float(source.get(nm,0))
     extra={'Proximal':10,'Intermediate':13,'Distal':8}[seg]
     a=base+extra
     if grips:
      srcsd='Right' if srcside=='R' else 'Left';a=float(grips[srcside]['angles'][srcsd+digit+seg])
     if digit=='Thumb' and not grips:a={'Proximal':-8,'Intermediate':12,'Distal':8}[seg]
     if sd==trail and digit=='Little' and not self.putting and grips:
      a=grips[srcside].get('overlapAngles',{}).get(('Right' if srcside=='R' else 'Left')+digit+seg,a)
     if sd==lead and digit=='Index' and self.putting and grips:
      a=grips[srcside].get('reverseOverlapAngles',{}).get(('Right' if srcside=='R' else 'Left')+digit+seg,a)
     if sd==trail and float(self.golf.get('release',0)):
      rel=float(self.golf['release']);free={'Proximal':10,'Intermediate':18,'Distal':10}[seg];a=a*(1-rel)+free*rel
     spread=0
     if grips:
      srcsd='Right' if srcside=='R' else 'Left';spread=float(grips[srcside].get('spreads',{}).get(srcsd+digit+seg,0))
     if grips and seg=='Proximal':
      exception='overlapAngles' if sd==trail and digit=='Little' and not self.putting else 'reverseOverlapAngles' if sd==lead and digit=='Index' and self.putting else None
      if exception:spread=float(grips[srcside].get(exception+'Spread',spread))
     axis=np.array(grips[srcside].get('flexAxes',{}).get(nm,[1,0,0])) if grips else np.array([1,0,0]);basis[self.rig.idx[nm]]=kin.rz(math.radians(spread))@kin.axis_angle(axis,math.radians(a))
