import sys; sys.path.insert(0, '.')
from pmo_t import *
from slab import *
V = np.load('data/V_base.npy'); T = Torso(V); T.make_basis(0.012, 0.009)
c = np.load('data/c_s_b2.npz'); P = T.positions(T.dy_mm(c['cF'], c['cB']))
Z = zone_mask(V); zs = np.arange(0.80, 1.36, 0.0025); F0, B0 = extremes(V, Z, zs)
F1, B1 = extremes(P, Z, zs); print('raw PMO:   max extreme drift front %.2f back %.2f mm' % (np.nanmax(np.abs(F1 - F0)) * 1000, np.nanmax(np.abs(B1 - B0)) * 1000))
P1, dF, dB = slab_fix(P, V, T.wf, T.wb); F1, B1 = extremes(P1, Z, zs); print('1x guard:  max drift front %.2f back %.2f mm' % (np.nanmax(np.abs(F1 - F0)) * 1000, np.nanmax(np.abs(B1 - B0)) * 1000))
for n, sg in ((3, 0.006), (5, 0.0045), (6, 0.003)):
    P2, a, b = slab_fix_iter(P, V, T.wf, T.wb, n=n, sigma=sg); print(f'{n}x guard sigma {sg}: max drift front {a:.2f} back {b:.2f} mm ; max |extra dy| {np.abs(P2[:,1]-P[:,1]).max()*1000:.2f} mm')
