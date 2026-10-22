"""full sagittal outline (all crossings) around the roof rear edge: python3.13 prof2.py <tag|start> u"""
import sys; sys.path.insert(0,'.')
from common import *
tag=sys.argv[1]; V = V0 if tag=='start' else np.load(f'data/V_{tag}.npy'); u=float(sys.argv[2])
S = section_x(V, u+1e-5)
# polyline pieces in (y,z); list segments with z in [0.73,0.83] and y>0.0 (rear half)
rows=[]
for (p,q) in S:
    for a in (p,q):
        pass
pts=[]
for (p,q) in S:
    if max(p[1],q[1])>0.73 and min(p[1],q[1])<0.83 and max(p[0],q[0])>0.02:
        pts.append((p[1],p[0])); pts.append((q[1],q[0]))
pts=sorted(set((round(z,4),round(y*1000,1)) for z,y in pts))
print(tag,'u',u,'(z, y_mm) points of rear outline:'); print(pts)
