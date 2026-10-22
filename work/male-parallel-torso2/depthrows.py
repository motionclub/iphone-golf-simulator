import sys; sys.path.insert(0, '.')
import prof, numpy as np
def rows(tag):
    P = prof.profile(f'r/sil_{tag}'); out = {}
    for zk in sorted(P['left']['plate'], key=float):
        zf = float(zk)
        if zf < 0.92 or zf > 1.30: continue
        dl = []
        for v in ('left', 'right'):
            a, b = P[v]['plate'][zk], P[v]['mesh'][zk]
            if a and b: dl.append((a[1] - a[0]) - (b[1] - b[0]))
        out[round(zf, 2)] = float(np.mean(dl))
    return out
A = rows(sys.argv[1]); B = rows(sys.argv[2])
print('z     ' + sys.argv[1] + '   ' + sys.argv[2])
for z in A: print(f'{z:.2f}  {A[z]:+5.1f}  {B[z]:+5.1f}  diff {B[z]-A[z]:+5.1f}')
print('rms', np.sqrt(np.mean(np.array(list(A.values()))**2)), np.sqrt(np.mean(np.array(list(B.values()))**2)))
