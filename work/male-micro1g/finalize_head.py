"""Headless delivery: open the Micro1f lock, sculpt Body_M head (positions only), build Face_M, save new blend, export FBX
(Body_M + Face_M), verify by re-import.  blender -b --factory-startup --python finalize_head.py -- <params.json|-> <out.blend> <out.fbx> <report.json>"""
import sys, json, hashlib
from pathlib import Path
import numpy as np
import bpy
from mathutils.kdtree import KDTree

W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1g')
E = W.parent / 'male-micro1e'
for p in (str(W), str(E)):
    if p not in sys.path:
        sys.path.insert(0, p)
import head_lock as hl, face_layers as fl

argv = sys.argv[sys.argv.index('--') + 1:]
params = json.loads(Path(argv[0]).read_text()) if argv[0] != '-' else {}
out_blend, out_fbx, report = Path(argv[1]), Path(argv[2]), Path(argv[3])
LOCK = W / 'baseline/HeroBase_Male_Silhouette.blend'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
lock_sha = sha(LOCK)

bpy.ops.wm.open_mainfile(filepath=str(LOCK))
body = bpy.data.objects['Body_M']
base = np.array([v.co[:] for v in body.data.vertices], float)
moved, V = hl.sculpt(body, base, params)
face = fl.Layers(body).build()
face.parent = None
bpy.ops.wm.save_as_mainfile(filepath=str(out_blend))
assert sha(LOCK) == lock_sha

# ---- export Body_M + Face_M
for o in bpy.data.objects:
    o.select_set(False)
body.select_set(True); face.select_set(True); bpy.context.view_layer.objects.active = body
args = dict(use_selection=True, object_types={'MESH'}, global_scale=1, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
            axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True, mesh_smooth_type='OFF', add_leaf_bones=False, bake_anim=False, path_mode='COPY')
bpy.ops.export_scene.fbx(filepath=str(out_fbx), **args)
src_body = V.copy()
src_face = np.array([v.co[:] for v in face.data.vertices], float)
body_tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
face_tris = sum(len(p.vertices) - 2 for p in face.data.polygons)
face_slots = [m.name for m in face.data.materials]
# ---- re-import check
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(out_fbx))
objs = {o.name: o for o in bpy.context.scene.objects if o.type == 'MESH'}
res = dict(lock_blend_sha256=lock_sha, out_blend_sha256=sha(out_blend), fbx_sha256=sha(out_fbx), head_verts_moved=moved,
           body_tris=body_tris, face_tris=face_tris, face_slots=face_slots, imported_objects=sorted(objs))
for name, src in (('Body_M', src_body), ('Face_M', src_face)):
    o = objs[name]; M = o.matrix_world
    co = np.array([(M @ v.co)[:] for v in o.data.vertices])
    kd = KDTree(len(co))
    for i, c in enumerate(co): kd.insert(c, i)
    kd.balance()
    d = np.array([kd.find(tuple(c))[2] for c in src])
    res[name] = dict(verts=len(co), tris=sum(len(p.vertices) - 2 for p in o.data.polygons), max_reimport_mm=float(d.max() * 1000),
                     materials=[m.name if m else None for m in o.data.materials])
report.write_text(json.dumps(res, indent=1)); print('FINALIZE_JSON ' + json.dumps(res))
