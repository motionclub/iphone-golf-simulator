"""Tuning-time fit check on the staged npz parts.  blender -b --factory-startup --python fitcheck.py -- <male|female> [old]
'old' evaluates the START kit shoes/socks (read from the start blend) on the new body = positive control."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from kitlib import *
from checklib import *

args = sys.argv[sys.argv.index('--') + 1:]
gender = args[0]
old = 'old' in args[1:]
BODY = {'male': f'{WORK}/data/body_male_d6c4dcfb.npz', 'female': f'{WORK}/data/body_female_a1d73a33.npz'}
zb = np.load(BODY[gender])
VB, FB = zb['V'], zb['F']
tree_body = bvh(VB, FB)
meas = json.load(open(f'{WORK}/data/foot_measure.json'))[gender]


def load_parts(kind):
    out = {}
    for f in 'RL':
        if old:
            bpy.ops.wm.open_mainfile(filepath=f'{WORK}/start/StandardKit_{"Male" if gender == "male" else "Female"}.blend')
            o = bpy.data.objects[f'Kit_{kind.capitalize()}_{f}_White']
            V, Fq = mesh_arrays(o)
            me = o.data
            tv = np.zeros(len(me.polygons), np.int32)
            me.attributes['kit_tag'].data.foreach_get('value', tv)
            tg = json.loads(me['kit_tagnames'])
            out[f] = dict(V=V, F=Fq, T=tv, tagnames=tg)
        else:
            z = np.load(f'{WORK}/data/{kind}{f}_{gender}.npz')
            out[f] = dict(V=z['V'], F=z['F'], T=z['T'], tagnames=[str(t) for t in z['tagnames']])
    return out


shoes = load_parts('shoe')
socks = load_parts('sock')
rep = dict(gender=gender, old_kit=old)
for side, f in ((+1, 'R'), (-1, 'L')):
    sh, sk = shoes[f], socks[f]
    Vs, Fs, Ts, tg = sh['V'], sh['F'], sh['T'], sh['tagnames']
    tree_sh = bvh(Vs, Fs)
    # collar rim: faces tagged sheet_rim* whose vertices are high
    rim_ids = [i for i, t in enumerate(tg) if t.startswith('sheet_rim')]
    rim_v = []
    for i in rim_ids:
        vi = np.unique(Fs[Ts == i])
        if Vs[vi][:, 2].mean() > 0.02:
            rim_v.append(vi)
    rim_vi = np.concatenate(rim_v)
    rim_z = Vs[rim_vi][:, 2]
    z_rim_min = float(rim_z.min())
    roll_ids = [i for i, t in enumerate(tg) if t == 'collar_roll']
    roll_top = float(Vs[np.unique(Fs[np.isin(Ts, roll_ids)])][:, 2].max()) if roll_ids else None
    # foot vertices below the collar
    leg = (VB[:, 0] * side > 0.02) & (VB[:, 2] < z_rim_min)
    P = VB[leg]
    w = winding_numbers(P, Vs, Fs)
    inside_wall = int((np.abs(w) > 0.5).sum())
    enc = enclosed_mask(P, Vs, Fs, tree_sh, sphere_dirs(16, (-90, -60, -35, -15, 0)), far=1.0)
    outside = ~enc
    dmin = nearest_dist(tree_sh, P)
    sock_leg = (sk['V'][:, 0] * side > 0.02) & (sk['V'][:, 2] < z_rim_min)
    Psk = sk['V'][sock_leg]
    wsk = winding_numbers(Psk, Vs, Fs)
    encs = enclosed_mask(Psk, Vs, Fs, tree_sh, sphere_dirs(12, (-90, -45, -15, 0)), far=1.0)
    # overhangs along the foot axis (this foot's own frame)
    O = np.array(meas['R' if side > 0 else 'L']['frame_origin'])
    phi = math.radians(meas['R' if side > 0 else 'L']['toe_out_deg'])
    ax = np.array([math.sin(phi), -math.cos(phi), 0.0])           # toe direction in body space (toes = -y, turned by the toe-out angle)
    toe = np.array(meas['R' if side > 0 else 'L']['toe_tip_world'])
    heel = np.array(meas['R' if side > 0 else 'L']['heel_point_world'])
    in_ids = [i for i, t in enumerate(tg) if t == 'sheet_in']
    out_ids = [i for i, t in enumerate(tg) if t == 'sheet_out']
    Vin = Vs[np.unique(Fs[np.isin(Ts, in_ids)])]
    Vout = Vs[np.unique(Fs[np.isin(Ts, out_ids + [i for i, t in enumerate(tg) if t == 'sole'])])]
    toe_over_in = float(((Vin - toe) @ ax).max())
    heel_over_in = float((-((Vin - heel) @ ax)).max())
    toe_over_out = float(((Vout - toe) @ ax).max())
    heel_over_out = float((-((Vout - heel) @ ax)).max())
    rep[f] = dict(rim_z_min=round(z_rim_min, 4), rim_z_max=round(float(rim_z.max()), 4), rim_z_mean=round(float(rim_z.mean()), 4), roll_top=roll_top,
                  foot_verts_below_collar=int(leg.sum()), foot_verts_inside_wall=inside_wall, foot_verts_not_enclosed=int(outside.sum()),
                  foot_to_shoe_min_mm=round(float(dmin.min() * 1000), 2),
                  sock_verts_below_collar=int(sock_leg.sum()), sock_verts_inside_wall=int((np.abs(wsk) > 0.5).sum()), sock_verts_not_enclosed=int((~encs).sum()),
                  toe_overhang_inner_mm=round(toe_over_in * 1000, 1), toe_overhang_outer_mm=round(toe_over_out * 1000, 1),
                  heel_overhang_inner_mm=round(heel_over_in * 1000, 1), heel_overhang_outer_mm=round(heel_over_out * 1000, 1),
                  sole_min_z=round(float(Vs[np.unique(Fs[np.isin(Ts, [i for i, t in enumerate(tg) if t == 'sole'])])][:, 2].min()), 5), shoe_min_z=round(float(Vs[:, 2].min()), 5))
    if outside.any():
        rep[f]['outside_examples'] = P[outside][:5].round(4).tolist()
    print(f, json.dumps(rep[f]))
json.dump(rep, open(f'{WORK}/tmp/fitcheck_{gender}{"_old" if old else ""}.json', 'w'), indent=1)
