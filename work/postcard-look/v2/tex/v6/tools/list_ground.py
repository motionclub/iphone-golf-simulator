import bpy, sys, numpy as np
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
n=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=R+f'blender/hole_{n}.blend')
for o in sorted(bpy.data.objects, key=lambda o:o.name):
    if o.type!='MESH' or not o.name.startswith(('TERRAIN','FAIRWAY','GREEN','TEE','BUNKER','CART','ROUGH')): continue
    me=o.data; M=np.array(o.matrix_world)
    co=np.array([v.co[:] for v in me.vertices]); co=(M[:3,:3]@co.T).T+M[:3,3]
    mats=[(m.name if m else None) for m in me.materials]
    # blender z up -> unity y; blender y -> unity z; yards? report metres bounds
    print(f'{o.name:24s} verts {len(me.vertices):6d} mats {mats} bbox x[{co[:,0].min():.0f},{co[:,0].max():.0f}] y[{co[:,1].min():.0f},{co[:,1].max():.0f}] z[{co[:,2].min():.1f},{co[:,2].max():.1f}]')
