"""NO_SLIDE_SUBSTITUTE (a): mean absolute rotation difference (degrees) of the two upper-leg and two lower-leg bones between each frame of a clip and the ReadyIdle pose (frame 0), averaged over the clip.
  blender -b export/HeroBase_<Hero>_MatchAnims.blend --python scripts/leg_diff.py -- <male|female>        -> data/leg_diff_<tag>.json"""
import json
import sys
import numpy as np
import bpy
REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
WORK = REPO + '/work/serve-and-feet'
tag = sys.argv[sys.argv.index('--') + 1]
rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
sc = bpy.context.scene
BONES = ['LeftUpperLeg', 'RightUpperLeg', 'LeftLowerLeg', 'RightLowerLeg']
for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'


def pose(name, f):
    act = bpy.data.actions[name]
    rig.animation_data_create(); rig.animation_data.action = act
    try: rig.animation_data.action_slot = act.slots[0]
    except Exception: pass
    sc.frame_set(f); bpy.context.view_layer.update()
    return {b: np.array(rig.pose.bones[b].rotation_quaternion) for b in BONES}


def ang(q1, q2):
    d = abs(float(np.dot(q1, q2))); d = min(1.0, d)
    return np.degrees(2 * np.arccos(d))


ready = pose('ReadyIdle', 0)
out = {}
for clip in ('Walk', 'RunForward', 'RunRight', 'RunLeft'):
    n = int(bpy.data.actions[clip].frame_end)
    per = [[ang(pose(clip, f)[b], ready[b]) for b in BONES] for f in range(n)]
    per = np.array(per)
    out[clip] = dict(mean_deg=float(per.mean()), per_bone_mean_deg={b: float(per[:, i].mean()) for i, b in enumerate(BONES)})
    print('LEGDIFF', tag, clip, round(out[clip]['mean_deg'], 1))
json.dump(out, open(f'{WORK}/data/leg_diff_{tag}.json', 'w'), indent=1)
