import numpy as np
M = np.load('data/plate_masks.npz'); S2 = 1.7039/288.5
L, R = M['sheet_left'], M['sheet_right']
aL = 791.5
est = []
for z in np.arange(0.25, 1.30, 0.02):
    r = int(round(338.5 - z/S2)); xl = np.nonzero(L[r])[0]; xr = np.nonzero(R[r])[0]
    if len(xl) < 3 or len(xr) < 3: continue
    # left panel faces left: front = xmin, back = xmax.  y = (x - aL)*S2
    yf = (xl.min() - aL)*S2; yb = (xl.max() - aL)*S2
    # right panel faces right: front = xmax, back = xmin.  y = -(x - b)*S2  ->  b = x + y/S2
    b_f = xr.max() + yf/S2; b_b = xr.min() + yb/S2
    est.append((z, b_f, b_b))
est = np.array(est)
print('z, b from front edge, b from back edge'); print(np.round(est[::3], 1))
print('median b_front %.1f  b_back %.1f  mean %.1f' % (np.median(est[:,1]), np.median(est[:,2]), np.median(np.r_[est[:,1], est[:,2]])))
sel = (est[:,0] > 0.6) & (est[:,0] < 1.1)
print('z .6-1.1: b_front %.1f b_back %.1f' % (np.median(est[sel,1]), np.median(est[sel,2])))
