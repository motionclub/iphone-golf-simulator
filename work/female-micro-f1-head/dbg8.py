import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-micro-f1-head')
import numpy as np, geo, facef, feat_f, loftf, fl
H = geo.Head(); sk = facef.Skin(H)
L = facef.Layer()
facef.eye_shell(H, L, sk, -1)
V = np.array(L.V); F = L.F
print(len(V), len(F))
# orientation sanity: count triangles whose normal points away from centre
bad = 0
for f in F:
    p = V[f]; n = np.cross(p[1]-p[0], p[2]-p[0]); 
    if np.linalg.norm(n) < 1e-12: bad += 1
print('degenerate faces', bad)
nphi=40
# are consecutive ring vertices neighbours?  print distance between ring k vertex i and i+1
for k in (1,3,6,8,9):
    ring = V[k*nphi:(k+1)*nphi]; d = np.linalg.norm(np.roll(ring,-1,axis=0)-ring,axis=1); print(k, 'edge mm min %.2f max %.2f' % (d.min()*1000, d.max()*1000))
# radial neighbours
for k in (1,3,6,8):
    a = V[k*nphi:(k+1)*nphi]; b = V[(k+1)*nphi:(k+2)*nphi]; d = np.linalg.norm(a-b,axis=1); print('radial', k, 'min %.2f max %.2f' % (d.min()*1000, d.max()*1000))
loftf.save_npz(str(fl.W/'data/shell_dbg.npz'), V, F)
