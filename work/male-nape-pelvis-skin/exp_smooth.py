import sys; sys.path.insert(0,'.')
from sculpt import *
iters = int(sys.argv[1]); tag = sys.argv[2]
X, Y, Z = V0[:,0], V0[:,1], V0[:,2]
w = band(Z, 0.74, 0.80, 1.00, 1.06) * (1 - smoothstep(0.17, 0.21, np.abs(X)))
V = taubin(V0, w, iters=iters)
d = np.linalg.norm(V - V0, axis=1) * 1000
print(tag, 'max move mm', d.max().round(2), 'moved>0.1mm', int((d > 0.1).sum()))
np.save(f'data/V_{tag}.npy', V)
