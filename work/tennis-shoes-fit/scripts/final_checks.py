"""Measured gates on the ASSEMBLED output blend.   blender -b --factory-startup --python final_checks.py -- <male|female>
Writes proof/raw/checks_<gender>.json.  Definitions: GATE_DEFS_preregistered.md (written before this run)."""
import sys, os, json, hashlib, math, collections, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from kitlib import *
from checklib import *
from kit_common import mesh_topology

gender = sys.argv[sys.argv.index('--') + 1]
NAME = 'Male' if gender == 'male' else 'Female'
BODY = {'male': (MALE_BODY_BLEND, 'Body_M', MALE_BODY_SHA), 'female': (FEMALE_BODY_BLEND, 'Body_F', FEMALE_BODY_SHA)}[gender]
OUT = f'{WORK}/export/StandardKit_{NAME}.blend'
START = f'{WORK}/start/StandardKit_{NAME}.blend'
SOCK_TOP = {'male': 0.300, 'female': 0.285}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
t0 = time.time()
rep = dict(gender=gender)

# ------------------------------------------------------------------------------------------------ SHAs (before anything is read)
rep['body_sha256_expected'] = BODY[2]
rep['body_sha256_before'] = sha(BODY[0])
assert rep['body_sha256_before'] == BODY[2], 'body SHA mismatch'
rep['start_kit_sha256'] = sha(START)
assert rep['start_kit_sha256'] == START_KIT_SHA[gender], 'start kit SHA mismatch'
rep['output_blend_sha256'] = sha(OUT)


def piece_hash(o):
    me = o.data
    h = hashlib.sha256()
    n = len(me.vertices)
    co = np.empty(n * 3, np.float32)
    me.vertices.foreach_get('co', co)
    h.update(co.tobytes())
    nl = len(me.loops)
    lv = np.empty(nl, np.int32)
    me.loops.foreach_get('vertex_index', lv)
    h.update(lv.tobytes())
    npoly = len(me.polygons)
    ls = np.empty(npoly, np.int32)
    me.polygons.foreach_get('loop_start', ls)
    mi = np.empty(npoly, np.int32)
    me.polygons.foreach_get('material_index', mi)
    h.update(ls.tobytes())
    h.update(mi.tobytes())
    for uv in me.uv_layers:
        a = np.empty(nl * 2, np.float32)
        uv.data.foreach_get('uv', a)
        h.update(a.tobytes())
    try:
        cn = np.empty(nl * 3, np.float32)
        me.corner_normals.foreach_get('vector', cn)
        h.update(cn.tobytes())
    except Exception:
        pass
    if 'kit_tag' in me.attributes:
        tv = np.empty(npoly, np.int32)
        me.attributes['kit_tag'].data.foreach_get('value', tv)
        h.update(tv.tobytes())
    h.update(json.dumps([m.name if m else None for m in me.materials]).encode())
    h.update(np.array(o.matrix_world, np.float64).tobytes())
    h.update(np.array(o.matrix_parent_inverse, np.float64).tobytes())
    h.update((o.parent.name if o.parent else '').encode())
    return h.hexdigest()


def collect_pieces():
    out = {}
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith(('Kit_Top_', 'Kit_Bottom_')):
            out[o.name] = piece_hash(o)
    return out


bpy.ops.wm.open_mainfile(filepath=START)
start_hashes = collect_pieces()
bpy.ops.wm.open_mainfile(filepath=OUT)
out_hashes = collect_pieces()
rep['other_pieces'] = dict(start=start_hashes, output=out_hashes, identical=bool(start_hashes == out_hashes and len(start_hashes) == 4))

# ------------------------------------------------------------------------------------------------ the body (read from the SHA-verified source blend)
with bpy.data.libraries.load(BODY[0], link=False) as (src, dst):
    dst.objects = [BODY[1]]
