import numpy as np, bpy, hashlib
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
L = REPO + "/Unity/Assets/Resources/Course/Look/"
im = bpy.data.images.load(L + "Basalt_C.png", check_existing=False); w, h = im.size
px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px)
lum = px.reshape(h, w, 4)[:, :, :3].mean(axis=2)
b = lum.mean(axis=0).reshape(128, 8).mean(axis=1)
print("PROFILE128 =", "(" + ", ".join("%.3f" % v for v in b) + ")")
print("MEAN", round(float(lum.mean()), 4))
for n in ("Basalt_C", "Basalt_E", "Basalt_N"):
    print("SHA", n, hashlib.sha256(open(L + n + ".png", "rb").read()).hexdigest()[:16])
