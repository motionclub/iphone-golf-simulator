import bpy,bmesh,math,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
W=Path(__file__).resolve().parents[1]
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def finish(path):
 # Continuous barycentric skin transfer removes discontinuous shoulder weights.
 polo=bpy.data.objects['Golf_Polo'];body=bpy.data.objects['Body_F' if 'Female' in path.name else 'Body_M'];body.data.calc_loop_triangles()
 triangles=[tuple(t.vertices) for t in body.data.loop_triangles];tree=BVHTree.FromPolygons([v.co for v in body.data.vertices],triangles,all_triangles=True)
 names={g.index:g.name for g in body.vertex_groups};groups={n:polo.vertex_groups.get(n) or polo.vertex_groups.new(name=n) for n in names.values()};keys=polo.data.shape_keys.key_blocks
 for v in polo.data.vertices:
  blend=smooth(1.04,1.12,v.co.z)
  if not blend:continue
  loc,normal,index,distance=tree.find_nearest(v.co);ids=triangles[index];a,b,c=[body.data.vertices[j].co for j in ids]
  bary=barycentric_transform(loc,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
  weights={polo.vertex_groups[g.group].name:g.weight*(1-blend) for g in v.groups}
  for j,amount in zip(ids,bary):
   for g in body.data.vertices[j].groups:weights[names[g.group]]=weights.get(names[g.group],0)+g.weight*max(0,amount)*blend
  values=sorted(weights.items(),key=lambda kv:-kv[1])[:4];total=sum(value for _,value in values)
  for g in polo.vertex_groups:g.remove([v.index])
  for name,value in values:groups[name].add([v.index],value/total,'REPLACE')
  # Preserve waist fit; the old shoulder corrections target the old finish.
  for key in list(keys)[1:]:key.data[v.index].co=keys[0].data[v.index].co+(key.data[v.index].co-keys[0].data[v.index].co)*(1-blend)
 polo.data.update();bpy.ops.wm.save_as_mainfile(filepath=str(path))
# The pocket backing should line the pockets, not overlay the centre of the trousers.
path=W/'export/Golf_Male_Draft.blend';bpy.ops.wm.open_mainfile(filepath=str(W/'rollback/followthrough-baseline/Golf_Male_Draft.blend'))
o=bpy.data.objects['Golf_PocketBag'];bm=bmesh.new();bm.from_mesh(o.data)
remove=[f for f in bm.faces if abs(f.calc_center_median().x)<.095 or f.calc_center_median().y>-.065]
bmesh.ops.delete(bm,geom=remove,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(o.data);bm.free();o.data.update()
o=bpy.data.objects['Golf_Trousers'];n=len(o.data.vertices)//2;keys=o.data.shape_keys.key_blocks;P=np.array([v.co[:] for v in keys[0].data]);Q=P[:n].copy();adj=[set() for _ in range(n)]
for f in o.data.polygons:
 ids=list(f.vertices)
 if all(i<n for i in ids):
  for a,b in zip(ids,ids[1:]+ids[:1]):adj[a].add(b);adj[b].add(a)
weights=np.array([(1-smooth(.06,.135,abs(x)))*smooth(.61,.71,z)*(1-smooth(.89,.96,z)) for x,y,z in Q])
for _ in range(22):
 D=np.array([Q[list(neighbours)].mean(0)-Q[i] if neighbours else np.zeros(3) for i,neighbours in enumerate(adj)])
 Q+=D*(weights*.32)[:,None]
D=Q-P[:n];changed=int((np.linalg.norm(D,axis=1)>.00001).sum())
for i in range(n):
 for j in [i,i+n]:
  for k in keys:k.data[j].co+=Vector(D[i])
  for k in list(keys)[1:]:k.data[j].co=keys[0].data[j].co+(k.data[j].co-keys[0].data[j].co)*(1-weights[i])
  o.data.vertices[j].co=keys[0].data[j].co
for p in o.data.polygons:p.use_smooth=True
o.data.update();finish(path)
# Preserve the fitted waistband; extend the pleated shell to mid-thigh.
path=W/'export/Golf_Female_Draft.blend';bpy.ops.wm.open_mainfile(filepath=str(W/'rollback/followthrough-baseline/Golf_Female_Draft.blend'))
rig=bpy.data.objects['Rig_Female'];right_positive=rig.data.bones['RightUpperLeg'].head_local.x>rig.data.bones['LeftUpperLeg'].head_local.x
o=bpy.data.objects['Golf_PleatedSkort'];keys=o.data.shape_keys.key_blocks;groups={n:o.vertex_groups.get(n) or o.vertex_groups.new(name=n) for n in ['Hips','LeftUpperLeg','RightUpperLeg']}
for i,v in enumerate(o.data.vertices):
 p=keys[0].data[i].co.copy();t=1-smooth(.795,.945,p.z)
 if p.z<.94:p.z=.94-(.94-p.z)*2.25
 # Ease around the moving thighs without widening the fitted hip.
 p.y+=math.copysign(.055*t,p.y+.02)
 for k in keys:k.data[i].co=p
 v.co=p
 if p.z<.943:
  leg=.82*max(0,min(1,(.94-p.z)/.33));right=.5
  if not right_positive:right=1-right
  for g in o.vertex_groups:g.remove([i])
  groups['Hips'].add([i],1-leg,'REPLACE');groups['RightUpperLeg'].add([i],leg*right,'REPLACE');groups['LeftUpperLeg'].add([i],leg*(1-right),'REPLACE')
o.data.update()
# Full opaque shorts use the original body surface/weights and extend below the seat.
old=bpy.data.objects.get('Golf_InnerShorts');bpy.data.objects.remove(old,do_unlink=True)
body=bpy.data.objects['Body_F'];rig=bpy.data.objects['Rig_Female'];names={g.index:g.name for g in body.vertex_groups};allowed={'Hips','Spine','LeftUpperLeg','RightUpperLeg','LeftLowerLeg','RightLowerLeg'}
keep={v.index for v in body.data.vertices if .60<v.co.z<1.04 and sum(g.weight for g in v.groups if names[g.group] in allowed)>.85}
faces=[p for p in body.data.polygons if all(i in keep for i in p.vertices)];used=sorted({i for p in faces for i in p.vertices});lookup={j:i for i,j in enumerate(used)}
me=bpy.data.meshes.new('Golf opaque coverage shorts');me.from_pydata([body.data.vertices[j].co+body.data.vertices[j].normal*.012 for j in used],[],[[lookup[j] for j in p.vertices] for p in faces]);me.update();o=bpy.data.objects.new('Golf_InnerShorts',me);bpy.context.scene.collection.objects.link(o);o.parent=rig;me.materials.append(bpy.data.materials['Golf_Bottom']);groups={name:o.vertex_groups.new(name=name) for name in names.values()}
for i,j in enumerate(used):
 for g in body.data.vertices[j].groups:groups[names[g.group]].add([i],g.weight,'REPLACE')
mod=o.modifiers.new('Match rig','ARMATURE');mod.object=rig
bm=bmesh.new();bm.from_mesh(me)
for z,normal in [(.625,(0,0,1)),(.986,(0,0,-1))]:bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,z),plane_no=normal,clear_inner=True,dist=.000001)
bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
for p in me.polygons:p.use_smooth=True
me.update()
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
solid=o.modifiers.new('Opaque turned shorts hem','SOLIDIFY');solid.thickness=.0022;solid.offset=-1;bpy.ops.object.modifier_apply(modifier=solid.name)
finish(path)
report={'maleCrotchSmoothedVertices':changed,'malePocketLining':'restricted to side pockets; centre overlay removed','femaleSkirtHemMetres':min(v.co.z for v in bpy.data.objects['Golf_PleatedSkort'].data.vertices),'femaleShortsHemMetres':.625,'femaleShortsClearanceMetres':.012};(W/'data/followthrough_bottoms.json').write_text(json.dumps(report,indent=2));print('BOTTOM_REFINEMENT',report)
