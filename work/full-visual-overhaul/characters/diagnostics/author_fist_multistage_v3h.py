"""Pose-volume sculpt against a rounded evaluated closed-hand envelope.
Retains source vertex topology, original rest positions, fixed wrist boundary,
all named bones and clips. Saves editable local closed-fist shape keys and
explicit posed normals from the smooth envelope for engine parity.
"""
import bpy,bmesh,pathlib,sys,json
from mathutils import Vector,Matrix,Quaternion,geometry
from mathutils.bvhtree import BVHTree
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_ClosedFistV3C.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'));
rig.animation_data_clear();fullPose={p.name:(p.rotation_quaternion.copy(),p.location.copy(),p.scale.copy()) for p in rig.pose.bones}
report={};outdir=R/'work/full-visual-overhaul/characters/exports/HandsV3H';outdir.mkdir(parents=True,exist_ok=True)
for stage in (.25,.50,.75,1.0):
 for p in rig.pose.bones:
  if any(p.name.startswith(side+d) for side in ('Left','Right') for d in ('Thumb','Index','Middle','Ring','Little')):
   q,l,scale=fullPose[p.name];p.rotation_quaternion=Quaternion().slerp(q,stage);p.location=l*stage;p.scale=Vector((1,1,1)).lerp(scale,stage)
 if body.data.shape_keys:
  for key in body.data.shape_keys.key_blocks:key.value=0
 bpy.context.view_layer.update();B=rig.matrix_world.inverted()@body.matrix_world;A=B.inverted();groups={g.index:g.name for g in body.vertex_groups};rest=[v.co.copy() for v in body.data.vertices]
 trans={b.name:A@rig.pose.bones[b.name].matrix@b.matrix_local.inverted()@B for b in rig.data.bones};matrices=[];posed=[]
 for i,v in enumerate(body.data.vertices):
  m=Matrix(((0,0,0,0),)*4);total=0
  for g in v.groups:
   if groups[g.group] in trans:m+=trans[groups[g.group]]*g.weight;total+=g.weight
  if total<.99:m=Matrix.Identity(4)
  matrices.append(m);posed.append(m@rest[i])
 for modifier in body.modifiers:
  if modifier.type=='ARMATURE':modifier.use_deform_preserve_volume=True
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();dqs=[v.co.copy() for v in mesh.vertices];polygons=[tuple(f.vertices) for f in mesh.polygons];ev.to_mesh_clear()
 normalGeo=bpy.data.meshes.new('DQS geometry normal oracle');normalGeo.from_pydata(dqs,[],polygons);normalGeo.update();dqsNormals=[v.normal.copy() for v in normalGeo.vertices]
 for modifier in body.modifiers:
  if modifier.type=='ARMATURE':modifier.use_deform_preserve_volume=False
 if not body.data.shape_keys:body.shape_key_add(name='Basis',from_mix=False)
 def ease(a,b,x):
  t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
 stageReport={}
 for side in ('Left','Right'):
  H=rig.data.bones[side+'Hand'].matrix_local.inverted()@B;ids={g.index for g in body.vertex_groups if g.name==side+'Hand' or g.name==side+'LowerArm' or any(g.name.startswith(side+d) for d in ('Thumb','Index','Middle','Ring','Little'))};handIds={g.index for g in body.vertex_groups if g.name==side+'Hand' or any(g.name.startswith(side+d) for d in ('Thumb','Index','Middle','Ring','Little'))}
  hp=[H@v for v in rest];region={i for i,v in enumerate(body.data.vertices) if -.02<hp[i].y<.25 and abs(hp[i].x)<.14 and abs(hp[i].z)<.1 and sum(g.weight for g in v.groups if g.group in ids)>.2};faces=[p for p in polygons if all(i in region for i in p)]
  digitIds={g.index for g in body.vertex_groups if any(g.name.startswith(side+d) for d in ('Thumb','Index','Middle','Ring','Little'))}
  # Closed fingers compress against each other. A small authored volume expansion
  # replaces the thin joint ribbons with a compact rounded knuckle row; rest/open
  # anatomy and every sports contact pose remain untouched.
  expanded=[p.copy() for p in dqs]
  for i,v in enumerate(body.data.vertices):
   amount=sum(g.weight for g in v.groups if g.group in digitIds)
   inflate=(.0035 if sex=='Male' else .0025)*ease(.35,.95,amount)*ease(.045,.065,hp[i].y)
   if inflate>0:expanded[i]+=dqsNormals[i]*inflate
  thumbSegments=[(A@rig.pose.bones[side+'Thumb'+j].head,A@rig.pose.bones[side+'Thumb'+j].tail) for j in ('Proximal','Intermediate','Distal')]
  def ThumbNear(p):
   distance=min((p-(a+(b-a)*max(0,min(1,(p-a).dot(b-a)/max(1e-12,(b-a).length_squared))))).length for a,b in thumbSegments)
   return 1-ease(.010,.023,distance)
  closeRadius=.0035*ease(.50,.90,stage)
  for i in region:expanded[i]+=dqsNormals[i]*(closeRadius*ThumbNear(dqs[i]))
  geo=bpy.data.meshes.new(side+'ClosedFistEnvelope');geo.from_pydata(expanded,[],faces);geo.update();target=bpy.data.objects.new(side+'EditableClosedFistSculpt',geo);bpy.context.collection.objects.link(target);bpy.context.view_layer.objects.active=target;target.select_set(True)
  # Close the diagnostic lower-forearm extraction and discard unused body verts.
  bm=bmesh.new();bm.from_mesh(geo);isolated=[v for v in bm.verts if not v.link_faces];bmesh.ops.delete(bm,geom=isolated,context='VERTS');boundary=[e for e in bm.edges if e.is_boundary];bmesh.ops.holes_fill(bm,edges=boundary,sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(geo);bm.free()
  rem=target.modifiers.new('WatertightClosedHandVolume','REMESH');rem.mode='VOXEL';rem.voxel_size=.00075;rem.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rem.name)
  if closeRadius>0:
   beforeNormals=[v.normal.copy() for v in target.data.vertices]
   for i,v in enumerate(target.data.vertices):v.co-=beforeNormals[i]*(closeRadius*ThumbNear(v.co))
  target.data.update()
  sm=target.modifiers.new('SculptedSoftKnuckles','SMOOTH');sm.factor=.55;sm.iterations=10;bpy.ops.object.modifier_apply(modifier=sm.name)
  target.data.update();target.data.calc_loop_triangles();tv=[v.co.copy() for v in target.data.vertices];tn=[v.normal.copy() for v in target.data.vertices];tris=[tuple(t.vertices) for t in target.data.loop_triangles];tree=BVHTree.FromPolygons(tv,tris,all_triangles=True)
  # Topology-aware tangential fairing redistributes the original closed skin
  # over the smooth outer volume. Each pass stays on that volume rather than
  # preserving the oscillating closest-point assignments of compressed loops.
  mask={};current=[p.copy() for p in dqs];adj=[set() for _ in rest]
  for e in body.data.edges:
   a,b=e.vertices;adj[a].add(b);adj[b].add(a)
  for i,v in enumerate(body.data.vertices):
   amount=sum(g.weight for g in v.groups if g.group in handIds);fade=ease(.04,.055,hp[i].y)
   if amount>.98 and fade>0:
    mask[i]=fade;nearest=tree.find_nearest(expanded[i]);current[i]=dqs[i].lerp(nearest[0],fade) if nearest[0] is not None else dqs[i]
  for cycle in range(60):
   nextpoints=[p.copy() for p in current]
   for i,fade in mask.items():
    if not adj[i]:continue
    mean=sum((current[j] for j in adj[i]),Vector())/len(adj[i]);near=tree.find_nearest(current[i]);n=near[1]
    delta=mean-current[i];tangent=delta-n*delta.dot(n);trial=current[i]+tangent*(.48*fade);nearest=tree.find_nearest(trial)
    if nearest[0] is not None:nextpoints[i]=trial.lerp(nearest[0],.65*fade)
   current=nextpoints
  # Independent normals of the *corrected posed topology*, not a geometric
  # nearest-face normal that can hide uneven triangle spacing.
  result=bpy.data.meshes.new(side+'SmoothedPosedSkin');result.from_pydata(current,[],polygons);result.update();newNormals=[v.normal.copy() for v in result.vertices]
  key=body.shape_key_add(name=('Hero_Fist_'+side if stage==1 else 'Hero_Fist_'+str(round(stage*100))+'_'+side),from_mix=False);normalAttr=body.data.attributes.new(('Hero_Fist_PosedNormal_'+side if stage==1 else 'Hero_Fist_PosedNormal_'+str(round(stage*100))+'_'+side),'FLOAT_VECTOR','POINT');changes=[];changed=0;skipped=0
  for i,fade in mask.items():
   m=matrices[i]
   if abs(m.determinant())<1e-7:skipped+=1;continue
   correction=(current[i]-posed[i]);key.data[i].co=m.inverted()@current[i];normalAttr.data[i].vector=newNormals[i];changes.append((correction.length,(key.data[i].co-rest[i]).length));changed+=1
  key.value=1;target.hide_render=True;target.hide_set(True);stageReport[side]={'vertices':changed,'maxPosedDeltaMetres':max(x[0] for x in changes),'maxBindDeltaMetres':max(x[1] for x in changes),'meanPosedDeltaMetres':sum(x[0] for x in changes)/len(changes),'singularSkipped':skipped,'outsideRetainedCutDeltaMetres':0,'closedSculptTriangles':len(tris),'construction':'DQS closed-volume sculpt, 60 topology-aware tangential fairing passes on watertight volume, explicit corrected-topology posed normals; rest/contact poses unchanged'}
 bpy.context.view_layer.update();report[str(round(stage*100))]=stageReport
 evaluated=body.evaluated_get(bpy.context.evaluated_depsgraph_get());golden=evaluated.to_mesh();base=[x for v in body.data.shape_keys.key_blocks['Basis'].data for x in v.co];posed=[x for v in golden.vertices for x in v.co]
 (outdir/f'{sex}_FistGolden_{round(stage*100)}.json').write_text(json.dumps({'source':'FistSurfaceV3H','weight':stage,'basePositions':base,'posedPositions':posed},separators=(',',':')));evaluated.to_mesh_clear()
 print('FIST_STAGE_COMPLETE',sex,stage,stageReport,flush=True)
bpy.context.view_layer.update();out=R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_FistSurfaceV3H.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out));(R/f'proof/full-visual-overhaul/characters/fist-envelope-v3h-{sex}.json').write_text(json.dumps(report,indent=2));print('FIST_ENVELOPE_V3H',sex,flush=True)
