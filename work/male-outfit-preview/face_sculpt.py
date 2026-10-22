"""Preview-only facial structure sculpt on a COPY of Body_M (coordinate displacement fields on the head).

Landmarks use the body-plate calibration (S = 1.7/593 m/px): eyes z 1.582, nose tip z ~1.540, mouth z 1.504.
Everything is a smooth field so the soft-plastic look is kept; nothing below z 1.43 moves.
"""
import numpy as np
import bpy
import bmesh

YC = -0.045          # head centre in y


def sm(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def g2(x, cx, sx, z, cz, sz):
    return np.exp(-((x - cx) / sx) ** 2 - ((z - cz) / sz) ** 2)


def normals(me):
    bm = bmesh.new(); bm.from_mesh(me); bm.normal_update()
    n = np.array([v.normal[:] for v in bm.verts]); bm.free(); return n


PR = dict(
    cheek_narrow=0.090,      # max |x| scale-down of the mid/lower face (fraction)
    brow=0.0035, socket=-0.0045, cheekbone=0.0035, temple=-0.0025,
    nose_bridge=0.006, nose_tip=0.020, nose_ala=0.009, nose_w=0.011,
    lips=0.0035, philtrum=-0.0015, chin_ball=0.0025, jaw_soft=0.0,
    eye_z=1.582, eye_x=0.031, nose_tip_z=1.540, nose_root_z=1.600, mouth_z=1.504,
)


def sculpt(obj, P=PR):
    me = obj.data
    V = np.array([v.co[:] for v in me.vertices], float)
    N = normals(me)
    x, y, z = V[:, 0], V[:, 1], V[:, 2]
    head = (z > 1.43) & (np.abs(x) < 0.14)
    front = (y < YC)                                   # face half
    fr = sm(YC + 0.02, YC - 0.05, y)                   # 0 at the back of the head, 1 on the face
    disp = np.zeros(len(V))
    ax = np.abs(x)
    # --- narrow the cheeks / jaw sides: scale |x| inward, strongest at z 1.50-1.56, only on the face half
    zw = sm(1.455, 1.50, z) * (1 - sm(1.57, 1.63, z))
    k = P['cheek_narrow'] * zw * sm(0.02, 0.07, ax) * (0.35 + 0.65 * fr)
    V[:, 0] = x * (1 - k)
    x = V[:, 0]; ax = np.abs(x)
    # --- brow ridge
    disp += P['brow'] * g2(ax, 0.030, 0.034, z, P['eye_z'] + 0.024, 0.009) * fr
    # --- eye sockets (recess), slightly almond
    for s in (-1, 1):
        disp += P['socket'] * g2(x, s * P['eye_x'], 0.021, z, P['eye_z'] - 0.002, 0.012) * fr
    # --- cheekbones
    for s in (-1, 1):
        disp += P['cheekbone'] * g2(x, s * 0.056, 0.020, z, P['eye_z'] - 0.030, 0.014) * fr
    # --- temples
    for s in (-1, 1):
        disp += P['temple'] * g2(x, s * 0.078, 0.016, z, P['eye_z'] + 0.012, 0.016) * fr
    # --- nose: bridge -> tip along the centre line, with alae
    tz = P['nose_tip_z']; rz = P['nose_root_z']
    u = np.clip((z - tz) / (rz - tz), 0, 1)           # 1 at root, 0 at tip
    along = sm(tz - 0.012, tz + 0.004, z) * (1 - sm(rz - 0.006, rz + 0.016, z))
    prof = P['nose_bridge'] + (P['nose_tip'] - P['nose_bridge']) * (1 - u) ** 1.6
    width = P['nose_w'] * (0.55 + 0.45 * (1 - u))
    nose = prof * np.exp(-(ax / width) ** 2) * along
    for s in (-1, 1):
        nose += P['nose_ala'] * g2(x, s * 0.015, 0.009, z, tz + 0.004, 0.007)
    # tip rounding: fade near the tip bottom
    nose *= (1 - sm(tz - 0.004, tz - 0.016, z))
    disp += nose * fr
    # --- lips mound + philtrum groove
    disp += P['lips'] * g2(ax, 0.0, 0.028, z, P['mouth_z'] + 0.002, 0.011) * fr
    disp += P['philtrum'] * g2(ax, 0.0, 0.005, z, P['mouth_z'] + 0.016, 0.009) * fr
    # --- chin ball
    disp += P['chin_ball'] * g2(ax, 0.0, 0.022, z, 1.462, 0.013) * fr
    # narrow the old blockout nose mound (flanks beside the nose) and cut the step under the tip
    disp += P.get('flank', -0.009) * np.exp(-((ax - 0.027) / 0.012) ** 2) * np.exp(-((z - 1.536) / 0.017) ** 2) * fr
    disp += P.get('lump', -0.010) * np.exp(-(ax / 0.030) ** 2) * np.exp(-((z - 1.533) / 0.020) ** 2) * fr
    disp += P.get('undertip', -0.006) * np.exp(-(ax / 0.013) ** 2) * np.exp(-((z - 1.519) / 0.007) ** 2) * fr
    disp *= head
    V = V + N * disp[:, None]
    if P.get('nose_mode', 'wedge') == 'wedge':
        # ---- explicit nose: flatten the old blockout mound to the cheek plane, then raise a rounded wedge whose
        #      centre ridge follows a profile target (z -> y) and whose half-width follows w(z)
        x, y, z = V[:, 0], V[:, 1], V[:, 2]; ax = np.abs(x)
        zb = np.arange(1.49, 1.64, 0.005)
        ch = []
        for zz in zb:
            m = (np.abs(z - zz) < 0.006) & (ax > 0.050) & (ax < 0.068) & (y < YC)
            ch.append(y[m].min() if m.any() else np.nan)
        ch = np.array(ch); ok = ~np.isnan(ch); cheek = np.interp(z, zb[ok], ch[ok])
        RZ = np.array([1.505, 1.515, 1.522, 1.528, 1.535, 1.542, 1.548, 1.560, 1.575, 1.590, 1.605, 1.620])
        RY = np.array([-0.150, -0.151, -0.154, -0.163, -0.173, -0.1765, -0.175, -0.169, -0.162, -0.156, -0.149, -0.1455]) + P.get('nose_y_off', 0.0)
        RW = np.array([0.005, 0.007, 0.009, 0.013, 0.017, 0.019, 0.018, 0.014, 0.011, 0.0095, 0.009, 0.009]) * P.get('nose_w_scale', 1.0)
        ridge = np.interp(z, RZ, RY); w = np.interp(z, RZ, RW)
        region = head & (y < YC) & (ax < 0.036) & (z > 1.503) & (z < 1.622)
        wgt = (1 - sm(0.026, 0.036, ax)) * sm(1.503, 1.512, z) * (1 - sm(1.612, 1.622, z))
        flat = cheek - 0.0025 * (1 - ax / 0.036)
        y_flat = np.maximum(y, flat)                         # push the old mound back to the cheek plane
        prof = np.clip(1 - (ax / np.maximum(w, 1e-4)) ** 2, 0, 1) ** 0.75
        y_nose = cheek + (ridge - cheek) * prof
        y_new = np.where(prof > 0, np.minimum(y_flat, y_nose), y_flat)
        V[region, 1] = y[region] + (y_new[region] - y[region]) * wgt[region]
    # keep everything below 1.43 exactly
    orig = np.array([v.co[:] for v in me.vertices], float)
    keep = ~head
    V[keep] = orig[keep]
    me.vertices.foreach_set('co', V.astype(np.float32).ravel()); me.update()
    return int(head.sum())
