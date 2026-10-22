"""Measures the round-6 gate quantities on any staged blend (control: the round-5 build). -- BLEND"""
import sys, json
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy
import hole08_look as K
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--") + 1])
sm = K._seen_summary(K.tee_seen_seam())
bf = K.arch_frame_bare_rock()
du, dv, n_ok, n_skip = K.tee_seam_uv_gap()
worst, jr = K.tee_path_seam_jump()
print("MEASURE", json.dumps(dict(seen=sm, bare=bf, plan_uv_step=(du, dv, n_ok), path_seam_jump=jr)))
