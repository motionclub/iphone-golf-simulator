"""Compare the CURRENT ArtDir blend against the start blend (Body_M positions) and against this chat's delta.  blender -b --python cmp_current.py -- <current.blend> <out.json>"""
import sys, json, numpy as np, bpy
a = sys.argv[sys.argv.index('--') + 1:]; cur, outj = a
D = np.load('export/f2_delta.npz'); idx = D['indices']; f32 = lambda x: x.astype(np.float32).astype(np.float64)
def read(p):
    bpy.ops.wm.open_mainfile(filepath=p); me = bpy.data.objects['Body_M'].data; V = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    fm = bpy.data.objects.get('Face_M'); F = None
    if fm: fv = np.empty(len(fm.data.vertices) * 3); fm.data.vertices.foreach_get('co', fv); F = fv.reshape(-1, 3)
    return V, [tuple(p.vertices) for p in me.polygons], F
V0, P0, F0 = read('baseline/HeroBase_Male_Silhouette.blend'); V1, P1, F1 = read(cur)
res = dict(topology_identical=P0 == P1, verts=(len(V0), len(V1)))
if len(V0) == len(V1):
    ch = np.any(f32(V0) != f32(V1), axis=1); res['body_verts_changed_vs_start'] = int(ch.sum())
    z = V0[:, 2]; res['changed_z_range_m'] = [float(z[ch].min()), float(z[ch].max())] if ch.any() else None
    res['changed_inside_my_delta_indices'] = int(ch[idx].sum()); res['delta_vertices'] = int(len(idx))
    cur_at = V1[idx]; res['delta_at_start_pos'] = int(np.all(cur_at == f32(D['base0']), axis=1).sum()); res['delta_at_new_pos'] = int(np.all(cur_at == f32(D['new']), axis=1).sum())
    res['changed_outside_delta_z_hist'] = {f'{lo:.1f}-{lo+0.2:.1f}': int(((z >= lo) & (z < lo + 0.2) & ch).sum()) for lo in np.arange(0, 1.8, 0.2)}
res['face_m_identical_to_start'] = bool(np.array_equal(F0, F1)) if F0 is not None and F1 is not None else None
json.dump(res, open(outj, 'w'), indent=1); print('CMP', json.dumps(res))
