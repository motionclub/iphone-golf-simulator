import sys, os, math, time, collections
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
import postcard_props_lib as PL
hole = os.environ.get("HOLE", "10")
bpy.ops.wm.open_mainfile(filepath=R + f"/work/postcard-look/baseline/blender/hole_{hole}.blend")
before = len(PL.legacy_rocks())
t = time.time()
rep = []
out = PL.swap_legacy_rocks(None, basalt=(hole == "10"), report=rep, seed=1)
dt = time.time() - t
bpy.context.view_layer.update()
sr = PL.stretch_report()
print(f"HOLE {hole}: legacy {before} -> {len(out)} instances in {dt:.1f}s; stretch ok={sr['ok']} n={sr['n']} scale {sr['min_scale']:.2f}..{sr['max_scale']:.2f} max ratio {sr['max_ratio']:.2f} violations {len(sr['violations'])} {sr['violations'][:3]}")
kinds = collections.Counter(o.data.name for o in out)
print(dict(kinds))
tris = 0
for o in out:
    o.data.calc_loop_triangles(); tris += len(o.data.loop_triangles)
print("tris", tris)
print("assert", PL.assert_no_legacy_rocks(None, raise_on_fail=False))
multi = [r for r in rep if r["instances"] > 1]
print("multi-instance plans", len(multi), multi[:3])
errs = np.array([r["err"] for r in rep])
print("box err (sum |log|) mean %.3f p90 %.3f max %.3f" % (errs.mean(), np.percentile(errs, 90), errs.max()))

if os.environ.get("RENDER"):
    import postcard_props_smoke as S  # noqa  (argv hack below)
