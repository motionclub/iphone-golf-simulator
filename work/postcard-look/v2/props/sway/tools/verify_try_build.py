import sys, os
sys.dont_write_bytecode = True
HERE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "..", "blender", "scripts"))
sys.path.insert(0, HERE)
import bpy, numpy as np
import postcard_props_smoke as S
import postcard_props_lib as PL
import postcard_look_lib as L
import postcard_lib as P
out = sys.argv[sys.argv.index("--") + 1]
S.fresh()
D = P.start("hole08_design", out_dir=out)
P.build_terrain(D); P.build_play_surfaces(D); P.build_water(D); P.build_gameplay(D)
PL.scatter(D, ["PLANT_SHRUB_A", "PLANT_SHRUB_B"], 30, seed=2)
PL.scatter(D, ["PLANT_AGAVE_A"], 10, seed=3)
PL.scatter(D, {"PLANT_FLOWER_PURPLE": 1, "PLANT_FLOWER_WHITE": 1}, 20, seed=4)
PL.scatter(D, {"PLANT_TUFT_A": 2, "PLANT_TUFT_B": 1}, 100, seed=1)
PL.hang_vines_on_cliff(D, 7.0, seed=6)
PL.scatter_fringe(D, tri_budget=30000, seed=3)
PL.scatter(D, ["PLANT_PINE_A", "PLANT_TREE_A"], 4, seed=5)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "hole_08.blend"))
L.export_look_fbx(D, os.path.join(out, "hole_08.fbx"))
print("done")
