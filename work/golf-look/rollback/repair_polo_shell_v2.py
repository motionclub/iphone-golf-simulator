"""Replace only the polo's main shell using the frozen body's vertex lineage.

Retains the draft's separate collar, buttons, placket, cuffs and turned trim.
Body, hair, face, rest rig and sockets stay byte-equivalent in identity checks.
"""
import bpy,bmesh,sys,json,shutil
from pathlib import Path
from mathutils import Matrix,Vector
W=Path(__file__).resolve().parents[1];sex=sys.argv[-1];female=sex=='Female'
rig=bpy.data.objects['Rig_'+sex];body=bpy.data.objects['Body_F' if female else 'Body_M'];old=bpy.data.objects['Golf_Polo']
rig.animation_data.action=None;rig.data.pose_position='REST'
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
adj=[set() for _ in old.data.vertices]
for e in old.data.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
seen=set();components=[]
for i in range(len(adj)):
 if i in seen:continue
 stack=[i];seen.add(i);ids=[]
 while stack:
  j=stack.pop();ids.append(j)
  for k in adj[j]:
   if k not in seen:seen.add(k);stack.append(k)
 components.append(ids)
large=set(max(components,key=len));bm=bmesh.new();bm.from_mesh(old.data);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[bm.verts[i] for i in large],context='VERTS');bm.to_mesh(old.data);bm.free()
old.name='Golf_Polo_Construction'
names={g.index:g.name for g in body.vertex_groups};allowed=['Hips','Spine','Chest','Shoulder','UpperArm']
keep=set();hem=.950 if female else .950
for v in body.data.vertices:
 if v.co.z<hem-.025:continue
 w={names[g.group]:g.weight for g in v.groups};upper=sum(value for n,value in w.items() if any(k in n for k in allowed))
 if upper<.35:continue
 side='Left' if v.co.x>0 else 'Right'
 bone=rig.data.bones[side+'UpperArm'];axis=bone.tail_local-bone.head_local
 t=(v.co-bone.head_local).dot(axis)/axis.length_squared
 arm=sum(value for n,value in w.items() if n.startswith(side) and any(k in n for k in ['UpperArm','LowerArm','Hand']))
 if arm>.45 and t>.80:continue
 keep.add(v.index)
polys=[p for p in body.data.polygons if all(i in keep for i in p.vertices)];used=sorted({i for p in polys for i in p.vertices});remap={v:i for i,v in enumerate(used)}
verts=[]
for i in used:
 v=body.data.vertices[i];p=v.co+v.normal*.010
 if abs(v.co.x)<.17 and v.co.z<1.29:p.x*=1.045;p.y*=1.06
 if p.y>0 and p.z<hem+.04:p.z-=.012
 verts.append(tuple(p))
me=bpy.data.meshes.new('Golf_Polo_BodyLineage');me.from_pydata(verts,[],[tuple(remap[i] for i in p.vertices) for p in polys]);me.update()
main=bpy.data.objects.new('Golf_Polo',me);bpy.context.scene.collection.objects.link(main)
groups={b.name:main.vertex_groups.new(name=b.name) for b in rig.data.bones}
for j,i in enumerate(used):
 for g in body.data.vertices[i].groups:
  if names[g.group] in groups:groups[names[g.group]].add([j],g.weight,'REPLACE')
main.data.materials.append(bpy.data.materials['Golf_Main'])
bpy.ops.object.select_all(action='DESELECT');main.select_set(True);bpy.context.view_layer.objects.active=main
# A planar turned hem, not a jagged selection boundary.
bm=bmesh.new();bm.from_mesh(main.data)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,hem),plane_no=(0,0,1),clear_inner=True,dist=.000001)
bm.to_mesh(main.data);bm.free()
sol=main.modifiers.new('Real shell thickness','SOLIDIFY');sol.thickness=.002;sol.offset=-1;bpy.ops.object.modifier_apply(modifier=sol.name)
for p in main.data.polygons:p.use_smooth=True
arm=main.modifiers.new('Same match rig','ARMATURE');arm.object=rig;main.parent=rig
rigid_names={'Hips','Spine','Chest','UpperChest','Neck','Head'}
# Collar and placket must follow the upper torso, rather than a nearby arm.
for v in old.data.vertices:
 if v.co.z>(1.28 if female else 1.33) and abs(v.co.x)<.14:
  for g in old.vertex_groups:g.remove([v.index])
  old.vertex_groups['Chest'].add([v.index],1,'REPLACE')
# Join the retained construction into the same polo renderer.
bpy.ops.object.select_all(action='DESELECT');old.select_set(True);main.select_set(True);bpy.context.view_layer.objects.active=main
bpy.ops.object.join()
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1,island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
rig.data.pose_position='POSE';rig.animation_data.action=bpy.data.actions['ReadyIdle']
if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
bpy.context.scene.frame_set(0)
p=Path(bpy.data.filepath);bk=W/'rollback/polo_lineage'/p.name;bk.parent.mkdir(exist_ok=True)
if not bk.exists():shutil.copy2(p,bk)
bpy.ops.wm.save_as_mainfile(filepath=str(p));main.data.calc_loop_triangles()
(W/f'data/polo_lineage_{sex}.json').write_text(json.dumps(dict(sex=sex,source_vertices=len(used),removed_main_vertices=len(large),polo_triangles=len(main.data.loop_triangles),status='candidate construction; identity/deformation/own-eye checks required'),indent=2)+'\n')
print('POLO LINEAGE',sex,len(used),len(main.data.loop_triangles),flush=True)
