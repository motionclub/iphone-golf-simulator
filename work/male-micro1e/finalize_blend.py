"""Headless: open the ORIGINAL baseline blend, replace Body_M geometry with the final arrays, save to a target path.
usage: blender -b --python finalize_blend.py -- verts.npy faces.pkl out.blend"""
import bpy, sys, numpy as np, pickle, hashlib
from pathlib import Path
argv = sys.argv[sys.argv.index('--')+1:]
vp, fp, out = argv
W = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(W/'baseline/HeroBase_Male_Silhouette.blend'))
o = bpy.data.objects['Body_M']; me = o.data
verts = np.load(vp); faces = pickle.load(open(fp, 'rb'))
mats = [m for m in me.materials]
me.clear_geometry()
me.from_pydata([tuple(v) for v in verts.tolist()], [], faces)
me.polygons.foreach_set('use_smooth', [True]*len(me.polygons))
for m in mats:
    if m not in list(me.materials): me.materials.append(m)
me.update()
me.validate(verbose=True)
tri = sum(len(p.vertices)-2 for p in me.polygons)
print('FINAL_COUNTS verts', len(me.vertices), 'polys', len(me.polygons), 'tris', tri, 'materials', [m.name for m in me.materials])
bpy.ops.wm.save_as_mainfile(filepath=out)
print('SAVED', out)
