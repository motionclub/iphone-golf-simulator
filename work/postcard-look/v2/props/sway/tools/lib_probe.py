import sys, os, json
import numpy as np
sys.dont_write_bytecode = True
HERE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "..", "blender", "scripts"))
sys.path.insert(0, HERE)
import bpy
import postcard_props_lib as PL
bpy.ops.wm.read_factory_settings(use_empty=True)
lib = PL.ensure_library()
rep = PL.library_report()
for k in sorted(rep):
    if k.startswith("PLANT_"):
        me = PL.library_object(k).data
        sw = PL.mesh_sway(me)
        z = np.array([v.co.z for v in me.vertices])
        print(f"{k:22s} verts {rep[k]['verts']:4d} faces {rep[k]['faces']:4d} tris {rep[k]['tris']:4d} h {z.max():.2f}  cls {sw['cls']:7s} R max {sw['R'].max():.2f} R@z<=0.01 {sw['R'][z<=0.01].max() if (z<=0.01).any() else -1:.3f}  G {sw['G'].min():.2f}-{sw['G'].max():.2f} B {sw['B'].max():.0f} A {sw['A'].min():.0f}")
