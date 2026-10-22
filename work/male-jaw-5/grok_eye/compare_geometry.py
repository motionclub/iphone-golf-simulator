import bpy, sys, json, numpy as np
from pathlib import Path
a, b, out = Path(sys.argv[sys.argv.index('--')+1]), Path(sys.argv[sys.argv.index('--')+2]), Path(sys.argv[sys.argv.index('--')+3])
bpy.ops.wm.open_mainfile(filepath=str(a))
co_a = np.array([v.co[:] for v in bpy.data.objects['Body_M'].data.vertices], float)
bpy.ops.wm.open_mainfile(filepath=str(b))
co_b = np.array([v.co[:] for v in bpy.data.objects['Body_M'].data.vertices], float)
assert co_a.shape == co_b.shape
d = np.linalg.norm(co_b - co_a, axis=1)
z = co_a[:, 2]
bands = {
    'all': slice(None),
    'feet_z<0.15': z < 0.15,
    'legs_0.15-0.9': (z >= 0.15) & (z < 0.9),
    'torso_0.9-1.35': (z >= 0.9) & (z < 1.35),
    'head_z>=1.35': z >= 1.35,
    'chin_1.38-1.55': (z >= 1.38) & (z < 1.55),
    'hands_rough': (z > 0.75) & (z < 1.15) & (np.abs(co_a[:,0]) > 0.25),
}
report = {'n': int(len(d)), 'max_mm': float(d.max()*1000), 'mean_mm': float(d.mean()*1000), 'changed_gt_0.1mm': int((d>1e-4).sum()), 'changed_gt_1mm': int((d>1e-3).sum())}
for name, mask in bands.items():
    dd = d[mask]
    report[name] = {'n': int(mask.sum() if hasattr(mask,'sum') else len(dd)), 'max_mm': float(dd.max()*1000), 'mean_mm': float(dd.mean()*1000), 'gt_1mm': int((dd>1e-3).sum())}
out.write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
