"""The verifier's own sea-stack measure (postcard_look_verify.stack_metrics) applied to every library spire kind (and the _WET / _BASALT twins) at scale 1.
usage: Blender -b --factory-startup --python stack_oracle.py -- [LIB.py]"""
import sys, os, importlib.util
R = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, R + "/blender/scripts"); sys.dont_write_bytecode = True
import numpy as np, bpy
a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
libpath = a[0] if a else R + "/blender/scripts/postcard_props_lib.py"
spec = importlib.util.spec_from_file_location("pl_under_test", libpath)
PL = importlib.util.module_from_spec(spec); sys.modules["pl_under_test"] = PL; spec.loader.exec_module(PL)
import postcard_look_verify as V
class S:
    def __init__(self): self._w = {}
    def wld(self, ob):
        if ob.name in self._w: return self._w[ob.name]
        me = ob.data
        me.calc_loop_triangles()
        nv = len(me.vertices); co = np.empty(nv * 3); me.vertices.foreach_get("co", co); Vv = co.reshape(-1, 3)
        nt = len(me.loop_triangles); tv = np.empty(nt * 3, np.int64); me.loop_triangles.foreach_get("vertices", tv)
        mi = np.empty(nt, np.int64); me.loop_triangles.foreach_get("material_index", mi)
        names = [s.material.name if s.material else "" for s in ob.material_slots] or [""]
        mi = np.clip(mi, 0, len(names) - 1)
        mw = np.array(ob.matrix_world)
        W = Vv @ mw[:3, :3].T + mw[:3, 3]
        T = tv.reshape(-1, 3)
        N, A = V.tri_geom(W, T)
        c = dict(W=W, T=T, N=N, A=A, mi=mi, names=names); self._w[ob.name] = c; return c
S_ = S()
res = []
for k in PL.SPIRE_KINDS:
    ob = PL.library_object(k)
    ob.matrix_world = __import__("mathutils").Matrix.Identity(4)
    bpy.context.view_layer.update()
    r = V.stack_metrics(S_, ob)
    res.append((k, r))
    print("STACK", k, "ok" if r["ok"] else "BAD", "H %.1f taper %.2f cap %.0f%% fill %.2f" % (r["H"], r["taper"], r["cap"] * 100, r["fill"]), r["why"])
