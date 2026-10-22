import sys, importlib.util, numpy as np
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
import bpy
argv = sys.argv[sys.argv.index("--")+1:]
hole = int(argv[0]); f = argv[1]
opts = m.parse_args([str(hole), "--look-dir", REPO + "/work/postcard-look/v2/gates/fixtures/look_at_run"])
design, dpath = m.load_design(hole, None); C = m.Ctx(hole, design, dpath, opts)
bpy.ops.wm.open_mainfile(filepath=f, load_ui=False)
S = m.Snap("blend", C)
for amin in (0.3, 0.15, 0.05):
    S.__dict__.pop("_white_geo", None)
    orig = m.white_geometry
    def wg(S_, C_, amin_=amin): return orig(S_, C_, amin_)
    m.white_geometry = wg
    cov, total, P, lid = m.white_reach_cover(S, C, 1.0, 10.0)
    runs, gaps = m.loop_runs(cov, lid, 1.0)
    V, T, A, own = wg(S, C)
    S.__dict__.pop("_white_geo", None)
    m.white_geometry = orig
    print("AMIN", amin, "cover %.1f%%" % (100*cov.mean()), "longest", max(runs, default=0), "mingap", min(gaps, default=0), "area/m %.2f" % (A.sum()/total))
