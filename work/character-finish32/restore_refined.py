import bpy,math,json
from pathlib import Path
from mathutils import Vector
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=r/'work/character-finish32'
bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Refined.blend'));o=bpy.data.objects['Kit_Top'];m=o.data;rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rows=[]
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o

bpy.ops.export_scene.fbx(filepath=str(r/'Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
