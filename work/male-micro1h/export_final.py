"""Export Body_M + Face_M from a final blend to FBX (original pipeline flags) and verify by re-import.
blender -b --factory-startup --python export_final.py -- <final.blend> <out.fbx> <report.json>"""
import sys, json, hashlib
from pathlib import Path
import numpy as np
import bpy
from mathutils.kdtree import KDTree
argv = sys.argv[sys.argv.index('--') + 1:]
blend, out_fbx, report = Path(argv[0]), Path(argv[1]), Path(argv[2])
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(blend))
body = bpy.data.objects['Body_M']; face = bpy.data.objects['Face_M']
for o in bpy.data.objects: o.select_set(False)
body.select_set(True); face.select_set(True); bpy.context.view_layer.objects.active = body
args = dict(use_selection=True, object_types={'MESH'}, global_scale=1, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
            axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True, mesh_smooth_type='OFF', add_leaf_bones=False, bake_anim=False, path_mode='COPY')
bpy.ops.export_scene.fbx(filepath=str(out_fbx), **args)
src = {}
for name, o in (('Body_M', body), ('Face_M', face)):
    src[name] = np.array([v.co[:] for v in o.data.vertices], float)
body_tris = sum(len(p.vertices) - 2 for p in body.data.polygons); face_tris = sum(len(p.vertices) - 2 for p in face.data.polygons)
face_slots = [m.name for m in face.data.materials]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(out_fbx))
objs = {o.name: o for o in bpy.context.scene.objects if o.type == 'MESH'}
res = dict(blend_sha256=sha(blend), fbx_sha256=sha(out_fbx), body_tris=body_tris, face_tris=face_tris, face_slots=face_slots, imported_objects=sorted(objs))
for name in ('Body_M', 'Face_M'):
    o = objs[name]; M = o.matrix_world
    co = np.array([(M @ v.co)[:] for v in o.data.vertices])
    kd = KDTree(len(co))
    for i, c in enumerate(co): kd.insert(c, i)
    kd.balance()
    d = np.array([kd.find(tuple(c))[2] for c in src[name]])
    res[name] = dict(verts=len(co), tris=sum(len(p.vertices) - 2 for p in o.data.polygons), max_reimport_mm=float(d.max() * 1000),
                     materials=[m.name if m else None for m in o.data.materials], height_m=float(co[:, 2].max() - co[:, 2].min()) if name == 'Body_M' else None)
report.write_text(json.dumps(res, indent=1)); print('EXPORT_JSON ' + json.dumps({k: res[k] for k in ('body_tris', 'face_tris', 'fbx_sha256')}))
