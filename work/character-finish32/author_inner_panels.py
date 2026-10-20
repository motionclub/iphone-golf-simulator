import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=r/'work/character-finish32';bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Refined.blend'));o=bpy.data.objects['Kit_Top'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');d=json.loads((w/'baseline/poses/male_intro.json').read_text())['parts'][0]
BP=[Vector((-d['vertices'][i],d['vertices'][i+1],d['vertices'][i+2])) for i in range(0,len(d['vertices']),3)];BN=[Vector((-d['normals'][i],d['normals'][i+1],d['normals'][i+2])) for i in range(0,len(d['normals']),3)];BT=[d['triangles'][i:i+3][::-1] for i in range(0,len(d['triangles']),3)];outer=BVHTree.FromPolygons([v.co for v in o.data.vertices],[list(f.vertices) for f in o.data.polygons]);keep=[]
axes={}
for side in ['Left','Right']:
 a=rig.matrix_world@rig.data.bones[side+'UpperArm'].head_local;b=rig.matrix_world@rig.data.bones[side+'LowerArm'].head_local;axes[side]=(a,(b-a).normalized())
for p in BP:
 x,y,z=p;side='Left' if x>0 else 'Right';a,axis=axes[side];s=(p-a).dot(axis);allowed=1.06<z<1.413 and abs(x)>.075 and (abs(x)<.185 or s<.17)
 if abs(x)<.105 and z>1.305:allowed=False
 if allowed:allowed=outer.find_nearest(p)[3]<.05
 keep.append(allowed)
faces=[f for f in BT if all(keep[i] for i in f)];ids=sorted(set(i for f in faces for i in f));index={j:i for i,j in enumerate(ids)};verts=[BP[i]+BN[i]*.004 for i in ids];m=bpy.data.meshes.new('PoloInnerStretchPanels');m.from_pydata(verts,[],[[index[i] for i in f] for f in faces]);m.update();uv=m.uv_layers.new(name='UVMap')
for f in m.polygons:
 f.use_smooth=True
 for li in f.loop_indices:
  p=m.vertices[m.loops[li].vertex_index].co;uv.data[li].uv=(p.x*2.5,p.z*2.5)
lining=bpy.data.objects.new('InnerStretchPanels',m);bpy.context.collection.objects.link(lining);lining.matrix_world=o.matrix_world.copy()
for material in o.data.materials:m.materials.append(material)
for g in o.vertex_groups:lining.vertex_groups.new(name=g.name)
for row,j in enumerate(ids):
 for k in range(4):
  amount=d['weights'][j*4+k];name=d['bones'][d['indices'][j*4+k]]
  if amount>0:lining.vertex_groups[name].add([row],amount,'REPLACE')
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);lining.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.join()
if o.data.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_InnerPanels.blend'))
bpy.ops.export_scene.fbx(filepath=str(w/'review-project/Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
print('INNER_PANELS',len(ids),len(faces),'total',len(o.data.vertices),len(o.data.polygons),flush=True)
