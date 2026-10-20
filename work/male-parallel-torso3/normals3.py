"""Do the stored (custom) corner normals follow the edited geometry?  blender -b --python normals3.py -- <blend> <fbx> <out.json>
compares corner normals (blend, and re-imported FBX) against freshly recomputed angle-weighted vertex normals of the same geometry, inside the torso zone."""
import sys, json
import numpy as np, bpy
a = sys.argv[sys.argv.index('--') + 1:]; blend, fbx, outj = a
def zone(V): return (V[:, 2] >= 0.77) & (V[:, 2] < 1.40) & (np.abs(V[:, 0]) <= np.where(V[:, 2] < 1.2, 0.205, 0.28))
def analyse(me, M=None):
    n = len(me.vertices); V = np.empty(n * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    me.calc_loop_triangles()
    cn = np.empty(len(me.loops) * 3); me.corner_normals.foreach_get('vector', cn) if hasattr(me, 'corner_normals') else me.loops.foreach_get('normal', cn); cn = cn.reshape(-1, 3)
    lv = np.empty(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', lv)
    # recomputed angle-weighted vertex normals
    nv = np.zeros((n, 3)); polys = [list(p.vertices) for p in me.polygons]
    for p in polys:
        P = V[p]; m = len(p); fn = np.zeros(3)
        for k in range(1, m - 1): fn += np.cross(P[k] - P[0], P[k + 1] - P[0])
        l = np.linalg.norm(fn)
        if l < 1e-18: continue
        fn /= l
        for k in range(m):
            u = P[(k + 1) % m] - P[k]; w = P[(k - 1) % m] - P[k]; ang = np.arccos(np.clip(u @ w / max(np.linalg.norm(u) * np.linalg.norm(w), 1e-18), -1, 1)); nv[p[k]] += fn * ang
    nv /= np.maximum(np.linalg.norm(nv, axis=1, keepdims=True), 1e-18)
    Z = zone(V); sel = Z[lv]; ang = np.degrees(np.arccos(np.clip((cn[sel] * nv[lv[sel]]).sum(1), -1, 1)))
    return dict(has_custom_normals=bool(me.has_custom_normals), zone_corner_count=int(sel.sum()), angle_deg_median=float(np.median(ang)), angle_deg_p95=float(np.percentile(ang, 95)), angle_deg_p99=float(np.percentile(ang, 99)), angle_deg_max=float(ang.max()))
bpy.ops.wm.open_mainfile(filepath=blend); res = {'blend': analyse(bpy.data.objects['Body_M'].data)}
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=fbx)
imp = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]; res['fbx_reimport'] = analyse(imp.data)
json.dump(res, open(outj, 'w'), indent=1); print('NORMALS', json.dumps(res))
