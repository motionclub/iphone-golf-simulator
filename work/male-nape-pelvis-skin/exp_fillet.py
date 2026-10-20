import sys; sys.path.insert(0,'.')
from sculpt import *
tag = sys.argv[1]; iters = int(sys.argv[2]); zc = float(sys.argv[3]) if len(sys.argv) > 3 else 0.787; hz = float(sys.argv[4]) if len(sys.argv) > 4 else 0.035
X,Y,Z = V0[:,0],V0[:,1],V0[:,2]; U=np.abs(X)
# weight: band around the crotch plane z=zc (half-height hz), |x|<0.12 fading to 0.16
w = np.exp(-0.5*((Z-zc)/hz)**2) * (1-smoothstep(0.11,0.16,U))
w = np.clip(w*1.0,0,1)
V = V0.copy()
for c in (1,2):     # smooth y and z only, keep x so the front/back silhouette extents stay
    V[:,c] = taubin_scalar(V[:,c], w, iters=iters)
d=np.linalg.norm(V-V0,axis=1)*1000; print(tag,'max move mm',d.max().round(2),'moved>0.1',int((d>0.1).sum()))
np.save(f'data/V_{tag}.npy',V)
