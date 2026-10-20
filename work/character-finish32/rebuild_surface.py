import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
w=Path('work/character-finish32');bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Sleeve.blend'));o=bpy.data.objects['Kit_Top'];rig=next(a for a in bpy.data.objects if a.type=='ARMATURE');m=o.data
bm=bmesh.new();bm.from_mesh(m);remaining=set(bm.verts);components=[]
while remaining:
 todo=[remaining.pop()];comp=set(todo)
 while todo:
  v=todo.pop()
  for e in v.link_edges:
   q=e.other_vert(v)
   if q in remaining:remaining.remove(q);comp.add(q);todo.append(q)
 components.append(comp)
main=max(components,key=len);bmesh.ops.delete(bm,geom=list(main),context='VERTS');bm.to_mesh(m);bm.free()
d=json.loads((w/'baseline/poses/male_intro.json').read_text())['parts'][0];BP=[Vector((-d['vertices'][i],*d['vertices'][i+1:i+3])) for i in range(0,len(d['vertices']),3)];BN=[Vector((-d['normals'][i],*d['normals'][i+1:i+3])) for i in range(0,len(d['normals']),3)];BT=[d['triangles'][i:i+3][::-1] for i in range(0,len(d['triangles']),3)];axes={}
for side in ['Left','Right']:
 a=rig.matrix_world@rig.data.bones[side+'UpperArm'].head_local;b=rig.matrix_world@rig.data.bones[side+'LowerArm'].head_local;axes[side]=(a,(b-a).normalized())
keep=[]
for p in BP:
 x,y,z=p;a,axis=axes['Left' if x>0 else 'Right'];s=(p-a).dot(axis)
 keep.append(1.015<z<1.407 and (abs(x)<.18 or s<.215))
faces=[f for f in BT if all(keep[i] for i in f)];ids=sorted(set(i for f in faces for i in f));idx={j:i for i,j in enumerate(ids)};verts=[]
for i in ids:
 p=BP[i];x,y,z=p;ease=.006
 if abs(x)<.18 and z<1.24:ease+=.012*max(0,1-abs(z-1.10)/.14)
 verts.append(p+BN[i]*ease)
me=bpy.data.meshes.new('PoloSurface');me.from_pydata(verts,[],[[idx[j] for j in f] for f in faces]);me.update();shell=bpy.data.objects.new('PoloSurface',me);bpy.context.collection.objects.link(shell);shell.matrix_world=o.matrix_world.copy()
for mat in o.data.materials:me.materials.append(mat)
for g in o.vertex_groups:shell.vertex_groups.new(name=g.name)
for row,j in enumerate(ids):
 for k in range(4):
  a=d['weights'][j*4+k];name=d['bones'][d['indices'][j*4+k]]
  if a>0:shell.vertex_groups[name].add([row],a,'REPLACE')
uv=me.uv_layers.new(name='UVMap')
for f in me.polygons:
 f.use_smooth=True
 for li in f.loop_indices:
  p=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(p.x*2.5,p.z*2.5)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
# Smooth only the cut edges; interior keeps the exact source-body correspondence.
for _ in range(5):
 edgeverts=[v for v in bm.verts if v.is_boundary];q={v:sum((e.other_vert(v).co for e in v.link_edges if e.is_boundary),Vector())/sum(e.is_boundary for e in v.link_edges) for v in edgeverts}
 for v,p in q.items():v.co=v.co.lerp(p,.4)
bm.to_mesh(me);bm.free()
bpy.ops.object.select_all(action='DESELECT');shell.select_set(True);bpy.context.view_layer.objects.active=shell
s=shell.modifiers.new('Cloth thickness','SOLIDIFY');s.thickness=.001;s.offset=-1;bpy.ops.object.modifier_apply(modifier=s.name)
o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.join()
if o.data.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
for f in o.data.polygons:f.use_smooth=True
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_Surface.blend'))
bpy.ops.export_scene.fbx(filepath=str(w/'review-project/Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
q=json.loads((w/'lining-queue.json').read_text());q[0]['name']='character-finish32-surface';q[0]['env']['VISUAL_CHARACTER_OUT']=str(w.resolve()/'surface');(w/'surface-queue.json').write_text(json.dumps(q,indent=2));print('SURFACE',len(o.data.vertices),sum(len(f.vertices)-2 for f in o.data.polygons),flush=True)
