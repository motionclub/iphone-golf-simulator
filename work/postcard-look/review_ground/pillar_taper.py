import sys, os, math
sys.dont_write_bytecode = True
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, os.path.join(REPO, "blender", "scripts"))
import numpy as np, bpy
bpy.ops.wm.open_mainfile(filepath=os.path.join(REPO, "work/postcard-look/review_ground/smoke_hole10/smoke_hole10.blend"))
pin = np.array(bpy.data.objects["MARKER_PIN"].matrix_world.translation[:2])
ter = bpy.data.objects["TERRAIN_CRATER"]
mw = np.array(ter.matrix_world)
TW = np.array([v.co[:] for v in ter.data.vertices]) @ mw[:3, :3].T + mw[:3, 3]
near = np.hypot(TW[:, 0] - pin[0], TW[:, 1] - pin[1]) < 60
def rad(W, lo, hi):
    m = (W[:, 2] >= lo) & (W[:, 2] < hi)
    r = np.hypot(W[m, 0] - pin[0], W[m, 1] - pin[1])
    return (round(float(np.percentile(r, 50)), 2), round(float(r.max()), 2)) if m.any() else None
print("TERRAIN pillar radius (median, max) by z band:", {b: rad(TW[near], *b) for b in [(5.9, 6.1), (3, 5), (0, 3), (-6.1, -3)]})
SW = []
for o in bpy.data.objects:
    if o.name.startswith("ROCK_SKIN"):
        m2 = np.array(o.matrix_world)
        W = np.array([v.co[:] for v in o.data.vertices]) @ m2[:3, :3].T + m2[:3, 3]
        if np.hypot(W[:, 0] - pin[0], W[:, 1] - pin[1]).max() < 60:
            SW.append(W)
SW = np.vstack(SW)
print("pillar SKIN radius (median, max) by z band:", {b: rad(SW, *b) for b in [(4.5, 6.0), (2, 4.5), (0, 2), (-1.7, 0)]})
