import numpy as np, bpy
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
L = REPO + "/Unity/Assets/Resources/Course/Look/"
def load(p):
    im = bpy.data.images.load(p, check_existing=False); w, h = im.size
    px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px); return px.reshape(h, w, 4)[:, :, :3]
for tag, p in (("NEW", L + "Basalt_C.png"), ("OLD", REPO + "/work/postcard-look/v2/tex/v5/before/Basalt_C.png")):
    C = load(p); lum = C.mean(axis=2); prof = lum.mean(axis=0)
    print(tag, "mean", round(float(lum.mean()), 4), "p10/50/90", [round(float(np.percentile(lum, q)), 3) for q in (10, 50, 90)])
    b = prof.reshape(32, 32).mean(axis=1)
    print(tag, "32-bin u profile:", " ".join("%.3f" % v for v in b))
    print(tag, "v profile (16 bins):", " ".join("%.3f" % v for v in lum.mean(axis=1).reshape(16, 64).mean(axis=1)))
