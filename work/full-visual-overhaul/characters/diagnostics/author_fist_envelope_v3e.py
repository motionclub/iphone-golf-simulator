"""Pose-volume sculpt against a rounded evaluated closed-hand envelope.
Retains source vertex topology, original rest positions, fixed wrist boundary,
all named bones and clips. Saves editable local closed-fist shape keys and
explicit posed normals from the smooth envelope for engine parity.
"""
import bpy,bmesh,pathlib,sys,json
from mathutils import Vector,Matrix,geometry
from mathutils.bvhtree import BVHTree
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_ClosedFistV3C.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'));bpy.context.view_layer.update();B=rig.matrix_world.inverted()@body.matrix_world;A=B.inverted();groups={g.index:g.name for g in body.vertex_groups};rest=[v.co.copy() for v in body.data.vertices]
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
report={}
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
 geo=bpy.data.meshes.new(side+'ClosedFistEnvelope');geo.from_pydata(expanded,[],faces);geo.update();target=bpy.data.objects.new(side+'EditableClosedFistSculpt',geo);bpy.context.collection.objects.link(target);bpy.context.view_layer.objects.active=target;target.select_set(True)
 # Close the diagnostic lower-forearm extraction and discard unused body verts.
 bm=bmesh.new();bm.from_mesh(geo);isolated=[v for v in bm.verts if not v.link_faces];bmesh.ops.delete(bm,geom=isolated,context='VERTS');boundary=[e for e in bm.edges if e.is_boundary];bmesh.ops.holes_fill(bm,edges=boundary,sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(geo);bm.free()
 rem=target.modifiers.new('WatertightClosedHandVolume','REMESH');rem.mode='VOXEL';rem.voxel_size=.00075;rem.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rem.name)
 sm=target.modifiers.new('SculptedSoftKnuckles','SMOOTH');sm.factor=.55;sm.iterations=10;bpy.ops.object.modifier_apply(modifier=sm.name)
 target.data.update();target.data.calc_loop_triangles();tv=[v.co.copy() for v in target.data.vertices];tn=[v.normal.copy() for v in target.data.vertices];tris=[tuple(t.vertices) for t in target.data.loop_triangles];tree=BVHTree.FromPolygons(tv,tris,all_triangles=True)
 key=body.shape_key_add(name='Hero_Fist_'+side,from_mix=False);normalAttr=body.data.attributes.new('Hero_Fist_PosedNormal_'+side,'FLOAT_VECTOR','POINT');changes=[];changed=0;skipped=0
 for i,v in enumerate(body.data.vertices):
  amount=sum(g.weight for g in v.groups if g.group in handIds);fade=ease(.04,.055,hp[i].y)
  if amount<.98 or fade<.000001:continue
  point,n,tri,distance=tree.find_nearest(expanded[i]);m=matrices[i]
  if point is None or abs(m.determinant())<1e-7:skipped+=1;continue
  correction=(point-posed[i])*fade;key.data[i].co=m.inverted()@(posed[i]+correction);a,b,c=tris[tri];smoothN=geometry.barycentric_transform(point,tv[a],tv[b],tv[c],tn[a],tn[b],tn[c]).normalized();normalAttr.data[i].vector=smoothN;changes.append((correction.length,(key.data[i].co-rest[i]).length));changed+=1
 key.value=1;target.hide_render=True;target.hide_set(True);report[side]={'vertices':changed,'maxPosedDeltaMetres':max(x[0] for x in changes),'maxBindDeltaMetres':max(x[1] for x in changes),'meanPosedDeltaMetres':sum(x[0] for x in changes)/len(changes),'singularSkipped':skipped,'outsideRetainedCutDeltaMetres':0,'closedSculptTriangles':len(tris),'construction':'DQS closed-volume sculpt with 2.5/3.5mm compressed digit volume expansion, watertight union, soft knuckles, explicit posed normals; rest/contact poses unchanged'}
bpy.context.view_layer.update();out=R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_FistSurfaceV3E.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out));(R/f'proof/full-visual-overhaul/characters/fist-envelope-v3e-{sex}.json').write_text(json.dumps(report,indent=2));print('FIST_ENVELOPE_V3E',sex,report,flush=True)
