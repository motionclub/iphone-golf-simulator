"""UV anisotropy of ROCK_SKIN pieces the way postcard_look_verify.uv_anisotropy measures it. Blender -b --python uv_aniso.py -- BLEND [objprefix]"""
import sys, os
sys.dont_write_bytecode = True
import numpy as np, bpy
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--") + 1])
pref = sys.argv[sys.argv.index("--") + 2] if len(sys.argv) > sys.argv.index("--") + 2 else "ROCK_SKIN"
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.startswith(pref): continue
    me = o.data; me.calc_loop_triangles()
    V = np.array([tuple(o.matrix_world @ v.co) for v in me.vertices])
    uvl = me.uv_layers[0].data
    tri = me.loop_triangles
    T = np.array([t.vertices[:] for t in tri]); LI = np.array([t.loops[:] for t in tri])
    uv = np.array([[uvl[l].uv[:] for l in tl] for tl in LI])
    a, b, c = V[T[:,0]], V[T[:,1]], V[T[:,2]]
    e1, e2 = b - a, c - a
    n1 = np.linalg.norm(e1, axis=1); ok = n1 > 1e-9
    x = e1 / np.maximum(n1, 1e-12)[:, None]
    nrm = np.cross(e1, e2); ln = np.linalg.norm(nrm, axis=1); ok &= ln > 1e-12
    y = np.cross(nrm / np.maximum(ln, 1e-12)[:, None], x)
    P = np.stack([np.stack([(e1*x).sum(1), (e1*y).sum(1)], 1), np.stack([(e2*x).sum(1), (e2*y).sum(1)], 1)], 1)
    Uv = np.stack([uv[:,1]-uv[:,0], uv[:,2]-uv[:,0]], 1)
    det = P[:,0,0]*P[:,1,1]-P[:,0,1]*P[:,1,0]; ok &= np.abs(det) > 1e-14
    Pi = np.linalg.inv(P[ok]); J = np.matmul(Pi, Uv[ok]); sv = np.linalg.svd(J, compute_uv=False)
    ratio = sv[:,0] / np.maximum(sv[:,1], 1e-12); A = 0.5 * ln[ok]
    frac = A[ratio > 4].sum() / A.sum()
    # density ratio (1/tile expected ~ sv geometric mean * tile)
    print(o.name, "tris", int(ok.sum()), "area>4:1 %.1f%%" % (100*frac), "mean %.1f" % np.average(np.minimum(ratio,1e3), weights=A), "median ratio %.2f" % np.median(ratio))
    if "-v" in sys.argv:
        bad = np.argsort(-(ratio*(A>0.05)))[:5]
        for k in bad: print("   worst ratio %.1f area %.2f at %s" % (ratio[k], A[k], a[ok][k].round(1)))
