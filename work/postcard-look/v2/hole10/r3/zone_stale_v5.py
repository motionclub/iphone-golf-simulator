import numpy as np, bpy
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
L = REPO + "/Unity/Assets/Resources/Course/Look/"
def G_of(path):
    im = bpy.data.images.load(path, check_existing=False); w, h = im.size
    px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px)
    return px.reshape(h, w, 4)[:, :, :3].max(axis=2) > 0.2
Gn = G_of(L + "Basalt_E.png"); Go = G_of(REPO + "/work/postcard-look/v2/tex/v5/before/Basalt_E.png")
w = Gn.shape[1]
ZONES = ((0.141, 0.211), (0.225, 0.350), (0.364, 0.435), (0.460, 0.525), (0.547, 0.705), (0.730, 0.795), (0.820, 0.920), (0.940, 1.110))
GLOW_U = (0.123, 0.446, 0.534, 0.718, 0.806, 0.930)
def share(G, a, b):
    cols = [i % w for i in range(int(round(a * w)), int(round(b * w)))]
    return G[:, cols].mean()
for a, b in ZONES:
    print("zone (%.3f,%.3f): glow share old tex %.3f%%  new tex %.3f%%" % (a, b, 100 * share(Go, a, b), 100 * share(Gn, a, b)))
for g in GLOW_U:
    for sgn in (-1, 1):
        a, b = (g - 0.016, g - 0.016 + 0.05) if sgn < 0 else (g + 0.016 - 0.05, g + 0.016)
        print("edge window at line %.3f %s (width .05): old %.2f%% new %.2f%%" % (g, "left" if sgn < 0 else "right", 100 * share(Go, a, b), 100 * share(Gn, a, b)))
