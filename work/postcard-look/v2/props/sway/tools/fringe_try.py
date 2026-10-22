"""Scratch build of a real hole design + scatter_fringe; prints stats (usage: -- TAG [budget] [seed])."""
import sys, os, time, math
sys.dont_write_bytecode = True
HERE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "..", "blender", "scripts"))
sys.path.insert(0, HERE)
import numpy as np
import bpy
import postcard_props_smoke as S
import postcard_props_lib as PL
import postcard_lib as P
A = sys.argv[sys.argv.index("--") + 1:]
tag = A[0]
budget = int(A[1]) if len(A) > 1 else 60000
seed = int(A[2]) if len(A) > 2 else 1
S.fresh()
D = P.start(f"hole{tag}_design", out_dir=os.path.join(S.SCRATCH, f"hole{tag}"))
t0 = time.time()
P.build_terrain(D); P.build_play_surfaces(D)
if tag == "10":
    P.build_water(D, 'WATER_LAVA', 'MAT_LAVA', shallow_material=None, foam_material=None, crest=False)
else:
    P.build_water(D)
P.build_gameplay(D)
path = S.make_path(D)
print("build", round(time.time() - t0, 1), "s, path", bool(path), flush=True)
t0 = time.time()
r = PL.scatter_fringe(D, tri_budget=budget, seed=seed)
print("fringe", round(time.time() - t0, 1), "s")
for k in ("count", "tris", "budget", "clusters", "singles", "by_kind", "scale_min", "scale_max", "lean_max_deg", "top_max_m", "capped", "edge", "edge_samples", "edge_covered", "edge_focus", "seeds", "corridor_m"):
    print(" ", k, r[k])

# ---- previews (Blender EEVEE, flat MAT_ ground: NOT Game view)
if "--render" in A:
    from mathutils import Vector
    S.setup_scene((620, 1000))
    sc = bpy.context.scene
    ground_cols = {"FAIRWAY": (120, 168, 52), "GREEN": (140, 190, 60), "TEE_BOX": (126, 170, 56)}
    # recolour flat MAT_ so the fringe reads against the ground (preview only)
    for ob in bpy.data.objects:
        if ob.type == 'MESH' and ob.name.startswith(("TERRAIN", "FAIRWAY", "GREEN", "TEE_BOX", "BUNKER")):
            col = (150, 168, 62)
            if ob.name.startswith("FAIRWAY"): col = (118, 166, 50)
            if ob.name.startswith("GREEN"): col = (136, 188, 58)
            if ob.name.startswith("BUNKER"): col = (214, 196, 140)
            m = S.ref_mat("PREV_" + ob.name.split("_")[0], col, rough=0.95)
            ob.data.materials.clear(); ob.data.materials.append(m)
    shots = {"08": [("tee", (0, 0), (19, 178)), ("appr", (19, 178), (-6, 340))],
             "09": [("tee", (0, 0), (3, 60)), ("appr", (13.5, 269), (6, 416))],
             "10": [("tee", (0, 0), (14.3, 66.2)), ("appr", (107.1, 159.3), (261, 164.7))]}[tag]
    YD = 0.9144
    for nm, ball, aim in shots:
        b = Vector((ball[0] * YD, ball[1] * YD, 6.0)); a = Vector((aim[0] * YD, aim[1] * YD, 6.0))
        d = (a - b); d.z = 0; d.normalize()
        cam = S.camera("CAM_" + nm, b - d * 4.5 * YD + Vector((0, 0, 2.4 * YD)), b + d * 1.5 * YD + Vector((0, 0, 0.3)), lens=30, clip=3000)
        sc.camera = cam
        sc.render.filepath = os.path.join(os.getcwd(), A[A.index("--render") + 1], f"fringe_{tag}_{nm}.png")
        bpy.ops.render.render(write_still=True)
        print("wrote", sc.render.filepath)

if "--render" in A:
    import numpy as np
    objs = [o for o in bpy.data.objects if o.name.startswith("PLANT_TUFT") and o.get("lk_fringe")]
    if objs:
        # a close-up at the densest 6 m neighbourhood of the fringe nearest the first still ball
        P_ = np.array([[o.location.x, o.location.y] for o in objs])
        ball0 = np.array([shots[0][1][0] * YD, shots[0][1][1] * YD])
        dd = np.hypot(*(P_ - ball0).T)
        order = np.argsort(dd)
        cen = P_[order[min(20, len(order) - 1)]]
        cnt = np.array([(np.hypot(*(P_ - c).T) < 4.0).sum() for c in P_])
        near = np.nonzero(dd < 60)[0]
        best = near[np.argmax(cnt[near])] if len(near) else int(np.argmax(cnt))
        cen = P_[best]
        z = objs[best].location.z
        # look along the edge: camera 7 m back toward the centreline of the hole
        h = D.hole
        toward = np.array([ball0[0] - cen[0], ball0[1] - cen[1]]); toward /= max(np.hypot(*toward), 1e-6)
        camp = Vector((cen[0] + toward[0] * 7.0, cen[1] + toward[1] * 7.0, z + 1.5))
        cam = S.camera("CAM_close", camp, Vector((cen[0], cen[1], z + 0.3)), lens=30, clip=3000)
        sc.camera = cam
        sc.render.filepath = os.path.join(os.getcwd(), A[A.index("--render") + 1], f"fringe_{tag}_close.png")
        bpy.ops.render.render(write_still=True)
        print("wrote", sc.render.filepath)
