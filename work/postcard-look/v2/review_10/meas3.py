import bpy,numpy as np,collections
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath='work/postcard-look/v2/hole10/stage/hole_10.fbx')
objs=[o for o in bpy.data.objects if o.type=='MESH']
print("FBX meshes",len(objs),"tris",sum(len(p.vertices)-2 for o in objs for p in o.data.polygons))
print("names templ",[o.name for o in objs if o.name.endswith(('_A','_B')) and 'PLANT' in o.name][:10])
print("FBX rocks",sum(o.name.startswith('ROCK_') for o in objs),"plants",sum(o.name.startswith('PLANT_') for o in objs))
# location of any plant/rock at origin
for o in objs:
    if o.name.startswith(('PLANT_','ROCK_')) and np.linalg.norm(np.array(o.matrix_world.translation))<1: print("AT ORIGIN",o.name)
print("empties",[o.name for o in bpy.data.objects if o.type=='EMPTY' and 'LAVA' in o.name])
# tuft scales/ plants stats
mats=collections.Counter(s.material.name for o in objs for s in o.material_slots if s.material); print(mats)