bo = dst.objects[0]
VB, FB = mesh_arrays(bo)
bpy.data.objects.remove(bo, do_unlink=True)
tree_body = bvh(VB, FB)
fit = [o for o in bpy.data.objects if o.name.startswith('FitRef_Body')]
rep['fitref_objects'] = [o.name for o in fit]
VF, FF = mesh_arrays(fit[0])
rep['fitref_vs_source_body'] = dict(same_vertex_count=bool(len(VF) == len(VB)), max_abs_diff_mm=float(np.abs(VF - VB).max() * 1000) if len(VF) == len(VB) else None,
                                    same_triangles=bool(len(FF) == len(FB) and (FF == FB).all()))

# ------------------------------------------------------------------------------------------------ pieces
def tags_of(o):
    me = o.data
    tv = np.zeros(len(me.polygons), np.int32)
    me.attributes['kit_tag'].data.foreach_get('value', tv)
    return tv, json.loads(me['kit_tagnames'])


P = {}
for cw in ('White', 'Black'):
    for kind in ('Shoe', 'Sock'):
        for f in 'LR':
            o = bpy.data.objects[f'Kit_{kind}_{f}_{cw}']
            V, F = mesh_arrays(o)
            tv, tg = tags_of(o)
            P[(cw, kind, f)] = dict(o=o, V=V, F=F, T=tv, tags=tg)
rep['colourway_geometry_identical'] = bool(all(np.array_equal(P[('White', k, f)]['V'], P[('Black', k, f)]['V']) and np.array_equal(P[('White', k, f)]['F'], P[('Black', k, f)]['F'])
                                               for k in ('Shoe', 'Sock') for f in 'LR'))

# ------------------------------------------------------------------------------------------------ landmarks of each foot (own axis)
def foot_frame(V, side):
    m = (V[:, 0] * side > 0.02) & (V[:, 2] < 0.035)
    Pp = V[m][:, :2]
    c = Pp.mean(0)
    u, s, vt = np.linalg.svd(Pp - c, full_matrices=False)
    ax = vt[0]
    if ax[1] > 0:
        ax = -ax
    return c, ax                                          # footprint centroid, unit toe direction (xy)


land = {}
for f, side in (('R', +1), ('L', -1)):
    c, ax2 = foot_frame(VB, side)
    ax = np.array([ax2[0], ax2[1], 0.0])
    leg = VB[VB[:, 0] * side > 0.02]
    low = leg[leg[:, 2] < 0.06]
    toe = low[np.argmax((low - np.append(c, 0)) @ ax)]
    low2 = leg[leg[:, 2] < 0.12]
    heel = low2[np.argmin((low2 - np.append(c, 0)) @ ax)]
    # ankle: narrowest cross-section area above z 0.07 (slices through the leg of this side)
    from slicer import slice_loops, area
    rows = []
    for z in np.arange(0.07, 0.28, 0.005):
        loops = [Lp for Lp in slice_loops(VB, FB, z) if len(Lp) >= 6 and Lp[:, 0].mean() * side > 0.02]
        if loops:
            rows.append((float(z), float(sum(area(q) for q in loops)), np.concatenate(loops).mean(0)))
    arr = np.array([r[1] for r in rows])
    sm = np.convolve(arr, np.ones(5) / 5, mode='same')
    k = 2 + int(np.argmin(sm[2:-2]))
    # instep junction: lowest z where the dorsal front contour reaches the shin line (y of the front of the leg at the ankle)
    fronts = []
    for z in np.arange(0.03, 0.30, 0.005):
        loops = [Lp for Lp in slice_loops(VB, FB, z) if len(Lp) >= 6 and Lp[:, 0].mean() * side > 0.02]
        if loops:
            Q = np.concatenate(loops)
            fronts.append((float(z), float(((Q - np.append(c, 0)) @ ax).max())))
    fronts = np.array(fronts)
    z_ank = rows[k][0]
    near = (fronts[:, 0] > z_ank - 0.02) & (fronts[:, 0] < z_ank + 0.06)
    shin = float(np.median(fronts[near, 1]))
    ok = np.nonzero((fronts[:, 1] <= shin + 0.004) & (fronts[:, 0] > 0.03))[0]
    z_junction = float(fronts[ok[0], 0]) if len(ok) else None
    dors = leg[(leg[:, 2] < 0.20) & (((leg - np.append(c, 0)) @ ax) > shin + 0.004)]
    instep_high = dors[np.argmax(dors[:, 2])]
    land[f] = dict(axis_xy=ax2.round(5).tolist(), toe_out_deg=round(float(np.degrees(np.arctan2(ax2[0], -ax2[1]))), 2), longest_toe_tip=toe.round(4).tolist(), heel_point=heel.round(4).tolist(),
                   foot_length_mm=round(float((toe - heel) @ ax * 1000), 1), instep_high_point=instep_high.round(4).tolist(), instep_junction_z=z_junction,
                   ankle_z_narrowest=round(float(z_ank), 4), ankle_area_cm2=round(float(rows[k][1] * 1e4), 1), ankle_centre_xy=rows[k][2][:2].round(4).tolist())
    land[f]['_c'] = np.append(c, 0)
    land[f]['_ax'] = ax
