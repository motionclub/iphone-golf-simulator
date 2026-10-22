import sys, os
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.argv = [sys.argv[0], "--"]
sys.path.insert(0, REPO + "/blender/scripts")
import importlib.util
spec = importlib.util.spec_from_file_location("smoke", REPO + "/blender/scripts/postcard_props_smoke.py")
m = importlib.util.module_from_spec(spec); sys.modules["smoke"] = m; spec.loader.exec_module(m)
m.round2_gates()
