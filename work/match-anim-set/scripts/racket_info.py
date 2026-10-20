"""racket geometry in the racket frame (origin = grip centre, Y = shaft towards the head, Z = face normal) + its pose relative to the
right-hand bone at bind.  blender -b <stage.blend> --python racket_info.py -- <tag>"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
import numpy as np, bpy
from mathutils import Matrix
from common import *
tag = args_after_dashes()[0]
rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
hr = bpy.data.objects['Hand_Racket']
bpy.context.view_layer.update()
Mh = np.array(rig.pose.bones['RightHand'].matrix)           # hand bone, armature space (== world; rig identity)
Mr = np.array(hr.matrix_world)
T_rh = np.linalg.inv(Mh) @ Mr                              # racket frame in the hand-bone frame
info = dict(tag=tag, T_hand_to_racket=T_rh.tolist(), racket_world_bind=Mr.tolist(), hand_world_bind=Mh.tolist())
Minv = np.linalg.inv(Mr)
def local_pts(o):
    co = mesh_co(o, world=True)
    return co @ Minv[:3, :3].T + Minv[:3, 3]
for n in ('Grip', 'ButtCap', 'StringBed', 'Racket_Classic'):
    o = bpy.data.objects[n]
    P = local_pts(o)
    info[n] = dict(n=len(P), min=P.min(0).tolist(), max=P.max(0).tolist(), center=P.mean(0).tolist())
sb = local_pts(bpy.data.objects['StringBed'])
info['head_center'] = ((sb.min(0) + sb.max(0)) / 2).tolist()
rk = local_pts(bpy.data.objects['Racket_Classic'])
# sample points on the frame: farthest-point subsample of the frame vertices (for visibility tests), 160 points
idx = np.round(np.linspace(0, len(rk) - 1, 160)).astype(int)
info['frame_samples'] = rk[idx].tolist()
info['length'] = float(rk[:, 1].max() - rk[:, 1].min())
json.dump(info, open(f'{DATA}/racket_{tag}.json', 'w'), indent=1)
print('RACKET', tag, 'head centre', np.round(info['head_center'], 3), 'ymax', round(rk[:,1].max(),3), 'ymin', round(rk[:,1].min(),3), 'T_rh pos', np.round(T_rh[:3,3],3))
