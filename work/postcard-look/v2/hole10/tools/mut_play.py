import bpy, sys
o = bpy.data.objects["FAIRWAY"]
o.data.vertices[10].co.z += 0.002
exec(compile(open("/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/hole10/tools/play_unchanged.py").read(), "play_unchanged.py", "exec"))
