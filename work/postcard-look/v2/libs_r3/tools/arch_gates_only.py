"""Run only the arch round gates (round2 arch, round3 arch, round4) of postcard_props_smoke quickly. usage: Blender -b --factory-startup --python arch_gates_only.py"""
import sys, os
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.argv = [sys.argv[0], "--", "--no-render", "--no-holes", "--no-baseline"]
sys.path.insert(0, REPO + "/blender/scripts")
import postcard_props_smoke as S
S.round2_gates(); S.round3_gates(); S.round4_gates()
bad = [r for r in S.RESULTS if not r[1]] if hasattr(S, "RESULTS") and S.RESULTS and isinstance(S.RESULTS[0], tuple) else []
print("DONE", len(S.RESULTS), "gates")
