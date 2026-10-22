import sys, numpy as np
sys.path.insert(0, 'tools')
from rawio import load
def lum(a): a = a[..., :3].astype(np.float64); return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
def blur(l, sig):
    if sig <= 0: return l
    k = np.exp(-0.5 * (np.arange(-int(3*sig)-1, int(3*sig)+2) / sig) ** 2); k /= k.sum()
    b = np.apply_along_axis(lambda r: np.convolve(r, k, 'same'), 1, l); return np.apply_along_axis(lambda c: np.convolve(c, k, 'same'), 0, b)
def tens(l, sig_pre, sig_int):
    b = blur(l, sig_pre); gx = np.gradient(b, axis=1); gy = np.gradient(b, axis=0)
    Jxx, Jyy, Jxy = blur(gx*gx, sig_int), blur(gy*gy, sig_int), blur(gx*gy, sig_int)
    # per-pixel eigen ratio then mean? and global
    gJ = np.array([[Jxx.mean(), Jxy.mean()], [Jxy.mean(), Jyy.mean()]]); ev = np.linalg.eigvalsh(gJ)
    tr = Jxx + Jyy; det = Jxx*Jyy - Jxy**2; disc = np.sqrt(np.maximum(tr*tr/4 - det, 0)); l1 = tr/2 + disc; l2 = tr/2 - disc
    coh = ((l1 - l2) / np.maximum(l1 + l2, 1e-9)).mean()
    return ev[1]/max(ev[0],1e-12), coh, (1+coh)/(1-coh)
boxes = {'ruin_low': ('hole09_3_ruin', (0,1100,900,1600)), 'ruin_patch': ('hole09_3_ruin', (500,1000,900,1400)), 'tee9': ('hole09_1_tee', (0,1100,900,1600))}
for sp, si in [(0,0),(0.7,0),(1,0),(0.7,4),(1,6),(0,8)]:
    row=[]
    for nm,(n,(x0,y0,x1,y1)) in boxes.items():
        l = lum(load(f'raw/{n}'))[y0:y1, x0:x1]; g, c, cr = tens(l, sp, si); row.append(f'{nm} glob {g:.2f} coh {c:.2f} cr {cr:.2f}')
    print(sp, si, ' | '.join(row))
