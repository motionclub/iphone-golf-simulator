"""Foot landmarks of both bodies (read from the npz dumps of the SHA-verified blends), per foot, in the foot's own frame
(toe = -y, heel = +y, ground z = 0, origin = footprint centroid).  Writes tmp/foot_measure_old_female.json.  numpy only."""
import json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from slicer import slice_loops, area

def foot_frame(V, side):
    m = (V[:, 0] * side > 0.02) & (V[:, 2] < 0.035)
    P = V[m][:, :2]
    c = P.mean(0)
    u, s, vt = np.linalg.svd(P - c, full_matrices=False)
    ax = vt[0]
    if ax[1] > 0:
        ax = -ax                      # axis points toward the toes (-y)
    phi = np.arctan2(ax[0], -ax[1])   # toe-out angle: + = toes turned toward +x
    cp, sp = np.cos(phi), np.sin(phi)
    R = np.array([[cp, -sp, 0], [sp, cp, 0], [0, 0, 1.0]])
    if abs((R[:2, :2] @ ax)[0]) > 1e-6:
        R = R.T
    O = np.array([c[0], c[1], 0.0])
    return O, R, float(np.degrees(phi))

out = {}
for name, fn in (('female_OLD_placeholder', 'data/fitref_female_old.npz'),):
    z_ = np.load(fn); V, F = z_['V'], z_['F']
    out[name] = {}
    for side, sn in ((+1, 'R'), (-1, 'L')):
        O, R, phi = foot_frame(V, side)
        sel = (V[:, 0] * side > 0.02) & (V[:, 2] < 0.40)
        Vl = (V - O) @ R.T
        # check frame: foot axis should now be along -y
        fp = Vl[(V[:, 0] * side > 0.02) & (V[:, 2] < 0.035)]
        d = {}
        d['frame_origin'] = O.round(5).tolist(); d['toe_out_deg'] = round(phi, 3)
        foot = Vl[(V[:, 0] * side > 0.02) & (V[:, 2] < 0.20)]          # foot + ankle + a bit of shin
        # longest toe: front-most vertex of everything below 60 mm
        low = Vl[(V[:, 0] * side > 0.02) & (V[:, 2] < 0.06)]
        i = np.argmin(low[:, 1]); d['toe_tip_local'] = low[i].round(5).tolist(); d['toe_tip_world'] = (low[i] @ R + O).round(5).tolist()
        # heel point: rear-most vertex below 0.12 (heel block)
        low2 = Vl[(V[:, 0] * side > 0.02) & (V[:, 2] < 0.12)]
        j = np.argmax(low2[:, 1]); d['heel_point_local'] = low2[j].round(5).tolist(); d['heel_point_world'] = (low2[j] @ R + O).round(5).tolist()
        d['foot_length_m'] = round(float(low2[j, 1] - low[i, 1]), 5)
        xs = Vl[(V[:, 0] * side > 0.02) & (V[:, 2] < 0.06)][:, 0]
        d['foot_width_m'] = round(float(xs.max() - xs.min()), 5)
        d['x_range_local'] = [round(float(xs.min()), 5), round(float(xs.max()), 5)]
        d['min_z'] = round(float(V[(V[:, 0] * side > 0.02)][:, 2].min()), 5)
        # sagittal contours + leg slices in the foot frame
        rows = []
        for z in np.arange(0.01, 0.34, 0.005):
            ls = [P for P in slice_loops(Vl, F, z) if len(P) >= 6 and (P[:, 0].mean() * 1.0) is not None]
            # keep the loop of THIS foot: its centroid on the right side in world
            keep = []
            for P in ls:
                w = P @ R + O
                if w[:, 0].mean() * side > 0.02:
                    keep.append(P)
            if not keep:
                continue
            P = np.concatenate(keep)
            rows.append((float(z), float(P[:, 1].min()), float(P[:, 1].max()), float(P[:, 0].min()), float(P[:, 0].max()),
                         float(sum(area(q) for q in keep)), float(P[:, 0].mean()), float(P[:, 1].mean())))
        rows = np.array(rows)
        d['rows_z_ymin_ymax_xmin_xmax_area_cx_cy'] = rows.round(5).tolist()
        # ankle: minimum cross-section area between z=0.07 and 0.28 (smoothed)
        m = (rows[:, 0] > 0.07) & (rows[:, 0] < 0.28)
        ar = np.convolve(rows[:, 5], np.ones(5) / 5, mode='same')
        idx = np.nonzero(m)[0]
        k = idx[np.argmin(ar[idx])]
        d['ankle_z'] = round(float(rows[k, 0]), 4); d['ankle_area_cm2'] = round(float(rows[k, 5] * 1e4), 2)
        d['ankle_center_local_xy'] = [round(float(rows[k, 6]), 5), round(float(rows[k, 7]), 5)]
        d['ankle_width_x_m'] = round(float(rows[k, 4] - rows[k, 3]), 5); d['ankle_depth_y_m'] = round(float(rows[k, 2] - rows[k, 1]), 5)
        # shin front y (vertical part of the front contour near the ankle) and instep junction height
        zz = rows[:, 0]
        yf = rows[:, 1]
        near = (zz > d['ankle_z'] - 0.02) & (zz < d['ankle_z'] + 0.06)
        y_shin = float(np.median(yf[near]))
        d['shin_front_y_local'] = round(y_shin, 5)
        ok = np.nonzero((yf >= y_shin - 0.004) & (zz > 0.03))[0]
        d['instep_junction_z'] = round(float(zz[ok[0]]), 4) if len(ok) else None
        # instep high point: highest z of the dorsal surface in front of the shin line (vertices with y < y_shin - 0.004, z < 0.2)
        dors = Vl[(V[:, 0] * side > 0.02) & (V[:, 2] < 0.20) & (Vl[:, 1] < y_shin - 0.004)]
        q = np.argmax(dors[:, 2]); d['instep_high_point_local'] = dors[q].round(5).tolist()
        # heel block: rear contour
        ym = rows[:, 2]
        y_ach = float(np.median(ym[(zz > d['ankle_z'] - 0.02) & (zz < d['ankle_z'] + 0.03)]))
        d['achilles_back_y_local'] = round(y_ach, 5)
        okb = np.nonzero((ym <= y_ach + 0.004) & (zz > 0.03))[0]
        d['heel_block_top_z'] = round(float(zz[okb[0]]), 4) if len(okb) else None
        out[name][sn] = d
        print(f"{name} {sn}: toe-out {phi:+.2f} deg | L {d['foot_length_m']*1000:.1f} W {d['foot_width_m']*1000:.1f} mm | toe tip {np.round(d['toe_tip_local'],4)} heel {np.round(d['heel_point_local'],4)} | "
              f"ankle z {d['ankle_z']:.3f} (A {d['ankle_area_cm2']} cm2, {d['ankle_width_x_m']*1000:.0f}x{d['ankle_depth_y_m']*1000:.0f} mm, centre {d['ankle_center_local_xy']}) | shin front y {d['shin_front_y_local']:.4f} instep junction z {d['instep_junction_z']} instep high {np.round(d['instep_high_point_local'],4)} | achilles y {d['achilles_back_y_local']:.4f} heel block top z {d['heel_block_top_z']} | min z {d['min_z']}")
json.dump(out, open('tmp/foot_measure_old_female.json', 'w'), indent=1)
