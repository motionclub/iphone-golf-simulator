import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
import numpy as np, bpy
from common import *
tag = args_after_dashes()[0]
rig_o = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
tr = np.load(f'{DATA}/anim_{tag}.npz')
worst = 0
for clip in ('Forehand', 'Serve', 'SliceApproach', 'ReadyIdle'):
    rig_o.animation_data.action = bpy.data.actions[clip]
    n = len(tr[f'{clip}/R_wrist'])
    for f in (0, n // 3, n // 2, n - 1):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        M = np.array(rig_o.pose.bones['RightHand'].matrix)
        d = np.abs(M[:3, 3] - tr[f'{clip}/R_wrist'][f]).max()
        worst = max(worst, d)
        print(clip, f, 'RightHand pos err %.2e' % d)
print('SMOKE worst', worst)
print('actions', [a.name for a in bpy.data.actions])
print('markers Forehand', [(m.name, m.frame) for m in bpy.data.actions['Forehand'].pose_markers])
print('props', {k: bpy.data.actions['Forehand'][k] for k in ('clip', 'watch_section', 'contact_time_s', 'thin', 'length_s')})
