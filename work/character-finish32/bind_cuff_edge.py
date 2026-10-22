import bpy,math,json
from pathlib import Path
from mathutils import Vector
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=r/'work/character-finish32'
bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Refined.blend'));o=bpy.data.objects['Kit_Top'];m=o.data;rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rows=[]
for side in ['Left','Right']:
 a=rig.matrix_world@rig.data.bones[side+'UpperArm'].head_local;b=rig.matrix_world@rig.data.bones[side+'LowerArm'].head_local;d=(b-a).normalized();count=0
 for v in m.vertices:
  q=v.co;p=o.matrix_world@q;s=(p-a).dot(d);rad=(p-a-d*s).length
  if q.x*a.x<=0 or abs(q.x)<.145 or q.z<1.16 or rad>.145:continue
  t=min(1,max(0,(s-.080)/.080));t=t*t*(3-2*t)
  if t<=0:continue
  weights={o.vertex_groups[g.group].name:g.weight*(1-t) for g in v.groups};weights[side+'UpperArm']=weights.get(side+'UpperArm',0)+t;weights=sorted(weights.items(),key=lambda x:-x[1])[:4];total=sum(x[1] for x in weights)
  for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
  for name,val in weights:o.vertex_groups[name].add([v.index],val/total,'REPLACE')
  count+=1
 rows.append({'side':side,'upperHead':list(a),'axis':list(d),'changed':count})
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_CuffEdge.blend'))
bpy.ops.export_scene.fbx(filepath=str(w/'review-project/Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
(w/'cuff-edge-source.json').write_text(json.dumps(rows,indent=2));print(rows)
