"""Evidence: run the OLD (v1, backup_at_start) swap_legacy_rocks on a baseline hole blend and count stretched instances."""
import sys, os, importlib.util, collections
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts")
import bpy, numpy as np
spec = importlib.util.spec_from_file_location("postcard_props_lib_old", R + "/work/postcard-look/v2/props/backup_at_start/postcard_props_lib.py")
OLD = importlib.util.module_from_spec(spec); spec.loader.exec_module(OLD)
hole = os.environ.get("HOLE", "10")
bpy.ops.wm.open_mainfile(filepath=R + f"/work/postcard-look/baseline/blender/hole_{hole}.blend")
sw = OLD.swap_legacy_rocks(None, basalt=(hole == "10"), seed=1)
bpy.context.view_layer.update()
bad2, badr, tot = 0, 0, 0
worst = (1, None)
for o in sw:
    sc = tuple(o.matrix_world.to_scale()); tot += 1
    if max(sc) > 2.0 + 1e-4 or min(sc) < 0.5 - 1e-4: bad2 += 1
    r = max(sc) / min(sc)
    if r > 2.0 + 1e-4: badr += 1
    if r > worst[0]: worst = (r, (o.name, tuple(round(v, 2) for v in sc)))
print(f"OLD_SWAP hole {hole}: {tot} swapped, {bad2} outside [0.5, 2.0], {badr} with max/min > 2, worst ratio {worst[0]:.2f} {worst[1]}")
