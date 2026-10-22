import sys; sys.path.insert(0,'.')
from lib import *
load(); clay_setup()
d=np.load('baseline/mesh.npz'); co=d['co']
hand=(co[:,0]>0.55)&(co[:,2]<0.98); c=co[hand].mean(0); print('hand centre',c)
T=tuple(c)
for name,az,el in [('front',0,0),('back',180,0),('side_in',270,0),('side_out',90,0),('threeq',35,20),('top',0,85),('bottom',0,-85)]:
    shot(f'r/look_hand_{name}.png',T,az,el,0.30,(700,700))
