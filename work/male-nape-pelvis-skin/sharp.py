import sys; sys.path.insert(0,'.')
from roughness import *
t=sys.argv[1]; V=np.load(f'data/V_{t}.npy'); d1=dihedral(V)
m=(d1>40)&(d0<25)
ids=np.where(m)[0]
ctr=(V0[ev[ids,0]]+V0[ev[ids,1]])/2
order=np.lexsort((ctr[:,0],ctr[:,2]))
for k in order[:60]: print(f'edge ctr x {ctr[k,0]*1000:6.1f} y {ctr[k,1]*1000:6.1f} z {ctr[k,2]*1000:6.1f} mm  dihedral {d1[ids[k]]:5.1f} (start {d0[ids[k]]:4.1f})')
