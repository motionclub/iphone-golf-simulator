import bpy,json
from pathlib import Path
w=Path('work/character-finish32');bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Refined.blend'));o=bpy.data.objects['Kit_Top'];rig=next(a for a in bpy.data.objects if a.type=='ARMATURE')
for v in o.data.vertices:
 if not (abs(v.co.x)>.10 and 1.10<v.co.z<1.42):continue
 groups=sorted([(g.group,g.weight) for g in v.groups],key=lambda x:-x[1])
 if not groups or groups[0][1]>=.70:continue
 total=sum(a for _,a in groups[1:]);largest=groups[0][0]
 for index,amount in groups:o.vertex_groups[index].add([v.index],.70 if index==largest else .30*amount/total,'REPLACE')
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_TwistProbe.blend'))
bpy.ops.export_scene.fbx(filepath=str(w/'review-project/Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
q=json.loads((w/'cuff-edge-queue.json').read_text());q[0]['name']='character-finish32-twist-source';q[0]['env']['VISUAL_CHARACTER_OUT']=str(w.resolve()/'twist-source');q[0]['env']['VISUAL_CHARACTER_CLOTH_CLIPS']='SliceApproach';(w/'twist-source-queue.json').write_text(json.dumps(q,indent=2))
