"""python mkc.py <tag> <flat.json|inline json>  -> data/cand_<tag>.npz  (flat dict of fit params; keys per fit_f.SPACE or any fhand param)"""
import sys, json
import numpy as np
import fit_f, asm_f
tag = sys.argv[1]; a = sys.argv[2]
x = json.load(open(a))['params'] if a.endswith('.json') else json.loads(a)
extra = {}
if 'extra' in x: extra = x.pop('extra')
par, pose = fit_f.split({**fit_f.DEFAULT, **x})
par.update(extra.get('par', {})); pose.update(extra.get('pose', {}))
Vn, polys, si, removed = asm_f.assemble(par, pose)
asm_f.save(asm_f.W / f'data/cand_{tag}.npz', Vn, polys, removed)
print('saved', tag, 'tris', asm_f.tri_count(polys), 'manifold', asm_f.check_manifold(polys))
