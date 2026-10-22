"""Export Body_M to FBX with the original pipeline flags and verify by re-import. usage: blender -b --python export_fbx.py -- final.blend out.fbx report.json"""
import bpy, sys, json, hashlib, numpy as np
from pathlib import Path
from mathutils import kdtree
argv=sys.argv[sys.argv.index('--')+1:]
src,out,rep=[Path(a) for a in argv]
bpy.ops.wm.open_mainfile(filepath=str(src))
body=bpy.data.objects['Body_M']
for o in bpy.data.objects: o.select_set(False)
body.select_set(True); bpy.context.view_layer.objects.active=body
args=dict(use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,bake_anim=False)
bpy.ops.export_scene.fbx(filepath=str(out),**args)
sha=hashlib.sha256(out.read_bytes()).hexdigest()
src_co=np.array([v.co[:] for v in body.data.vertices])
# re-import into a clean scene and compare
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(out))
objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert len(objs)==1,len(objs)
imp=objs[0]
M=imp.matrix_world
co=np.array([(M@v.co)[:] for v in imp.data.vertices])
kd=kdtree.KDTree(len(co))
for i,c in enumerate(co): kd.insert(c,i)
kd.balance()
d=np.array([kd.find(tuple(c))[2] for c in src_co])
tris=sum(len(p.vertices)-2 for p in imp.data.polygons)
r=dict(fbx=str(out),fbx_sha256=sha,src_verts=len(src_co),imported_verts=len(co),imported_tris=int(tris),
       max_nearest_distance_mm=float(d.max()*1000),mean_nearest_distance_mm=float(d.mean()*1000),
       reimport_height_m=float(co[:,2].max()-co[:,2].min()),imported_scale=list(imp.scale),imported_rotation=[float(x) for x in imp.rotation_euler])
Path(rep).write_text(json.dumps(r,indent=2)); print(json.dumps(r,indent=2))
