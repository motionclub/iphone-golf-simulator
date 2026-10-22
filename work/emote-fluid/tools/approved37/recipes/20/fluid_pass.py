"""Rerunnable offline polish on the existing baked keys, with protected contacts.
blender -b --factory-startup --python fluid_pass.py -- male|female|both
Writes candidates only. Does not install or modify meshes, bone identities, or gameplay.
"""
import sys,json,math,array,shutil,os
from pathlib import Path
import numpy as np
import bpy
from mathutils import Matrix,Vector,Quaternion
sys.path.insert(0,str(Path(__file__).parent))
from fluid_spec import *
import fbx_curves as FB
W=Path(os.environ.get('FLUID_WORK',str(Path(__file__).resolve().parents[1])))
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def bell(t,a,b):return math.sin(math.pi*(t-a)/(b-a))**2 if a<t<b else 0.
def qs(q,t):
 t=np.clip(t,0,len(q)-1);i=int(t);return Quaternion(tuple(q[i])).slerp(Quaternion(tuple(q[min(len(q)-1,i+1)])),t-i)
def unit(v):return v/max(np.linalg.norm(v),1e-12)
def mat(p,r):
 m=Matrix(r.tolist()).to_4x4();m.translation=Vector(p.tolist());return m

def soften(p,protect,impacts,ranges):
 p=p.copy();n=len(p);log=[]
 stationary=np.zeros(n,dtype=bool);steps=np.linalg.norm(np.diff(p,axis=0),axis=1);stationary[1:-1]=(steps[:-1]<1e-5)|(steps[1:]<1e-5)
 def pinned(f):return stationary[f] or protect[f] or f in impacts or any(a<=f<=b for a,b in ranges)
 for iteration in range(1):
  v=np.diff(p,axis=0);den=np.linalg.norm(v[:-1],axis=1)*np.linalg.norm(v[1:],axis=1)
  ang=np.degrees(np.arccos(np.clip(np.divide(np.sum(v[:-1]*v[1:],axis=1),den,out=np.ones_like(den),where=den>1e-10),-1,1)))
  for f in [i+1 for i,a in enumerate(ang) if a>55 and not any(abs(i+1-k)<=1 for k in impacts)]:
   if pinned(f):continue
   tangent=unit(p[min(n-1,f+2)]-p[max(0,f-2)])
   if np.linalg.norm(tangent)<.01:tangent=unit(v[max(0,f-2)])
   axis=unit(np.cross(tangent,[0,0,1]))
   if np.linalg.norm(axis)<.1:axis=unit(np.cross(tangent,[1,0,0]))
   amp=min(.018,max(.003,np.linalg.norm(v[max(0,f-2):min(len(v),f+2)],axis=1).max()*.75))
   for k in range(max(0,f-3),min(n,f+4)):
    if not pinned(k):p[k]+=axis*amp*math.sin((k-f)*math.pi/4)*math.cos((k-f)*math.pi/8)**2
   log.append(dict(frame=f,kink_before_deg=float(ang[f-1]),offset_m=float(amp)))
 return p,log

