"""SHA-256 of the F-curve data of every action of a blend (read-only):  blender -b <blend> --python hash_actions.py -- <out.json>"""
import hashlib, json, sys
import numpy as np
import bpy
out = sys.argv[sys.argv.index('--') + 1]
res = {}
for act in bpy.data.actions:
    h = hashlib.sha256()
    fcs = sorted(act.fcurves, key=lambda f: (f.data_path, f.array_index)) if hasattr(act, 'fcurves') else []
    if not fcs:   # Blender 5: layered actions
        try:
            fcs = []
            for layer in act.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        fcs += list(cb.fcurves)
            fcs = sorted(fcs, key=lambda f: (f.data_path, f.array_index))
        except Exception:
            fcs = []
    for fc in fcs:
        n = len(fc.keyframe_points)
        co = np.empty(n * 2); fc.keyframe_points.foreach_get('co', co)
        h.update(fc.data_path.encode()); h.update(str(fc.array_index).encode()); h.update(co.astype(np.float64).tobytes())
    res[act.name] = dict(sha256=h.hexdigest(), fcurves=len(fcs), frame_range=[float(act.frame_range[0]), float(act.frame_range[1])])
json.dump(res, open(out, 'w'), indent=1)
print('HASHED', len(res), 'actions, fcurves total', sum(r['fcurves'] for r in res.values()))