rep['foot_landmarks'] = {f: {k: v for k, v in d.items() if not k.startswith('_')} for f, d in land.items()}

# ------------------------------------------------------------------------------------------------ FOOT_INSIDE / TOE / HEEL (White objects; Black geometry verified identical above)
fi = {}
enc_dirs = sphere_dirs(16, (-90, -60, -35, -15, 0))
enc_dirs_s = sphere_dirs(12, (-90, -45, -15, 0))
for f, side in (('R', +1), ('L', -1)):
    sh, sk = P[('White', 'Shoe', f)], P[('White', 'Sock', f)]
    Vs, Fs, Ts, tg = sh['V'], sh['F'], sh['T'], sh['tags']
    tree_sh = bvh(Vs, Fs)
    rim_vi = np.concatenate([np.unique(Fs[Ts == i]) for i, t in enumerate(tg) if t.startswith('sheet_rim') and Vs[np.unique(Fs[Ts == i])][:, 2].mean() > 0.02])
    rim_z = Vs[rim_vi][:, 2]
    z_rim_min = float(rim_z.min())
    roll_vi = np.unique(Fs[np.isin(Ts, [i for i, t in enumerate(tg) if t == 'collar_roll'])])
    leg_mask = (VB[:, 0] * side > 0.02) & (VB[:, 2] < z_rim_min)
    Pf = VB[leg_mask]
    cen = VB[FB].mean(1)
    tri_in = (cen[:, 0] * side > 0.02) & (cen[:, 2] < z_rim_min)
    Pc = cen[tri_in]
    w = winding_numbers(Pf, Vs, Fs)
    wc = winding_numbers(Pc, Vs, Fs)
    enc = enclosed_mask(Pf, Vs, Fs, tree_sh, enc_dirs)
    encc = enclosed_mask(Pc, Vs, Fs, tree_sh, enc_dirs)
    d_v = nearest_dist(tree_sh, Pf)
    d_c = nearest_dist(tree_sh, Pc)
    foot_faces = FB[((np.isin(FB, np.nonzero(leg_mask)[0])).all(1))]
    overlap_pairs = len(tree_sh.overlap(bvh(VB, foot_faces)))
    # every foot / leg vertex up to the HIGHEST collar point: none may sit inside shoe material (a skin vertex inside a wall needs a surface crossing; shoe-vs-body pairs are counted below too)
    up_mask = (VB[:, 0] * side > 0.02) & (VB[:, 2] < float(rim_z.max()))
    w_up = winding_numbers(VB[up_mask], Vs, Fs, chunk=600)
    # sock
    Vk, Fk = sk['V'], sk['F']
    sk_mask = (Vk[:, 0] * side > 0.02) & (Vk[:, 2] < z_rim_min)
    Psk = Vk[sk_mask]
    wk = winding_numbers(Psk, Vs, Fs)
    enck = enclosed_mask(Psk, Vs, Fs, tree_sh, enc_dirs_s)
    sk_out_ids = [i for i, t in enumerate(sk['tags']) if t.endswith('_out')]
    sk_in_ids = [i for i, t in enumerate(sk['tags']) if t.endswith('_in')]
    sk_out_v = Vk[np.unique(Fk[np.isin(sk['T'], sk_out_ids)])]
    sk_in_v = Vk[np.unique(Fk[np.isin(sk['T'], sk_in_ids)])]
    tree_sk = bvh(Vk, Fk)
    d_sock_shoe = nearest_dist(tree_sh, sk_out_v[sk_out_v[:, 2] < z_rim_min])
    d_skin_sockin = signed_dist(tree_body, sk_in_v[(sk_in_v[:, 0] * side > 0.02) & (sk_in_v[:, 2] < SOCK_TOP[gender] - 0.03)])
    # overhangs along this foot's axis
    L = land[f]
    ax, c = L['_ax'], L['_c']
    toe, heel = np.array(L['longest_toe_tip']), np.array(L['heel_point'])
    Vin = Vs[np.unique(Fs[np.isin(Ts, [i for i, t in enumerate(tg) if t == 'sheet_in'])])]
    Vout = Vs[np.unique(Fs[np.isin(Ts, [i for i, t in enumerate(tg) if t in ('sheet_out', 'sole')])])]
    fi[f] = dict(
        collar_rim_z_min=round(z_rim_min, 4), collar_rim_z_mean=round(float(rim_z.mean()), 4), collar_rim_z_max=round(float(rim_z.max()), 4),
        collar_roll_top_z=round(float(Vs[roll_vi][:, 2].max()), 4), collar_height_above_ground_mm=dict(
            min=round((z_rim_min - float(Vs[:, 2].min())) * 1000, 1), mean=round((float(rim_z.mean()) - float(Vs[:, 2].min())) * 1000, 1), max=round((float(rim_z.max()) - float(Vs[:, 2].min())) * 1000, 1)),
        foot_vertices_below_collar=int(leg_mask.sum()), foot_triangle_centroids_below_collar=int(tri_in.sum()),
        foot_verts_up_to_highest_collar_point=int(up_mask.sum()), foot_verts_up_to_highest_collar_point_inside_shoe_material=int((np.abs(w_up) > 0.5).sum()),
        foot_verts_inside_shoe_material=int((np.abs(w) > 0.5).sum()), foot_tri_centroids_inside_shoe_material=int((np.abs(wc) > 0.5).sum()),
        foot_verts_not_enclosed=int((~enc).sum()), foot_tri_centroids_not_enclosed=int((~encc).sum()),
        foot_verts_outside_shoe=int(((np.abs(w) > 0.5) | (~enc)).sum() + ((np.abs(wc) > 0.5) | (~encc)).sum()),
        foot_to_shoe_min_mm=round(float(min(d_v.min(), d_c.min()) * 1000), 2), foot_to_shoe_p05_mm=round(float(np.percentile(np.concatenate([d_v, d_c]), 5) * 1000), 2),
        foot_shoe_triangle_overlap_pairs=int(overlap_pairs),
        sock_vertices_below_collar=int(sk_mask.sum()), sock_verts_inside_shoe_material=int((np.abs(wk) > 0.5).sum()), sock_verts_not_enclosed=int((~enck).sum()),
        sock_outer_to_shoe_min_mm=round(float(d_sock_shoe.min() * 1000), 2),
        sock_inner_to_skin_min_mm=round(float(d_skin_sockin.min() * 1000), 2),
        toe_overhang_inner_mm=round(float(((Vin - toe) @ ax).max() * 1000), 1), toe_overhang_outer_mm=round(float(((Vout - toe) @ ax).max() * 1000), 1),
        heel_overhang_inner_mm=round(float((-((Vin - heel) @ ax)).max() * 1000), 1), heel_overhang_outer_mm=round(float((-((Vout - heel) @ ax)).max() * 1000), 1),
        shoe_min_z=round(float(Vs[:, 2].min()), 5))
    if fi[f]['foot_verts_outside_shoe']:
        fi[f]['outside_examples'] = Pf[(np.abs(w) > 0.5) | (~enc)][:5].round(4).tolist()
