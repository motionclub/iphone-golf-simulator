"""ALL_CLIPS: re-import every FBX and compare with the baked blend.

  blender -b --factory-startup --python verify_fbx.py -- ref  <male|female>      # dump the reference rig + sampled poses from the baked blend
  blender -b --factory-startup --python verify_fbx.py -- check <male|female>     # import all 16 FBX of that hero and compare

Per FBX: exactly one armature; same bone names and rest head positions as the blend's rig (<= 0.1 mm); an animation whose frame count equals the action's;
the posed bone heads at four sampled frames equal the blend's (<= 1 mm)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Vector

from common import *

a_ = args_after_dashes()
mode, tag = a_[0], a_[1]
H = HERO[tag]
REF = f'{DATA}/ref_pose_{tag}.json'


def pose_heads(rig):
    return {pb.name: list(map(float, (rig.matrix_world @ pb.head))) for pb in rig.pose.bones}


if mode == 'ref':
    bpy.ops.wm.open_mainfile(filepath=H['blend'])
    rig = bpy.data.objects[H['rig']]
    sc = bpy.context.scene
    meta = json.load(open(f'{DATA}/bake_{tag}.json'))['clips']
    out = dict(rest={b.name: list(map(float, (rig.matrix_world @ b.head_local))) for b in rig.data.bones}, clips={})
    for clip in CLIPS:
        act = bpy.data.actions[clip]
        rig.animation_data_create()
        rig.animation_data.action = act
        try:
            rig.animation_data.action_slot = act.slots[0]
        except Exception:
            pass
        n = int(round(act.frame_end - act.frame_start)) + 1
        c = meta[clip]['contact_s']
        frames = sorted(set([0, n // 3, n // 2, n - 1] + ([int(round(c * FPS))] if c is not None else [])))
        out['clips'][clip] = dict(frames=n, samples={})
        for f in frames:
            sc.frame_set(f)
            bpy.context.view_layer.update()
            out['clips'][clip]['samples'][str(f)] = pose_heads(rig)
    json.dump(out, open(REF, 'w'))
    print('REF_DONE', tag, len(out['clips']))

else:
    ref = json.load(open(REF))
    res = {}
    for clip in CLIPS:
        path = f'{EXPORT}/fbx/{H["label"]}_{clip}.fbx'
        r = dict(path=path, exists=os.path.exists(path), bytes=os.path.getsize(path) if os.path.exists(path) else 0)
        try:
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.fbx(filepath=path, axis_forward='-Z', axis_up='Y')
            arms = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
            r['armatures'] = len(arms)
            imp = arms[0]
            bones = {b.name: b for b in imp.data.bones}
            r['bone_count'] = len(bones)
            r['names_equal'] = sorted(bones) == sorted(ref['rest'])
            worst_rest = 0.0
            for n, p in ref['rest'].items():
                if n in bones:
                    q = imp.matrix_world @ bones[n].head_local
                    worst_rest = max(worst_rest, float((q - Vector(p)).length))
            r['rest_head_max_err_mm'] = worst_rest * 1000.0
            act = imp.animation_data.action if imp.animation_data else None
            r['has_action'] = act is not None
            if act is not None:
                fr = act.frame_range
                r['frame_range'] = [float(fr[0]), float(fr[1])]
                r['frame_count'] = int(round(fr[1] - fr[0])) + 1
                r['expected_frames'] = ref['clips'][clip]['frames']
                r['frames_equal'] = r['frame_count'] == r['expected_frames']
                sc = bpy.context.scene
                worst = 0.0
                f0 = int(round(fr[0]))
                for fs, heads in ref['clips'][clip]['samples'].items():
                    sc.frame_set(f0 + int(fs))
                    bpy.context.view_layer.update()
                    for n, p in heads.items():
                        if n in imp.pose.bones:
                            q = imp.matrix_world @ imp.pose.bones[n].head
                            worst = max(worst, float((q - Vector(p)).length))
                r['pose_max_err_mm'] = worst * 1000.0
            r['meshes'] = sorted(o.name for o in bpy.context.scene.objects if o.type == 'MESH')
            r['ok'] = bool(r['armatures'] == 1 and r['names_equal'] and r['rest_head_max_err_mm'] <= 0.1 and r.get('frames_equal') and r.get('pose_max_err_mm', 1e9) <= 1.0)
        except Exception as e:           # noqa
            r['error'] = repr(e)
            r['ok'] = False
        res[clip] = r
        print('FBXCHK', clip, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k in ('armatures', 'names_equal', 'rest_head_max_err_mm', 'frames_equal', 'pose_max_err_mm', 'ok', 'error')})
    json.dump(res, open(f'{DATA}/verify_fbx_{tag}.json', 'w'), indent=1)
    print('FBXCHK_DONE', tag, sum(1 for v in res.values() if v['ok']), '/', len(res))
