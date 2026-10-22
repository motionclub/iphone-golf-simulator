"""Run hole10_build.py with one constant replaced (experiments only): Blender -b --python build_variant.py -- OUTDIR 'SKIN_PIECE_M = 15.0' 'SKIN_PIECE_M = 140.0'"""
import sys
a = sys.argv[sys.argv.index("--") + 1:]
out, old, new = a[0], a[1], a[2]
f = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts/hole10_build.py"
src = open(f).read()
assert old in src, old
src = src.replace(old, new, 1)
sys.argv = [f, "--", "--out", out, "--no-render"]
__file__ = f
exec(compile(src, f, "exec"))
