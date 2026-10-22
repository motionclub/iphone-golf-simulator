import sys
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.argv = [sys.argv[0], "--", "--no-render", "--no-holes", "--no-baseline"]
sys.path.insert(0, REPO + "/blender/scripts")
import postcard_props_smoke as S
S.round4_stack_gates()
