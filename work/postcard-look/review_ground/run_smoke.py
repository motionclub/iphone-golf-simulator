"""Reviewer wrapper: runs the owner's postcard_look_smoke.py unchanged, but blocks its unconditional copy of the hole-9
blend into the owner's lib_ground/ folder (reviewer must not write owner files). Args are passed through after '--'."""
import os, sys, shutil, runpy
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
OWNER = os.path.join(REPO, "work", "postcard-look", "lib_ground")
_real = shutil.copyfile
def _guard(src, dst, *a, **k):
    if os.path.abspath(dst).startswith(OWNER):
        print(f"[review] BLOCKED write into owner folder: {dst}", flush=True)
        return dst
    return _real(src, dst, *a, **k)
shutil.copyfile = _guard
runpy.run_path(os.path.join(REPO, "blender", "scripts", "postcard_look_smoke.py"), run_name="__main__")
