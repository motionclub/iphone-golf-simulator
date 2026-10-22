"""Bake all 24 families × two handednesses onto one immutable hero skeleton.
Run with a rollback draft open. Produces a master, traces, and explicit manifest.
"""
import bpy,sys,json,math,hashlib
from pathlib import Path
import numpy as np
from mathutils import Matrix,Vector
W=Path(__file__).resolve().parents[1];R=W.parents[1]
sys.path.insert(0,str(R/'work/match-anim-set/scripts'))
sys.path.insert(0,str(W/'scripts'))
import kin,motions
from golf_solver import GolfSolver

sex=sys.argv[sys.argv.index('--')+1];tag=sex.lower();rig=bpy.data.objects['Rig_'+sex]
sc=bpy.context.scene;sc.render.fps=120;sc.render.fps_base=1
bpy.context.preferences.filepaths.save_version=0
prefixes=tuple(f'{family}_{sex}_{hand}' for family in motions.FAMILIES for hand in ('RH','LH'))
for action in list(bpy.data.actions):
 if action.name.startswith(prefixes):bpy.data.actions.remove(action,do_unlink=True)
for o in list(bpy.data.objects):
 if o.name.startswith(('GolfClub','GolfHandle','GolfShaft','GolfBallContactReference','Review_')):bpy.data.objects.remove(o,do_unlink=True)
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.location=(0,0,0);pb.scale=(1,1,1)
rig.data.pose_position='POSE';rig.animation_data_create();rig.animation_data.action=None
for tr in list(rig.animation_data.nla_tracks):rig.animation_data.nla_tracks.remove(tr)
src=R/'work/match-anim-set/data'
rd=json.loads((src/f'rig_{tag}.json').read_text())
by={b.name:b for b in rig.data.bones}
for b in rd['bones']:
 actual=by[b['name']]
 if np.max(np.abs(np.array(actual.matrix_local)-np.array(b['matrix_local'])))>1e-5:raise RuntimeError('Rest transform mismatch: '+b['name'])
k=kin.Rig(rd);s=GolfSolver(k,json.loads((src/f'racket_{tag}.json').read_text()),json.loads((src/f'hands_{tag}.json').read_text()))

def fingerprint(o):
 return hashlib.sha256(repr(([(tuple(v.co),[(g.group,g.weight) for g in v.groups]) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])).encode()).hexdigest()
base={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('Body_','Face_','Hair_'))}
rest={b.name:list(map(list,b.matrix_local)) for b in rig.data.bones}

# Rollback garments remain in the file; approved tennis references stay hidden.
for o in bpy.data.objects:
 if o.type=='MESH' and (o.name.startswith('Kit_') or o.name in ('Grip','ButtCap','StringBed','Racket_Classic','Collider_Racket')):o.hide_render=True;o.hide_set(True)
 if o.type=='MESH' and o.name=='Golf_Glove_Right':o.hide_render=True

def mat(name,rgb,roughness,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*rgb,1)
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*rgb,1);bs.inputs['Roughness'].default_value=roughness;bs.inputs['Metallic'].default_value=metal
 return m
rubber=mat('GolfEquipment_Grip',(.018,.020,.022),.70);steel=mat('GolfEquipment_Shaft',(.38,.40,.43),.23,.9);headmat=mat('GolfEquipment_Head',(.05,.055,.06),.25,.65)
club=bpy.data.objects.new('GolfClub',None);sc.collection.objects.link(club);club.empty_display_type='ARROWS';club.rotation_mode='QUATERNION'
def cylinder(name,r,depth,y,material):
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=depth,location=(0,y,0),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name=name
 o.data.materials.append(material);o.parent=club
 for p in o.data.polygons:p.use_smooth=True
 return o
