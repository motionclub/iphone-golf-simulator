import sys, json, bpy, numpy as np
bpy.ops.wm.open_mainfile(filepath='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/export/HeroBase_Female_MicroF3_head_STAGED.blend')
face = bpy.data.objects['Face_F']; mf = face.data
Vf = np.array([v.co[:] for v in mf.vertices]); mats = [m.name for m in mf.materials]
k = mats.index('Face_Lip'); ids = sorted({v for p in mf.polygons if p.material_index == k for v in p.vertices}); P = Vf[ids]
print('Face_Lip verts', len(ids), 'z range', P[:, 2].min(), P[:, 2].max(), 'x range', P[:, 0].min(), P[:, 0].max())
for xt in (0.0, 0.0046, 0.0092, 0.0138):
    m = np.abs(P[:, 0] - xt) < 0.00035
    print('x=%.4f: n %d  z min %.4f max %.4f' % (xt, m.sum(), P[m, 2].min() if m.any() else np.nan, P[m, 2].max() if m.any() else np.nan))
