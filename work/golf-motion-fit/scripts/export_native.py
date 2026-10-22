"""Version 3 native hero export: immutable rig, morph targets, lazy 120 Hz clips.
C maps Blender world (-right, -forward, up) to the native hero frame.
"""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
W=Path(__file__).resolve().parents[1];R=W.parents[1];sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];sc=bpy.context.scene
sys.path.insert(0,str(R/'work/match-anim-set/scripts'));sys.path.insert(0,str(W/'scripts'));import kin,motions
k=kin.Rig(str(R/f'work/match-anim-set/data/rig_{sex.lower()}.json'));names=k.names;idx=k.idx
C=np.array([[-1,0,0],[0,0,1],[0,1,0]],float);C4=np.eye(4);C4[:3,:3]=C
out=W/'native';out.mkdir(exist_ok=True);clipdir=out/'GolfAnimations';clipdir.mkdir(exist_ok=True)
manifest=json.loads((W/f'export/golf_manifest_{sex}.json').read_text());traces=np.load(W/f'data/animations_{sex}.npz');profiles={p['part']:p for p in json.loads((W/f'export/material_profiles_{sex}.json').read_text())}
base=f'AddressIron_{sex}_RH';rig.data.pose_position='POSE';rig.animation_data.action=bpy.data.actions[base];club=bpy.data.objects['GolfClub'];club.animation_data.action=bpy.data.actions[base+'_Equipment']
for tr in rig.animation_data.nla_tracks:tr.mute=True
for tr in club.animation_data.nla_tracks:tr.mute=True
for o in bpy.data.objects:
 if o.type=='MESH' and o.data.shape_keys:
  o.data.shape_keys.animation_data_clear()
  for key in o.data.shape_keys.key_blocks:key.value=0
sc.frame_set(0);bpy.context.view_layer.update()
rest=np.array([np.array(b.matrix_local) for b in rig.data.bones]);restInv=np.linalg.inv(rest)
pose=np.array([np.array(b.matrix) for b in rig.pose.bones]);skin=pose@restInv
source=[o for o in bpy.data.objects if o.type=='MESH' and (o.name.startswith(('Body_','Face_')) or (o.name.startswith('Golf_') and '_High' not in o.name) or o.name.startswith(('GolfHandle','GolfShaft','GolfClubFace')))]
source=sorted(source,key=lambda o:o.name);parts=[];rigparts=[];rigid=[];gearbase={};rigblob=bytearray();blob=bytearray()
old=json.loads((R/f'GolfArcade/Unity/CharacterAssets/MatchHero_{sex}.json').read_text());looks={sub['material']:sub['look'] for p in old['parts'] for sub in p['submeshes']}
def append(arr,buf):
 offset=len(buf);buf.extend(np.ascontiguousarray(arr).tobytes());return offset
def look(role,o,mi):
 if role in looks:result=dict(looks[role])
 else:result=dict(looks['Kit_Shirt'] if o.name in profiles else looks['Skin'])
 if o.name in profiles:
  p=profiles[o.name];result.update(shader='TennisCloth',normalMap='MatchHero_'+p['normalMap'],maskMap='MatchHero_'+p['maskMap'],weaveMap='MatchHero_GolfMotion_FabricAtlas',fabricVersion=2,heroProfile=0,weaveTile=p.get('weaveTile',60),tileMetres=p.get('tileMetres',.026),useGarmentMaps=1,normalStrength=1,weaveAngle=0,exposure=.78 if 'Shoe' in o.name else 1.05)
 if role=='Skin':result['color']=looks['Skin']['color']
 elif role in looks and not o.name.startswith('Golf'):result['color']=looks[role]['color']
 else:
  mat=o.data.materials[mi];bs=mat.node_tree.nodes.get('Principled BSDF') if mat and mat.use_nodes else None
  linear=np.array(bs.inputs['Base Color'].default_value[:3] if bs else (.04,.04,.04));rgb=np.where(linear<=.0031308,12.92*linear,1.055*linear**(1/2.4)-.055)
  result['color']=list(map(float,rgb))+[1]
 if o.name.startswith(('GolfHandle','GolfShaft','GolfClubFace')):result.update(bumpScale=0,bumpMap='',bumpTriplanar=0,smoothness=.7 if o.name!='GolfHandle' else .2)
 if 'Buckle' in o.name:result.update(shader='TennisCharacter',useGarmentMaps=0,bumpScale=0,bumpMap='',bumpTriplanar=0,smoothness=.7)
 if 'Hair' in o.name:result.update(shader='TennisCharacter',smoothness=.12,wrap=.3,rimStrength=.1,subsurface=[0,0,0,1],bumpScale=0,bumpMap='',bumpTriplanar=0)
 return result
