"""R1 noise floor: the same racket-vs-socket measure on shipped clips that were NOT made by this job (read-only import).  blender -b --factory-startup --python noise_floor.py"""
import bpy, math, json, numpy as np
R = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
res = {}
for label in ('Male', 'Female'):
    for clip, path in (('Forehand', R + f'work/match-anim-set/export/fbx/{label}_Forehand.fbx'), ('ReadyIdle', R + f'work/match-anim-set/export/fbx/{label}_ReadyIdle.fbx')):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=path, axis_forward='-Z', axis_up='Y')
        hr, rc = bpy.data.objects['Hand_Racket'], bpy.data.objects['Racket_Classic']
        arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
        fr = arm.animation_data.action.frame_range
        sc = bpy.context.scene
        wd, wp = 0.0, 0.0
        for f in range(int(fr[0]), int(fr[1]) + 1):
            sc.frame_set(f); bpy.context.view_layer.update()
            A, B = np.array(hr.matrix_world), np.array(rc.matrix_world)
            wd = max(wd, math.degrees(math.acos(max(-1, min(1, (np.trace(A[:3, :3] @ B[:3, :3].T) - 1) / 2)))))
            wp = max(wp, float(np.linalg.norm(A[:3, 3] - B[:3, 3])))
        res[f'{label}_{clip}'] = dict(max_rot_dev_deg=wd, max_pos_dev_m=wp)
        print('NOISE', label, clip, round(wd, 4), 'deg', wp, 'm')
json.dump(res, open(R + 'work/emotes/data/r1_noise_floor.json', 'w'), indent=1)