rep['foot_inside'] = fi
# ---- layer-vs-layer intersections: sock vs shoe, shoe vs body, left vs right shoe, shoe vertices inside sock material
ov = {}
for f in 'LR':
    sh, sk = P[('White', 'Shoe', f)], P[('White', 'Sock', f)]
    tsh, tsk = bvh(sh['V'], sh['F']), bvh(sk['V'], sk['F'])
    near = sh['V'][sh['V'][:, 2] < 0.2]
    wsk = winding_numbers(near, sk['V'], sk['F'], chunk=300)
    ov[f] = dict(sock_vs_shoe_triangle_pairs=int(len(tsh.overlap(tsk))), shoe_vs_body_triangle_pairs=int(len(tsh.overlap(tree_body))), sock_vs_body_triangle_pairs=int(len(tsk.overlap(tree_body))),
                 shoe_vertices_inside_sock_material=int((np.abs(wsk) > 0.5).sum()))
ov['L_vs_R_shoe_triangle_pairs'] = int(len(bvh(P[('White', 'Shoe', 'L')]['V'], P[('White', 'Shoe', 'L')]['F']).overlap(bvh(P[('White', 'Shoe', 'R')]['V'], P[('White', 'Shoe', 'R')]['F']))))
rep['layer_overlaps'] = ov
print('foot_inside done', round(time.time() - t0, 1), 's', flush=True)

