import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, bpy
from kitlib import *
from fitbody import *
for g in ('female',):
    bodies = load_set(g)
    for b in bodies:
        V = b['V']
        m = (np.abs(V[:,0]) > 0.19) & (V[:,2] < 1.0) & (V[:,2] > 0.55)
        print(b['name'], "verts |x|>0.19 z in .55-1.0:", m.sum(), "z min", V[m,2].min().round(3), "x range", np.abs(V[m,0]).min().round(3), np.abs(V[m,0]).max().round(3), "y range", V[m,1].min().round(3), V[m,1].max().round(3))
        # per-z inner x (min |x| among |x|>0.19 verts) 
        for z in (0.70,0.72,0.74,0.76,0.80,0.84,0.88,0.92):
            mm = (np.abs(V[:,2]-z) < 0.006) & (np.abs(V[:,0]) > 0.15)
            if mm.any():
                print(f"   z={z:.2f} arm/hand |x| min {np.abs(V[mm,0]).min():.3f} max {np.abs(V[mm,0]).max():.3f}  y {V[mm,1].min():.3f}..{V[mm,1].max():.3f}")
