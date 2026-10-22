import bpy, sys, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=sys.argv[-1])
names=['PLANT_SHRUB_A','PLANT_AGAVE_A','ROCK_CRAG_A','ROCK_CRAG_B','ROCK_SEASTACK_B','DRESS_BLOCK_A','ROCK_BLOCK_A','ROCK_LEDGE_A']
for o in bpy.data.objects:
    if o.type=='MESH' and (o.name in names or o.name.split('.')[0] in names):
        mw=o.matrix_world; vs=np.array([tuple(mw@v.co) for v in o.data.vertices]); 
        print(o.name,'parent',o.parent.name if o.parent else None,'bbox',vs.min(0).round(2),vs.max(0).round(2))
