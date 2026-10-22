"""reviewer's metric (reproduced exactly on the 10-04 21:02 stills: 5.46 / 8.20 / 2.06): global eigenvalue ratio of the structure tensor of the UNBLURRED luminance gradient (np.gradient) over a crop."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rawio import load
def lum(a): a = a[..., :3].astype(np.float64); return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
def ratio(l):
    gx = np.gradient(l, axis=1); gy = np.gradient(l, axis=0)
    J = np.array([[np.mean(gx*gx), np.mean(gx*gy)], [np.mean(gx*gy), np.mean(gy*gy)]]); ev = np.linalg.eigvalsh(J)
    return float(ev[1] / max(ev[0], 1e-12)), float(0.5*np.degrees(np.arctan2(2*J[0,1], J[0,0]-J[1,1])))
BOX = {'ruin_lower_third': ('hole09_3_ruin', (0,1100,900,1600)), 'ruin_steep_patch': ('hole09_3_ruin', (500,1000,900,1400)), 'tee9_lower': ('hole09_1_tee', (0,1100,900,1600)),
       'tee8_lower': ('hole08_1_tee', (0,1100,900,1600)), 'appr9_lower': ('hole09_2_approach', (0,1100,900,1600)), 'appr8_lower': ('hole08_2_approach', (0,1100,900,1600)), 'tee10_lower': ('hole10_1_tee', (0,1100,900,1600))}
if __name__ == '__main__':
    d = sys.argv[1]; ok_all = True
    for nm, (n, (x0, y0, x1, y1)) in BOX.items():
        if not os.path.exists(f'{d}/{n}.raw'): continue
        r, a = ratio(lum(load(f'{d}/{n}'))[y0:y1, x0:x1])
        print(f'  {nm:18s} {n} crop {x0},{y0},{x1},{y1}: eigenvalue ratio {r:5.2f}  dominant gradient {a:4.0f} deg')
