"""Blender -b --factory-startup --python ground_uv_control.py -- BLEND [--expect-fail]: prints the GROUND_UV stats of a blend (the negative control = the stage before the repair)."""
import sys, os
import bpy
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ground_uv_lib as G
args = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=args[0])
st = G.stats(bpy.data.objects)
ok, txt = G.verdict(st)
for k, v in sorted(st.items(), key=lambda kv: -kv[1]["total_m2"])[:4]:
    print(f"UV {k}: {v['n_big']} triangles > {G.RATIO:g}:1 cover {v['total_m2']:.1f} m2 (largest {v['single_m2']:.1f} m2), worst {v['worst']:.1f}:1")
print(txt[:700])
exp_fail = "--expect-fail" in args
print(f"CONTROL {os.path.basename(os.path.dirname(args[0]))}: ground UV sliver gate {'PASS' if ok else 'FAIL'} ({'expected FAIL, detected' if (exp_fail and not ok) else 'UNEXPECTED' if exp_fail else ''})")
