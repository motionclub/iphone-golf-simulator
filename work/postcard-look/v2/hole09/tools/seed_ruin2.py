import bpy, sys, numpy as np, math
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import postcard_props_lib as PL, postcard_lib as P
YD = 0.9144
walls = [dict(p0=(-67.0, 94.0), p1=(-58.0, 93.0)), dict(p0=(-67.0, 94.0), p1=(-68.0, 109.0)), dict(p0=(-68.0, 109.0), p1=(-58.0, 112.0)), dict(p0=(-58.0, 93.0), p1=(-57.0, 99.0))]
rc = np.array(P.m(sum(w[k][0] for w in walls for k in ("p0","p1"))/8.0, sum(w[k][1] for w in walls for k in ("p0","p1"))/8.0))
big = lambda p: tuple(rc + (np.array(P.m(*p)) - rc) * 1.2)
def pol_samples(path, step=0.5):
    pts = [np.array(p) for p in path]; out = []
    for i in range(len(pts)-1):
        L = np.hypot(*(pts[i+1]-pts[i])); n = max(1, int(L/step))
        for k in range(n): out.append(pts[i] + (pts[i+1]-pts[i]) * k / n)
    return np.array(out)
def evalr(objs, path, base=0.0):
    V = np.array([tuple(o.matrix_world @ v.co) for o in objs for v in o.data.vertices])
    S = pol_samples(path); top = []
    for s in S:
        m = np.hypot(V[:,0]-s[0], V[:,1]-s[1]) < 0.9
        top.append(V[m,2].max()-base if m.any() else 0.0)
    return np.array(top)
cases = {"west_north": ([big(walls[0]["p1"]), big(walls[0]["p0"]), big(walls[1]["p1"])], 4.0), "stub": ([big(walls[3]["p0"]), big(walls[3]["p1"])], 3.4)}
for nm, (path, h) in cases.items():
    res = []
    for seed in range(27, 80):
        for o in [o for o in bpy.data.objects if o.name.startswith("DRESS_")]: bpy.data.objects.remove(o)
        r = PL.build_ruin(None, path, height_m=h, thickness_m=1.5, doorway_at=None, seed=seed, course_h=0.85, block_l=(1.3, 2.1), base_z=0.0, name=f"DRESS_RUIN_T{seed}", fallen=False)
        bpy.context.view_layer.update()
        t = evalr(r["walls"], path)
        res.append((seed, round(float(t.max()),2), round(float((t >= 0.6*h).mean()),2), round(float((t < 0.5).mean()),2)))
    print(nm, sorted(res, key=lambda r: -(r[2] - 2*r[3]))[:6])
