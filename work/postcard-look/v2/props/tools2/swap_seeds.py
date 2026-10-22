"""Swap each baseline hole with several seeds; print stretch / composition / anchoring extremes. Scratch only."""
import sys, os, math, collections
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
import postcard_props_lib as PL
for hole in ("08", "09", "10"):
    for seed in (1, 2, 3, 4, 5, 77):
        bpy.ops.wm.open_mainfile(filepath=f"{R}/work/postcard-look/baseline/blender/hole_{hole}.blend")
        PL._COUNTERS.clear()
        leg = {}
        for o in PL.legacy_rocks():
            co = np.array([list(o.matrix_world @ v.co) for v in o.data.vertices]); leg[o.name] = (co.min(0), co.max(0))
        rep = []
        out = PL.swap_legacy_rocks(None, basalt=(hole == "10"), seed=seed, report=rep)
        mem = {r["legacy"]: r["members"] for r in rep}
        bpy.context.view_layer.update()
        sr = PL.stretch_report(); cr = PL.swap_composition_report()
        sc = np.array([s for _o, s in PL.instance_scales()])
        g = collections.defaultdict(list)
        for o in out: g[o["lk_swap"]].append(o)
        db, dt = [], []
        for k, v in g.items():
            pts = np.concatenate([np.array([list(o.matrix_world @ vv.co) for vv in o.data.vertices]) for o in v])
            a2, b2 = min(leg[m][0][2] for m in mem[k]), max(leg[m][1][2] for m in mem[k])
            db.append(pts[:, 2].min() - a2); dt.append(pts[:, 2].max() - b2)
        print(f"{hole} seed {seed}: n {len(out)} scale {sc.min():.3f}..{sc.max():.3f} max/min {sr['max_ratio']:.3f} viol {len(sr['violations'])} | "
              f"stacks {len(cr['vertical_stacks'])} clones {len(cr['clones'])} | bottom min {min(db):.2f} top {min(dt):.2f}..{max(dt):.2f} | "
              f"tris {sum(len(o.data.polygons) for o in out)}")
