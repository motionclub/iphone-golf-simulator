import sys, numpy as np
sys.path.insert(0, 'tools')
from rawio import load
def lum(a): a = a[..., :3].astype(np.float64); return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
def tensor(l, sig=1.0):
    # gaussian blur via separable kernel
    k = np.exp(-0.5 * (np.arange(-4, 5) / sig) ** 2); k /= k.sum()
    b = np.apply_along_axis(lambda r: np.convolve(r, k, 'same'), 1, l); b = np.apply_along_axis(lambda c: np.convolve(c, k, 'same'), 0, b)
    gx = np.gradient(b, axis=1); gy = np.gradient(b, axis=0)
    J = np.array([[np.mean(gx*gx), np.mean(gx*gy)], [np.mean(gx*gy), np.mean(gy*gy)]])
    ev = np.linalg.eigvalsh(J); ang = 0.5*np.degrees(np.arctan2(2*J[0,1], J[0,0]-J[1,1]))
    return ev[1]/max(ev[0],1e-12), ang
for d, n, box in [(a, b, c) for a, b, c in [(x.split(':')[0], x.split(':')[1], tuple(map(int, x.split(':')[2].split(',')))) for x in sys.argv[1:]]]:
    l = lum(load(f'{d}/{n}')); x0, y0, x1, y1 = box
    r, ang = tensor(l[y0:y1, x0:x1])
    print(f'{d}/{n} box {box}: eigen ratio {r:.2f}  (sqrt {np.sqrt(r):.2f}) dominant gradient dir {ang:.0f} deg')
