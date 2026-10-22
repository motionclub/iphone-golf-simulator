import sys, os, math
sys.dont_write_bytecode = True
sys.argv = [sys.argv[0], "--"] + ["--out", "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/hole10/scratch_diag", "--no-render"]
os.makedirs("/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/hole10/scratch_diag", exist_ok=True)
__file__ = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts/hole10_build.py"
exec(compile(open(__file__).read(), __file__, "exec"))
bad, ncut = blocked_lines(D, stacks)
print("STUCK", sorted(bad), ncut)
for i, st in enumerate(stacks):
    m = st["main"]
    print(i, SC["stacks"][i], m.data.name, tuple(round(v,2) for v in m.scale), "top", round(max(top_z(o) for o in st["obs"]),2), "BAD" if i in bad else "")
