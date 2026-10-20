"""One FBX per clip and hero (same object set and flags as work/match-anim-set/scripts/export_fbx.py: metres, axis_forward -Z, axis_up Y, no leaf bones, baked 30 fps).

  blender -b export/blend/HeroBase_<Hero>_Emotes.blend --python export_emotes.py -- <male|female> [clip ...]
Writes export/fbx/<Hero>_<Clip>.fbx and data/fbx_<hero>.json.  The racket object is animated only in the clips that detach it."""
import json
import os
import sys

import bpy

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
W = REPO + '/work/emotes'
sys.path.insert(0, REPO + '/work/match-anim-set/scripts')
from common import sha256_file  # noqa: E402

CLIPS = ['Emote_Scuba', 'Emote_Thrust', 'Emote_Spike']
a_ = sys.argv[sys.argv.index('--') + 1:]
tag = a_[0]
names = a_[1:] or CLIPS
H = dict(male=dict(label='Male', body='Body_M', face='Face_M', hair=None, rig='Rig_Male'), female=dict(label='Female', body='Body_F', face='Face_F', hair='Hair_F', rig='Rig_Female'))[tag]
OUT = W + '/export/fbx'
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
sc.render.fps = 30
sc.render.fps_base = 1.0
rig = bpy.data.objects[H['rig']]
rk = bpy.data.objects['Racket_Classic']
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
    ract = bpy.data.actions.get(clip + '_Racket')
    if ract is None:
        if rk.animation_data is not None:
            rk.animation_data_clear()          # a clip that never detaches the racket carries NO animation on it (no baked float noise on the socket relation)
    else:
        rk.animation_data_create()
        rk.animation_data.action = ract
    if ract is not None:
        try:
            rk.animation_data.action_slot = ract.slots[0]
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
    res[clip] = dict(path=path, bytes=os.path.getsize(path), sha256=sha256_file(path), frames=nF, racket_action=ract is not None)
    print('FBX', clip, nF, os.path.getsize(path), 'racket anim' if ract is not None else '')
    if rk.animation_data is not None:
        rk.animation_data.action = None
jp = f'{W}/data/fbx_{tag}.json'                                       # merge: the intro clips keep their entries
allres = json.load(open(jp)) if os.path.exists(jp) else {}
allres.update(res)
json.dump(allres, open(jp, 'w'), indent=1)
print('FBX_DONE', tag, len(res))
