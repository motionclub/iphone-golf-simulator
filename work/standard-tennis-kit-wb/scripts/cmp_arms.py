import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, bpy
from kitlib import *
from fitbody import *
bodies = load_set('female')
for z in (1.26, 1.20, 1.16, 1.12, 1.08, 1.0):
    print(f"--- z={z}")
    for b in bodies:
        L = slice_plane(b['V'], b['F'], 2, z)
        s = []
        for P in L:
            if len(P) < 6: continue
            i = loop_info(P)
            if i['c'][0] > 0.1:
                s.append(f"x[{i['min'][0]:+.3f},{i['max'][0]:+.3f}] y[{i['min'][1]:+.3f},{i['max'][1]:+.3f}] A={i['area']*1e4:.0f}")
        print(f"  {b['name']:18s}", ' | '.join(s))
