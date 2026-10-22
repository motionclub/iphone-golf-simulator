import sys; sys.path.insert(0,'.')
from snap import *
V=np.load('data/V_K2.npy')
Vt=V.copy()
# widen legs outward by 6 mm about each leg's centre line in x and push forward 5 mm in y (smoothly faded at the zone top)
fade=smoothstep(ZT,ZT-0.1,V[:,2])*ZONE
cx=np.where(V[:,0]>0,0.15,-0.15)
Vt[:,0]+=fade*(V[:,0]-cx)*0.06
Vt[:,1]+=fade*(V[:,1]+0.03)*0.05
print('before:',fmt(metrics(V,('bald_front','bald_back','left'))))
print('perturbed:',fmt(metrics(Vt,('bald_front','bald_back','left'))))
Vs=snap(Vt,3,0.7)
print('snapped:',fmt(metrics(Vs,('bald_front','bald_back','left'))))
