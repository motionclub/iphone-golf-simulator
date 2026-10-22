"""40 seeds x holes 08/09 (and 10 x 8): stretch / composition counts only. Scratch only."""
import sys, os
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
import postcard_props_lib as PL
tot = {}
for hole, seeds in (("08", range(100, 140)), ("09", range(100, 140)), ("10", range(100, 108))):
    bad = []
    for seed in seeds:
        bpy.ops.wm.open_mainfile(filepath=f"{R}/work/postcard-look/baseline/blender/hole_{hole}.blend")
        PL._COUNTERS.clear()
        out = PL.swap_legacy_rocks(None, basalt=(hole == "10"), seed=seed)
        bpy.context.view_layer.update()
        sr = PL.stretch_report(); cr = PL.swap_composition_report()
        if not sr["ok"] or not cr["ok"]:
            bad.append((seed, len(sr["violations"]), cr["vertical_stacks"][:2], cr["clones"][:2]))
    print(f"MANY {hole}: {len(list(seeds))} seeds, bad {len(bad)} {bad[:5]}")
