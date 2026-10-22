"""Watertight authored hand patches on the approved rig. No head/outside-wrist drift.
Source bones use thumb-v2; runtime FBX is exported against old rest for its bridge.
"""
import bpy,bmesh,pathlib,sys,json,math
from mathutils import Vector,Matrix
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
source=R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_Tennis_ThumbRigV2.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.data.pose_position='REST'
body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body_'));body.data=body.data.copy()
old_rest={}
with bpy.data.libraries.load(str(R/f'work/match-anim-set/export/HeroBase_{sex}_MatchAnims.blend'),link=False) as (src,dst):dst.armatures=[rig.data.name]
original=dst.armatures[0];old_rest={b.name:b.matrix_local.copy() for b in original.bones}
CUT=.035;NEW=.040
originalPositions=[v.co.copy() for v in body.data.vertices];originalNormals={tuple(round(c,7) for c in v.co):v.normal.copy() for v in body.data.vertices};stats=[]
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def sphere(name,point,radius,parts):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=10,location=point);o=bpy.context.object;o.name=name;o.scale=radius;parts.append(o)
def tube(name,a,b,r1,r2,parts):
 d=b-a;bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=r1,radius2=r2,depth=d.length,location=(a+b)*.5);o=bpy.context.object;o.name=name;o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector((0,0,1)).rotation_difference(d.normalized());parts.append(o);sphere(name+'_base',a,(r1,r1,r1),parts);sphere(name+'_tip',b,(r2,r2,r2),parts)
