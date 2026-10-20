"""Editable golf control tracks. Metres in the hero (right, forward, up) frame.

These controls are solved on the current rest rig, never the V4 skeleton.
LH controls are evaluated explicitly with left as trail and right as lead.
"""
import math
import numpy as np
import kin
from pose import frame_from_axes

FAMILIES = ['NeutralIdle','AddressDriver','AddressIron','AddressWedge','AddressPutt',
 'Waggle','AimLeft','AimRight','Drive','IronSwing','HalfSwing','Pitch','Chip',
 'BunkerShot','Putt','SwingAbort','Recovery','WalkStart','WalkLoop','WalkStop',
 'BallPickup','TeePlacement','GoodShot','Disappointed']
SHOTS = {'Drive':(3.4,1.55,1.92,1.08,1.), 'IronSwing':(3.1,1.4,1.72,.96,.92),
 'HalfSwing':(2.5,1.05,1.35,.96,.58),'Pitch':(2.35,.95,1.25,.90,.46),
 'Chip':(1.95,.75,1.05,.90,.24),'BunkerShot':(2.65,1.1,1.45,.90,.66),
 'Putt':(2.0,.8,1.15,.84,.10)}

def frame(shaft, face):
 return frame_from_axes(kin.a2w(shaft), kin.a2w(face))

def key(t, pos, shaft, pel=(0,15,0), chest=(0,14,0), heel=0, face=(-1,0,0), **kw):
 return dict(t=t,handle=np.asarray(pos,float),orientation=kin.mat_to_quat(frame(shaft,face)),
             pel_rot=np.asarray(pel,float),chest_rot=np.asarray(chest,float),heel=float(heel),**kw)

def address(equipment='iron'):
 length={'driver':1.08,'iron':.96,'wedge':.90,'putter':.84}[equipment]
 ball=np.array([-.12 if equipment=='driver' else -.04,{'driver':.90,'iron':.80,'wedge':.75,'putter':.70}[equipment],.022])
 shaft=kin.unit(np.array([.035,.52,-1.]))
 # Face meets the back of a regulation ball, not its centre.
 ball=ball+np.array([.02135,0,0])
 h=ball-shaft*length
 return key(0,h,shaft,pel=(0,20,0),chest=(0,20,0),pel_drop=-.07 if equipment=='putter' else -.02),length,ball

