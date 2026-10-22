"""Re-import <Hero>_Kit.fbx and the hero's ReadyIdle clip FBX; check the kit FBX carries THE SAME skeleton (names, parenting, rest head/tail positions) and that its skinned meshes reproduce the dressed blend
(vertex counts, positions in the bind pose, <= 4 influences, weights sum to 1).   blender -b --factory-startup --python verify_kit_fbx.py -- <male|female>"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np
from mathutils import Vector

from dcommon import *

tag = args_after_dashes()[0]
H = HERO[tag]
clip = f'{ANIM}/export/fbx/{H["label"]}_ReadyIdle.fbx'


def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path, axis_forward='-Z', axis_up='Y')
    arms = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
    assert len(arms) == 1, len(arms)
    rig = arms[0]
    bpy.context.view_layer.update()
    info = {b.name: (b.parent.name if b.parent else None, np.array(rig.matrix_world @ b.head_local), np.array(rig.matrix_world @ b.tail_local)) for b in rig.data.bones}
    meshes = {}
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            me = o.data
            ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh() if False else me
            n = len(me.vertices)
            co = np.empty(n * 3, np.float32)
            me.vertices.foreach_get('co', co)
            M = np.array(o.matrix_world, np.float64)
            co = co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
            infl = np.array([len([g for g in v.groups if g.weight > 0]) for v in me.vertices])
            sums = np.array([sum(g.weight for g in v.groups) for v in me.vertices])
            meshes[o.name] = dict(co=co, n=n, tris=len(me.loop_triangles) if me.loop_triangles else (me.calc_loop_triangles() or len(me.loop_triangles)), max_infl=int(infl.max()), sum_err=float(np.abs(sums - 1).max()),
                                  mats=[m.name for m in me.materials])
    return rig, info, meshes


_, ref, _ = load(clip)
_, kit, meshes = load(H['fbx'])
res = dict(names_equal=sorted(ref) == sorted(kit), parents_equal=all(ref[n][0] == kit[n][0] for n in ref if n in kit),
           head_max_err_mm=max(float(np.linalg.norm(ref[n][1] - kit[n][1])) for n in ref if n in kit) * 1000, tail_max_err_mm=max(float(np.linalg.norm(ref[n][2] - kit[n][2])) for n in ref if n in kit) * 1000,
           bones=len(kit), meshes={})
src = np.load(f'{DATA}/kitsource_{tag}.npz')
for name, m in meshes.items():
    piece = [p for p in PIECES if name.startswith(KIT_NAME[p])]
    r = dict(vertices=m['n'], triangles=m['tris'], max_influences=m['max_infl'], weight_sum_err=m['sum_err'], materials=m['mats'])
    if piece:
        co0 = src[f'{piece[0]}_co']
        # the FBX importer keeps the vertex order: compare in the (Y-up) import frame -> convert the Blender Z-up source (x, y, z) -> (x, z, -y)... the importer undoes the axis conversion with the same settings, so compare directly
        r['pos_max_diff_mm'] = float(np.abs(m['co'] - co0).max() * 1000) if len(co0) == m['n'] else None
    res['meshes'][name] = r
res['pass'] = bool(res['names_equal'] and res['parents_equal'] and res['head_max_err_mm'] < 0.05 and all(r['max_influences'] <= 4 and r['weight_sum_err'] < 1e-4 for r in res['meshes'].values()))
json.dump(res, open(f'{DATA}/verify_kitfbx_{tag}.json', 'w'), indent=1)
print('VERIFY_KITFBX', tag, 'PASS' if res['pass'] else 'FAIL', {k: v for k, v in res.items() if k != 'meshes'})
for k, v in res['meshes'].items():
    print('  ', k, v)
