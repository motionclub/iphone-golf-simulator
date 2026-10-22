"""UV Jacobian anisotropy (texture stretch) of meshes: per triangle the singular-value ratio of d(uv*tile)/d(surface); area-weighted p50/p95, share of area > 2x, share degenerate.
usage: Blender -b --factory-startup --python uv_stretch.py -- [blend]   (no blend: the props library DRESS_BLOCK_A/B + arch + spires)"""
import sys, os
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy, numpy as np
import postcard_props_lib as PL
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def uvstats(ob, tile=None):
    me = ob.data
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    co = np.empty(len(me.vertices)*3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    M = np.array(ob.matrix_world)
    co = (co @ M[:3, :3].T)
    idx = np.empty(nt*3, np.int32); me.loop_triangles.foreach_get("vertices", idx); idx = idx.reshape(-1, 3)
    lo = np.empty(nt*3, np.int32); me.loop_triangles.foreach_get("loops", lo); lo = lo.reshape(-1, 3)
    uv = np.empty(len(me.loops)*2); me.uv_layers.active.data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
    pm = np.empty(nt, np.int32); me.loop_triangles.foreach_get("material_index", pm)
    mats = [m.name if m else "" for m in me.materials]
    tl = np.array([PL.TILE.get(mats[k], 4.0) if k < len(mats) else 4.0 for k in pm.tolist()]) if tile is None else np.full(nt, tile)
    P0, P1, P2 = co[idx[:, 0]], co[idx[:, 1]], co[idx[:, 2]]
    U0, U1, U2 = uv[lo[:, 0]], uv[lo[:, 1]], uv[lo[:, 2]]
    e1, e2 = P1 - P0, P2 - P0
    n = np.cross(e1, e2); A3 = 0.5*np.linalg.norm(n, axis=1)
    f1, f2 = (U1 - U0)*tl[:, None], (U2 - U0)*tl[:, None]
    Auv = 0.5*np.abs(f1[:, 0]*f2[:, 1] - f1[:, 1]*f2[:, 0])
    out = []
    ratio = np.ones(nt); degen = (A3 > 1e-9) & (Auv < 1e-4*A3)
    for i in range(nt):
        if A3[i] < 1e-9: continue
        # basis in the plane
        t1 = e1[i]/np.linalg.norm(e1[i]); nn = n[i]/np.linalg.norm(n[i]); t2 = np.cross(nn, t1)
        p = np.array([[np.dot(e1[i], t1), np.dot(e1[i], t2)], [np.dot(e2[i], t1), np.dot(e2[i], t2)]])
        q = np.array([f1[i], f2[i]])
        try:
            J = np.linalg.solve(p, q)      # surface -> uv*tile
            sv = np.linalg.svd(J, compute_uv=False)
            ratio[i] = sv[0]/max(sv[1], 1e-9)
        except np.linalg.LinAlgError:
            ratio[i] = 1e9
    w = A3 / A3.sum()
    o = np.argsort(ratio); cw = np.cumsum(w[o])
    p50 = ratio[o][np.searchsorted(cw, 0.5)]; p95 = ratio[o][min(np.searchsorted(cw, 0.95), nt-1)]
    return dict(tris=nt, p50=float(p50), p95=float(p95), over2=float(w[ratio > 2.0].sum()), over4=float(w[ratio > 4.0].sum()), degen=float(w[degen].sum()))
if a:
    bpy.ops.wm.open_mainfile(filepath=a[0])
    pref = a[1] if len(a) > 1 else "ROCK_SKIN"
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith(pref):
            print("UVS", o.name, uvstats(o))
else:
    PL.ensure_library(["DRESS_BLOCK_A", "DRESS_BLOCK_B"] + list(PL.SEASTACK_KINDS))
    for k in ["DRESS_BLOCK_A", "DRESS_BLOCK_B"] + list(PL.SEASTACK_KINDS):
        print("UVS", k, uvstats(PL.library_object(k)))
    r = PL.build_masonry_arch(None, (0, 0, 0), 0.0, span_m=7.5, height_m=11.0, seed=8, base_rock=False, vines=False)
    print("UVS arch", uvstats(r["arch"]))
