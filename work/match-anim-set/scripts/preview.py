"""Preview helpers (run inside Blender, headless): apply solved poses to the rig, render behind / side views with Workbench, tile sheets.

  blender -b <stage_or_final.blend> --python preview.py -- <tag> ready <out_prefix>
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Matrix, Quaternion, Vector

from common import *
import kin
import pose as PS


def load_all(tag):
    rig = kin.Rig(f'{DATA}/rig_{tag}.json')
    racket = json.load(open(f'{DATA}/racket_{tag}.json'))
    hands = json.load(open(f'{DATA}/hands_{tag}.json'))
    return rig, PS.Solver(rig, racket, hands)


def apply_pose(rig_obj, rig, basis, hips_loc, prev_q=None):
    """write the solved basis rotations / hips location into the pose bones (quaternions with sign continuity)."""
    qs = {}
    for i, nm in enumerate(rig.names):
        q = kin.mat_to_quat(basis[i])
        if prev_q is not None and np.dot(q, prev_q[nm]) < 0:
            q = -q
        qs[nm] = q
        rig_obj.pose.bones[nm].rotation_quaternion = Quaternion(q.tolist())
    rig_obj.pose.bones['Hips'].location = Vector(np.asarray(hips_loc).tolist())
    return qs


def setup_scene(rig_obj, floor=True, size=12.0, cam_lens=50, samples=16, court=True):
    """dressed-look studio (EEVEE, cyclorama, key/fill/rim that ride with the camera).  Read-only import of the dressed-look helper."""
    sys.path.insert(0, REPO + '/work/dressed-look/scripts')
    import studio
    for o in bpy.data.objects:
        if o.type in ('CAMERA', 'LIGHT') and not o.name.startswith('Studio'):
            o.hide_render = True
        if o.type == 'EMPTY' and not o.name.startswith('Hand_Racket'):
            o.hide_render = True
    cam = studio.setup(samples=samples, bg=(0.30, 0.33, 0.38), cyc_rgb=(0.22, 0.34, 0.45) if court else (0.5, 0.52, 0.56))
    studio.set_floor_z(0.0)
    return cam


def render(cam, view, root_xy, path, res=(520, 700), dist=None, target_z=0.95, lens=50):
    import studio
    c = np.asarray(root_xy, float)
    az, el, d = {'behind': (180.0, 8.0, 5.4), 'side': (90.0, 6.0, 5.2), 'front': (0.0, 6.0, 5.4), 'behind_hi': (180.0, 22.0, 6.0),
                 'q_behind': (150.0, 12.0, 5.4), 'q_front': (35.0, 8.0, 4.6), 'behind_c': (180.0, 8.0, 3.6), 'side_c': (90.0, 6.0, 3.6)}[view]
    d = dist or d
    studio.shot(path, (c[0], c[1] - 0.05, target_z), az=az, el=el, dist=d, lens=lens, res=res, turn_lights=True)


if __name__ == '__main__':
    tag, what, outp = args_after_dashes()[:3]
    rig_o = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    rig, solver = load_all(tag)
    cam = setup_scene(rig_o)
    P = json.loads(args_after_dashes()[3]) if len(args_after_dashes()) > 3 else {}
    basis, hips_loc, info = solver.solve(P)
    apply_pose(rig_o, rig, basis, hips_loc)
    bpy.context.view_layer.update()
    # FK cross-check against Blender
    Q, Pos = rig.fk(basis, hips_loc)
    worst = 0.0
    for i, nm in enumerate(rig.names):
        M = np.array(rig_o.pose.bones[nm].matrix)
        worst = max(worst, float(np.abs(M[:3, 3] - Pos[i]).max()))
    print('FK_vs_BLENDER', worst)
    for k in sorted(info):
        v = info[k]
        if isinstance(v, (int, float, np.floating)):
            print('  %-24s %.4f' % (k, v))
    print('  sweet spot (world)', np.round(info['sweet'], 3), ' racket origin', np.round(info['rk_origin'], 3))
    root = rig.root_origin
    for v in ('behind', 'side', 'front'):
        render(cam, v, root, f'{outp}_{v}.png')
