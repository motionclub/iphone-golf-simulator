"""Chat 4: the approved 30 Hz match strokes on a 60 Hz grid without re-solving them.

  blender -b work/match-anim-set/export/HeroBase_<Hero>_MatchAnims.blend --python resample60.py -- <out.blend> [clip ...]

Every action's 30 Hz keys (LINEAR, one per frame, written by match-anim-set bake.py) are kept exactly on the even 60 Hz frames; each odd
frame is the uniform Catmull-Rom midpoint of its four 30 Hz neighbours (quaternions hemisphere-aligned, then normalised). So the motion
is the approved solve at every shared frame (APPROVED gate by construction) and the in-betweens follow the curve instead of a straight line.
Pose markers (Contact, LeftRelease) move to the doubled frame; custom props keep the clip's seconds (length, contact) and say fps = 60."""
import sys
import bpy
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
out = argv[0]
only = set(argv[1:])
sc = bpy.context.scene
sc.render.fps = 60; sc.render.fps_base = 1.0


def cr_mid(p0, p1, p2, p3):
    return (-p0 + 9 * p1 + 9 * p2 - p3) / 16.0


report = []
for act in list(bpy.data.actions):
    name = act.name
    if only and name not in only:
        continue
    if act.get('fps', 30) == 60:
        continue
    curves = {}
    fcs = [fc for layer in act.layers for strip in layer.strips for slot in act.slots for fc in strip.channelbag(slot).fcurves] if not hasattr(act, 'fcurves') else list(act.fcurves)
    for fc in fcs:
        curves.setdefault(fc.data_path, {})[fc.array_index] = fc
    n = int(round(act.frame_end - act.frame_start)) + 1
    f0 = int(round(act.frame_start))
    new = {}
    for path, comps in curves.items():
        idx = sorted(comps)
        S = np.array([[comps[i].evaluate(f0 + k) for i in idx] for k in range(n)])   # (n, ncomp): the approved keys
        quat = path.endswith('rotation_quaternion') and len(idx) == 4
        if quat:
            for k in range(1, n):
                if np.dot(S[k], S[k - 1]) < 0:
                    S[k] = -S[k]
        m = 2 * n - 1
        T = np.zeros((m, len(idx)))
        T[0::2] = S
        for k in range(n - 1):
            p0 = S[max(k - 1, 0)]; p1 = S[k]; p2 = S[k + 1]; p3 = S[min(k + 2, n - 1)]
            v = cr_mid(p0, p1, p2, p3)
            if quat:
                v = v / np.linalg.norm(v)
            T[2 * k + 1] = v
        new[path] = (idx, T, comps)
    # rewrite the curves in place (same action, same slot, same groups)
    for path, (idx, T, comps) in new.items():
        for j, i in enumerate(idx):
            fc = comps[i]
            fc.keyframe_points.clear()
            fc.keyframe_points.add(len(T))
            co = np.empty(len(T) * 2)
            co[0::2] = np.arange(len(T)) + 2 * f0
            co[1::2] = T[:, j]
            fc.keyframe_points.foreach_set('co', co)
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
            fc.update()
    for mk in act.pose_markers:
        mk.frame = 2 * mk.frame
    act.frame_start = 2 * f0
    act.frame_end = 2 * f0 + 2 * (n - 1)
    act['fps'] = 60
    act['resampled_from_30'] = True
    report.append(f'{name}: {n} -> {2 * n - 1} frames')

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print('RESAMPLE60', out, '\n' + '\n'.join(report))
