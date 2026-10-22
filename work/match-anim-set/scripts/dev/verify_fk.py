"""debug: numpy FK (kin.Rig) vs Blender's pose-bone matrices for random poses.  blender -b <stage.blend> --python verify_fk.py -- <tag>"""
import sys, json, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
import numpy as np, bpy
from mathutils import Quaternion, Vector
from common import *
import kin
tag = args_after_dashes()[0]
rig_o = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
R = kin.Rig(f'{DATA}/rig_{tag}.json')
rng = np.random.RandomState(3)
worst_pos = worst_rot = 0.0
for trial in range(4):
    B = np.zeros((R.n, 3, 3))
    for i, nm in enumerate(R.names):
        ax = rng.normal(size=3); ang = rng.uniform(-0.8, 0.8)
        B[i] = kin.axis_angle(ax, ang)
        q = kin.mat_to_quat(B[i])
        rig_o.pose.bones[nm].rotation_quaternion = Quaternion(q.tolist())
    loc = rng.uniform(-0.05, 0.05, 3)
    hb = rig_o.pose.bones['Hips']; hb.location = Vector(loc.tolist())
    bpy.context.view_layer.update()
    Q, P = R.fk(B, hips_loc=loc)
    for i, nm in enumerate(R.names):
        M = np.array(rig_o.pose.bones[nm].matrix)
        worst_pos = max(worst_pos, float(np.abs(M[:3, 3] - P[i]).max()))
        worst_rot = max(worst_rot, float(np.abs(M[:3, :3] - Q[i]).max()))
print('FK_CHECK', tag, 'max head position error %.2e m, max rotation error %.2e' % (worst_pos, worst_rot))
