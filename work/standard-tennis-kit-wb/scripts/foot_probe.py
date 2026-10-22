import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, bpy
from kitlib import *
from fitbody import *
for g in ('male', 'female'):
    bodies = load_set(g)
    for b in bodies:
        V = b['V']
        for side in (+1, -1):
            m = (V[:,0]*side > 0.02) & (V[:,2] < 0.035)
            P = V[m][:, :2]
            c = P.mean(0)
            u, s, vt = np.linalg.svd(P - c, full_matrices=False)
            ax = vt[0]
            if ax[1] > 0: ax = -ax          # point toward -y (toes)
            ang = np.degrees(np.arctan2(ax[0]*side, -ax[1]))
            proj = (P - c) @ ax
            lat = (P - c) @ np.array([-ax[1], ax[0]])
            print(f"{b['name']:18s} side {side:+d}: footprint centre {c.round(3)} axis {ax.round(3)} toe-out {ang:.1f} deg  length {proj.max()-proj.min():.3f}  width {lat.max()-lat.min():.3f}  zmin {V[(V[:,0]*side>0.02)&(V[:,2]<0.2),2].min():.4f}")
        # ankle circumference at z=0.10 and 0.12, 0.16 right foot
        for z in (0.08, 0.10, 0.12, 0.16, 0.20):
            L = slice_plane(V, b['F'], 2, z)
            for Pp in L:
                if len(Pp) > 6 and Pp[:,0].mean() > 0.02:
                    i = loop_info(Pp)
                    print(f"      z={z:.2f} right leg loop x[{i['min'][0]:.3f},{i['max'][0]:.3f}] y[{i['min'][1]:.3f},{i['max'][1]:.3f}] A={i['area']*1e4:.0f}cm2")
