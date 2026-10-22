"""Fit yaw (and horizontal offset) of the two 3/4 plate panels from the cranium width profile.  blender -b --factory-startup --python calib34.py
Compares plate skin-mask widths per row (apex-aligned) against loft-proxy alpha silhouettes at several camera azimuths."""
import sys, json
import numpy as np
import bpy
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1h')
import h1lib as H, loft as L, proxy as PX

# plate widths (first/last skin col per row) for the two panels, rows 400..464 step 4 (apex row ~397)
PL = {'q3L': {400: (193, 247), 408: (177, 263), 416: (168, 273), 424: (161, 280), 432: (156, 285), 440: (153, 288), 448: (151, 291), 456: (149, 292), 464: (146, 293)},
      'q3R': {400: (602, 655), 408: (587, 671), 416: (578, 681), 424: (571, 688), 432: (567, 693), 440: (563, 697), 448: (561, 699), 456: (559, 701), 464: (556, 702)}}
APEX_ROW = 397.0

V, F = PX.build_proxy(3)
lf = L.Loft()
P, _, _ = L.remap(V, lf)
bpy.ops.wm.read_factory_settings(use_empty=True)
o = H.make_mesh_object('proxy', P, [f for f in F])
H.setup_render()
s = bpy.context.scene
s.render.film_transparent = True; s.render.image_settings.color_mode = 'RGBA'


def render_alpha(az, res=(1200, 1200), scale=0.40, target=(0, -0.04, 1.58)):
    H.shot(H.W / 'r/proxy0/_cal.png', target, az, 0, scale, res)
    img = bpy.data.images.load(str(H.W / 'r/proxy0/_cal.png'), check_existing=False)
    a = np.array(img.pixels[:]).reshape(res[1], res[0], 4)[:, :, 3]
    bpy.data.images.remove(img)
    return a[::-1]            # top row first


def widths(a, scale, res, rows_z):
    """rows_z: z values -> pixel rows; returns (left,right) edge columns in metres from image centre"""
    mpp = scale / res[0]
    out = []
    zc = 1.58
    for z in rows_z:
        r = int(round(res[1] / 2 - (z - zc) / mpp))
        line = a[r] > 0.5
        if line.any():
            xs = np.where(line)[0]; out.append(((xs[0] - res[0] / 2) * mpp, (xs[-1] - res[0] / 2) * mpp))
        else:
            out.append((np.nan, np.nan))
    return np.array(out)


res = (1200, 1200); scale = 0.40
rows = np.array(sorted(PL['q3L'].keys()))
zrows = H.TOP - (rows - APEX_ROW) * H.K
best = {}
for name in ('q3L', 'q3R'):
    pw = np.array([(PL[name][r][1] - PL[name][r][0] + 1) * H.K for r in rows])
    pc = np.array([(PL[name][r][1] + PL[name][r][0]) / 2 * H.K for r in rows])
    res_tab = []
    for az in np.arange(20, 66, 2.5):
        a = render_alpha(az, res, scale)
        w = widths(a, scale, res, zrows)
        mw = w[:, 1] - w[:, 0]
        err = float(np.sqrt(np.nanmean((mw - pw) ** 2)) * 1000)
        res_tab.append((err, float(az), (mw * 1000).round(1).tolist()))
    res_tab.sort()
    print(name, 'plate widths mm', (pw * 1000).round(1).tolist())
    for e, az, mw in res_tab[:4]:
        print(f'   az={az:5.1f}  rms={e:5.2f} mm  mesh widths {mw}')
    best[name] = res_tab[0][1]
print('BEST', best)
