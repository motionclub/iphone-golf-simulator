"""blender -b --factory-startup --python lips_proto.py -- in.blend out.blend [params.json] : replace the lip paint of Face_F by the plate-measured strips (lips3) on the blend's own skin"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f3-head/tools')
import bpy, numpy as np
import lips3
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
p = dict(lips3.P0)
if len(a) > 2:
    for k, v in json.load(open(a[2])).items(): p[k] = v
body = bpy.data.objects['Body_F']; face = bpy.data.objects['Face_F']
skin = lips3.skin_from_object(body)
S = lips3.build_strips(skin, p)
print('strips', {k: (len(v['V']), len(v['F']), 'miss', v['miss']) for k, v in S.items()})
print(lips3.replace_in_face(face, S, custom_normals=bool(p.get('custom_normals', 1))))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
