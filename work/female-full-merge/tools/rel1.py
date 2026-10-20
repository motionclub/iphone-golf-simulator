import numpy as np
D = {k: np.load(f'data/{k}.npz') for k in ['artdir_body','base_body','f3_body','form5_body','arms_body']}
def keyset(V): return {tuple(v): i for i, v in enumerate(V.astype(np.float32))}
A = D['artdir_body']['V']; B = D['base_body']['V']; F = D['f3_body']['V']; T = D['form5_body']['V']; M = D['arms_body']['V']
print('art', A.shape, 'base', B.shape, 'f3', F.shape, 'form5', T.shape, 'arms', M.shape)
# F3 vs ArtDir exact position matches
kA = keyset(A)
mF = np.array([kA.get(tuple(v), -1) for v in F.astype(np.float32)])
print('F3 verts exactly equal to an ArtDir vertex:', (mF >= 0).sum(), 'of', len(F), ' dup-keys in ArtDir:', len(A) - len(kA))
print('F3 index range of matched:', np.nonzero(mF >= 0)[0].min(), np.nonzero(mF >= 0)[0].max(), ' first unmatched idx:', np.nonzero(mF < 0)[0].min() if (mF<0).any() else None)
idx_m = np.nonzero(mF >= 0)[0]; print('matched count contiguous prefix?', np.array_equal(idx_m, np.arange(len(idx_m))), 'identity?', np.array_equal(mF[idx_m], idx_m))
um = np.nonzero(mF < 0)[0]; print('unmatched F3 verts: n', len(um), 'z range', F[um,2].min(), F[um,2].max())
mt = mF[mF>=0]; print('matched F3 verts z range', F[mF>=0,2].min(), F[mF>=0,2].max())
# ArtDir verts not used by F3
usedA = np.zeros(len(A), bool); usedA[mt] = True
print('ArtDir verts absent from F3:', (~usedA).sum(), ' z range', A[~usedA,2].min(), A[~usedA,2].max())
# base vs ArtDir
mB = np.array([kA.get(tuple(v), -1) for v in B.astype(np.float32)])
print('base verts exactly equal to ArtDir vert:', (mB>=0).sum(), 'of', len(B), '; unmatched', (mB<0).sum())
# FORM5 vs ArtDir by index
d = np.abs(T - A).max(1); print('FORM5 vs ArtDir by index: moved', (d>0).sum(), 'max mm', d.max()*1000)
