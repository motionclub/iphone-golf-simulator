import sys, importlib.util, numpy as np
REPO = "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator"
spec = importlib.util.spec_from_file_location("pcv", REPO + "/blender/scripts/postcard_look_verify.py")
m = importlib.util.module_from_spec(spec); sys.modules["pcv"] = m; spec.loader.exec_module(m)
import bpy
# real Look files + synthetic at 256 / 512 / 1024
look = sys.argv[sys.argv.index("--")+1] if "--" in sys.argv and len(sys.argv) > sys.argv.index("--")+1 else REPO + "/Unity/Assets/Resources/Course/Look"
print("LOOK", look)
for stem in ("Fairway_C", "Green_C", "Rough_C", "Scrub_C", "Sand_C", "Cliff_C", "Rock_C", "Path_C", "Masonry_C", "Basalt_C", "CliffDark_C"):
    px = m.image_stats(f"{look}/{stem}.png")["px"]
    a = m.albedo_structure(px, stem)
    print(f"  {stem:12s} {px.shape[1]}px win {a['win']} floor {a['floor']} frac_raw {a['frac_raw']:.2f} frac_blur {a['frac_blur']:.2f} p10 {a['p10']:.4f} periodic {a['periodic']:.3f} gsd {a['gsd']:.3f}")
