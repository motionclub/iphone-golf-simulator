import sys, json
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
sys.path.insert(0, REPO + "/blender/scripts"); sys.dont_write_bytecode = True
import bpy
import hole08_look as K
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--") + 1])
sc = K.tee_seen_seam(cols=range(0, 900, 6), near=30, far=40)
print("MEASURE_PATH", json.dumps(dict(n_path=len(sc["path"]), gap_rows_total=sum(q[4] for q in sc["path"]), gap_rows_per_col=[q[4] for q in sc["path"]][:40], dv=[round(q[3], 4) for q in sc["path"]][:10])))
