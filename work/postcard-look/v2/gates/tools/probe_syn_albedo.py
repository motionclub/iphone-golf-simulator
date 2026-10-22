import sys, importlib.util, numpy as np
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
def img(stem, n, fine, hi):
    h, s, v, vsd, hw, sd = m.ST_ALBEDO[stem]
    rng = np.random.default_rng(sd)
    nv = vsd * (0.55 * m.st_noise(n, rng, 0.6, 4, 40) + 0.45 * m.st_noise(n, rng, 0.9, 3, 12) + fine * m.st_noise(n, rng, 0.3, 16, hi))
    nh = hw * m.st_noise(n, rng, 1.0, 2, 10)
    ns = 0.04 * m.st_noise(n, rng, 1.0, 2, 10)
    return m.st_hsv_img(h, s, v, nh, ns, nv)
for fine, hi in ((0.0, 40), (0.5, 120), (0.8, 160), (1.0, 200)):
    for n in (512,):
        out = []
        for stem in ("Fairway", "Green", "Rough", "Scrub"):
            px = np.ones((n, n, 4)); px[..., :3] = img(stem, n, fine, hi)
            a = m.albedo_structure(px.astype(np.float32), stem + "_C")
            out.append(f"{stem} {a['frac_raw']:.2f}/{a['frac_blur']:.2f} p10 {a['p10']:.3f} per {a['periodic']:.3f}")
        print("FINE", fine, hi, n, " | ".join(out))