for side in ('Left','Right'):
 hand=rig.data.bones[side+'Hand'];H=hand.matrix_local.inverted()@rig.matrix_world.inverted()@body.matrix_world;toBody=H.inverted();parts=[];chain={}
 for digit in ('Index','Middle','Ring','Little','Thumb'):
  names=[side+digit+j for j in ('Proximal','Intermediate','Distal')];points=[hand.matrix_local.inverted()@rig.data.bones[n].head_local for n in names]
  distal=body.vertex_groups[names[-1]];candidates=[]
  for v in body.data.vertices:
   w=sum(g.weight for g in v.groups if g.group==distal.index)
   if w>.4:candidates.append(H@v.co)
  distances=[(p-points[-1]).length for p in candidates];limit=max(distances)*.8 if distances else 0;tips=[p for p,d in zip(candidates,distances) if d>limit]
  tip=sum(tips,Vector())/len(tips) if tips else points[-1]+(points[-1]-points[-2]).normalized()*.015
  if (tip-points[-1]).length<.009:tip=points[-1]+(points[-1]-points[-2]).normalized()*.012
  points.append(tip);chain[digit]=points
  radius=([.0085,.009,.008,.0065,.0105] if sex=='Male' else [.0075,.008,.007,.006,.0095])[('Index','Middle','Ring','Little','Thumb').index(digit)]
  for k in range(3):tube(side+digit+str(k),points[k],points[k+1],radius*(1-k*.1),radius*(.9-k*.1),parts)
 # A smooth palm and exact-radius wrist overlap the proximal phalanges. Voxel union
 # removes all primitive intersections; it is one continuous closed surface.
 first=[chain[d][0] for d in ('Index','Middle','Ring','Little')];cx=sum(p.x for p in first)/4;top=sum(p.y for p in first)/4
 width=(max(p.x for p in first)-min(p.x for p in first))*.5+.011
 sphere(side+'Palm',Vector((cx,top*.46,0)),(width,top*.57,.016 if sex=='Male' else .0145),parts)
 sphere(side+'Wrist',Vector((0,-.012,0)),(.020 if sex=='Male' else .0175,.042,.014),parts)
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();patch=bpy.context.object;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 # Joined primitive coordinates are global hand-space; clear their translated origin.
 world=patch.matrix_world.copy()
 for v in patch.data.vertices:v.co=world@v.co
 patch.matrix_world=Matrix.Identity(4)
 rem=patch.modifiers.new('ContinuousPalmAndDigits','REMESH');rem.mode='VOXEL';rem.voxel_size=.002;rem.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rem.name)
 sm=patch.modifiers.new('SoftKnuckleTransition','SMOOTH');sm.factor=.55;sm.iterations=4;bpy.ops.object.modifier_apply(modifier=sm.name)
 de=patch.modifiers.new('AuthoredHandBudget','DECIMATE');de.ratio=.42;de.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=de.name)
 # Slice the new wrist above the old cut. Their original loops are lofted, not
 # hidden behind detached shells. All existing old wrist boundary positions remain.
 pb=bmesh.new();pb.from_mesh(patch.data);bmesh.ops.bisect_plane(pb,geom=list(pb.verts)+list(pb.edges)+list(pb.faces),plane_co=Vector((0,NEW,0)),plane_no=Vector((0,1,0)),clear_inner=True,clear_outer=False,dist=1e-6)
 newLoop=[v for v in pb.verts if any(e.is_boundary for e in v.link_edges)];assert len(newLoop)>8
 bm=bmesh.new();bm.from_mesh(body.data);layer=bm.verts.layers.deform.active
 groupIds={g.index for g in body.vertex_groups if g.name==side+'Hand' or g.name==side+'LowerArm' or g.name.startswith(side) and any(d in g.name for d in ('Thumb','Index','Middle','Ring','Little'))}
 def region(v):
  p=H@v.co;return abs(p.x)<.14 and abs(p.z)<.10 and -.04<p.y<.25 and sum(w for g,w in v[layer].items() if g in groupIds)>.2
 faces=[f for f in bm.faces if all(region(v) for v in f.verts)];verts={v for f in faces for v in f.verts};edges={e for f in faces for e in f.edges}
 plane=toBody@Vector((0,CUT,0));normal=H.to_3x3().transposed()@Vector((0,1,0));bmesh.ops.bisect_plane(bm,geom=list(verts)+list(edges)+faces,plane_co=plane,plane_no=normal,dist=1e-6)
 removed=[f for f in bm.faces if all(region(v) for v in f.verts) and (H@f.calc_center_median()).y>CUT+1e-6];bmesh.ops.delete(bm,geom=removed,context='FACES')
 oldLoop=[v for v in bm.verts if abs((H@v.co).y-CUT)<1e-5 and any(e.is_boundary for e in v.link_edges) and region(v)];assert len(oldLoop)>8,(side,len(oldLoop))
 # Weld only coincident cut-ring seam duplicates. The retained positions/weights
 # agree, while an unwelded UV seam makes an angular loft ambiguous.
 bmesh.ops.remove_doubles(bm,verts=oldLoop,dist=1e-6)
 oldLoop=[v for v in bm.verts if abs((H@v.co).y-CUT)<1e-5 and any(e.is_boundary for e in v.link_edges) and region(v)]
 cutWeights=[(H@v.co,dict(v[layer])) for v in oldLoop]
 def wristWeights(p):
  angle=math.atan2(p.z,p.x);ordered=sorted(cutWeights,key=lambda a:abs(math.atan2(math.sin(math.atan2(a[0].z,a[0].x)-angle),math.cos(math.atan2(a[0].z,a[0].x)-angle))))[:2]
  weights={};total=0
  for point,groups in ordered:
   angular=abs(math.atan2(math.sin(math.atan2(point.z,point.x)-angle),math.cos(math.atan2(point.z,point.x)-angle)));w=1/max(.0001,angular);total+=w
   for g,value in groups.items():weights[g]=weights.get(g,0)+value*w
  return {g:w/total for g,w in weights.items()}
 isolated=[v for v in bm.verts if not v.link_faces and region(v) and (H@v.co).y>CUT];bmesh.ops.delete(bm,geom=isolated,context='VERTS')
 bm.verts.ensure_lookup_table();made={}
 handGroup=body.vertex_groups[side+'Hand'].index;lowerGroup=body.vertex_groups[side+'LowerArm'].index
 for v in pb.verts:
  n=bm.verts.new(toBody@v.co);made[v]=n;p=v.co;digit,points=min(chain.items(),key=lambda item:min((p-(a+(b-a)*max(0,min(1,(p-a).dot(b-a)/(b-a).length_squared)))).length for a,b in zip(item[1],item[1][1:])))
  lengths=[(b-a).length for a,b in zip(points,points[1:])];stations=[0,lengths[0],lengths[0]+lengths[1],sum(lengths)];nearest=1e9;s=0
  for k,(a,b) in enumerate(zip(points,points[1:])):
   t=max(0,min(1,(p-a).dot(b-a)/(b-a).length_squared));distance=(p-a-(b-a)*t).length
   if distance<nearest:nearest=distance;s=stations[k]+lengths[k]*t
  radius=.014 if digit=='Thumb' else .011
  digitBlend=(1-smooth(radius*.7,radius*1.3,nearest))*smooth(.001,.015,s)
  # Palm remains rigid to Hand; proximal/middle/tip transitions are smooth 4-weight.
  mid=smooth(lengths[0]-.006,lengths[0]+.006,s);end=smooth(lengths[0]+lengths[1]-.005,lengths[0]+lengths[1]+.005,s)
  names=[side+digit+j for j in ('Proximal','Intermediate','Distal')];weights={handGroup:1-digitBlend,body.vertex_groups[names[0]].index:digitBlend*(1-mid),body.vertex_groups[names[1]].index:digitBlend*mid*(1-end),body.vertex_groups[names[2]].index:digitBlend*end}
  if p.y<NEW+.030:
   base=wristWeights(p);amount=smooth(NEW,NEW+.030,p.y);keys=set(base)|set(weights);weights={g:base.get(g,0)*(1-amount)+weights.get(g,0)*amount for g in keys}
  total=sum(weights.values());n[layer].clear()
  for g,w in weights.items():
   if w>1e-6:n[layer][g]=w/total
 for f in pb.faces:bm.faces.new([made[v] for v in f.verts])
 oldLoop.sort(key=lambda v:math.atan2((H@v.co).z,(H@v.co).x));newLoop.sort(key=lambda v:math.atan2(v.co.z,v.co.x));oldAngles=[math.atan2((H@v.co).z,(H@v.co).x) for v in oldLoop];newAngles=[math.atan2(v.co.z,v.co.x) for v in newLoop]
 # Monotone angular zipper handles different loop vertex counts without fans.
 i=j=0
 while i<len(oldLoop) or j<len(newLoop):
  oldNext=oldAngles[(i+1)%len(oldLoop)]+(2*math.pi if i+1>=len(oldLoop) else 0);newNext=newAngles[(j+1)%len(newLoop)]+(2*math.pi if j+1>=len(newLoop) else 0)
  a=oldLoop[i%len(oldLoop)];b=made[newLoop[j%len(newLoop)]]
  if i<len(oldLoop) and (j>=len(newLoop) or oldNext<newNext):c=oldLoop[(i+1)%len(oldLoop)];bm.faces.new([a,b,c]);i+=1
  else:c=made[newLoop[(j+1)%len(newLoop)]];bm.faces.new([a,b,c]);j+=1
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free();pb.free();bpy.data.objects.remove(patch,do_unlink=True);body.data.update()
 stats.append({'side':side,'originalRetainedHandLocalY':CUT,'newLoftHandLocalY':NEW,'oldWristBoundaryVertices':len(oldLoop),'newWristBoundaryVertices':len(newLoop),'removedHandFaces':len(removed),'newHandVertices':len(made),'bodyTriangles':sum(len(p.vertices)-2 for p in body.data.polygons),'chainHandLocal':{d:[list(p) for p in points] for d,points in chain.items()},'wristCutWeights':[{str(g):w for g,w in groups.items()} for point,groups in cutWeights]})