def run(tag,clip):
 label=tag.title();z=np.load(W/'data/before'/f'trace_{tag}_{clip}.npz');names=json.loads(str(z['meta']))['bones'];ix={nm:i for i,nm in enumerate(names)};n=len(z['M']);spec=SPEC[clip]
 bpy.ops.wm.open_mainfile(filepath=str(W/'data/before'/f'{label}_{clip}.blend'));sc=bpy.context.scene;arm=next(o for o in sc.objects if o.type=='ARMATURE');f0=int(arm.animation_data.action.frame_range[0]);pbs=arm.pose.bones;mw=arm.matrix_world.copy();mi=mw.inverted()
 # The pose solve needs bones only; original FBX geometry is serialized unchanged.
 for obj in sc.objects:
  if obj.type=='MESH':
   for modifier in obj.modifiers:modifier.show_viewport=False
 M=z['M'];Q=z['Q'];loc=z['LOC'];scales=z['SCALE'];dq=Q.copy();dl=loc.copy();protect=np.zeros(n,dtype=bool);protect[[0,n-1]]=True;offsets=[];settles=[]
 from phase_tracks import build as phase_tracks
 dq,plan_moves,offsets=phase_tracks(Q,names,spec,clip)
 if clip=='Intro_Pushups':
  from phase_tracks import ramp
  from timeline import source_times
  for aa,bb,peak in [(0,9,float(source_times(n,clip,[6])[0])),(74,82,float(source_times(n,clip,[77])[0]))]:
   for f in range(aa,bb+1):
    weight=ramp(f,aa,bb,peak,.9);dl[f,ix['Hips']]=(1-weight)*loc[aa,ix['Hips']]+weight*loc[bb,ix['Hips']]
 for m in spec['moves']:
  b=m['pose']
  if m['stretch']:
   sign=-1 if m['stretch']=='squash' else 1
   for f in range(max(1,b-4),min(n-1,b+5)):
    factor=sign*.06*bell(f,b-5,b+5)
    for nm in ['Spine','Chest','Neck','Head']:
     pb=pbs[nm];v=pb.bone.matrix_local.to_3x3().inverted()@(pb.bone.head_local-pb.parent.bone.head_local);dl[f,ix[nm]]+=np.array(v)*factor
 (W/'proof'/f'plan_{tag}_{clip}.json').write_text(json.dumps(plan_moves,indent=2))
 if clip=='Intro_Wave':
  i=ix['Chest']
  for f in range(1,n-1):
   amount=-2*smooth((f-6)/10)*(1-smooth((f-39)/13));dq[f,i]=np.array(Quaternion((0,0,1),math.radians(amount))@Quaternion(tuple(dq[f,i])))
  for f in range(12,44):
   amount=12*math.cos((f-15)*2*math.pi/12)*smooth((f-11)/4)*(1-smooth((f-39)/4));i=ix['LeftLowerArm'];dq[f,i]=np.array(Quaternion(tuple(dq[f,i]))@Quaternion((1,0,0),math.radians(amount)))
 for a,b in spec['holds']:
  if clip=='Emote_Thrust':continue # Integrated into phase_tracks before the following action.
  if b-a<=15:continue
  i=ix['Chest'];delta=Quaternion(tuple(dq[a,i]))@Quaternion(tuple(dq[max(0,a-1),i])).inverted();axis=delta.axis if delta.angle>1e-5 else Vector((1,0,0))
  for f in range(max(a,8),min(n-1,b+5)):
   if not protect[f]:dq[f,i]=np.array(Quaternion(axis,math.radians(2.4)*np.clip((f-a)/max(1,b-a),0,1)**3*(1-smooth((f-b)/4)))@Quaternion(tuple(dq[f,i])))
 if clip=='Emote_Thrust':
  for f in range(52,min(n-1,73)):
   phase=(f-51)*2*math.pi/10;envelope=bell(f,51,74)
   dq[f,ix['Head']]=np.array(Quaternion(tuple(dq[f,ix['Head']]))@Quaternion((1,0,0),math.radians(1.25)*math.cos(phase)*envelope)@Quaternion((0,0,1),math.radians(2.5)*math.sin(phase)*envelope))
 if clip=='Intro_Wave':
  for f in range(1,n-1):dq[f,ix['RightShoulder']]=np.array(Quaternion(tuple(dq[f,ix['RightShoulder']]))@Quaternion((0,0,1),math.radians(7)*bell(f,7,n-8)))
 for i,nm in enumerate(names):
  if nm.startswith('Left') and any(x in nm for x in ['Thumb','Index','Middle','Ring','Little']) and clip not in ['Emote_Scuba','Intro_Pushups']:
   for f in range(1,n-1):dq[f,i]=qs(Q[:,i],f-1)
 headpath=[]
 for f in range(n):
  sc.frame_set(f0+f)
  for i,nm in enumerate(names):
   pb=pbs[nm];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(tuple(dq[f,i]));pb.location=Vector(dl[f,i]);pb.scale=Vector(scales[f,i])
  bpy.context.view_layer.update();headpath.append(np.array(mw@pbs['Head'].tail))
 headpath=np.array(headpath);headtarget,headarcs=soften(headpath,protect,spec['impacts'],[]);headcorrection=headtarget-headpath
 trails={};arcs={'HeadTop':headarcs}
 for side in ['Left','Right']:
  ranges=[]
  if clip=='Emote_Scuba':ranges=[[16,104]] if side=='Left' else [[120,124]]
  if clip=='Intro_Pushups':ranges=[[13,17],[28,55],[64,74]]
  if clip=='Emote_Thrust':ranges=[[18,20],[35,37],[51,66],[77,91]]
  trails[side],arcs[side]=soften(M[:,ix[side+'Hand'],:3,3],protect,spec['impacts'],ranges)
  if tag=='female' and clip=='Emote_Spike' and side=='Right':
   for f in range(13,22):trails[side][f,1]-=.03*bell(f,12,22)
 arm.animation_data_clear();rk=bpy.data.objects['Racket_Classic'];rk.animation_data_clear();auth=np.zeros_like(M);HR=np.zeros_like(z['HR']);RC=np.zeros_like(z['RC']);errors=[]
 def setworld(nm,m):pbs[nm].matrix=mi@m;bpy.context.view_layer.update()
 def ik(side,target,orient,elbow):
  u,l,h=[pbs[side+s] for s in ['UpperArm','LowerArm','Hand']];S=np.array(mw@u.head);a=(l.bone.head_local-u.bone.head_local).length;b=(h.bone.head_local-l.bone.head_local).length;d=target-S;L=np.linalg.norm(d);reach=min(max(L,abs(a-b)+1e-5),a+b-1e-6);direction=unit(d);w=S+direction*reach;pole=elbow-S;pole=unit(pole-direction*np.dot(pole,direction))
  if np.linalg.norm(pole)<.01:pole=unit(np.cross(direction,[1,0,0]))
  along=(a*a+reach*reach-b*b)/(2*reach);height=math.sqrt(max(0,a*a-along*along));e=S+direction*along+pole*height
  for pb,head,tail in [(u,S,e),(l,e,w)]:
   yy=unit(tail-head);source=Matrix(M[f,ix[pb.name]].tolist()).to_quaternion();source_y=source@Vector((0,1,0));aligned=source_y.rotation_difference(Vector(yy.tolist()))@source;setworld(pb.name,mat(head,np.array(aligned.to_matrix())))
  setworld(h.name,mat(w,orient));return float(np.linalg.norm(w-target))*1000
 for f in range(n):
  sc.frame_set(f0+f)
  for i,nm in enumerate(names):
   pb=pbs[nm];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(tuple(dq[f,i]));pb.location=Vector(dl[f,i]);pb.scale=Vector(scales[f,i])
  bpy.context.view_layer.update()
  if not protect[f]:
   neck=mw@pbs['Neck'].matrix;neck.translation+=Vector(headcorrection[f]);setworld('Neck',neck)
   if clip in ['Emote_Spike','Emote_Scuba','Emote_Thrust','Intro_Pushups']:
    for side in ['Left','Right']:setworld(side+'Shoulder',Matrix(M[f,ix[side+'Shoulder']].tolist()))
   for side in ['Left','Right']:
    if side=='Left' and clip in ['Intro_Wave','Intro_BringIt']:continue
    target=trails[side][f].copy();orient=np.array(Matrix(M[f,ix[side+'Hand']].tolist()).to_quaternion().to_matrix());ef=f
    if clip=='Emote_Scuba' and side=='Left' and 16<=f<=104:
     current=np.array(mw@pbs['Head'].matrix);pinned=current@np.linalg.inv(M[f,ix['Head']])@M[f,ix['LeftHand']];target=pinned[:3,3];orient=np.array(Matrix(pinned.tolist()).to_quaternion().to_matrix());ef=f
    errors.append(dict(frame=f,side=side,error_mm=ik(side,target,orient,M[ef,ix[side+'LowerArm'],:3,3])))
  for i,nm in enumerate(names):auth[f,i]=np.array(mw@pbs[nm].matrix)
  HR[f]=auth[f,ix['RightHand']]@np.linalg.inv(M[f,ix['RightHand']])@z['HR'][f]
  attached=not ((clip=='Emote_Scuba' and 6<=f<123) or (clip=='Intro_Pushups' and 13<=f<73));RC[f]=HR[f]@np.linalg.inv(z['HR'][f])@z['RC'][f] if attached else z['RC'][f]
 raw,version,models,channels=FB.read(W/'rollback/fbx'/f'{label}_{clip}.fbx');parent={nm:(pbs[nm].parent.name if pbs[nm].parent else None) for nm in names};values={};last={}
 for nm in names+['Racket_Classic']:
  if nm=='Root':continue
  rr=[];tt=[]
  from mathutils import Euler
  last[nm]=Euler(tuple(float(FB.data(channels[nm,'Lcl Rotation',ax],b'KeyValueFloat')[0])*math.pi/180 for ax in 'XYZ'),'XYZ')
  for f in range(n):
   m=Matrix(auth[f,ix[nm]].tolist()) if nm in ix else Matrix(RC[f].tolist());pm=Matrix(auth[f,ix[parent[nm]]].tolist()) if nm in ix and parent[nm] else mw if nm in ix else Matrix(HR[f].tolist());local=pm.inverted()@m;eu=local.to_quaternion().to_euler('XYZ',last.get(nm));last[nm]=eu;rr.append([v*180/math.pi for v in eu]);tt.append(list(local.translation))
  values[nm,'Lcl Rotation']=np.array(rr);values[nm,'Lcl Translation']=np.array(tt)
 changed=0
 for (nm,prop,axis),curve in channels.items():
  if nm not in names+['Racket_Classic'] or nm=='Root' or prop not in ['Lcl Rotation','Lcl Translation']:continue
  if nm=='Racket_Classic' and clip not in ['Emote_Scuba','Intro_Pushups']:continue
  old=np.array(FB.data(curve,b'KeyValueFloat'));arr=values[nm,prop][:,'XYZ'.index(axis)].copy()
  if len(old)!=n:raise ValueError((nm,prop,len(old),n))
  arr[protect]=old[protect];time=np.array(FB.data(curve,b'KeyTime'),float)/46186158000.
  nn=len(arr);FB.assign(curve,b'KeyTime',array.array('l',np.rint(time*46186158000.).astype(np.int64).tolist()));FB.assign(curve,b'KeyValueFloat',array.array('f',arr.astype(np.float32).tolist()));changed+=1
  secant=np.diff(arr)/np.diff(time);slopes=np.zeros(nn);slopes[0]=secant[0];slopes[-1]=secant[-1]
  for k in range(1,nn-1):
   aa,bb=secant[k-1:k+1];slopes[k]=2*aa*bb/(aa+bb) if aa*bb>0 else 0
  flags=(1<<3)|(1<<10)|(1<<12)|(1<<14);FB.assign(curve,b'KeyAttrFlags',array.array('i',[flags]*nn));tangent=np.zeros((nn,4),np.float32);tangent[:,0]=slopes;tangent[:-1,1]=slopes[1:];tangent[-1,1]=slopes[-1]
  FB.assign(curve,b'KeyAttrDataFloat',array.array('f',tangent.ravel().tolist()));FB.assign(curve,b'KeyAttrRefCount',array.array('i',[1]*nn))
 from rotation_rekey import apply as rekey_rotations
 auth,HR,RC,retime=rekey_rotations(channels,clip,n,arm,names,auth,HR,RC,M)
 (W/'proof'/f'retime_{tag}_{clip}.json').write_text(json.dumps(retime,indent=2))
 dest=W/'candidate/fbx'/f'{label}_{clip}.fbx';FB.write(dest,raw,version);shutil.copy2(W/'rollback/fbx'/f'{label}_{clip}.fbx.meta',str(dest)+'.meta')
 np.savez_compressed(W/'candidate'/f'authored_{tag}_{clip}.npz',M=auth,HR=HR,RC=RC,frames=n,meta=json.dumps(dict(clip=clip,hero=tag,changed_curves=changed,offsets=offsets,arcs=arcs,ik_error_max_mm=max(x['error_mm'] for x in errors))))
 (W/'proof'/f'ik_{tag}_{clip}.json').write_text(json.dumps(errors,indent=2))
 print('POLISH',tag,clip,'curves',changed,'IK maximum mm',max(x['error_mm'] for x in errors),flush=True)
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:];tags=['male','female'] if not args or args[0]=='both' else [args[0]]
 for tag in tags:
  for clip in (args[1:] or CLIPS):run(tag,clip)
