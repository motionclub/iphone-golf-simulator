import bpy, numpy as np
for ob in bpy.data.objects:
    if ob.type!='MESH' or not ob.name.startswith(('PLANT_','ROCK_','DRESS_BLOCK')): continue
    mw=np.array(ob.matrix_world); co=np.array([v.co[:] for v in ob.data.vertices]); w=co@mw[:3,:3].T+mw[:3,3]
    if w[:,2].min()>7.0:
        print(ob.name, 'zmin %.2f zmax %.2f'%(w[:,2].min(), w[:,2].max()), 'xy', w[:,:2].mean(0).round(1))
