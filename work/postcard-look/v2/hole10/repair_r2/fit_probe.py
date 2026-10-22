# probe: Procrustes (rotation + translation, scale fixed = 1/tile) fit of the three vertex UVs of the sliver triangles
import bpy, sys, math
import numpy as np
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=args[0])
TILE = 10.0
for name in ("FAIRWAY_FIRSTCUT", "FAIRWAY"):
    o = bpy.data.objects[name]; me = o.data; lay = me.uv_layers.active.data
    M = np.array(o.matrix_world)
    rows = []
    for p in me.polygons:
        idx = list(p.loop_indices)
        P = np.array([(M @ np.array([*me.vertices[me.loops[l].vertex_index].co, 1.0]))[:2] for l in idx]) / TILE
        U = np.array([lay[l].uv[:] for l in idx])
        # current ratio
        e = P[1:] - P[0]; d = U[1:] - U[0]
        det = np.linalg.det(d.T)
        if abs(det) < 1e-12: r = 1e3
        else:
            s = np.linalg.svd(e.T @ np.linalg.inv(d.T), compute_uv=False)
            r = s[0] / max(s[1], 1e-12)
        area = abs(np.cross(P[1] - P[0], P[2] - P[0])) / 2 * TILE * TILE
        if r > 2.0:
            pc, uc = P.mean(0), U.mean(0)
            Hc = (P - pc).T @ (U - uc)
            th = math.atan2(Hc[0, 1] - Hc[1, 0], Hc[0, 0] + Hc[1, 1])
            R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
            fitU = (P - pc) @ R.T + uc
            res = np.hypot(*(fitU - U).T) * TILE
            rows.append((name, p.index, round(float(r), 1), round(float(area), 1), np.round(res, 2).tolist(), round(math.degrees(th), 1)))
    for rr in rows: print('FIT', rr)
