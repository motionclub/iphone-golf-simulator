import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, bpy, bmesh
from kitlib import *
bpy.ops.wm.open_mainfile(filepath=f'{WORK}/export/StandardKit_Female.blend')
for nm in ('Kit_Sock_R_White', 'Kit_Sock_L_White'):
    o = bpy.data.objects[nm]
    bm = bmesh.new(); bm.from_mesh(o.data)
    for e in bm.edges:
        if len(e.link_faces) > 2:
            a, b = e.verts
            print(nm, "edge at", np.array(((a.co + b.co) / 2)[:]).round(4), "faces", len(e.link_faces), "len mm", round(e.calc_length() * 1000, 2))
    bm.free()