cylinder('GolfHandle',.014,.29,.00,rubber);cylinder('GolfShaft',.004,.84,.54,steel)
for equipment,size in [('Iron',(.085,.035,.024)),('Driver',(.110,.090,.075)),('Wedge',(.082,.045,.028)),('Putter',(.105,.034,.022))]:
 bpy.ops.mesh.primitive_cube_add(size=1,location=(0,.96,-size[2]/2));head=bpy.context.object;head.name='GolfClubFace'+('' if equipment=='Iron' else '_'+equipment);head.scale=size;head.data.materials.append(headmat);head.parent=club
 # Rounded bodies retain a planar face through the authored contact origin.
 bpy.context.view_layer.objects.active=head;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 bevel=head.modifiers.new('Club head edge radius','BEVEL');bevel.width=.004 if equipment=='Driver' else .002;bevel.segments=3;bpy.ops.object.modifier_apply(modifier=bevel.name)
 head.hide_render=equipment!='Iron';head['GolfEquipment']=equipment.lower()

contact=bpy.data.objects.new('GolfClubContact',None);sc.collection.objects.link(contact);contact.parent=club;contact.location=(0,.96,0)
ball=bpy.data.objects.new('GolfBallContactReference',None);sc.collection.objects.link(ball);ball.empty_display_type='SPHERE';ball.empty_display_size=.02135

def curve(act,obj,path,index,values):
 f=act.fcurve_ensure_for_datablock(obj,path,index=index);n=len(values);f.keyframe_points.add(n)
 co=np.empty(n*2);co[0::2]=np.arange(n);co[1::2]=values;f.keyframe_points.foreach_set('co',co)
 for p in f.keyframe_points:p.interpolation='LINEAR'
 f.update()

manifest=[];traces={};controls={};metrics=[]
for hand in ('RH','LH'):
 for family in motions.FAMILIES:
  d=motions.definition(family);duration=d['duration'];times=np.arange(round(duration*120)+1)/120
  n=len(times);q=np.empty((n,k.n,4));hl=np.empty((n,3));cq=np.empty((n,4));cp=np.empty((n,3));drift=[];projection=[];contacts=[];correctives=[]
  s.reset()
  for j,t in enumerate(times):
   p=motions.controls(d,float(t),s.scale);B,loc,info=s.evaluate(p,hand,d['length'],d['equipment']=='putter');Q,Pos=k.fk(B,loc)
   for bi in range(k.n):
    q[j,bi]=kin.mat_to_quat(B[bi])
    if j and np.dot(q[j,bi],q[j-1,bi])<0:q[j,bi]*=-1
   hl[j]=loc;cp[j]=info['handle'];cq[j]=kin.mat_to_quat(info['club_rot'])
   if j and np.dot(cq[j],cq[j-1])<0:cq[j]*=-1
   drift.append(max(np.linalg.norm(Pos[k.idx[sd+'Hand']]-(cp[j]+info['club_rot']@s.last_anchors[side][:3,3])) for side,sd in [('L','Left'),('R','Right')] if s.attached[side]))
   projection.append(info['handle_projection_m']);contacts.append(info['club_contact'])
   correctives.append([min(1,abs(float(p['pel_rot'][0]))/72),min(1,abs(float(p['pel_drop']))/.16)])
  if d['loop']:
   q[-1]=q[0];hl[-1]=hl[0];cp[-1]=cp[0];cq[-1]=cq[0];correctives[-1]=correctives[0]
  ident=f'{family}_{sex}_{hand}';a=bpy.data.actions.new(ident);a.use_fake_user=True;rig.animation_data.action=a
  for bi,nm in enumerate(k.names):
   if nm=='Root':continue
   for c in range(4):curve(a,rig,f'pose.bones["{nm}"].rotation_quaternion',c,q[:,bi,c])
  for c in range(3):curve(a,rig,'pose.bones["Hips"].location',c,hl[:,c])
  a.use_frame_range=True;a.frame_start=0;a.frame_end=n-1
  for marker,t in [('Address',0),('Top',d['top']),('Impact',d['impact']),('Recovery',d['recovery']),('Finish',duration)]:
   if t is not None:a.pose_markers.new(marker).frame=round(t*120)
  track=rig.animation_data.nla_tracks.new();track.name=ident;track.mute=True;track.strips.new(ident,0,a)
  ca=bpy.data.actions.new(ident+'_Equipment');ca.use_fake_user=True;club.animation_data_create();club.animation_data.action=ca
  for c in range(3):curve(ca,club,'location',c,cp[:,c])
  for c in range(4):curve(ca,club,'rotation_quaternion',c,cq[:,c])
  ca.use_frame_range=True;ca.frame_start=0;ca.frame_end=n-1
  ct=club.animation_data.nla_tracks.new();ct.name=ident;ct.mute=True;ct.strips.new(ident,0,ca)
  contactError=None
  if d['impact'] is not None:
   wanted=k.root_origin+kin.a2w(d['ball']*s.scale)
   if hand=='LH':wanted[0]*=-1
   contactError=float(np.linalg.norm(contacts[round(d['impact']*120)]-wanted))
  item=dict(id=ident,motion=family,body=tag,handedness='right' if hand=='RH' else 'left',duration=duration,loop=d['loop'],backswingTop=d['top'],impact=d['impact'],recovery=d['recovery'],equipment=d['equipment'],clubLength=d['length']*s.scale,fps=120,frames=n,correctiveTracks=['GolfHipTwist','GolfThighLift'],animationAction=ident,equipmentAction=ca.name,rootMotion=False)
  manifest.append(item);traces[ident+'_quats']=q.astype('f4');traces[ident+'_hips']=hl.astype('f4');traces[ident+'_clubPosition']=cp.astype('f4');traces[ident+'_clubQuats']=cq.astype('f4');traces[ident+'_correctives']=np.array(correctives,'f4')
  metrics.append(dict(id=ident,samples=n,handDriftMaxM=max(drift),handleProjectionMaxM=max(projection),contactErrorM=contactError,finite=bool(np.isfinite(q).all() and np.isfinite(hl).all()),quaternionNormError=float(np.max(np.abs(np.linalg.norm(q,axis=-1)-1)))))
  controls[family]=d
  print('BAKE',ident,n,'drift_mm',round(max(drift)*1000,5),'contact_mm',None if contactError is None else round(contactError*1000,3),flush=True)

