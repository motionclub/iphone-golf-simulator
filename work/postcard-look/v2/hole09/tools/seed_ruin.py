import bpy, sys, numpy as np, math
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import postcard_props_lib as PL, postcard_lib as P
import hole09_look as HL
YD = 0.9144
def prof(objs, a, b, base=0.0, step=0.5):
    d = (b - a); L = np.hypot(*d); d /= L
    V = []
    for o in objs:
        me = o.data
        for v in me.vertices: 
            w = o.matrix_world @ v.co; V.append((w.x, w.y, w.z))
    V = np.array(V)
    s = (V[:, 0] - a[0]) * d[0] + (V[:, 1] - a[1]) * d[1]
    out = []
    for s0 in np.arange(0, L, step):
        m = (s >= s0) & (s < s0 + step)
        out.append((V[m, 2].max() - base, V[m, 2].min() - base) if m.any() else (0.0, 0.0))
    return np.array(out)
walls = [dict(p0=(-67.0, 94.0), p1=(-58.0, 93.0)), dict(p0=(-67.0, 94.0), p1=(-68.0, 109.0)), dict(p0=(-68.0, 109.0), p1=(-58.0, 112.0)), dict(p0=(-58.0, 93.0), p1=(-57.0, 99.0))]
rc = np.array(P.m(sum(w[k][0] for w in walls for k in ("p0","p1"))/8.0, sum(w[k][1] for w in walls for k in ("p0","p1"))/8.0))
big = lambda p: tuple(rc + (np.array(P.m(*p)) - rc) * 1.2)
a, b = np.array(big(walls[2]["p0"])), np.array(big(walls[2]["p1"]))
res = []
for seed in range(26, 90):
    for o in [o for o in bpy.data.objects if o.name.startswith("DRESS_")]: bpy.data.objects.remove(o)
    r = PL.build_ruin(None, [tuple(a), tuple(b)], height_m=5.6, thickness_m=1.5, doorway_at=0.5, doorway_w=2.1, doorway_h=2.6, seed=seed, course_h=0.85, block_l=(1.3, 2.1), base_z=0.0, name=f"DRESS_RUIN_T{seed}", fallen=False)
    bpy.context.view_layer.update()
    pr = prof(r["walls"], a, b)
    mx = pr[:, 0]
    L = len(mx)
    door = [(i, p) for i, p in enumerate(pr) if p[1] > 1.5]
    frac4 = float((mx >= 4.0).mean()); frac3 = float((mx >= 3.0).mean()); gaps = float((mx < 0.5).mean())
    res.append((seed, round(mx.max(), 2), round(frac4, 2), round(frac3, 2), round(gaps, 2), len(door)))
for r in sorted(res, key=lambda r: -(r[2] * 2 + r[3] - r[4] * 2 + (0.3 if r[5] >= 3 else 0)))[:12]:
    print(r)
