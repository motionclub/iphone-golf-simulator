import bpy, sys, numpy as np, math
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import postcard_lib as P, postcard_look_lib as L, postcard_props_lib as PL, hole09_look as HL
D = P.start("hole09_design", out_dir="/tmp/dbg9")
D.mod.SCENERY["tee_box_m"] = (10.4, 13.2)
P.build_terrain(D); P.build_play_surfaces(D); P.build_water(D, shallow_material=None, foam_material=None); P.build_gameplay(D)
L.look_materials(D); L.retarget_materials(D)
reef = PL.scatter(D, ["ROCK_BOULDER_A", "ROCK_BLOCK_A", "ROCK_BOULDER_B"], 10, region=PL.region_band(D, 3.6, 11.0, "sea"), seed=28,
                      min_gap=14.0, scale_range=(1.25, 1.9), z=(-0.15, 0.25), sink=0.0, wet=True, surface="sea")
print("reef", len(reef))
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith(("ROCK_", "CLIFF_ROCK")) and not o.name.startswith(("ROCK_SKIN", "ROCK_WALL")):
        Wv = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
        c2 = Wv[:, :2].mean(0)
        sd = float(P.signed_dist_m(D, np.array([c2[0]]), np.array([c2[1]]))[0])
        print(o.name, round(Wv[:,2].min(),2), round(Wv[:,2].max(),2), round(sd,2), o.users_collection[0].name)