# Named studio views are part of each editable master.
for i in range(8):
 angle=i*math.pi/4;name=f'Review_{i*45:03d}';data=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,data);sc.collection.objects.link(o)
 o.location=(3.5*math.sin(angle),-3.5*math.cos(angle),1.15);o.rotation_euler=(Vector((0,0,.90))-o.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=2.2
for name,pos,target,scale in [('Review_Overhead',(0,0,4),(0,0,0),2.5),('Review_Hands',(0,-2,1.1),(0,-.4,.9),.42),('Review_Waist',(0,-2,.85),(0,0,.85),.72)]:
 data=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=scale
sc.camera=bpy.data.objects['Review_000'];sc.frame_start=0;sc.frame_end=408
rig.animation_data.action=bpy.data.actions[f'Drive_{sex}_RH'];club.animation_data.action=bpy.data.actions[f'Drive_{sex}_RH_Equipment'];sc.frame_set(0)
now={name:fingerprint(bpy.data.objects[name]) for name in base}
assert base==now,'Body or face geometry/weights changed'
assert rest=={b.name:list(map(list,b.matrix_local)) for b in rig.data.bones},'Rest transforms changed'
def serial(o):return o.tolist() if isinstance(o,np.ndarray) else float(o) if isinstance(o,np.generic) else o
(W/f'data/controls_{sex}.json').write_text(json.dumps(controls,default=serial,indent=2)+'\n')
(W/f'data/animation_check_{sex}.json').write_text(json.dumps(dict(immutableBodies=base,immutableSkeleton=True,metrics=metrics),indent=2)+'\n')
(W/f'export/golf_manifest_{sex}.json').write_text(json.dumps(dict(version=1,skeleton='hero-articulated-v1',body=tag,clips=manifest),indent=2)+'\n')
np.savez_compressed(W/f'data/animations_{sex}.npz',**traces)
bpy.ops.wm.save_as_mainfile(filepath=str(W/f'export/Golf_{sex}_Master.blend'),compress=True)
print('MASTER_COMPLETE',sex,len(manifest),flush=True)
