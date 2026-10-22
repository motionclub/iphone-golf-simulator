import sys, os, math, importlib.util
sys.dont_write_bytecode = True
HERE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "..", "blender", "scripts"))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
import postcard_props_smoke as S
import postcard_props_lib as PL
spec = importlib.util.spec_from_file_location("PLold", os.path.join(os.path.dirname(os.path.dirname(HERE)), "work", "postcard-look", "v2", "props", "sway", "backup", "postcard_props_lib.py"))
PLo = importlib.util.module_from_spec(spec); spec.loader.exec_module(PLo)
out = sys.argv[sys.argv.index("--") + 1]
S.fresh(); PL.write_plants_atlas()
S.setup_scene((1500, 700))
g = S.ref_mat("REF_GROUND", (126, 140, 60), rough=0.95)
S.ref_plane("REF_G", 0, 0, 0.0, 200, 200, g.name)
which = sys.argv[sys.argv.index("--") + 2]
mod, label = (PLo, "OLD stair-step haunch") if which == "old" else (PL, "NEW concentric-arc slanted courses + chips")
for k, (span, hgt, broken, seed) in enumerate(((7.5, 11.0, False, 8), (9.1, 11.5, False, 8), (6.0, 9.0, True, 12))):
    mod.build_masonry_arch(None, (-17.0 + k * 17.0, 0.0, 0.0), 0.0, span_m=span, height_m=hgt, seed=seed, base_rock=False, vines=False, broken=broken)
cam = S.camera("CAM_A", Vector((0.0, -40.0, 6.5)), Vector((0.0, 0.0, 5.5)), lens=30)
S.title(cam, "arch haunch %s: spans 7.5 / 9.1 / 6.0 broken" % label, size=0.04)
sc = bpy.context.scene; sc.camera = cam
sc.render.filepath = os.path.join(out, "arch_haunch_%s.png" % which)
bpy.ops.render.render(write_still=True)
print("wrote", sc.render.filepath)
