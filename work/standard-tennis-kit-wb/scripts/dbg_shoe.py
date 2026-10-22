import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import shoe as SH
from kit_common import *
g = sys.argv[sys.argv.index('--')+1]
res = SH.build_shoe(g, side=+1, verbose=True)
V, F = res['V'], res['F']
for i, l in enumerate(boundary_loops(F)):
    p = V[l]
    print(i, len(l), "z", p[:,2].min().round(4), p[:,2].max().round(4), "y", p[:,1].min().round(3), p[:,1].max().round(3), "x", p[:,0].min().round(3), p[:,0].max().round(3))
print("shell bbox", V.min(0).round(3), V.max(0).round(3))
