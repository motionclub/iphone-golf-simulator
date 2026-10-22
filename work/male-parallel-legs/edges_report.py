import sys; sys.path.insert(0,'.')
from edges import *
from leglib import *
V=V0
zs=np.arange(0.02,0.76,0.04)
print('front-view runs (u=x) for bald_front / sheet_front vs mesh vertex x extents (+x leg: outer max x, inner min x)')
for z in zs:
    rows=[]
    for v in ('bald_front','sheet_front','bald_back','sheet_back'):
        sp=spans(v,z)
        rows.append(' '.join('[%+.3f,%+.3f]'%(a,b) for a,b in sp))
    s=ZONE&(np.abs(V[:,2]-z)<0.006)&(V[:,0]>0)
    s2=ZONE&(np.abs(V[:,2]-z)<0.006)&(V[:,0]<0)
    m=('mesh +x: [%+.3f,%+.3f] -x: [%+.3f,%+.3f]'%(V[s,0].min(),V[s,0].max(),V[s2,0].min(),V[s2,0].max())) if s.sum() and s2.sum() else ''
    print('z=%.2f'%z, '| bf',rows[0],'| sf',rows[1],'| bb',rows[2],'| sb',rows[3],'|',m)
