"""KIT FBX per hero: the SAME armature as the clip FBXs (bones, rest pose, nothing animated) + the six skinned kit meshes.  Flags copied from work/match-anim-set/scripts/export_fbx.py (metres,
axis_forward -Z, axis_up Y, no leaf bones, smoothing 'OFF' = normals only) except bake_anim, which is off (no animation).

  blender -b export/HeroBase_<Hero>_Dressed.blend --python export_kit_fbx.py -- <male|female>
Writes export/<Hero>_Kit.fbx and data/kitfbx_<hero>.json (sha256, bytes)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy

from dcommon import *

tag = args_after_dashes()[0]
H = HERO[tag]
sc = bpy.context.scene
rig = bpy.data.objects[H['rig']]
rig.animation_data_create()
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.location = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.rotation_euler = (0, 0, 0)
    pb.scale = (1, 1, 1)
sc.frame_set(0)
bpy.context.view_layer.update()
for o in bpy.data.objects:
    o.select_set(False)
objs = [rig] + [bpy.data.objects[KIT_NAME[p]] for p in PIECES]
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = rig
os.makedirs(EXPORT, exist_ok=True)
bpy.ops.export_scene.fbx(filepath=H['fbx'], use_selection=True, object_types={'ARMATURE', 'MESH'}, global_scale=1.0, apply_unit_scale=True,
                         apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True, mesh_smooth_type='OFF',
                         add_leaf_bones=False, bake_anim=False, path_mode='STRIP', use_armature_deform_only=False)
json.dump(dict(path=H['fbx'], bytes=os.path.getsize(H['fbx']), sha256=sha256_file(H['fbx'])), open(f'{DATA}/kitfbx_{tag}.json', 'w'), indent=1)
print('KITFBX', H['fbx'], os.path.getsize(H['fbx']))
