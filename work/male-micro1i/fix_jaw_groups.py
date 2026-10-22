"""Replace LOOP_jaw_ear_L/R vertex-group membership with the continuous edge path (geometry untouched).  blender -b --python fix_jaw_groups.py -- <in.blend> <out.blend> <jaw_loops.pkl>"""
import sys, pickle
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
import bpy
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); jl = pickle.load(open(argv[2], 'rb'))
body = bpy.data.objects['Body_M']; me = body.data
before = {}
for name, key in (('LOOP_jaw_ear_L', 'L'), ('LOOP_jaw_ear_R', 'R')):
    vg = body.vertex_groups[name]
    old = [v.index for v in me.vertices if any(g.group == vg.index for g in v.groups)]
    before[name] = len(old)
    if old: vg.remove(old)
    vg.add([int(i) for i in jl[key]], 1.0, 'REPLACE')
for name in before:
    vg = body.vertex_groups[name]; new = [v.index for v in me.vertices if any(g.group == vg.index for g in v.groups)]
    print(name, 'members', before[name], '->', len(new))
bpy.ops.wm.save_as_mainfile(filepath=argv[1]); print('saved', argv[1])
