"""Foot grounding table:  blender -b export/_stage/<Hero>_rig.blend --python foot_ground.py -- <male|female>
How far the lowest skinned vertex dips below its standing height when one heel is raised by theta degrees (the toes bone stays flat, the foot bone pitches
about the ball joint, some toe vertices are partly weighted to the foot bone).  Writes data/foot_ground_<hero>.json {heel_deg, lift_m}: the extra lift the
solver adds to a foot with a raised heel, so that no vertex goes below the floor."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy

from common import *
import kin
import preview as PV

tag = args_after_dashes()[0]
H = HERO[tag]
rig_o = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
body = bpy.data.objects[H['body']]
rig, solver = PV.load_all(tag)
solver.foot_dip = None                                   # measure without any compensation
sc = bpy.context.scene


def zmin(theta_l, theta_r):
    P = dict(solver.ready)
    P['lf_heel'], P['rf_heel'] = float(theta_l), float(theta_r)
    solver.reset()
    basis, hl, info = solver.solve(P)
    PV.apply_pose(rig_o, rig, basis, hl)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eo = body.evaluated_get(dg)
    me = eo.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    eo.to_mesh_clear()
    return float(co[:, 2].min())


z0 = zmin(0, 0)
heel = list(np.arange(0.0, 80.1, 5.0))
dips = []
for th in heel:
    zl = zmin(th, 0)
    zr = zmin(0, th)
    dips.append(max(0.0, z0 - min(zl, zr)))
# monotone envelope (the lift never decreases with the heel angle up to the maximum)
lift = list(np.maximum.accumulate(dips))
json.dump(dict(tag=tag, z_standing=z0, heel_deg=[float(h) for h in heel], dip_m=[float(d) for d in dips], lift_m=[float(x) for x in lift]), open(f'{DATA}/foot_ground_{tag}.json', 'w'), indent=1)
print('FOOT_GROUND_DONE', tag, 'standing z %.1f mm' % (z0 * 1000), [(int(h), round(x * 1000, 1)) for h, x in zip(heel, lift)])
