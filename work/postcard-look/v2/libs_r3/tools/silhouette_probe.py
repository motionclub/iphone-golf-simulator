"""Silhouette irregularity of the library spires: mean absolute deviation of the left / right silhouette edge from the straight line through its ends (12 %..85 % of the height), as a share of the mean width,
over 4 azimuths. usage: Blender -b --factory-startup --python silhouette_probe.py -- [LIB.py]"""
import sys, importlib.util, math
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts"); sys.dont_write_bytecode = True
import numpy as np, bpy
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
libpath = a[0] if a else R + "/blender/scripts/postcard_props_lib.py"
spec = importlib.util.spec_from_file_location("pl_under_test", libpath)
PL = importlib.util.module_from_spec(spec); sys.modules["pl_under_test"] = PL; spec.loader.exec_module(PL)
def irregularity(me, H, azs=(0, 45, 90, 135), n=44):
    co, tris, _ = PL._np_mesh(me)
    out = []
    for az in azs:
        t = math.radians(az); ax = np.array([math.cos(t), math.sin(t)])
        L, Rr = [], []
        for z in np.linspace(0.12 * H, 0.85 * H, n):
            sec = PL.mesh_section(co, tris, z)[:, :2]
            if len(sec) < 3: continue
            u = sec @ ax; L.append(u.min()); Rr.append(u.max())
        L, Rr = np.array(L), np.array(Rr); zz = np.arange(len(L))
        w = (Rr - L).mean()
        dev = 0
        for e in (L, Rr):
            c = np.polyfit(zz, e, 3)                         # the global taper / lean / bend is a smooth cubic; shoulders, notches and bites are what is left
            dev += np.abs(e - np.polyval(c, zz)).mean()
        out.append(dev / 2 / max(w, 1e-9))
    return float(np.mean(out))
res = {}
for k in PL.SPIRE_KINDS:
    ob = PL.library_object(k)
    res[k] = irregularity(ob.data, PL.SPIRE_SPECS[k]["height"])
    print("SIL", k, "%.3f" % res[k])
print("SILMEAN %.3f" % np.mean(list(res.values())))
