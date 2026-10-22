import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import polo as PO
from kit_common import *
g = sys.argv[sys.argv.index('--')+1]
res = PO.build_polo(g, verbose=False)
V, F = res['sheet']
surf = Surface(V, F)
P = PO.PARAMS[g]
for z in np.arange(0.97, 1.16, 0.01):
    l, n, idx, d = surf.tree.ray_cast([0.0, P['side_y'], z], [1, 0, 0])
    print(f"z={z:.2f}: hit x={'MISS' if idx is None else round(l[0],3)}")
