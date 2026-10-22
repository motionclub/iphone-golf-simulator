"""Phase 0: inspect the Micro1g lock (read-only). blender -b --factory-startup --python inspect0.py -- <blend>"""
import sys, json
import numpy as np
import bpy, bmesh

blend = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=blend)
out = {}
out['objects'] = [(o.name, o.type, tuple(round(c, 4) for c in o.location), tuple(round(c, 4) for c in o.scale)) for o in bpy.data.objects]
body = bpy.data.objects['Body_M']
me = body.data
out['mods'] = [m.type for m in body.modifiers]
out['vgroups'] = [g.name for g in body.vertex_groups]
out['shape_keys'] = [k.name for k in me.shape_keys.key_blocks] if me.shape_keys else []
out['uv'] = [u.name for u in me.uv_layers]
out['attrs'] = [(a.name, a.domain, a.data_type) for a in me.attributes]
out['materials'] = [m.name if m else None for m in me.materials]
out['n_verts'] = len(me.vertices); out['n_polys'] = len(me.polygons); out['n_edges'] = len(me.edges)
out['poly_sizes'] = {int(k): int(v) for k, v in zip(*np.unique([len(p.vertices) for p in me.polygons], return_counts=True))}
V = np.array([v.co[:] for v in me.vertices])
out['bbox'] = [V.min(0).tolist(), V.max(0).tolist()]
# head zone
z = V[:, 2]
for zc in (1.40, 1.43, 1.45, 1.47, 1.50, 1.55, 1.60, 1.65):
    m = z > zc
    out[f'verts_z>{zc}'] = int(m.sum())
# edge length stats in head zone
E = np.array([e.vertices[:] for e in me.edges])
L = np.linalg.norm(V[E[:, 0]] - V[E[:, 1]], axis=1)
zm = (V[E[:, 0], 2] + V[E[:, 1], 2]) / 2
for lo, hi in ((1.43, 1.47), (1.47, 1.52), (1.52, 1.58), (1.58, 1.64), (1.64, 1.72), (1.43, 1.72)):
    m = (zm > lo) & (zm <= hi)
    out[f'edge_mm z{lo}-{hi}'] = dict(n=int(m.sum()), mean=float(L[m].mean() * 1000), min=float(L[m].min() * 1000), max=float(L[m].max() * 1000))
# cameras and empties
s = bpy.context.scene
out['scene'] = dict(engine=s.render.engine, unit=s.unit_settings.system, scale=s.unit_settings.scale_length, res=(s.render.resolution_x, s.render.resolution_y))
cams = {}
for o in bpy.data.objects:
    if o.type == 'CAMERA':
        cams[o.name] = dict(loc=[round(c, 4) for c in o.location], rot=[round(c, 4) for c in o.rotation_euler], type=o.data.type, ortho=round(o.data.ortho_scale, 4), shift=(round(o.data.shift_x, 4), round(o.data.shift_y, 4)))
out['cams'] = cams
out['empties'] = {o.name: dict(loc=[round(c, 4) for c in o.location], rot=[round(c, 4) for c in o.rotation_euler], scale=[round(c, 4) for c in o.scale]) for o in bpy.data.objects if o.type == 'EMPTY'}
out['face_M'] = bool(bpy.data.objects.get('Face_M'))
# manifold / boundary
bm = bmesh.new(); bm.from_mesh(me)
out['boundary_edges'] = sum(1 for e in bm.edges if e.is_boundary)
out['nonmanifold_edges'] = sum(1 for e in bm.edges if not e.is_manifold)
out['loose_verts'] = sum(1 for v in bm.verts if not v.link_edges)
val = np.array([len(v.link_edges) for v in bm.verts])
out['valence_hist'] = {int(k): int(c) for k, c in zip(*np.unique(val, return_counts=True))}
# neck: ring of verts near z where the head narrows. Slice widths by z in the neck/head
for zc in np.arange(1.36, 1.72, 0.02):
    m = (np.abs(V[:, 2] - zc) < 0.004) & (np.abs(V[:, 0]) < 0.25)
    if m.any():
        out[f'slice z{zc:.2f}'] = dict(n=int(m.sum()), xmin=round(float(V[m, 0].min()), 4), xmax=round(float(V[m, 0].max()), 4), ymin=round(float(V[m, 1].min()), 4), ymax=round(float(V[m, 1].max()), 4))
print('INSPECT_JSON ' + json.dumps(out))
