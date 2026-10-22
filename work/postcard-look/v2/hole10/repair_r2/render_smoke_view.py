"""Wrapper: patch LK_SMOKE into an unlit pale-lavender stand-in with the runtime's AlphaGain 1.35 (GolfLook), then run tools/render_views.py with the same argv.
usage: Blender -b STAGE.blend --python render_smoke_view.py -- <render_views args>"""
import sys, bpy, runpy
m = bpy.data.materials.get("LK_SMOKE")
nt = m.node_tree
b = nt.nodes["Principled BSDF"]
tex = nt.nodes["Image Texture"]
for l in list(nt.links):
    if l.to_socket.name in ("Alpha", "Base Color"):
        nt.links.remove(l)
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.use_clamp = True; mul.inputs[1].default_value = 1.35
nt.links.new(tex.outputs["Alpha"], mul.inputs[0]); nt.links.new(mul.outputs[0], b.inputs["Alpha"])
b.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)
b.inputs["Emission Color"].default_value = (0.62, 0.56, 0.60, 1.0)
b.inputs["Emission Strength"].default_value = 1.0
b.inputs["Roughness"].default_value = 1.0
sys.argv = [sys.argv[0], "--"] + sys.argv[sys.argv.index("--") + 1:]
runpy.run_path("/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/hole10/tools/render_views.py", run_name="__main__")
