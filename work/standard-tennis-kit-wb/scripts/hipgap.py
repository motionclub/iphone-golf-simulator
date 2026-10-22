import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, bpy
from kitlib import *
from fitbody import *
bodies = load_set('female')
for z in (0.70, 0.74, 0.78, 0.82, 0.86, 0.90):
    print(f"--- z={z}")
    for b in bodies[:2]:
        L = slice_plane(b['V'], b['F'], 2, z)
        for P in L:
            if len(P) < 6: continue
            i = loop_info(P)
            if i['c'][0] > 0.0:
                print(f"  {b['name']:18s} loop x[{i['min'][0]:+.3f},{i['max'][0]:+.3f}] y[{i['min'][1]:+.3f},{i['max'][1]:+.3f}] A={i['area']*1e4:.1f}cm2 n={i['n']}")