for p in body.data.polygons:p.use_smooth=True
body.data.update();normals=[originalNormals.get(tuple(round(c,7) for c in v.co),v.normal.copy()) for v in body.data.vertices];body.data.normals_split_custom_set_from_vertices(normals)
sourceOut=R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_ContinuousHandsV2.blend';bpy.ops.wm.save_as_mainfile(filepath=str(sourceOut))
# FBX meshes deliberately retain original imported rest. Runtime's versioned bridge
# updates binds and all old clips consistently after loading this new local geometry.
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
thumbs=[s+'Thumb'+j for s in ('Left','Right') for j in ('Proximal','Intermediate','Distal')]
for n in thumbs:rig.data.edit_bones[n].use_connect=False
for n in thumbs:
 b=rig.data.edit_bones[n];b.matrix=old_rest[n];b.length=original.bones[n].length
for n in thumbs:rig.data.edit_bones[n].use_connect=original.bones[n].use_connect
bpy.ops.object.mode_set(mode='OBJECT');bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
out=R/f'work/full-visual-overhaul/characters/exports/Hands/{sex}.fbx';out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.fbx(filepath=str(out),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='STRIP')
report={'sex':sex,'source':str(sourceOut),'runtimeRest':'original53; versioned bridge required before new thumb pose','construction':'voxel union smooth palm/five articulated digits, original wrist ring loft, original outside-hand coordinates/normals retained','stats':stats,'sourceVisualGate':'UNVERIFIED: actual evaluated fist/grip proof required'}
(R/f'proof/full-visual-overhaul/characters/continuous-hands-{sex}.json').write_text(json.dumps(report,indent=2));print('CONTINUOUS_HAND_SOURCE_COMPLETE',sex,stats,flush=True)
