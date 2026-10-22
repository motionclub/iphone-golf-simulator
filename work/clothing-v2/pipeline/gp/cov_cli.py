"""GARMENT PIPELINE helper: rest coverage of a worn set (today's dump with candidates replaced), per body vertex bitmask.
Blender -b --factory-startup --python gp/cov_cli.py -- <hero> <cand_dir or -> <out.npz> [extra candidate npz ...]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import rig, scene, evaluate as EV, candidate as CA
a = sys.argv[sys.argv.index('--') + 1:]
h = rig.Hero(a[0]); items = scene.items_from_dump(h)
cand = CA.load_dir(a[1], h) if a[1] != '-' and os.path.isdir(a[1]) else {}
for extra in a[3:]:
    cand.update(CA.load_one(extra, h))
items = [cand.get(i.tag, i) for i in items]
have = {i.tag for i in items}; items += [v for k, v in sorted(cand.items()) if k not in have and k != 'body']   # brand-new pieces (not in the dump) join the worn set
items[0].drawn = np.ones(len(items[0].tri), bool)
tb, vb = EV.coverage(items, cache_dir=os.path.join(rig.PIPE, 'cache', h.id), vertices=True)
np.savez(a[2], body_bits=vb[0], tags=np.array([i.tag for i in items]))
print('COVCLI', a[2], int((vb[0] != 0).sum()))
