import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, lab
gl = lab.gl
def fund(a):
    n = a.shape[0]
    b = gl.blur(a.astype(np.float32), n / 48.0)
    P = np.abs(np.fft.fft2(b - b.mean())) ** 2
    kf = np.abs(np.fft.fftfreq(n) * n); KX, KY = np.meshgrid(kf, kf); km = np.maximum(KX, KY)
    return float(P[km == 1].sum() / P[(km >= 1) & (km <= 6)].sum())
d = gl.mat_lava(1024, 1201, 1)
E = d['E']; C = d['C']
print('fund E lum %.3f  E R %.3f  C R %.3f  C lum %.3f' % (fund(gl.lum(E)), fund(E[..., 0]), fund(C[..., 0]), fund(gl.lum(C))))
