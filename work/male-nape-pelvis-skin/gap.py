import sys; sys.path.insert(0,'.')
from contours import *
d = Path(sys.argv[1])
for v in ('bald_front','bald_back'):
    t = mask(M / f'{v}_target.png'); n = mask(d / f'{v}.png'); c = CAM[v]
    print('==', v, ' z | plate gap (x_lo,x_hi mm) | now gap')
    for z in np.arange(0.60, 0.82, 0.01):
        r = int(round(row_of_z(v, z)))
        out = []
        for m in (t, n):
            xs = np.where(m[r, c['roi'][0]:c['roi'][2]+1])[0] + c['roi'][0]
            # find the gap nearest the centre: background run between two foreground runs near centre_x
            cx = c['centre_x']; row = m[r]
            # scan outward from centre
            if row[int(round(cx))]: out.append('closed'); continue
            lo = int(round(cx)); hi = int(round(cx))
            while not row[lo-1] and lo > c['roi'][0]: lo -= 1
            while not row[hi+1] and hi < c['roi'][2]: hi += 1
            out.append(f'({(lo-cx)*c["metres_per_pixel"]*1000:6.1f},{(hi-cx)*c["metres_per_pixel"]*1000:6.1f})')
        print(f'{z:.2f} | {out[0]:>20} | {out[1]:>20}')
