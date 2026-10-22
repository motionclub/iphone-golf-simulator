"""60 Hz authoring solve before serialization: quaternion paths and world contact IK.
The source is the authored in-memory pose, not a re-import of the output. Blender poses form
an independent pre-export reference. READY-edge retiming was explicitly authorized by Adnan.
"""
import math,array
import numpy as np
from mathutils import Quaternion,Euler,Matrix,Vector
import bpy
import fbx_curves as FB

def unit(v):return v/max(np.linalg.norm(v),1e-12)
def apply(channels,clip,n,arm,names,M,HR,RC,original_M,tag=None):
 source={k:(np.array(FB.data(c,b'KeyTime'),float)/46186158000.*30,np.array(FB.data(c,b'KeyValueFloat'),float)) for k,c in channels.items()}
 from timeline import source_times
 dest=np.arange((n-1)*2+1)/2;times=source_times(n,clip,dest)
 ix={nm:i for i,nm in enumerate(names)};pbs=arm.pose.bones;mw=arm.matrix_world.copy();mi=mw.inverted();rests={nm:(pbs[nm].parent.bone.matrix_local.inverted()@pbs[nm].bone.matrix_local if pbs[nm].parent else pbs[nm].bone.matrix_local) for nm in names}
 prevEuler={nm:Euler(tuple(np.interp(0,*source[nm,'Lcl Rotation',a])*math.pi/180 for a in 'XYZ'),'XYZ') for nm in names+['Racket_Classic']};values={k:[] for k in source if k[0] in names+['Racket_Classic'] and k[1] in ['Lcl Rotation','Lcl Translation','Lcl Scaling']};expected=[];outHR=[];outRC=[];prevHand={};rolllogs=[];errors=[]
 socket=Matrix((np.linalg.inv(M[0,ix['RightHand']])@HR[0]).tolist())
 def poseAt(i,t,reference=None):
  ref=M if reference is None else reference
  lo=int(t);hi=min(n-1,lo+1);u=t-lo;qa=Matrix(ref[lo,i].tolist()).to_quaternion();qb=Matrix(ref[hi,i].tolist()).to_quaternion();m=qa.slerp(qb,u).to_matrix().to_4x4();m.translation=Vector(((1-u)*ref[lo,i,:3,3]+u*ref[hi,i,:3,3]).tolist());return m
 def objectAt(mm,t):
  lo=int(t);hi=min(n-1,lo+1);u=t-lo;m=Matrix(mm[lo].tolist()).to_quaternion().slerp(Matrix(mm[hi].tolist()).to_quaternion(),u).to_matrix().to_4x4();m.translation=Vector(((1-u)*mm[lo,:3,3]+u*mm[hi,:3,3]).tolist());return m
 def setworld(nm,m):pbs[nm].matrix=mi@m;bpy.context.view_layer.update()
 def wristTwist(q,prev):
  r=q@prev.inverted();a=2*math.atan2(r.y,r.w);return (a+math.pi)%(2*math.pi)-math.pi
 def limb(side,kind,t):
  suffix=['UpperArm','LowerArm','Hand'] if kind=='arm' else ['UpperLeg','LowerLeg','Foot'];u,l,h=[pbs[side+s] for s in suffix];reference=original_M if kind=='leg' else M;wanted=poseAt(ix[h.name],t,reference);pole=np.array(poseAt(ix[l.name],t,reference).translation);target=np.array(wanted.translation)
  if tag=='male' and clip=='Intro_Pushups' and kind=='arm' and side=='Left':
   for aa,bb in [(3,10),(71,82)]:
    if aa<t<bb:pole[1]-=.10*math.sin(math.pi*(t-aa)/(bb-aa))**2
  if clip=='Emote_Scuba' and kind=='arm' and side=='Left' and 16<=t<=112:
   originalHand=poseAt(ix['LeftHand'],t,original_M);headMoved=(mw@pbs['Head'].matrix)@poseAt(ix['Head'],t,original_M).inverted()@originalHand
   release_u=float(np.clip((t-104)/8,0,1));weight=1-release_u*release_u*(3-2*release_u)
   wanted=originalHand.to_quaternion().slerp(headMoved.to_quaternion(),weight).to_matrix().to_4x4();wanted.translation=originalHand.translation.lerp(headMoved.translation,weight);target=np.array(wanted.translation)
  if clip=='Intro_Pushups' and kind=='arm' and side=='Right' and 0<dest[f]<7:
   ready=poseAt(ix['RightHand'],0,original_M).to_quaternion();goal=poseAt(ix['RightHand'],9,original_M).to_quaternion();delta=goal@ready.inverted();angle=delta.angle;angle=angle-2*math.pi if angle>math.pi else angle;counter=Quaternion(delta.axis,-math.copysign(math.radians(10),angle))@ready;nf=dest[f]
   if nf<=3:
    blend=nf/3;blend=blend*blend*(3-2*blend);orientation=ready.slerp(counter,blend)
   else:
    blend=(nf-3)/4;blend=blend*blend*(3-2*blend);orientation=counter.slerp(wanted.to_quaternion(),blend)
   position=wanted.translation.copy();wanted=orientation.to_matrix().to_4x4();wanted.translation=position;target=np.array(position)
  S=np.array(mw@u.head);a=(l.bone.head_local-u.bone.head_local).length;b=(h.bone.head_local-l.bone.head_local).length;d=target-S;L=np.linalg.norm(d)
  if clip=='Emote_Scuba' and kind=='arm' and side=='Right' and 16<=t<=104:
   minimum=.994*(a+b);target=S+unit(d)*max(L,minimum);d=target-S;L=np.linalg.norm(d)
   wantedRotation=(mw@pbs['Hips'].matrix).to_quaternion()@poseAt(ix['Hips'],t,original_M).to_quaternion().inverted()@poseAt(ix['RightHand'],t,original_M).to_quaternion();wanted=wantedRotation.to_matrix().to_4x4();wanted.translation=Vector(target.tolist())
  if clip=='Emote_Scuba' and kind=='arm' and side=='Left' and 16<=t<=112 and L>a+b-1e-7:
   correction=unit(d)*(L-(a+b-1e-7));shoulder=mw@pbs['LeftShoulder'].matrix;shoulder.translation+=Vector(correction.tolist());setworld('LeftShoulder',shoulder);S=np.array(mw@u.head);d=target-S;L=np.linalg.norm(d)
  reach=min(max(L,abs(a-b)+1e-6),a+b-1e-7);direction=unit(d);w=S+direction*reach;v=pole-S;v=unit(v-direction*np.dot(v,direction))
  if np.linalg.norm(v)<.01:v=unit(np.cross(direction,[1,0,0]))
  along=(a*a+reach*reach-b*b)/(2*reach);height=math.sqrt(max(0,a*a-along*along));e=S+direction*along+v*height
  for pb,head,tail in [(u,S,e),(l,e,w)]:
   yy=unit(tail-head);src=poseAt(ix[pb.name],t,reference).to_quaternion();ori=(src@Vector((0,1,0))).rotation_difference(Vector(yy.tolist()))@src
   if kind=='arm' and pb==l and h.name in prevHand:
    rq=rests[h.name].to_quaternion().inverted();handWorld=wanted.to_quaternion();previous=prevHand[h.name]
    def candidate(beta,baseOri=ori):return rq@(Quaternion(Vector(yy.tolist()),beta)@baseOri).inverted()@handWorld
    beta=0.;tw=wristTwist(candidate(beta),previous);target_tw=float(np.clip(tw,-math.radians(12),math.radians(12)))
    if abs(tw)>math.radians(12):
     for it in range(8):
      value=wristTwist(candidate(beta),previous);err=(value-target_tw+math.pi)%(2*math.pi)-math.pi
      if abs(err)<1e-5:break
      eps=1e-3;dvalue=(wristTwist(candidate(beta+eps),previous)-value+math.pi)%(2*math.pi)-math.pi
      if abs(dvalue)<1e-6:break
      beta-=float(np.clip(err/(dvalue/eps),-.5,.5))
     ori=Quaternion(Vector(yy.tolist()),beta)@ori;rolllogs.append(dict(frame60=int(round(t*2)),bone=pb.name,roll_deg=beta*180/math.pi,wrist_increment_before_deg=tw*180/math.pi,wrist_increment_after_deg=wristTwist(candidate(beta),previous)*180/math.pi))
   mm=ori.to_matrix().to_4x4();mm.translation=Vector(head.tolist());setworld(pb.name,mm)
  wanted.translation=Vector(w.tolist());setworld(h.name,wanted)
  if kind=='arm':prevHand[h.name]=rests[h.name].to_quaternion().inverted()@(mw@l.matrix).to_quaternion().inverted()@wanted.to_quaternion()
  else:setworld(side+'Toes',poseAt(ix[side+'Toes'],t,original_M))
  errors.append(dict(frame60=int(round(t*2)),bone=h.name,error_mm=float(np.linalg.norm(w-target)*1000)))
 from arc_rounding import solve as round_arc
 nativeframes=np.arange(n);native_times=source_times(n,clip,nativeframes);headlen=pbs['Head'].bone.length
 headpath=np.array([np.array(poseAt(ix['Head'],tt).translation)+np.array(poseAt(ix['Head'],tt).col[1][:3])*headlen for tt in native_times]);headlock=np.zeros(n,bool);headlock[[0,-1]]=True;head_goals,head_arc_log=round_arc(headpath,headlock)
 for f,t in enumerate(times):
  lo=int(t);hi=min(n-1,lo+1);u=t-lo
  for nm in names:
   qa=Euler(tuple(np.interp(lo,*source[nm,'Lcl Rotation',a])*math.pi/180 for a in 'XYZ'),'XYZ').to_quaternion();qb=Euler(tuple(np.interp(hi,*source[nm,'Lcl Rotation',a])*math.pi/180 for a in 'XYZ'),'XYZ').to_quaternion();local=qa.slerp(qb,u).to_matrix().to_4x4();local.translation=Vector(tuple(np.interp(t,*source[nm,'Lcl Translation',a]) for a in 'XYZ'))
   for j,a in enumerate('XYZ'):
    scale=np.interp(t,*source[nm,'Lcl Scaling',a]) if (nm,'Lcl Scaling',a) in source else 1
    for i in range(3):local[i][j]*=float(scale)
   pbs[nm].matrix_basis=rests[nm].inverted()@local
  bpy.context.view_layer.update()
  if f not in [0,len(times)-1]:
   headWanted=Vector([float(np.interp(dest[f],nativeframes,head_goals[:,j])) for j in range(3)]);headNow=mw@pbs['Head'].matrix;headTopNow=headNow.translation+headNow.col[1].to_3d()*headlen;headDelta=headWanted-headTopNow;neck=mw@pbs['Neck'].matrix;neck.translation+=headDelta;setworld('Neck',neck)
   for side in ['Left','Right']:
    limb(side,'leg',t)
    if clip in ['Emote_Spike','Emote_Scuba','Emote_Thrust','Intro_Pushups']:setworld(side+'Shoulder',poseAt(ix[side+'Shoulder'],t))
    if side!='Left' or clip not in ['Intro_Wave','Intro_BringIt']:limb(side,'arm',t)
  else:
   for side in ['Left','Right']:
    hh=pbs[side+'Hand'];prevHand[hh.name]=rests[hh.name].to_quaternion().inverted()@hh.parent.matrix.to_quaternion().inverted()@hh.matrix.to_quaternion()
  posed=np.array([np.array(mw@pbs[nm].matrix) for nm in names]);grip=(mw@pbs['RightHand'].matrix)@socket;attached=not (clip=='Emote_Scuba' and 6<=t<123 or clip=='Intro_Pushups' and 13<=t<73);racket=grip.copy() if attached else objectAt(RC,t)
  if f%2==0:expected.append(posed);outHR.append(np.array(grip));outRC.append(np.array(racket))
  for nm in names+['Racket_Classic']:
   world=mw@pbs[nm].matrix if nm in ix else racket;parent=mw@pbs[nm].parent.matrix if nm in ix and pbs[nm].parent else mw if nm in ix else grip;local=parent.inverted()@world;eu=local.to_quaternion().to_euler('XYZ',prevEuler[nm]);prevEuler[nm]=eu
   for j,a in enumerate('XYZ'):
    if (nm,'Lcl Rotation',a) in values:values[nm,'Lcl Rotation',a].append(float(eu[j]*180/math.pi))
    if (nm,'Lcl Translation',a) in values:values[nm,'Lcl Translation',a].append(float(local.translation[j]))
    if (nm,'Lcl Scaling',a) in values:values[nm,'Lcl Scaling',a].append(float(np.interp(t,*source[nm,'Lcl Scaling',a])))
 endpoint_raw_preservation=[]
 # Restore original endpoint values only within the same continuous Euler chart.
 # A 180/360 degree chart switch remains an explicit failure; never bridge it with a spin.
 for nm in names+['Racket_Classic']:
  keys=[(nm,'Lcl Rotation',a) for a in 'XYZ']
  if all(k in values for k in keys):
   for endpoint in [0,-1]:
    original=np.array([source[k][1][endpoint] for k in keys]);current=np.array([values[k][endpoint] for k in keys]);samechart=bool(np.max(abs(original-current))<.001)
    if samechart:
     for j,k in enumerate(keys):values[k][endpoint]=float(original[j])
    endpoint_raw_preservation.append(dict(bone=nm,endpoint=endpoint,rotation_preserved=samechart,chart_delta_deg=(current-original).tolist()))
 for k in values:
  if k[1] in ['Lcl Translation','Lcl Scaling']:
   values[k][0]=float(source[k][1][0]);values[k][-1]=float(source[k][1][-1])
 for k,vals in values.items():
  vals=np.array(vals);c=channels[k];count=len(vals);sec=np.diff(vals)*60;slopes=np.zeros(count);slopes[0]=sec[0];slopes[-1]=sec[-1]
  for j in range(1,count-1):
   a,b=sec[j-1:j+1];slopes[j]=2*a*b/(a+b) if a*b>0 else 0
  tangent=np.zeros((count,4));tangent[:,0]=slopes;tangent[:-1,1]=slopes[1:];tangent[-1,1]=slopes[-1]
  for key,value in [(b'KeyTime',array.array('l',np.rint(dest/30*46186158000.).astype(np.int64).tolist())),(b'KeyValueFloat',array.array('f',vals.tolist())),(b'KeyAttrFlags',array.array('i',[(1<<3)|(1<<10)|(1<<12)|(1<<14)]*count)),(b'KeyAttrDataFloat',array.array('f',tangent.ravel().tolist())),(b'KeyAttrRefCount',array.array('i',[1]*count))]:FB.assign(c,key,value)
 return np.array(expected),np.array(outHR),np.array(outRC),dict(destination_frames=dest.tolist(),source_frames=times.tolist(),rotation_rate_hz=60,ready_retime_authorized=True,world_contact_solve_hz=60,ik_error_max_mm=max(x['error_mm'] for x in errors),ik=errors,forearm_roll=rolllogs,head_arc_destination=head_arc_log,endpoint_raw_preservation=endpoint_raw_preservation)