# ------------------------------------------------------------------------------------------------ NO_SKIN_GAP: camera-ray visibility of the skin below the sock top
occV = np.concatenate([P[('White', k, f)]['V'] for k in ('Shoe', 'Sock') for f in 'LR'])
offs = np.cumsum([0] + [len(P[('White', k, f)]['V']) for k in ('Shoe', 'Sock') for f in 'LR'])
occF = np.concatenate([P[('White', k, f)]['F'] + offs[i] for i, (k, f) in enumerate([(k, f) for k in ('Shoe', 'Sock') for f in 'LR'])])
tree_occ = bvh(occV, occF, eps=2e-4)
zlim = SOCK_TOP[gender] - 0.030                  # below the cuff band (the open top edge of the sock is reported separately)
zlim_cuff = SOCK_TOP[gender] - 0.004
exp_all = []
tested_all = 0
samples_all = 0
for f, side in (('R', +1), ('L', -1)):
    S, N = skin_samples(VB, FB, side, zlim)
    samples_all += len(S)
    ex, tested = exposed_skin(S, N, occV, occF, tree_occ, tree_body, VB)
    tested_all += tested
    for s_, e_, a_, nd_ in ex:
        exp_all.append(dict(foot=f, p=s_, el=e_, az=a_, n_dot_view=nd_))
# informational: the cuff band itself (the open end of the sock seen from above)
cuff_exposed = 0
cuff_tested = 0
for f, side in (('R', +1), ('L', -1)):
    S, N = skin_samples(VB, FB, side, zlim_cuff, zmin=zlim)
    ex_c, t_c = exposed_skin(S, N, occV, occF, tree_occ, tree_body, VB)
    cuff_exposed += len(ex_c)
    cuff_tested += t_c
rep['skin_visibility_cuff_band'] = dict(z_range=[round(zlim, 4), round(zlim_cuff, 4)], ray_tests=cuff_tested, exposed=cuff_exposed,
                                        note='skin inside the open top end of the sock seen from above through the 3-4 mm gap between leg and cuff (not an ankle band)')
sect = collections.Counter()
for e in exp_all:
    # azimuth convention of view_dirs: camera direction d = (sin a, -cos a): a = 0 is the camera in FRONT (-y)
    sect['front' if (e['az'] < 60 or e['az'] > 300) else 'rear' if 120 < e['az'] < 240 else 'side'] += 1
exz = np.array([e['p'][2] for e in exp_all]) if exp_all else np.zeros(0)
exn = np.array([e['n_dot_view'] for e in exp_all]) if exp_all else np.zeros(0)
json.dump(exp_all, open(f'{WORK}/proof/raw/exposed_{gender}.json', 'w'))
rep['skin_visibility_stats'] = dict(exposed=len(exp_all), z_min=round(float(exz.min()), 4) if len(exz) else None, z_max=round(float(exz.max()), 4) if len(exz) else None,
                                   depth_below_sock_top_mm=[round((float(P[('White', 'Sock', 'R')]['V'][:, 2].max()) - float(exz.max())) * 1000, 1), round((float(P[('White', 'Sock', 'R')]['V'][:, 2].max()) - float(exz.min())) * 1000, 1)] if len(exz) else None,
                                   n_dot_view_min=float(exn.min()) if len(exn) else None, n_dot_view_max=float(exn.max()) if len(exn) else None,
                                   elevations=dict(collections.Counter(e['el'] for e in exp_all)))
