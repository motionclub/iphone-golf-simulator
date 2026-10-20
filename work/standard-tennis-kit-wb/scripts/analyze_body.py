import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/standard-tennis-kit-wb/scripts')
import numpy as np, bpy
from kitlib import *
which = sys.argv[sys.argv.index('--')+1]
if which == 'male':
    body = load_body(MALE_BLEND, 'Body_M')
else:
    body = load_body(FEMALE_BLEND, 'Body_F')
V, F = mesh_arrays(body)
print("verts", len(V), "tris", len(F), "z", V[:,2].min(), V[:,2].max())
print("x range", V[:,0].min(), V[:,0].max(), " y range", V[:,1].min(), V[:,1].max())
zs = np.arange(0.0, 1.72, 0.04)
for z in zs:
    L = slice_plane(V, F, 2, z)
    infos = []
    for P in L:
        if len(P) < 4: continue
        i = loop_info(P)
        infos.append((i['min'][0], i['max'][0], i['min'][1], i['max'][1], i['area']))
    infos.sort()
    s = " | ".join(f"x[{a:+.3f},{b:+.3f}] y[{c:+.3f},{d:+.3f}] A={ar*1e4:.0f}cm2" for a,b,c,d,ar in infos)
    print(f"z={z:.2f} n={len(infos)}: {s}")