def definition(name):
 equipment='putter' if name in ('Putt','AddressPutt') else 'driver' if name in ('Drive','AddressDriver') else 'wedge' if name in ('Pitch','Chip','BunkerShot','AddressWedge') else 'iron'
 a,length,ball=address(equipment);loop=name in ('NeutralIdle','Waggle','WalkLoop') or name.startswith('Address')
 d=dict(family=name,equipment=equipment,length=length,ball=ball,loop=loop,duration=2.4,top=None,impact=None,recovery=None,keys=[])
 def cp(t,**kw):
  k=dict(a);k['t']=t;k.update(kw);return k
 if name in SHOTS:
  dur,top,impact,length,amp=SHOTS[name];d.update(duration=dur,top=top,impact=impact,length=length,recovery=dur-.45)
  if name=='Putt':
   # Pendulum, quiet pelvis, reverse-overlap hands; identical face at contact.
   d['keys']=[cp(0),cp(top,handle=a['handle']+[.12,0,.018]),cp(impact),cp(impact+.28,handle=a['handle']+[-.15,0,.02]),cp(dur,handle=a['handle']+[-.10,0,.013])]
  else:
   h=a['handle']; pback=np.array([.48,.34,1.50]); pfinish=np.array([-.28,.22,1.40])
   b=h+(pback-h)*amp;f=h+(pfinish-h)*amp
   rb=kin.qslerp(a['orientation'],kin.mat_to_quat(frame([-.95,.10,.12],[0,-1,0])),amp)
   rf=kin.qslerp(a['orientation'],kin.mat_to_quat(frame([.86,.10,-.49],[0,1,0])),amp)
   d['keys']=[cp(0),cp(top*.45,handle=h+[.19*amp,-.06,.12*amp],pel_rot=np.array([22*amp,15,0]),chest_rot=np.array([30*amp,14,-4*amp])),
    cp(top,handle=b,orientation=rb,pel_rot=np.array([40*amp,12,0]),chest_rot=np.array([48*amp,12,-5*amp])),
    cp(top+(impact-top)*.40,handle=b+[0,.025,-.09*amp],orientation=rb,pel_rot=np.array([12*amp,14,0]),chest_rot=np.array([40*amp,13,-3*amp])),
    cp(impact-.10,handle=h+[.09*amp,0,.09*amp],pel_rot=np.array([-28*amp,20,0]),chest_rot=np.array([8*amp,20,3*amp]),heel=12*amp),
    cp(impact,pel_rot=np.array([-36*amp,20,0]),chest_rot=np.array([6*amp,20,5*amp]),heel=18*amp),
    cp(impact+.22,handle=h+[-.28*amp,0,.27*amp],orientation=kin.qslerp(a['orientation'],rf,.70),pel_rot=np.array([-60*amp,10,0]),chest_rot=np.array([-18*amp,10,4*amp]),heel=38*amp),
    cp(dur-.45,handle=f,orientation=rf,pel_rot=np.array([-72*amp,3,0]),chest_rot=np.array([-30*amp,3,0]),heel=48*amp),
    cp(dur,handle=f,orientation=rf,pel_rot=np.array([-72*amp,3,0]),chest_rot=np.array([-30*amp,3,0]),heel=48*amp)]
   if name=='BunkerShot':
    for k in d['keys']:k['stance']=.54;k['pel_drop']=-.045
 elif name=='NeutralIdle':
  k=key(0,[-.28,.06,.90],[-.45,.06,-.89],pel=(0,0,0),chest=(0,0,0),release=1,stance=.34)
  b=dict(k);b['t']=1.2;b['handle']=k['handle']+np.array([0,0,.004]);c=dict(k);c['t']=2.4;d['keys']=[k,b,c]
 elif name.startswith('Address'):
  d['keys']=[cp(0),cp(1.2,handle=a['handle']+[0,0,.004],chest_rot=np.array([0,20.3,0])),cp(2.4)]
 elif name=='Waggle':
  d['keys']=[cp(0),cp(.6,handle=a['handle']+[.018,0,.012],orientation=kin.qslerp(a['orientation'],kin.mat_to_quat(frame([.18,.57,-.79],[-1,0,0])),1)),cp(1.2),cp(1.8,handle=a['handle']+[-.018,0,.012]),cp(2.4)]
 elif name in ('AimLeft','AimRight'):
  angle=-20 if name=='AimLeft' else 20
  d['duration']=1.2;d['keys']=[cp(0),cp(.6,aim=angle),cp(1.2,aim=angle)]
 elif name in ('SwingAbort','Recovery'):
  src=definition('IronSwing');k=dict(src['keys'][2 if name=='SwingAbort' else -1]);k['t']=0
  d['duration']=1.3;d['keys']=[k,cp(1.3)]
 elif name.startswith('Walk'):
  d['duration']=1.2 if name=='WalkLoop' else .75
  d['keys']=[cp(0),cp(d['duration'])];d['walk']=name
 elif name in ('BallPickup','TeePlacement'):
  hold=np.array([-.27,.15,1.0]);upright=kin.mat_to_quat(frame([0,0,-1],[-1,0,0]))
  d['duration']=2.2;d['keys']=[cp(0),cp(.40,handle=hold,orientation=upright,release=1),cp(.95,handle=np.array([-.30,.10,.665]),orientation=kin.mat_to_quat(frame([-.75,0,-.66],[-1,0,0])),pel_rot=np.array([0,35,0]),chest_rot=np.array([0,45,0]),pel_drop=-.48,release=1),cp(1.35,handle=np.array([-.30,.10,.665]),orientation=kin.mat_to_quat(frame([-.75,0,-.66],[-1,0,0])),pel_rot=np.array([0,35,0]),chest_rot=np.array([0,45,0]),pel_drop=-.48,release=1),cp(1.85,handle=hold,orientation=upright,release=1),cp(2.2)]
 elif name=='GoodShot':
  d['duration']=2.3;d['keys']=[cp(0),cp(.75,handle=np.array([-.24,.18,1.28]),pel_rot=np.array([-20,2,0]),chest_rot=np.array([-10,2,0]),reaction=1),cp(1.35,handle=np.array([-.24,.18,1.31]),reaction=1),cp(2.3)]
 elif name=='Disappointed':
  d['duration']=2.2;d['keys']=[cp(0),cp(.8,handle=a['handle']+[0,-.05,-.06],head=20),cp(1.4,handle=a['handle']+[0,-.05,-.06],head=20),cp(2.2)]
 return d

def controls(d,t,scale=1.):
 keys=d['keys'];i=next((i for i in range(len(keys)-1) if keys[i+1]['t']>=t),len(keys)-2)
 a,b=keys[i:i+2];u=max(0,min(1,(t-a['t'])/(b['t']-a['t'])));u=u*u*(3-2*u)
 p={}
 for n,default in dict(handle=None,orientation=None,pel_rot=None,chest_rot=None,heel=0,aim=0,pel_drop=0,release=0,reaction=0,head=0,stance=.46).items():
  av=a.get(n,default);bv=b.get(n,default)
  p[n]=kin.qslerp(av,bv,u) if n=='orientation' else np.asarray(av)*(1-u)+np.asarray(bv)*u
 p['handle']=p['handle']*scale
 p['orientation']=kin.quat_to_mat(p['orientation'])
 if float(p['aim']):
  rot=kin.rz(-math.radians(float(p['aim'])));p['orientation']=rot@p['orientation'];p['handle']=kin.w2a(rot@kin.a2w(p['handle']))
 p['pel_rot'][0]+=p['aim'];p['chest_rot'][0]+=0
 p['walk_phase']=0.;p['walk_amp']=0.
 if d.get('walk'):
  ph=2*math.pi*t/1.2;p['walk_phase']=ph
  amp=1 if d['walk']=='WalkLoop' else math.sin(min(1,t/d['duration'])*math.pi/2) if d['walk']=='WalkStart' else math.cos(min(1,t/d['duration'])*math.pi/2)
  p['walk_amp']=amp;p['pel_drop']=.025*math.cos(2*ph)*amp;p['pel_rot']=np.array([4*math.sin(ph)*amp,2,0]);p['chest_rot']=np.array([-8*math.sin(ph)*amp,2,0]);p['handle']=np.array([-.28,.08,.90])*scale;p['orientation']=frame([-.40,.08,-.88],[-1,0,0]);p['release']=1.;p['free_hand']=np.array([.24,.02+.08*math.sin(ph)*amp,.90])*scale
 if d['family']=='NeutralIdle':p['free_hand']=np.array([.24,.02,.92])*scale
 return p