rep['skin_visibility'] = dict(skin_samples=samples_all, ray_tests=tested_all, z_max=round(zlim, 4), elevations_deg=[-10, 0, 10, 25, 45], azimuth_step_deg=15, beam='1 mm (5 rays), exact ray-triangle confirmation',
                              exposed=len(exp_all), exposed_by_sector=dict(sect), examples=exp_all[:8])
print('skin visibility done', round(time.time() - t0, 1), 's', len(exp_all), 'exposed of', tested_all, flush=True)

# sock-to-collar overlap
sock_over = {}
for f, side in (('R', +1), ('L', -1)):
    sk = P[('White', 'Sock', f)]
    sh = P[('White', 'Shoe', f)]
    top = float(sk['V'][:, 2].max())
    floor = float(sk['V'][:, 2].min())
    rim_vi = np.concatenate([np.unique(sh['F'][sh['T'] == i]) for i, t in enumerate(sh['tags']) if t.startswith('sheet_rim') and sh['V'][np.unique(sh['F'][sh['T'] == i])][:, 2].mean() > 0.02])
    rz = sh['V'][rim_vi][:, 2]
    sock_over[f] = dict(sock_top_z=round(top, 4), sock_lowest_z=round(floor, 4), sock_top_above_rim_mm=dict(min=round((top - float(rz.max())) * 1000, 1), at_lowest_rim=round((top - float(rz.min())) * 1000, 1)),
                        sock_below_rim_mm=dict(min=round((float(rz.min()) - floor) * 1000, 1)))
    sock_over[f]['overlap_mm_min'] = round(min(sock_over[f]['sock_top_above_rim_mm']['min'], sock_over[f]['sock_below_rim_mm']['min']), 1)
rep['sock_collar_overlap'] = sock_over

# ------------------------------------------------------------------------------------------------ SOLE_GROUNDED + MIRROR
sg = {}
for cw in ('White', 'Black'):
    for f in 'LR':
        sh = P[(cw, 'Shoe', f)]
        sole_v = sh['V'][np.unique(sh['F'][np.isin(sh['T'], [i for i, t in enumerate(sh['tags']) if t == 'sole'])])]
        tread_v = sh['V'][np.unique(sh['F'][np.isin(sh['T'], [i for i, t in enumerate(sh['tags']) if t == 'tread'])])]
        sg[f'{cw}_{f}'] = dict(sole_bottom_z=round(float(sole_v[:, 2].min()), 6), tread_bottom_z=round(float(tread_v[:, 2].min()), 6), shoe_min_z=round(float(sh['V'][:, 2].min()), 6),
                               sole_flat_z_p01=round(float(np.percentile(sole_v[:, 2], 1)), 5))
rep['sole'] = sg
sw, sb = P[('White', 'Shoe', 'R')], P[('White', 'Shoe', 'L')]
VRm = sw['V'] * np.array([-1, 1, 1])
tL = bvh(sb['V'], sb['F'])
tRm = bvh(VRm, sw['F'][:, [0, 2, 1]])
d1 = nearest_dist(tL, VRm)
d2 = nearest_dist(tRm, sb['V'])
shift = sb['V'].mean(0) - sw['V'].mean(0)
tRt = bvh(sw['V'] + shift, sw['F'])
d3 = np.maximum(nearest_dist(tRt, sb['V']).max(), nearest_dist(bvh(sb['V'], sb['F']), sw['V'] + shift).max())


def signed_volume(V, F):
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    return float(np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6.0)


