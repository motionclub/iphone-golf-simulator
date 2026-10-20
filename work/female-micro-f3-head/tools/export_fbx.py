"""Export Body_F + Face_F from the assembled blend to FBX (same flags as the male pipeline) and verify by re-import (positions AND shading normals: MicroF3 carries custom normals).
blender -b --factory-startup --python export_fbx.py -- <assembled.blend> <out.fbx> <report.json>"""
import sys, json, hashlib
from pathlib import Path
import numpy as np
import bpy
from mathutils.kdtree import KDTree
argv = sys.argv[sys.argv.index('--') + 1:]
blend, out_fbx, report = Path(argv[0]), Path(argv[1]), Path(argv[2])
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(blend))
body = bpy.data.objects['Body_F']; face = bpy.data.objects['Face_F']
for o in bpy.data.objects: o.select_set(False)
body.select_set(True); face.select_set(True); bpy.context.view_layer.objects.active = body
args = dict(use_selection=True, object_types={'MESH'}, global_scale=1, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
            axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True, mesh_smooth_type='OFF', add_leaf_bones=False, bake_anim=False, path_mode='COPY')
out_fbx.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.fbx(filepath=str(out_fbx), **args)
src = {n: np.array([v.co[:] for v in o.data.vertices], float) for n, o in (('Body_F', body), ('Face_F', face))}
def loop_data(o, world):
    me = o.data; n = len(me.loops)
    cn = np.empty(n * 3); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
    lv = np.empty(n, np.int32); me.loops.foreach_get('vertex_index', lv)
    co = np.array([v.co[:] for v in me.vertices], float); P = co[lv]
    if world:
        M = np.array(o.matrix_world); P = (M[:3, :3] @ P.T).T + M[:3, 3]; cn = (M[:3, :3] @ cn.T).T
    cn = cn / np.maximum(np.linalg.norm(cn, axis=1, keepdims=True), 1e-12)
    return P, cn
src_loops = {n: loop_data(o, False) for n, o in (('Body_F', body), ('Face_F', face))}
body_tris = sum(len(p.vertices) - 2 for p in body.data.polygons); face_tris = sum(len(p.vertices) - 2 for p in face.data.polygons)
face_slots = [m.name for m in face.data.materials]; body_slots = [m.name for m in body.data.materials]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(out_fbx))
objs = {o.name: o for o in bpy.context.scene.objects if o.type == 'MESH'}
res = dict(blend_sha256=sha(blend), fbx_sha256=sha(out_fbx), body_tris=body_tris, face_tris=face_tris, face_slots=face_slots, body_slots=body_slots, imported_objects=sorted(objs))
for name in ('Body_F', 'Face_F'):
    o = objs[name]; M = o.matrix_world
    co = np.array([(M @ v.co)[:] for v in o.data.vertices])
    kd = KDTree(len(co))
    for i, c in enumerate(co): kd.insert(c, i)
    kd.balance()
    d = np.array([kd.find(tuple(c))[2] for c in src[name]])
    Pl, Nl = loop_data(o, True); Ps, Ns = src_loops[name]
    kd2 = KDTree(len(Pl))
    for i, c in enumerate(Pl): kd2.insert(c, i)
    kd2.balance()
    sel = np.where(Ps[:, 2] > 1.40)[0] if name == 'Body_F' else np.arange(len(Ps))      # head loops of Body_F / all Face_F loops
    # loops that share a position with another loop of a DIFFERENT normal (coincident verts of separate paint shells) cannot be matched by position: excluded and counted
    kds = KDTree(len(Ps))
    for i, c in enumerate(Ps): kds.insert(c, i)
    kds.balance()
    amb = []
    for i in sel:
        for (_, j, dd) in kds.find_range(tuple(Ps[i]), 1e-7):
            if j != i and float(np.dot(Ns[i], Ns[j])) < np.cos(np.radians(0.5)): amb.append(i); break
    amb = set(amb); sel = np.array([i for i in sel if i not in amb])
    idx = np.array([kd2.find(tuple(Ps[i]))[1] for i in sel])
    ang = np.degrees(np.arccos(np.clip((Ns[sel] * Nl[idx]).sum(1), -1, 1)))
    res[name + '_normals'] = dict(loops_checked=int(len(sel)), ambiguous_coincident_loops_skipped=int(len(amb)), max_deg=float(ang.max()), mean_deg=float(ang.mean()), p99_deg=float(np.percentile(ang, 99)), over_1deg=int((ang > 1.0).sum()))
    res[name] = dict(verts=len(co), tris=sum(len(p.vertices) - 2 for p in o.data.polygons), max_reimport_mm=float(d.max() * 1000),
                     materials=[m.name if m else None for m in o.data.materials], height_m=float(co[:, 2].max() - co[:, 2].min()) if name == 'Body_F' else None)
report.write_text(json.dumps(res, indent=1)); print('EXPORT_JSON ' + json.dumps({k: res[k] for k in ('body_tris', 'face_tris', 'fbx_sha256', 'Body_F_normals', 'Face_F_normals')}))
