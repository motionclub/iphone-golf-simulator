"""Swap one baseline hole blend (HOLE=08|09|10, SEED=n) and print stretch / composition / anchoring numbers. Scratch only: never saves."""
import sys, os, math, collections, time
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
import postcard_props_lib as PL
hole = os.environ.get("HOLE", "09"); seed = int(os.environ.get("SEED", "1"))
bpy.ops.wm.open_mainfile(filepath=f"{R}/work/postcard-look/baseline/blender/hole_{hole}.blend")
leg = {}
for o in PL.legacy_rocks():
    co = np.array([list(o.matrix_world @ v.co) for v in o.data.vertices]); leg[o.name] = (co.min(0), co.max(0))
rep = []
t0 = time.time()
out = PL.swap_legacy_rocks(None, basalt=(hole == "10"), seed=seed, report=rep)
dt = time.time() - t0
bpy.context.view_layer.update()
sr = PL.stretch_report()
cr = PL.swap_composition_report()
print(f"HOLE {hole} seed {seed}: legacy {len(rep)} -> {len(out)} instances in {dt:.1f}s; classes {dict(collections.Counter(r['cls'] for r in rep))}")
print(f"  stretch: n {sr['n']} scale {sr['min_scale']:.3f}..{sr['max_scale']:.3f} max/min {sr['max_ratio']:.3f} violations {len(sr['violations'])}")
print(f"  composition: ok {cr['ok']} groups {cr['groups']} pieces {cr['pieces']} vertical stacks {len(cr['vertical_stacks'])} {cr['vertical_stacks'][:4]} clones {len(cr['clones'])} {cr['clones'][:4]}")
print("  kinds:", dict(collections.Counter(o.data.name for o in out)))
multi = [r for r in rep if r["instances"] > 1]
print("  multi-instance boxes:", len(multi), [(r["legacy"], r["cls"], r["box"], r["n"], r["instances"]) for r in multi[:12]])
g = collections.defaultdict(list)
for o in out: g[o["lk_swap"]].append(o)
rows = []
for k, v in g.items():
    pts = np.concatenate([np.array([list(o.matrix_world @ vv.co) for vv in o.data.vertices]) for o in v])
    mem = [r["members"] for r in rep if r["legacy"] == k][0]
    a2, b2 = min(leg[m][0][2] for m in mem), max(leg[m][1][2] for m in mem)
    rows.append((k, v[0].data.name, a2, b2, pts[:, 2].min(), pts[:, 2].max()))
d_bot = np.array([r[4] - r[2] for r in rows]); d_top = np.array([r[5] - r[3] for r in rows])
print("  bottom delta: min %.2f p10 %.2f med %.2f p90 %.2f max %.2f" % (d_bot.min(), np.percentile(d_bot, 10), np.median(d_bot), np.percentile(d_bot, 90), d_bot.max()))
print("  top delta: min %.2f p10 %.2f med %.2f p90 %.2f max %.2f" % (d_top.min(), np.percentile(d_top, 10), np.median(d_top), np.percentile(d_top, 90), d_top.max()))
w = [r for r in rows if abs(r[5] - r[3]) > 1.0 or r[4]-r[2] < -0.2]
print("  tops differing >1.0 m or bottoms lower:", len(w))
for r in w[:30]:
    print("     ", r[0], r[1], "legacy z %.1f..%.1f new z %.1f..%.1f" % (r[2], r[3], r[4], r[5]))
chk = PL.assert_no_legacy_rocks(None, raise_on_fail=False)
print("  assert_no_legacy_rocks", chk["ok"], "rocks", chk["rocks"], "min verts", chk["min_verts"])