rep['mirror'] = dict(hausdorff_mirror_R_to_L_mm=round(float(max(d1.max(), d2.max()) * 1000), 5), hausdorff_translated_copy_mm=round(float(d3 * 1000), 2),
                     signed_volume_R_cm3=round(signed_volume(sw['V'], sw['F']) * 1e6, 2), signed_volume_L_cm3=round(signed_volume(sb['V'], sb['F']) * 1e6, 2),
                     length_R_mm=round(float((sw['V'][:, 1].max() - sw['V'][:, 1].min()) * 1000), 2), length_L_mm=round(float((sb['V'][:, 1].max() - sb['V'][:, 1].min()) * 1000), 2),
                     sole_height_R_mm=round(float(-sg['White_R']['sole_bottom_z'] * 1000), 2), sole_height_L_mm=round(float(-sg['White_L']['sole_bottom_z'] * 1000), 2),
                     tris_R=int(len(sw['F'])), tris_L=int(len(sb['F'])), shoe_x_centroid_R=round(float(sw['V'][:, 0].mean()), 4), shoe_x_centroid_L=round(float(sb['V'][:, 0].mean()), 4))

# ------------------------------------------------------------------------------------------------ sockets / parenting / transforms / names
soc = {}
for cw in ('White', 'Black'):
    for kind in ('Shoe', 'Sock'):
        for f in 'LR':
            o = bpy.data.objects[f'Kit_{kind}_{f}_{cw}']
            want = f'Foot_{f}_Shoe_{cw}'
            soc[o.name] = dict(parent=o.parent.name if o.parent else None, parent_ok=bool(o.parent is not None and o.parent.name == want and o.parent.get('socket_name') == f'Foot_{f}_Shoe'),
                               mesh_world_identity=bool(np.allclose(np.array(o.matrix_world), np.eye(4), atol=1e-9)), local_identity=bool(np.allclose(np.array(o.matrix_basis), np.eye(4), atol=1e-9)),
                               materials=[m.name for m in o.data.materials], closed=bool(mesh_topology(*mesh_arrays(o))['boundary_edges'] == 0), modifiers=len(o.modifiers))
for cw in ('White', 'Black'):
    for f in 'LR':
        e = bpy.data.objects[f'Foot_{f}_Shoe_{cw}']
        soc[e.name] = dict(type=e.type, world_identity=bool(np.allclose(np.array(e.matrix_world), np.eye(4), atol=1e-9)), socket_name=e.get('socket_name'), parent=e.parent.name if e.parent else None)
rep['sockets'] = soc
rep['armature_objects'] = [o.name for o in bpy.data.objects if o.type == 'ARMATURE']

# ------------------------------------------------------------------------------------------------ names (no ArmsCand anywhere), materials, logos
names = [o.name for o in bpy.data.objects] + [m.name for m in bpy.data.meshes] + [m.name for m in bpy.data.materials] + [c.name for c in bpy.data.collections]
rep['arms_cand_names'] = [n for n in names if 'armscand' in n.lower() or 'arms_cand' in n.lower() or 'arms cand' in n.lower()]
rep['materials_in_blend'] = sorted(m.name for m in bpy.data.materials)
rep['images_in_blend'] = [i.name for i in bpy.data.images if i.name not in ('Render Result', 'Viewer Node')]
rep['text_objects'] = [o.name for o in bpy.data.objects if o.type == 'FONT']
rep['tag_vocabulary_shoe'] = sorted(P[('White', 'Shoe', 'R')]['tags'])
rep['piece_tris'] = {k[0] + '_' + k[1] + '_' + k[2]: int(len(v['F'])) for k, v in P.items() if k[0] == 'White'}
rep['topology'] = {f'{k[1]}_{k[2]}': mesh_topology(v['V'], v['F']) for k, v in P.items() if k[0] == 'White'}
rep['body_sha256_after'] = sha(BODY[0])
rep['start_kit_sha256_after'] = sha(START)
rep['elapsed_s'] = round(time.time() - t0, 1)
os.makedirs(f'{WORK}/proof/raw', exist_ok=True)
json.dump(rep, open(f'{WORK}/proof/raw/checks_{gender}.json', 'w'), indent=1)
print('checks written', rep['elapsed_s'], 's')
