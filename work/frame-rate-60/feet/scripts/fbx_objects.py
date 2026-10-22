"""Object list of FBX files (import into an empty scene):  blender -b --factory-startup --python scripts/fbx_objects.py -- <out.json> <fbx> ...   (GATE 2: no new object in the Serve FBX)"""
import json, sys
import bpy
a = sys.argv[sys.argv.index('--') + 1:]
out, files = a[0], a[1:]
res = {}
for f in files:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=f)
    res[f.split('/')[-1]] = sorted(f'{o.type}:{o.name.split(".")[0]}' for o in bpy.data.objects)
    print('FBXOBJ', f.split('/')[-1], len(bpy.data.objects))
json.dump(res, open(out, 'w'), indent=1)
