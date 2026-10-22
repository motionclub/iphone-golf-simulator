import sys, os, importlib.util
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
import bpy, numpy as np
argv = sys.argv[sys.argv.index("--") + 1:]
f = argv[0]
opts = m.parse_args(["8"])
design, dpath = m.load_design(8, None)
C = m.Ctx(8, design, dpath, opts)
bpy.ops.wm.open_mainfile(filepath=f, load_ui=False)
S = m.Snap("blend", C)
cov, total, P, lid = m.white_reach_cover(S, C, 1.0, m.TH2["foam_reach"])
print("total", total, "n", len(cov), "cov frac", cov.mean())
for li in np.unique(lid):
    sel = np.flatnonzero(lid == li)
    c = cov[sel]
    # runs and gaps (circular)
    n = len(c)
    idx = np.flatnonzero(c)
    if len(idx) == 0: continue
    runs = []
    start = None
    for i in range(n):
        if c[i] and (i == 0 or not c[i-1]): start = i
        if c[i] and (i == n-1 or not c[i+1]): runs.append((start, i))
    for a, b in zip(runs, runs[1:] + runs[:1]):
        gap = (b[0] - a[1] - 1) % n
        pa = P[sel[a[1]]]; pb = P[sel[b[0]]]
        print(f"loop {li}: run {a}-> len {a[1]-a[0]+1}, gap {gap} from ({pa[0]:.1f},{pa[1]:.1f}) to ({pb[0]:.1f},{pb[1]:.1f})")