for o in source:
 mesh=o.data;mesh.calc_loop_triangles();n=len(mesh.loops);vertex=np.array([l.vertex_index for l in mesh.loops]);P=np.array([v.co[:] for v in mesh.vertices])[vertex];N=np.array([v.vector[:] for v in mesh.corner_normals]);UV=np.array([u.uv[:] for u in mesh.uv_layers.active.data]) if mesh.uv_layers.active else None
 # Corner vertices preserve normal splits and UV seams exactly in both renderers.
 weights=np.zeros((len(mesh.vertices),4),np.float32);indices=np.zeros((len(mesh.vertices),4),np.uint8)
 for v in mesh.vertices:
  row=sorted([(idx[o.vertex_groups[g.group].name],g.weight) for g in v.groups if o.vertex_groups[g.group].name in idx and g.weight>1e-7],key=lambda p:p[1],reverse=True)[:4]
  if not row:row=[(idx['Head'] if ('Face' in o.name or 'Hair' in o.name) else 0,1.)]
  total=sum(w for i,w in row)
  for j,(i,w) in enumerate(row):indices[v.index,j]=i;weights[v.index,j]=w/total
 skinned=not o.name.startswith(('Face_','GolfHandle','GolfShaft','GolfClubFace'))
 world=np.array(o.matrix_world);Pworld=np.einsum('ij,nj->ni',world[:3,:3],P)+world[:3,3];Nworld=N@world[:3,:3].T;Nworld/=np.linalg.norm(Nworld,axis=1)[:,None]
 if skinned:
  Wv=weights[vertex];Iv=indices[vertex];M=(skin[Iv]*Wv[:,:,None,None]).sum(1);ready=np.einsum('nij,nj->ni',M[:,:3,:3],Pworld)+M[:,:3,3];normal=np.einsum('nij,nj->ni',M[:,:3,:3],Nworld);normal/=np.linalg.norm(normal,axis=1)[:,None]
 else:ready=Pworld;normal=Nworld
 bp=(Pworld@C.T).astype('<f4');bn=(Nworld@C.T).astype('<f4');rp=(ready@C.T).astype('<f4');rn=(normal@C.T).astype('<f4')
 name='Body' if o.name.startswith('Body_') else 'Face' if o.name.startswith('Face_') else o.name
 sub=[]
 for mi,mat in enumerate(mesh.materials):
  tri=np.array([t.loops[:] for t in mesh.loop_triangles if t.material_index==mi and not (name=='Body' and mesh.attributes.get('golf_covered') and mesh.attributes['golf_covered'].data[t.polygon_index].value)],dtype='<i4').reshape(-1)
  role='Skin' if name=='Body' else mat.name.split('.')[0]
  if role.startswith('Golf_'):
   role=('Kit_GolfHardware' if 'Buckle' in name else 'Kit_ShortsBand' if 'Belt' in name else 'Kit_Shorts') if any(a in name for a in ['Trousers','Skort','InnerShorts','Belt','Buckle','Pocket']) else 'Kit_GolfHead' if any(a in name for a in ['Cap','Visor','Brim']) else 'Kit_GolfGlove' if 'Glove' in name else 'Golf_Hair' if 'Hair' in name else role
  sub.append(dict(material=role,indexOffset=append(tri,blob),indexCount=len(tri),look=look(role,o,mi)))
 part=dict(name=name,kind='body' if name=='Body' else 'face' if name=='Face' else 'kit',vertexCount=n,positionOffset=append(rp,blob),normalOffset=append(rn,blob),swingPositionOffset=0,swingNormalOffset=0,uvOffset=append(UV.astype('<f4'),blob) if UV is not None and name!='Body' else -1,bindPositionOffset=append(bp,blob),submeshes=sub)
 if 'Glove' in name:part['variantHand']='right' if 'Left' in name else 'left'
 if name.startswith('GolfClubFace'):part['equipment']=o.get('GolfEquipment','iron')
 parts.append(part)
 if skinned:
  targets=[]
  if mesh.shape_keys:
   for key in list(mesh.shape_keys.key_blocks)[1:]:
    kp=np.array([v.co[:] for v in key.data])[vertex];kp=np.einsum('ij,nj->ni',world[:3,:3],kp)+world[:3,3]
    # SCNMorpher additive targets are deltas, unlike FBX absolute targets.
    km=bpy.data.meshes.new('GolfCorrectiveNormals');local=[v.co[:] for v in key.data];km.from_pydata(local,[],[tuple(p.vertices) for p in mesh.polygons]);km.update()
    for a,b in zip(km.polygons,mesh.polygons):a.use_smooth=b.use_smooth
    kn=np.array([v.vector[:] for v in km.corner_normals])@world[:3,:3].T;kn/=np.maximum(np.linalg.norm(kn,axis=1)[:,None],1e-9);bpy.data.meshes.remove(km)
    targets.append(dict(name=key.name,positionOffset=append(((kp-Pworld)@C.T).astype('<f4'),rigblob),normalOffset=append(((kn-Nworld)@C.T).astype('<f4'),rigblob)))
  rigparts.append(dict(part=name,kind='skin',vertexCount=n,bindPositionOffset=append(bp,rigblob),bindNormalOffset=append(bn,rigblob),weightOffset=append(weights[vertex].astype('<f4'),rigblob),indexOffset=append(indices[vertex],rigblob),inverseBindOffset=append((C4@restInv@C4.T).astype('<f4'),rigblob),track=-1,bones=list(range(k.n)),correctives=targets))
 else:
  track=k.n+len(rigid);rigid.append(name);rigparts.append(dict(part=name,kind='rigid',vertexCount=n,bindPositionOffset=0,bindNormalOffset=0,weightOffset=0,indexOffset=0,inverseBindOffset=0,track=track,bones=[]))
  gearbase[name]=C4@world@C4.T
  if name=='Face':gearbase[name]=C4@pose[idx['Head']]@C4.T
 print('NATIVE_PART',sex,name,n,flush=True)
