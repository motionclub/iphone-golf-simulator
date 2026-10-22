"""Quick preview: python view_kit.py -- <gender> <part,part,...> <white|black> <out_prefix> [preset] [nobody]
Parts are staged npz names under data/ (e.g. polo_male,shorts_male).  Renders front / 3-4 / side / back."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viewlib import *

args = sys.argv[sys.argv.index('--') + 1:]
gender, names, cw, prefix = args[:4]
preset = args[4] if len(args) > 4 else 'full'
nobody = 'nobody' in args[5:]
PRESETS = {
    'full': dict(views=(('front', 0, 3), ('q3', 38, 4), ('side', 90, 3), ('back', 180, 3)), target=(0, -0.05, 0.86), dist=6.4, lens=105, res=(520, 760)),
    'waist': dict(views=(('front', 0, 4), ('q3', 38, 6), ('side', 90, 4), ('back', 180, 4)), target=(0, -0.05, 0.96), dist=2.6, lens=85, res=(560, 560)),
    'upper': dict(views=(('front', 0, 3), ('q3', 38, 4), ('side', 90, 3), ('back', 180, 3)), target=(0, -0.05, 1.18), dist=3.4, lens=85, res=(560, 640)),
    'low': dict(views=(('front', 0, 2), ('q3', 38, 3), ('side', 90, 2), ('back', 180, 2)), target=(0, -0.05, 0.70), dist=3.2, lens=85, res=(560, 640)),
}
if preset.startswith('{'):                      # custom: JSON {"views": [[name, az, el], ...], "target": [x,y,z], "dist": d, "lens": l, "res": [w,h]}
    import json as _j
    c = _j.loads(preset)
    PRESETS['custom'] = dict(views=tuple(tuple(v) for v in c['views']), target=tuple(c['target']), dist=c.get('dist', 1.2), lens=c.get('lens', 85), res=tuple(c.get('res', (560, 560))))
    preset = 'custom'
pr = PRESETS[preset]
fresh_scene()
lift = LIFT[gender]
mats = colorway_materials(cw)
if not nobody:
    b = body_object(gender)
    b.location.z = lift
for nm in names.split(','):
    o = part_object(nm, load_part(nm), mats)
    o.location.z = lift
rs.setup(samples=32)
t = pr['target']
shot_set(prefix, pr['views'], (t[0], t[1], t[2] + lift), dist=pr['dist'], lens=pr['lens'], res=pr['res'])
print('done', prefix)
