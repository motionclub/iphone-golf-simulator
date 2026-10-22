"""Apply a vertex array + custom vertex normals to the START blend (Body_M only; Face_M untouched), save blend.
blender -b --factory-startup --python apply_j.py -- <V.npy> <N.npy> <out.blend> [base.blend]"""
import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head/pylib')
import numpy as np
import bpy
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1l-head'
argv = sys.argv[sys.argv.index('--') + 1:]
V = np.load(argv[0]); Nn = np.load(argv[1]); out = argv[2]; base = argv[3] if len(argv) > 3 else W + '/baseline/HeroBase_Male_Silhouette.9bfd788a.blend'
bpy.ops.wm.open_mainfile(filepath=base)
body = bpy.data.objects['Body_M']; me = body.data
assert len(me.vertices) == len(V) == len(Nn)
me.vertices.foreach_set('co', V.astype(np.float32).ravel()); me.update()
me.normals_split_custom_set_from_vertices([tuple(x) for x in Nn]); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out)
print('saved', out)