(out/f'GolfHero_{sex}.bin').write_bytes(blob);(out/f'GolfHero_{sex}_Rig.bin').write_bytes(rigblob)
def rot(q):
 q=q/np.linalg.norm(q,axis=-1,keepdims=True);w,x,y,z=np.moveaxis(q,-1,0)
 return np.stack([1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)],-1).reshape(q.shape[:-1]+(3,3))
clips=[]
# Each convex skin blend is contained by the union of its weighted bone
# spheres. Include the maximum authored garment correction and club length.
radius=0.0
for o in source:
 if o.name.startswith(("GolfHandle","GolfShaft","GolfClubFace","Face_")):continue
 for v in o.data.vertices:
  for g in v.groups:
   name=o.vertex_groups[g.group].name
   if g.weight>1e-7 and name in idx:radius=max(radius,float(np.linalg.norm(np.array(v.co)-rest[idx[name],:3,3])))
radius+=.081
for e in manifest['clips']:
 ident=e['id'];B=rot(traces[ident+'_quats']);Q=np.empty_like(B);P=np.empty(B.shape[:2]+(3,));loc=traces[ident+'_hips']
 for i in range(k.n):
  parent=k.parent[i];Q[:,i]=k.rel_rot[i]@B[:,i] if parent<0 else Q[:,parent]@k.rel_rot[i]@B[:,i];off=np.broadcast_to(k.rel_off[i],(len(B),3)).copy()
  if names[i]=='Hips':off+=np.einsum('ij,nj->ni',k.rel_rot[i],loc)
  P[:,i]=off if parent<0 else P[:,parent]+np.einsum('nij,nj->ni',Q[:,parent],off)
 bone=np.broadcast_to(np.eye(4),(len(B),k.n,4,4)).copy();bone[:,:,:3,:3]=Q;bone[:,:,:3,3]=P;bone=C4@bone@C4.T
 cm=np.broadcast_to(np.eye(4),(len(B),4,4)).copy();cm[:,:3,:3]=rot(traces[ident+'_clubQuats']);cm[:,:3,3]=traces[ident+'_clubPosition'];cm=C4@cm@C4.T
 matrices=[bone[:,i] for i in range(k.n)]
 for nm in rigid:
  if nm=='Face':M=bone[:,idx['Head']]@np.linalg.inv(gearbase[nm])
  else:
   o=bpy.data.objects[nm];local=np.array(o.matrix_basis);local[1,3]=(e['clubLength']+.12)/2 if nm=='GolfShaft' else e['clubLength'] if nm.startswith('GolfClubFace') else local[1,3]
   if nm=='GolfShaft':local[:3,2]*=(e['clubLength']-.12)/.84
   M=cm@(C4@local@C4.T)@np.linalg.inv(gearbase[nm])
  matrices.append(M)
 tracks=np.empty((len(B),len(matrices),10),'<f4')
 for j,M in enumerate(matrices):
  tracks[:,j,:3]=M[:,:3,3];scale=np.linalg.norm(M[:,:3,:3],axis=1);tracks[:,j,7:]=scale
  for f in range(len(B)):
   quat=kin.mat_to_quat(M[f,:3,:3]/scale[f]);tracks[f,j,3:7]=quat[[1,2,3,0]]
   if f and np.dot(tracks[f,j,3:7],tracks[f-1,j,3:7])<0:tracks[f,j,3:7]*=-1
 (clipdir/f'{ident}.bin').write_bytes(tracks.tobytes())
 coeff=traces[ident+'_correctives'];(clipdir/f'{ident}_Correctives.json').write_text(json.dumps(dict(fps=120,names=e['correctiveTracks'],values=coeff.tolist(),trailRelease=[float(motions.controls(motions.definition(e['motion']),i/120,k.J['head_top'][2]/1.70465994)['release']) for i in range(e['frames'])]),separators=(',',':')))
 gearRadius=e['clubLength']+.16
 boundsMin=np.minimum(bone[:,:,:3,3].min(axis=(0,1))-radius,cm[:,:3,3].min(axis=0)-gearRadius)
 boundsMax=np.maximum(bone[:,:,:3,3].max(axis=(0,1))+radius,cm[:,:3,3].max(axis=0)+gearRadius)
 clips.append(dict(id=ident,name=ident,loop=e['loop'],length=e['duration'],fps=120,contact=(e['impact'] or 0)/e['duration'],frames=e['frames'],offset=0,boundsMin=boundsMin.tolist(),boundsMax=boundsMax.tolist(),file=ident,motion=e['motion'],handedness=e['handedness'],impact=e['impact'],backswingTop=e['backswingTop'],recovery=e['recovery'],equipment=e['equipment'],clubLength=e['clubLength'],correctiveFile=ident+'_Correctives'))
 print('NATIVE_CLIP',ident,flush=True)
