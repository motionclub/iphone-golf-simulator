"""Scratch wrapper (calibration 2026-10-04): runs G's postcard_look_smoke.py for one hole with build_cliff_skin(piece_m=<given>) as the default,
writing everything under --out (never the repo's lib_ground/smoke_holeNN). Purpose: find the piece_m at which hole 10's ROCK_SKIN pieces satisfy
PostcardImportCheck's ROCK_NEAR_LAVA_CHUNKED (every ROCK_ renderer within 25 yd of a LAVA_LIGHT is <= 24 yd across).
usage: Blender -b --factory-startup --python smoke_piece.py -- <hole 08|09|10> <piece_m> <out dir>"""
import os, runpy, sys
a = sys.argv[sys.argv.index("--") + 1:]
hole, piece, out = a[0], float(a[1]), os.path.abspath(a[2])
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
scripts = os.path.join(REPO, "blender", "scripts")
sys.path.insert(0, scripts)
sys.dont_write_bytecode = True
import postcard_look_lib as L
_orig = L.build_cliff_skin
def patched(*args, **kw):
    kw.setdefault("piece_m", piece)
    return _orig(*args, **kw)
L.build_cliff_skin = patched
smoke = os.path.join(scripts, "postcard_look_smoke.py")
sys.argv = [smoke, "--", "--hole", hole, "--out", out, "--no-render"]
runpy.run_path(smoke, run_name="__main__")
