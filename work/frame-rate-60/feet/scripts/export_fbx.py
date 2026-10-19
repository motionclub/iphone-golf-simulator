"""One FBX per new clip and hero, same object set and flags as work/match-anim-set/scripts/export_fbx.py (metres, axis_forward -Z, axis_up Y, no leaf bones, baked 30 fps).

  blender -b export/HeroBase_<Hero>_MatchAnims.blend --python scripts/export_fbx.py -- <male|female> [clip ...]
Writes export/fbx/<Hero>_<Clip>.fbx and data/fbx_<hero>.json (sha256, bytes, frames).  Only the clips named here are exported (default: the five new ones)."""
import json
import os
import sys

import bpy

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
WORK = REPO + '/work/frame-rate-60/feet'
sys.path.insert(0, REPO + '/work/match-anim-set/scripts')
from common import sha256_file  # noqa: E402

a_ = sys.argv[sys.argv.index('--') + 1:]
tag = a_[0]
names = a_[1:] or ['Serve', 'Walk', 'RunForward', 'RunLeft', 'RunRight']
H = dict(male=dict(label='Male', body='Body_M', face='Face_M', hair=None, rig='Rig_Male'), female=dict(label='Female', body='Body_F', face='Face_F', hair='Hair_F', rig='Rig_Female'))[tag]
OUT = WORK + '/export/fbx'
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
sc.render.fps = 60
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
    res[clip] = dict(path=path, bytes=os.path.getsize(path), sha256=sha256_file(path), frames=nF, frame_start=int(act.frame_start), frame_end=int(act.frame_end),
                     objects=[o.name for o in objs])
    print('FBX', clip, nF, os.path.getsize(path))
json.dump(res, open(f'{WORK}/data/fbx_{tag}{"_partial" if a_[1:] else ""}.json', 'w'), indent=1)
print('FBX_DONE', tag, len(res))
