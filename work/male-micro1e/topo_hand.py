import numpy as np,sys
sys.path.insert(0,'.')
from wire import plot
d=np.load('baseline/mesh.npz'); co=d['co']; e=d['edges']
sel=(co[:,0]>0.40)&(co[:,2]<1.02)
print('hand verts',sel.sum())
# front view (x,z) and top-ish views
plot(co,e,sel,(0,2),(0.40,0.70,0.76,1.04),size=1100,path='topo_hand_xz.png')
plot(co,e,sel,(1,2),(-0.18,0.04,0.76,1.04),size=1100,path='topo_hand_yz.png')
sel2=(co[:,0]>0.40)&(co[:,2]<1.02)&(co[:,1]<-0.09)
plot(co,e,sel2,(0,2),(0.40,0.70,0.76,1.04),size=1100,path='topo_hand_xz_front.png')
