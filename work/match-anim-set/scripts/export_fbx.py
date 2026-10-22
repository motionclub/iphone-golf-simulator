"""One FBX per clip and hero:  blender -b export/HeroBase_<Hero>_MatchAnims.blend --python export_fbx.py -- <male|female> [clip ...]
Each FBX = the fitted armature + its skinned body / face / hair + the racket on its hand socket, with that clip as the only (baked, 30 fps) animation.
Flags follow work/male-micro1h/export_final.py (metres, axis_forward -Z, axis_up Y, no leaf bones).  Writes export/fbx/<Hero>_<Clip>.fbx and data/fbx_<hero>.json."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy

from common import *

a_ = args_after_dashes()
tag = a_[0]
names = a_[1:] or CLIPS
H = HERO[tag]
OUT = EXPORT + '/fbx'
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
sc.render.fps = FPS
sc.render.fps_base = 1.0
rig = bpy.data.objects[H['rig']]
want = [rig.name, H['body'], H['face'], 'Hand_Racket', 'Racket_Classic', 'Grip', 'ButtCap', 'StringBed']
if H['hair']:
    want.append(H['hair'])
objs = [bpy.data.objects[n] for n in want]
res = {}
for clip in names:
    act = bpy.data.actions[clip]
    rig.animation_data_create()
    rig.animation_data.action = act
    try:
        rig.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    nF = int(round(act.frame_end - act.frame_start)) + 1
    sc.frame_start, sc.frame_end = int(act.frame_start), int(act.frame_end)
    sc.frame_set(int(act.frame_start))
    for o in bpy.data.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = rig
    path = f'{OUT}/{H["label"]}_{clip}.fbx'
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'ARMATURE', 'MESH', 'EMPTY'}, global_scale=1.0, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True, mesh_smooth_type='OFF',
                             add_leaf_bones=False, bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False, bake_anim_use_all_actions=False,
                             bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=0.0, path_mode='STRIP',
                             use_armature_deform_only=False)
    res[clip] = dict(path=path, bytes=os.path.getsize(path), sha256=sha256_file(path), frames=nF, frame_start=int(act.frame_start), frame_end=int(act.frame_end))
    print('FBX', clip, nF, os.path.getsize(path))
json.dump(res, open(f'{DATA}/fbx_{tag}{"_partial" if a_[1:] else ""}.json', 'w'), indent=1)
print('FBX_DONE', tag, len(res))
