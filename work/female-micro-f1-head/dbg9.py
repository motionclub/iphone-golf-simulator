import bpy, sys, math
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np
bpy.ops.wm.open_mainfile(filepath='data/b3.blend')
fo = bpy.data.objects['Face_F']; bo = bpy.data.objects['Body_F']
print('face polys', len(fo.data.polygons), 'verts', len(fo.data.vertices))
# polygon normals vs view: count faces whose normal points toward -y (toward camera) among eye-material faces
mi = np.array([p.material_index for p in fo.data.polygons]); 
import collections
print(collections.Counter(mi.tolist()))
nrm = np.array([p.normal[:] for p in fo.data.polygons]); cen = np.array([p.center[:] for p in fo.data.polygons])
sel = (mi >= 2) & (mi <= 7) & (cen[:,0] < 0)
print('shell faces left eye', sel.sum(), 'mean normal', nrm[sel].mean(0), 'frac facing -y', (nrm[sel][:,1] < 0).mean())
