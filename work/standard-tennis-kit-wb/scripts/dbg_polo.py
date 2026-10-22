import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import polo as PO
from kit_common import *
res = PO.build_polo(sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'male', verbose=False)
V, F = res['sheet']
loops = boundary_loops(F)
for i,l in enumerate(loops):
    pts = V[l]; print(i, len(l), "z range", pts[:,2].min().round(3), pts[:,2].max().round(3), "x", pts[:,0].min().round(3), pts[:,0].max().round(3), "y", pts[:,1].min().round(3), pts[:,1].max().round(3))
print(res['info'])
# front neck z
nl = V[loops[res['info']['neck']]]
c = nl.mean(0)
phi = np.arctan2(nl[:,0]-c[0], -(nl[:,1]-c[1]))
o = np.argsort(phi)
print("neck center", c.round(3), "front z (phi~0):", np.interp(0, phi[o], nl[o][:,2]).round(4), "back z:", np.interp(np.pi-0.01, phi[o], nl[o][:,2]).round(4))
print("shell z range at x=0,y<-0.1:", V[(abs(V[:,0])<0.01)&(V[:,1]<-0.12)][:,2].min().round(3), V[(abs(V[:,0])<0.01)&(V[:,1]<-0.12)][:,2].max().round(3))
