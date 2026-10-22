"""Gate 1 KIT_SKINNED (Blender source) + kit geometry-unchanged check.   blender -b export/HeroBase_<Hero>_Dressed.blend --python check_skin.py -- <male|female>
Writes data/gate1_<hero>.json."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np

from dcommon import *

tag = args_after_dashes()[0]
H = HERO[tag]
rig = bpy.data.objects[H['rig']]
bones = [b.name for b in rig.data.bones if b.use_deform]
src = np.load(f'{DATA}/kitsource_{tag}.npz')
res = {}
ok_all = True
for p in PIECES:
    o = bpy.data.objects[KIT_NAME[p]]
    me = o.data
    W = bone_weight_matrix(o, bones)
    groups = [vg.name for vg in o.vertex_groups]
    names_ok = all(g in bones for g in groups)
    nz = (W > 0).sum(1)
    sums = W.sum(1)
    co = mesh_co(o)
    dpos = np.abs(co - src[f'{p}_co']).max()
    lv = np.empty(len(me.loops), np.int32)
    me.loops.foreach_get('vertex_index', lv)
    ls = np.empty(len(me.polygons), np.int32)
    me.polygons.foreach_get('loop_start', ls)
    cn = np.empty(len(me.loops) * 3, np.float32)
    if me.has_custom_normals:
        me.corner_normals.foreach_get('vector', cn)
    dcn = float(np.abs(cn.reshape(-1, 3) - src[f'{p}_cn']).max()) if me.has_custom_normals else -1.0
    r = dict(vertices=len(co), max_influences=int(nz.max()), min_influences=int(nz.min()), sum_err_max=float(np.abs(sums - 1).max()), unweighted=int((sums <= 0).sum()),
             group_names_are_deform_bones=bool(names_ok), geometry_max_pos_diff_mm=float(dpos * 1000), topology_equal=bool((lv == src[f'{p}_lv']).all() and (ls == src[f'{p}_ls']).all()),
             custom_normals=bool(me.has_custom_normals), custom_normal_max_diff=dcn, materials=[m.name for m in me.materials], armature_modifier=[(m.type, m.object.name) for m in o.modifiers])
    r['pass'] = bool(r['max_influences'] <= 4 and r['sum_err_max'] <= 1e-4 and r['unweighted'] == 0 and names_ok and r['topology_equal'] and dpos < 1e-6 and (dcn < 1e-5 or dcn < 0))
    ok_all &= r['pass']
    res[p] = r
    print(p, r)
json.dump(dict(tag=tag, pieces=res, pass_=bool(ok_all)), open(f'{DATA}/gate1_{tag}.json', 'w'), indent=1)
print('GATE1', tag, 'PASS' if ok_all else 'FAIL')
