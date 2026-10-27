# Reader for HeroLodCoverProbe.Dump meshes.
import numpy as np
def load(path):
    b = open(path, 'rb').read(); o = 0
    def take(dt, cnt):
        nonlocal o; a = np.frombuffer(b, dt, cnt, o); o += a.nbytes; return a
    n = int(take('<i4', 1)[0])
    m = dict(n=n, pos=take('<f4', 3 * n).reshape(n, 3), nrm=take('<f4', 3 * n).reshape(n, 3), col=take('u1', 4 * n).reshape(n, 4))
    for ch in range(5): m['uv%d' % ch] = take('<f4', 4 * n).reshape(n, 4)
    bw = take('<i4', 8 * n).reshape(n, 8); m['bi'] = bw[:, :4]; m['bw'] = bw[:, 4:].view('<f4')
    subs = int(take('<i4', 1)[0]); m['tris'] = []
    for s in range(subs): c = int(take('<i4', 1)[0]); m['tris'].append(take('<i4', c).reshape(-1, 3))
    return m
