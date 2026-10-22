"""Blender: check that the numpy linear-blend skinning of the foot vertices equals Blender's evaluated mesh on a few solved poses (read-only)."""
import sys, json, numpy as np, bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/feet/scripts')
import loco
from mathutils import Quaternion, Vector
tag = sys.argv[sys.argv.index('--') + 1]
hero = loco.Hero(tag)
rig_o = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
body = bpy.data.objects['Body_M' if tag == 'male' else 'Body_F']
def apply(basis, hl):
    for i, nm in enumerate(hero.rig.names):
        q = loco.kin.mat_to_quat(basis[i]); rig_o.pose.bones[nm].rotation_quaternion = Quaternion(q.tolist())
    rig_o.pose.bones['Hips'].location = Vector(np.asarray(hl).tolist())
    bpy.context.view_layer.update()
def blender_verts():
    dg = bpy.context.evaluated_depsgraph_get(); eo = body.evaluated_get(dg); me = eo.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); eo.to_mesh_clear(); return co.reshape(-1, 3)
tests = [dict(), dict(lf_heel=40.0, lf_lift=0.05), dict(rf_heel=-12.0, rf_lift=0.03, rf_foot=[0.2, 0.5], pel_rot=[20, 5, 3]), dict(lf_foot=[-0.2, -0.3], lf_heel=70.0, lf_lift=0.2, lf_yaw=40.0)]
worst = 0
for T in tests:
    P = dict(hero.ready); P.update(T)
    hero.S.reset(); b, h, info = hero.S.solve(P)
    apply(b, h)
    bv = blender_verts()
    S = hero.skin_mats(b, h)
    for sd in 'LR':
        mine = hero.foot_verts(sd, S); ref = bv[hero.foot_sel[sd]]
        e = np.abs(mine - ref).max(); worst = max(worst, e)
    print('  test', list(T.keys()), 'foot low (numpy) L/R mm', [round((hero.foot_low(b, h)[s] - hero.floor) * 1000, 2) for s in 'LR'], 'blender', [round((bv[hero.foot_sel[s]][:, 2].min() - hero.floor) * 1000, 2) for s in 'LR'])
print('LBS_CHECK', tag, 'max abs vertex error mm', worst * 1000, 'floor mm', hero.floor * 1000, 'bind toe deg', hero.bind_toe_deg)
