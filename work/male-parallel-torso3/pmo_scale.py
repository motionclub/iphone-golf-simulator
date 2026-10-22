import sys; sys.path.insert(0, '.')
from pmo_t import *
tag = sys.argv[1]; V = np.load('data/V_base.npy'); T = Torso(V, plate_sigma=2.5, hp_iters=3); T.make_basis(0.012, 0.009)
d = np.load(f'data/c_{tag}.npz'); cF, cB = d['cF'], d['cB']
print('scale  data_rms  score_front score_back  max|dy|')
for g in (0.0, 0.6, 1.0, 1.25, 1.5, 1.8, 2.2):
    r = T.residual(g * cF, g * cB); sc = T.score(g * cF, g * cB); dy = T.dy_mm(g * cF, g * cB)
    print(f'{g:4.2f}   {math.sqrt((r @ r) / T.m_res):.4f}   {sc["front"]:.3f}  {sc["back"]:.3f}   {np.abs(dy).max():.2f}')
