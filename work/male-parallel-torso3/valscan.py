import sys
sys.path.insert(0, '.')
from pmo_val import *
V = np.load('data/V_base.npy'); T = Torso(V); T.make_basis(0.012, 0.009); VL = Val(T)
def show(tag, P):
    s = VL.score(P); print(f'{tag:8s} ' + ' '.join(f'{k} {v:+.3f}' for k, v in s.items()))
show('base', V)
for tag in sys.argv[1:]:
    show(tag, np.load(f'data/V_{tag}.npy'))