anchors={};grips=json.loads((W/f'data/grip_{sex}.json').read_text());leftGrips=json.loads((W/f'data/grip_{sex}_LH.json').read_text());baseClub=C4@np.array(club.matrix_world)@C4.T;reflection=np.diag([-1,1,1])
for hand in ['RH','LH']:
 rows=[]
 for side in ['L','R']:
  anchor=np.array((grips if hand=='RH' else leftGrips)[side]['anchor'])[:3,3]
  world=baseClub@np.r_[C@anchor,1];rows.append(world[:3].tolist())
 anchors[hand]=rows
result=dict(version=3,sport='golf',sex=sex,baseClip=base,swingClip=f'Drive_{sex}_RH',parts=parts,materials=[],swingFrames=[],swingTimes=[],swingLength=3.4,swingContact=1.92,height=float(k.J['head_top'][2]),headCentreY=1.47,headTopY=float(k.J['head_top'][2]),headRadius=.115,rig=dict(file=f'GolfHero_{sex}_Rig',bones=names,rigid=rigid,trackCount=k.n+len(rigid),floatsPerTrack=10,parts=rigparts,clips=clips,golfWristRH=anchors['RH'],golfWristLH=anchors['LH']))
(out/f'GolfHero_{sex}.json').write_text(json.dumps(result,indent=2)+'\n')
print('NATIVE_EXPORT_COMPLETE',sex,flush=True)
