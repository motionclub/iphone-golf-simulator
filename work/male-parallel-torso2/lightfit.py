import sys
sys.path.insert(0, '.')
from plateview import *
V = np.load('data/V_base.npy'); N = vertex_normals(V)
body = (V[:, 2] < 1.40) & (np.abs(V[:, 0]) < 0.40)            # torso + proximal limbs, no head, no hands
for name in ('front', 'back'):
    vw = View(name); vis = visible(vw, V, N, sel=V[:, 2] < 1.40) & body
    col, row = vw.project(V); I = bilinear(gblur(PLATE, 4.0), col, row)
    A = sh2(N[vis]); y = I[vis]
    c, *_ = np.linalg.lstsq(A, y, rcond=None); pred = A @ c
    r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    lin = c[1:4]; d = lin / np.linalg.norm(lin)
    # express light direction in the camera frame: right (+x_img), up (+z), toward camera
    right, up, toward = vw.right, np.array([0, 0, 1.0]), vw.toward
    print(f'{name}: visible body verts {vis.sum()}  SH2 fit R^2 {r2:.3f}  rms {np.sqrt(((y-pred)**2).mean()):.2f} lum levels (std {y.std():.1f})')
    print('   SH coeffs', np.round(c, 2), '\n   first-order light dir (camera frame: right, up, toward):', np.round([d @ right, d @ up, d @ toward], 2), ' => azimuth(+right) %.0f deg, elevation %.0f deg' % (np.degrees(np.arctan2(d @ right, d @ toward)), np.degrees(np.arcsin(d @ up))))
