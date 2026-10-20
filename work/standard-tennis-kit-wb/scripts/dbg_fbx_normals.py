import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, bpy
from kitlib import *
blend = f'{WORK}/export/StandardKit_Female.blend'
bpy.ops.wm.open_mainfile(filepath=blend)
src = bpy.data.objects['Kit_Bottom_Skort_F_White']
me = src.data
cn_src = np.array([c.vector[:] for c in me.corner_normals])
pos_src = np.array([me.vertices[l.vertex_index].co[:] for l in me.loops])
print("src loops", len(me.loops), "verts", len(me.vertices), "polys", len(me.polygons))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=f'{WORK}/export/StdKit_Female_White.fbx')
imp = [o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('Kit_Bottom_Skort_F')][0]
m2 = imp.data
print("imp loops", len(m2.loops), "verts", len(m2.vertices), "polys", len(m2.polygons))
cn_imp = np.array([c.vector[:] for c in m2.corner_normals])
pos_imp = np.array([(imp.matrix_world @ m2.vertices[l.vertex_index].co)[:] for l in m2.loops])
if len(cn_src) == len(cn_imp):
    dpos = np.linalg.norm(pos_src - pos_imp, axis=1)
    print("loop position diff max (m):", dpos.max())
    ang = np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i', cn_src, cn_imp), -1, 1)))
    print("per-loop normal deviation: mean", ang.mean(), "p99", np.percentile(ang,99), "max", ang.max(), "n>1deg", int((ang>1).sum()), "of", len(ang))
    bad = np.nonzero(ang > 1)[0]
    if len(bad):
        # which polys / where
        pidx = np.array([me.loops[i].vertex_index for i in bad[:10]])
        print("bad loop positions:", pos_src[bad[:6]].round(3).tolist())
        print("src normals:", cn_src[bad[:4]].round(3).tolist()); print("imp normals:", cn_imp[bad[:4]].round(3).tolist())
        # face area of bad loops' polys
        loop_poly = np.zeros(len(me.loops), int)
        for p in me.polygons:
            for li in range(p.loop_start, p.loop_start + p.loop_total): loop_poly[li] = p.index
        pa = np.array([me.polygons[loop_poly[i]].area for i in bad[:20]])
        print("bad polys area (m2):", pa.round(8).tolist()[:10])
