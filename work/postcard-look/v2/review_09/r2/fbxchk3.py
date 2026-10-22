import bpy, sys, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=sys.argv[-1])
out=[]
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith(('PLANT','ROCK','DRESS')):
        mw=o.matrix_world; vs=np.array([tuple(mw@v.co) for v in o.data.vertices]); c=vs.mean(0)
        if abs(c[0])<20 and abs(c[1])<20: out.append((o.name,c.round(1).tolist()))
print('props centred within 20m of tee:',len(out),out[:20])
