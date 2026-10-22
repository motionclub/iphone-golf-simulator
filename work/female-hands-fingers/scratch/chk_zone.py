import numpy as np
Z = np.load('../female-arms-form2/data/zones_cur.npz')
for k in Z.files:
    a = Z[k]; print(k, a.shape, a.dtype, int(a.sum()) if a.dtype == bool else a[:5])
D = np.load('data/mesh_start.npz'); V = D['V']
arm = Z['arm'] if 'arm' in Z.files else None
if arm is not None:
    idx = np.nonzero(arm)[0]; print('arm zone z range', V[idx,2].min(), V[idx,2].max(), 'x', V[idx,0].min(), V[idx,0].max())
    for side in (1,-1):
        ring = np.load(f'data/start_hand_ring_{side}.npy'); print('side', side, 'ring in arm zone', int(arm[ring].sum()), '/', len(ring))
